from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
import docx
import requests
import io
import os
import logging
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DocSummary")

# 初始化 FastAPI 应用 给后端服务 “起名字、定版本”，是 FastAPI 应用的入口
app = FastAPI(title="文档解析总结工具", version="1.0")

# 解决跨域问题 前端从 5173 域请求后端 8000 域的接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],#允许「所有域」的前端访问当前后端接口
    allow_credentials=True,
    allow_methods=["*"],#允许「所有域」的前端访问当前后端接口（POST）
    allow_headers=["*"],#允许前端请求头中携带任意信息
)

# Ollama 配置（Windows 本地默认地址）1提供的生成文本的 API 地址 2模型名字
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen:7b-chat")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "12000"))
SUMMARY_NUM_PREDICT = int(os.getenv("SUMMARY_NUM_PREDICT", "500"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))

_session = requests.Session()
_retry = Retry(
    total=2,
    connect=2,
    read=2,
    status=2,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"],
)
_adapter = HTTPAdapter(max_retries=_retry, pool_connections=10, pool_maxsize=10)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)

# 读取Word文档内容（适配Windows编码）
def read_word_file(content: bytes, filename: str) -> str:
    logger.info(f"开始解析Word文档: {filename}")
    try:
        # 读取上传的文件流，指定编码兼容Windows
        file_content = io.BytesIO(content)#python-docx 库只能解析文件对象
        doc = docx.Document(file_content)#用 python-docx 打开内存中的 Word 文档
        # 拼接所有段落文本，过滤空行，空格，空段
        full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
        if not full_text:
            logger.warning(f"文档 {filename} 无有效文本内容")
            raise HTTPException(status_code=400, detail="Word文档无有效文本内容")#请求参数错误
        logger.info(f"文档解析成功，提取字符数: {len(full_text)}")
        return full_text
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析Word文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析Word失败：{str(e)}")#服务器内部错误

# 调用Ollama的qwen3模型生成总结
def summarize_text(text: str) -> str:
    logger.info("开始调用 Ollama 进行总结...")
    if len(text) > MAX_PROMPT_CHARS:
        text = text[:MAX_PROMPT_CHARS]
    # 优化提示词，适配qwen3的中文处理
    prompt = f"""请用简洁、清晰的中文总结以下Word文档的核心内容，覆盖主要信息点：
    {text}
    总结要求：
    1. 不超过300字
    2. 逻辑清晰，分点（可选）
    3. 无冗余信息
    """
    
    try:
        start_time = time.perf_counter()
        response = _session.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,#关闭流式输出（流式输出是逐字返回，这里需要一次性返回完整总结）；
                "options": {
                    "temperature": OLLAMA_TEMPERATURE,
                    "num_predict": SUMMARY_NUM_PREDICT,
                },
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,  # Windows下适当延长超时时间
            headers={"Content-Type": "application/json; charset=utf-8"}  # 强制UTF-8编码
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(status_code=502, detail=f"Ollama返回错误：{result.get('error')}")
        summary = (result.get("response") or "").strip() if isinstance(result, dict) else ""
        if not summary:
            raise HTTPException(status_code=502, detail="Ollama未返回总结内容")
        logger.info(
            f"Ollama 调用成功，总结长度: {len(summary)}，耗时: {time.perf_counter() - start_time:.2f}s"
        )
        return summary
    except requests.exceptions.ConnectionError:
        logger.error("无法连接本地Ollama服务")
        # 提示Windows特有的Ollama启动方式
        raise HTTPException(status_code=503, detail="无法连接本地Ollama服务！请检查：1. Ollama已启动（可在任务管理器查看ollama进程）；2. 端口11434未被占用；3. 执行ollama serve启动服务")
    except requests.exceptions.Timeout:
        logger.error("Ollama调用超时")
        raise HTTPException(status_code=504, detail="Ollama调用超时，请稍后重试或缩短文档内容")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"总结生成过程出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"总结生成失败：{str(e)}")

# 文档总结接口（核心接口）
@app.post("/summarize-word", summary="上传Word文档并生成总结")#post接口，提交数据
async def summarize_word(file: UploadFile = File(...)):
    logger.info(f"收到 /summarize-word 请求, 文件名: {file.filename}")
    # 校验文件类型（小写）
    filename = (file.filename or "").lower()
    if filename.endswith(".doc"):
        logger.warning(f"文件格式不支持: {filename}")
        raise HTTPException(status_code=400, detail="暂不支持.doc格式，请另存为.docx后再上传")
    if not filename.endswith(".docx"):
        logger.warning(f"文件格式不支持: {filename}")
        raise HTTPException(status_code=400, detail="仅支持.docx格式的Word文档")

    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="文件过大，请上传不超过10MB的Word文档")

        # 1. 解析Word内容
        text = await run_in_threadpool(read_word_file, content, file.filename)
        # 2. 调用模型生成总结
        summary = await run_in_threadpool(summarize_text, text)
    finally:
        await file.close()
    # 3. 返回结果
    logger.info("请求处理完成，准备返回结果")
    return {
        "code": 200,
        "message": "总结成功",
        "data": {
            "original_text": text[:500] + "..." if len(text) > 500 else text,
            "summary": summary
        }
    }

# 健康检查接口
@app.get("/health", summary="健康检查")
async def health_check():
    return {"status": "ok", "message": "后端服务正常运行（Windows），Ollama模型：" + MODEL_NAME}

# 启动服务（Windows下指定编码为UTF-8）
if __name__ == "__main__":
    import uvicorn#astAPI 的官方服务器，FastAPI 本身是框架，需要 Uvicorn 作为运行时
    os.system("chcp 65001")#将控制台编码设置为 UTF-8
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

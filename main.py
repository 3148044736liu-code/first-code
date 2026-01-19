from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import docx
import requests
from pydantic import BaseModel
import io
import os

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
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen:7b-chat" 

# 读取Word文档内容（适配Windows编码）
def read_word_file(file: UploadFile) -> str:
    try:
        # 读取上传的文件流，指定编码兼容Windows
        file_content = io.BytesIO(file.file.read())#python-docx 库只能解析文件对象
        doc = docx.Document(file_content)#用 python-docx 打开内存中的 Word 文档
        # 拼接所有段落文本，过滤空行，空格，空段
        full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
        if not full_text:
            raise HTTPException(status_code=400, detail="Word文档无有效文本内容")#请求参数错误
        return full_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析Word失败：{str(e)}")#服务器内部错误

# 调用Ollama的qwen3模型生成总结
def summarize_text(text: str) -> str:
    # 优化提示词，适配qwen3的中文处理
    prompt = f"""请用简洁、清晰的中文总结以下Word文档的核心内容，覆盖主要信息点：
    {text}
    总结要求：
    1. 不超过300字
    2. 逻辑清晰，分点（可选）
    3. 无冗余信息
    """
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,#关闭流式输出（流式输出是逐字返回，这里需要一次性返回完整总结）；
                "temperature": 0.2,#值越低，模型输出越稳定、越保守；值越高越随机
                "max_tokens": 500  # 限制总结长度
            },
            timeout=120,  # Windows下适当延长超时时间
            headers={"Content-Type": "application/json; charset=utf-8"}  # 强制UTF-8编码
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "总结生成失败")
    except requests.exceptions.ConnectionError:
        # 提示Windows特有的Ollama启动方式
        raise HTTPException(status_code=503, detail="无法连接本地Ollama服务！请检查：1. Ollama已启动（可在任务管理器查看ollama进程）；2. 端口11434未被占用；3. 执行ollama serve启动服务")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"总结生成失败：{str(e)}")

# 文档总结接口（核心接口）
@app.post("/summarize-word", summary="上传Word文档并生成总结")#post接口，提交数据
async def summarize_word(file: UploadFile = File(...)):
    # 校验文件类型（小写）
    filename = file.filename.lower()
    if not filename.endswith((".docx", ".doc")):
        raise HTTPException(status_code=400, detail="仅支持.docx/.doc格式的Word文档")
    
    # 1. 解析Word内容
    text = read_word_file(file)
    # 2. 调用模型生成总结
    summary = summarize_text(text)
    # 3. 返回结果
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
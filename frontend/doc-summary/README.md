# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

npm create vite@latest doc-summary -- --template vue #创建package.json及初始化环境

main.py的作用：
提供 HTTP 接口，接收前端上传的 Word 文档（.docx/.doc）；
解析 Word 文档中的文本内容；
调用本地 Ollama 服务的 qwen:7b-chat 模型，生成文档内容总结；
返回解析后的原文预览和模型生成的总结结果给前端；
解决跨域、Windows 编码、超时等适配问题，保证服务稳定运行。

整体部署流程
**阶段 1：基础环境准备（前置依赖）**
安装 Python（3.9+ 版本）
安装 Node.js（含 npm）
安装 Ollama（本地 AI 模型服务）
**阶段 2：AI 模型部署（Ollama 拉取模型）**
拉取通义千问对话模型：ollama pull qwen:7b-chat
**阶段 3后端服务部署（FastAPI）:**
创建后端目录 & 编写代码
新建目录 D:\ZhiHai，在该目录下创建 main.py，粘贴咱们的 FastAPI 代码（确保 MODEL_NAME = "qwen:7b-chat"）
安装后端依赖:python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn python-docx requests pydantic python-multipart
启动后端服务:python main.py
**阶段 4前端服务部署**（Vue + Vite）:
#创建前端目录并初始化项目:
mkdir D:\ZhiHai\frontend && cd D:\ZhiHai\frontend
npm create vite@latest doc-summary -- --template vue
cd doc-summary
安装前端依赖:
npm install
npm install axios element-plus
启动前端服务:npm run dev
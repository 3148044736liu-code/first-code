<template>
  <div class="app-container">
    <div class="background-text">ZhiHai</div>
    <div class="main-content">
      <!-- 头部区域 -->
      <div class="header-section">
        <div class="logo-container">
          <el-icon class="logo-icon" :size="40" color="#fff"><Document /></el-icon>
          <h1 class="app-title">Word文档一键总结工具</h1>
        </div>
        <p class="app-subtitle">基于 AI 大模型的智能文档分析助手，快速提取核心内容</p>
      </div>

      <!-- 上传区域 -->
      <el-card class="upload-card" shadow="hover">
        <el-upload
          class="upload-demo"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          accept=".docx,.doc"
          :limit="1"
          :on-exceed="handleExceed"
        >
          <div class="upload-icon" aria-hidden="true">
            <svg viewBox="0 0 48 48" width="48" height="48" focusable="false">
              <path
                class="upload-icon__bg"
                d="M24 46c12.15 0 22-9.85 22-22S36.15 2 24 2 2 11.85 2 24s9.85 22 22 22Z"
              />
              <path
                class="upload-icon__doc"
                d="M18 14h10l5 5v15a3 3 0 0 1-3 3H18a3 3 0 0 1-3-3V17a3 3 0 0 1 3-3Z"
              />
              <path class="upload-icon__fold" d="M28 14v6h6" />
              <path class="upload-icon__arrow" d="M24 32V22" />
              <path class="upload-icon__arrow" d="M20.5 25.5 24 22l3.5 3.5" />
            </svg>
          </div>
          <div class="el-upload__text">
            将 Word 文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .docx / .doc 格式，文件大小不超过 10MB
            </div>
          </template>
        </el-upload>

        <div class="action-area">
          <el-button 
            type="primary" 
            size="large"
            @click="summarize" 
            :loading="loading"
            :disabled="!fileList.length"
            class="submit-btn"
            round
          >
            {{ loading ? '正在智能分析中...' : '开始一键总结' }}
          </el-button>
        </div>
      </el-card>

      <!-- 总结结果展示 -->
      <transition name="el-fade-in-linear">
        <div v-if="summaryResult" class="result-section">
          <el-card class="result-card" shadow="always">
            <template #header>
              <div class="card-header">
                <span class="header-title">
                  <el-icon><Connection /></el-icon> 分析结果
                </span>
                <el-tag type="success" effect="dark">分析完成</el-tag>
              </div>
            </template>
            
            <div class="result-content">
              <div class="result-block">
                <h3 class="block-title">原文预览</h3>
                <div class="text-box original-text">
                  {{ summaryResult.original_text }}
                </div>
              </div>
              
              <div class="result-block">
                <h3 class="block-title highlight">核心总结</h3>
                <div class="text-box summary-text">
                  {{ summaryResult.summary }}
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Document, Connection } from '@element-plus/icons-vue';
import axios from 'axios';

// 状态管理
const fileList = ref([]); // 上传的文件列表
const loading = ref(false); // 加载状态
const summaryResult = ref(null); // 总结结果

// 后端接口地址（后端运行在localhost:8000）
const API_BASE_URL = "http://localhost:8000";

// 监听文件选择
const handleFileChange = (file) => {
  fileList.value = [file]; // 只保留最新选择的文件
  summaryResult.value = null; // 清空旧结果
};

// 文件超出限制
const handleExceed = (files) => {
  fileList.value = [files[0]];
  summaryResult.value = null;
  ElMessage.info('已替换为最新选择的文件');
};

// 提交总结请求
const summarize = async () => {
  if (!fileList.value.length) {
    ElMessage.warning("请先选择Word文件");
    return;
  }

  const file = fileList.value[0].raw;
  const formData = new FormData();
  formData.append("file", file);

  loading.value = true;
  summaryResult.value = null;
  
  try {
    // 调用后端总结接口
    const response = await axios.post(
      `${API_BASE_URL}/summarize-word`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 120000, // 延长超时时间到120秒
      }
    );

    if (response.data.code === 200) {
      summaryResult.value = response.data.data;
      ElMessage.success("总结生成成功！");
    } else {
      ElMessage.error(response.data.message || "总结失败");
    }
  } catch (error) {
    const errMsg = error.response?.data?.detail || "服务器连接失败，请检查后端服务是否启动";
    ElMessage.error(errMsg);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  /* 蓝色渐变背景 */
  background: linear-gradient(135deg, #1c92d2 0%, #f2fcfe 100%);
  padding: 40px 20px;
  box-sizing: border-box;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  position: relative;
  overflow: hidden;
}

/* ZhiHai 艺术字背景 */
.background-text {
  position: fixed;
  right: 2%;
  bottom: 0;
  transform: translateY(10%);
  font-size: 25vh;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.3);
  white-space: nowrap;
  pointer-events: none;
  z-index: 0;
  font-family: 'Arial Black', sans-serif;
  letter-spacing: 10px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  line-height: 1;
}

.main-content {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.header-section {
  text-align: center;
  margin-bottom: 40px;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.app-title {
  font-size: 2.5rem;
  color: #fff;
  margin: 0;
  font-weight: 600;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
  margin: 0;
  font-weight: 300;
}

.upload-card {
  border-radius: 16px;
  border: none;
  margin-bottom: 30px;
  transition: transform 0.3s, box-shadow 0.3s;
  background: transparent;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
}

.upload-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(31, 38, 135, 0.2);
}

.upload-demo {
  text-align: center;
}

.upload-card :deep(.el-card__body) {
  background-color: transparent;
}

.upload-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto;
  transform: translateZ(0);
  transition: transform 180ms ease, filter 180ms ease;
}

.upload-icon svg {
  display: block;
  width: 48px;
  height: 48px;
}

.upload-icon__bg {
  fill: rgba(64, 158, 255, 0.95);
}

.upload-icon__doc,
.upload-icon__fold,
.upload-icon__arrow {
  fill: none;
  stroke: rgba(255, 255, 255, 0.96);
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.upload-icon__arrow {
  transition: transform 180ms ease;
  transform-origin: 24px 24px;
}

.upload-demo:hover .upload-icon {
  transform: translateY(-2px) scale(1.06);
  filter: drop-shadow(0 10px 18px rgba(31, 38, 135, 0.25));
}

.upload-demo:hover .upload-icon__arrow {
  transform: translateY(-1.5px);
}

.upload-demo:active .upload-icon {
  transform: translateY(0) scale(0.98);
  filter: drop-shadow(0 6px 10px rgba(31, 38, 135, 0.18));
}

.upload-demo:active .upload-icon__arrow {
  transform: translateY(0);
}

:deep(.el-upload--text.is-drag:focus-visible) .upload-icon {
  filter: drop-shadow(0 0 0 rgba(0, 0, 0, 0));
}

:deep(.el-upload--text.is-drag:focus-visible) .el-upload-dragger {
  outline: 3px solid rgba(64, 158, 255, 0.9);
  outline-offset: 4px;
}

@media (prefers-color-scheme: dark) {
  .upload-icon__bg {
    fill: rgba(32, 160, 255, 0.92);
  }

  .upload-icon__doc,
  .upload-icon__fold,
  .upload-icon__arrow {
    stroke: rgba(255, 255, 255, 0.98);
  }

  :deep(.el-upload--text.is-drag:focus-visible) .el-upload-dragger {
    outline-color: rgba(32, 160, 255, 0.92);
  }
}

.el-upload__text {
  font-size: 16px;
  margin-top: 10px;
}

.el-upload__text em {
  color: #409EFF;
  font-weight: bold;
}

.el-upload__tip {
  color: #909399;
  margin-top: 10px;
}

.action-area {
  margin-top: 25px;
  text-align: center;
}

.submit-btn {
  width: 220px;
  font-weight: bold;
  letter-spacing: 1px;
  font-size: 16px;
  background: linear-gradient(90deg, #409EFF 0%, #3a8ee6 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.4);
  transition: all 0.3s;
}

.submit-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.5);
}

.submit-btn:active {
  transform: scale(0.98);
}

.result-card {
  border-radius: 16px;
  border: none;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.block-title {
  font-size: 16px;
  color: #606266;
  margin-bottom: 12px;
  margin-top: 0;
  border-left: 4px solid #dcdfe6;
  padding-left: 10px;
}

.block-title.highlight {
  border-left-color: #409EFF;
  color: #303133;
  font-weight: bold;
}

.text-box {
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  font-size: 14px;
  border: 1px solid #ebeef5;
}

.summary-text {
  background-color: #ecf5ff;
  border-color: #d9ecff;
  color: #409EFF;
  font-size: 15px;
}

/* 覆盖 Element Plus 默认样式 */
:deep(.el-upload-dragger) {
  border-radius: 12px;
  border: 2px dashed #dcdfe6;
  background-color: #fafafa;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409EFF;
  background-color: #ecf5ff;
}

:deep(.el-card__header) {
  padding: 18px 24px;
  background-color: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid #ebeef5;
}
</style>

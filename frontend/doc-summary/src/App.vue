<template>
  <div class="word-summary-container">
    <el-page-header content="Word文档一键总结工具"></el-page-header>
    <el-card class="upload-card">
      <el-upload
        class="upload-demo"
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".docx,.doc"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">
          将Word文件拖到此处，或<em>点击上传</em>
        </div>
        <div class="el-upload__tip" slot="tip">
          仅支持.docx/.doc格式，文件大小不超过10MB
        </div>
      </el-upload>

      <el-button 
        type="primary" 
        @click="summarize" 
        :disabled="!fileList.length || loading"
        style="margin-top: 20px;"
      >
        <el-icon v-if="loading"><loading /></el-icon>
        一键总结
      </el-button>
    </el-card>

    <!-- 总结结果展示 -->
    <el-card class="result-card" v-if="summaryResult">
      <template #header>
        <div class="card-header">
          <span>总结结果</span>
        </div>
      </template>
      <el-divider content-position="left">原文预览</el-divider>
      <el-input
        type="textarea"
        :value="summaryResult.original_text"
        readonly
        :rows="8"
        placeholder="暂无原文"
      ></el-input>
      <el-divider content-position="left">核心总结</el-divider>
      <el-input
        type="textarea"
        :value="summaryResult.summary"
        readonly
        :rows="6"
        placeholder="暂无总结"
      ></el-input>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
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
  try {
    // 调用后端总结接口
    const response = await axios.post(
      `${API_BASE_URL}/summarize-word`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 60000, // 超时60秒
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
.word-summary-container {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 20px;
}

.upload-card {
  margin-bottom: 20px;
  padding: 20px;
}

.result-card {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
<template>
  <div class="home-container">
    <div class="hero-section">
      <h2>欢迎使用中文文本阅读障碍辅助工具</h2>
      <p>我们提供多种阅读辅助功能，帮助有阅读障碍的用户更轻松地阅读和理解中文文本。</p>
      <div class="action-buttons">
        <el-button type="primary" @click="navigateToEditor">开始编辑</el-button>
        <el-button @click="navigateToReader">打开阅读器</el-button>
      </div>
    </div>
    
    <div class="features-section">
      <h3>核心功能</h3>
      <div class="features-grid">
        <div class="feature-card">
          <el-icon class="feature-icon"><Document /></el-icon>
          <h4>文本编辑</h4>
          <p>支持文本输入、导入和编辑，为后续处理做准备。</p>
        </div>
        <div class="feature-card">
          <el-icon class="feature-icon"><Reading /></el-icon>
          <h4>意群划分</h4>
          <p>将文本划分为合理的意群，帮助用户更好地理解文本结构。</p>
        </div>
        <div class="feature-card">
          <el-icon class="feature-icon"><Star /></el-icon>
          <h4>主次内容区分</h4>
          <p>识别文本中的重要内容，突出显示，提高阅读效率。</p>
        </div>
        <div class="feature-card">
          <el-icon class="feature-icon"><Translate /></el-icon>
          <h4>文本简化</h4>
          <p>将复杂文本简化为更易理解的形式，适合阅读障碍用户。</p>
        </div>
        <div class="feature-card">
          <el-icon class="feature-icon"><InfoFilled /></el-icon>
          <h4>词语释义</h4>
          <p>提供词语的详细释义，帮助用户理解生僻词汇。</p>
        </div>
        <div class="feature-card">
          <el-icon class="feature-icon"><Mics /></el-icon>
          <h4>文本转语音</h4>
          <p>将文本转换为语音，支持语音朗读，减轻阅读负担。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Document, Reading, Star, Translate, InfoFilled, Mics } from '@element-plus/icons-vue'

const router = useRouter()

const navigateToEditor = () => {
  router.push('/editor')
}

const navigateToReader = () => {
  router.push('/reader')
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  padding: 4rem 2rem;
  background: linear-gradient(135deg, #409EFF 0%, #667EEA 100%);
  color: white;
  border-radius: 8px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.hero-section h2 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.hero-section p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.features-section {
  margin-top: 3rem;
}

.features-section h3 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 2rem;
  color: #333;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  font-size: 3rem;
  color: #409EFF;
  margin-bottom: 1rem;
}

.feature-card h4 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #333;
}

.feature-card p {
  color: #666;
  line-height: 1.5;
}
</style>

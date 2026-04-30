<template>
  <div class="editor-container">
    <h2>文本编辑器</h2>
    <el-form label-width="100px">
      <el-form-item label="内容">
        <el-input
          v-model="content"
          type="textarea"
          :rows="8"
          placeholder="请输入要处理的文本"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button type="info" size="small" @click="loadExampleText">
          <el-icon><Document /></el-icon> 添加示例文本
        </el-button>
      </el-form-item>

      <el-divider>文本处理选项</el-divider>
      
      <div class="processing-options">
        <div class="option-item">
          <el-checkbox v-model="processingOptions.enableChunk">启用意群划分</el-checkbox>
          <el-select 
            v-if="processingOptions.enableChunk"
            v-model="processingOptions.chunkLevel" 
            placeholder="选择划分程度"
            class="option-select"
          >
            <el-option label="轻度划分" :value="1" />
            <el-option label="中度划分" :value="2" />
            <el-option label="高度划分" :value="3" />
          </el-select>
          <div class="option-desc" v-if="processingOptions.enableChunk">
            轻度：意群较大，适合快速阅读；中度：平衡划分；高度：意群较小，适合细致阅读
          </div>
        </div>
        
        <div class="option-item">
          <el-checkbox v-model="processingOptions.enableSimplify">启用文本简化</el-checkbox>
          <el-select 
            v-if="processingOptions.enableSimplify"
            v-model="processingOptions.simplifyLevel" 
            placeholder="选择简化程度"
            class="option-select"
          >
            <el-option label="轻度简化" :value="1" />
            <el-option label="中度简化" :value="2" />
            <el-option label="深度简化" :value="3" />
          </el-select>
        </div>
        
        <div class="option-item">
          <el-checkbox v-model="processingOptions.enableMainContent">启用主次内容区分</el-checkbox>
        </div>
      </div>

      <el-divider>文件操作</el-divider>
      
      <el-form-item label="文件上传">
        <el-upload
          class="upload-demo"
          action="#"
          :auto-upload="false"
          :on-change="handleFileUpload"
          :show-file-list="false"
          accept=".txt,.pdf,.doc,.docx"
          :file-list="[]"
        >
          <el-button type="primary" size="small">
            <el-icon><Upload /></el-icon> 选择文件
          </el-button>
        </el-upload>
        <span class="upload-tip">支持 TXT、PDF、Word 文件</span>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="processText" :loading="processing">
          <el-icon><MagicStick /></el-icon> 处理文本
        </el-button>
        <el-button @click="clearText">
          <el-icon><Delete /></el-icon> 清空
        </el-button>
        <el-button @click="navigateToReader">
          <el-icon><Reading /></el-icon> 打开阅读器
        </el-button>
        <el-button v-if="currentDocument.content" type="success" @click="exportProcessedText">
          <el-icon><Download /></el-icon> 导出处理后文本
        </el-button>
      </el-form-item>
    </el-form>
    
    <div v-if="processing" class="processing-indicator">
      <el-loading type="spinner" text="正在处理文本..." />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/appStore'
import { processText as apiProcessText, processTextAsync, getTaskStatus, uploadFile } from '../utils/api'
import { Upload, Document, MagicStick, Delete, Reading, Download } from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const content = ref('')
const processing = ref(false)

const currentDocument = computed(() => appStore.currentDocument)

const processingOptions = reactive({
  enableChunk: true,
  chunkLevel: 2,  // 1=轻度, 2=中度, 3=高度
  enableSimplify: false,
  simplifyLevel: 1,
  enableMainContent: false,
  posTagging: false
})

const exampleTexts = [
  {
    title: '示例文本 - 春天的故事',
    content: '春天来了，万物复苏。小草从地里钻出来，花儿也开了。小鸟在树上唱歌，蝴蝶在花丛中飞舞。阳光温暖地照在大地上，一切都充满了生机。这是一个美丽的季节，让我们一起去感受大自然的魅力吧！'
  },
  {
    title: '示例文本 - 科技改变生活',
    content: '随着科技的发展，我们的生活发生了巨大的变化。智能手机让我们可以随时随地与他人联系，互联网让信息传播更加迅速。人工智能正在改变我们的工作方式，自动驾驶技术让出行更加安全。科技让我们的生活变得更加便捷和美好。'
  },
  {
    title: '示例文本 - 健康饮食',
    content: '健康的饮食对我们的身体非常重要。我们应该多吃蔬菜和水果，它们富含维生素和纤维。少吃油腻和高糖的食物，这些食物对身体不好。每天要喝足够的水，保持身体的水分平衡。规律的饮食习惯能让我们拥有健康的身体。'
  }
]

const loadExampleText = () => {
  const randomIndex = Math.floor(Math.random() * exampleTexts.length)
  const example = exampleTexts[randomIndex]
  content.value = example.content
}

const processText = async () => {
  if (!content.value) {
    alert('请输入文本内容')
    return
  }
  
  processing.value = true
  try {
    // 确保用户信息已加载
    const token = localStorage.getItem('token')
    if (token && !appStore.user) {
      // 如果有token但没有用户信息，尝试获取用户信息
      const { getUserInfo } = await import('../utils/api')
      try {
        const userInfo = await getUserInfo()
        appStore.setUser(userInfo)
        // 重新加载设置和历史记录
        await appStore.loadReaderSettings()
        await appStore.loadReadingHistory()
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 获取用户信息失败，清除token
        localStorage.removeItem('token')
      }
    }
    
    // 同步词性标注设置到processingOptions，以便保存到历史记录
    processingOptions.posTagging = appStore.readerSettings.posTagging
    
    const options = {
      enableChunk: processingOptions.enableChunk,
      chunkLevel: processingOptions.chunkLevel,
      enableSimplify: processingOptions.enableSimplify,
      simplifyLevel: processingOptions.simplifyLevel,
      enableMainContent: processingOptions.enableMainContent,
      pos_tagging: processingOptions.posTagging
    }
    
    console.log('发送文本处理请求:', options)
    
    // 检查文本长度，决定使用同步还是异步处理
    if (content.value.length > 1000) {
      // 使用异步处理
      console.log('文本较长，使用异步处理')
      // 获取当前文档的ID
      const documentId = appStore.currentDocument.id
      console.log('当前文档ID:', documentId, '类型:', typeof documentId)
      
      // 确保 documentId 是数字类型
      const numericDocId = documentId ? parseInt(documentId, 10) : null
      console.log('转换后的文档ID:', numericDocId, '类型:', typeof numericDocId)
      
      const taskData = await processTextAsync(content.value, options, numericDocId)
      console.log('异步任务创建成功:', taskData)
      
      // 显示处理中的提示
      alert('文本正在处理中，请稍候...')
      
      // 轮询任务状态
      const checkTaskStatus = async () => {
        try {
          const taskStatus = await getTaskStatus(taskData.task_id)
          console.log('任务状态:', taskStatus)
          
          if (taskStatus.status === 'completed') {
            // 任务完成，处理结果
            const result = taskStatus.result
            console.log('文本处理API返回结果:', result)
            
            // 转换字段名以匹配前端期望的格式
            const processedResult = {
              processedContent: result.processed_text || '',
              simplifiedContent: result.simplifiedContent || '',
              segments: result.segments || [],
              simplifiedSegments: result.simplified_segments || [],
              pos_tags: result.pos_tags || [],
              simplified_pos_tags: result.simplified_pos_tags || []
            }
            
            console.log('转换后的结果:', processedResult)
            
            // 使用后端返回的document_id（如果存在），否则使用现有文档ID
            const documentId = taskData.document_id || appStore.currentDocument.id
            console.log('使用文档ID:', documentId)
            
            appStore.updateCurrentDocument({
              id: documentId,
              content: content.value,
              processedInEditor: true,  // 标记为在编辑器中处理过
              ...processedResult
            })
            
            // 添加阅读历史
            appStore.addReadingHistory({
              id: Date.now(),
              title: appStore.currentDocument.title || '未命名文档',
              document_id: documentId,
              content: content.value,
              processedContent: processedResult.processedContent,
              simplifiedContent: processedResult.simplifiedContent,
              segments: JSON.stringify(processedResult.segments),
              simplifiedSegments: JSON.stringify(processedResult.simplifiedSegments),
              pos_tags: JSON.stringify(processedResult.pos_tags),
              simplified_pos_tags: JSON.stringify(processedResult.simplified_pos_tags),
              processing_settings_snapshot: JSON.stringify(processingOptions),
              reading_time: 0,
              last_read_at: new Date().toISOString().slice(0, 19).replace('T', ' ').toString()
            })
            
            // 保存文档到 documents 表
            await appStore.saveCurrentDocument()
            
            router.push('/reader')
            processing.value = false
          } else if (taskStatus.status === 'failed') {
            // 任务失败
            console.error('任务处理失败:', taskStatus.error)
            alert(`处理失败: ${taskStatus.error || '未知错误'}`)
            processing.value = false
          } else {
            // 任务仍在处理中，继续轮询
            setTimeout(checkTaskStatus, 2000) // 每2秒检查一次
          }
        } catch (error) {
          console.error('获取任务状态失败:', error)
          alert('获取处理状态失败，请稍后重试')
          processing.value = false
        }
      }
      
      // 开始轮询
      setTimeout(checkTaskStatus, 2000)
    } else {
      // 使用同步处理
      // 获取当前文档的ID
      const documentId = appStore.currentDocument.id
      console.log('当前文档ID:', documentId)
      const result = await apiProcessText(content.value, options, documentId)
      console.log('文本处理API返回结果:', result)
      
      // 检查是否建议使用异步处理
      if (result.suggest_async) {
        // 用户确认是否使用异步处理
        if (confirm('文本较长，建议使用异步处理。是否切换到异步处理？')) {
          processing.value = false
          // 重新调用，使用异步处理
          const taskData = await processTextAsync(content.value, options, documentId)
          console.log('异步任务创建成功:', taskData)
          
          // 显示处理中的提示
          alert('文本正在处理中，请稍候...')
          
          // 轮询任务状态
          const checkTaskStatus = async () => {
            try {
              const taskStatus = await getTaskStatus(taskData.task_id)
              console.log('任务状态:', taskStatus)
              
              if (taskStatus.status === 'completed') {
                // 任务完成，处理结果
                const result = taskStatus.result
                console.log('文本处理API返回结果:', result)
                
                // 转换字段名以匹配前端期望的格式
                const processedResult = {
                  processedContent: result.processed_text || '',
                  simplifiedContent: result.simplifiedContent || '',
                  segments: result.segments || [],
                  simplifiedSegments: result.simplified_segments || [],
                  pos_tags: result.pos_tags || [],
                  simplified_pos_tags: result.simplified_pos_tags || []
                }
                
                console.log('转换后的结果:', processedResult)
                
                // 使用后端返回的document_id（如果存在），否则使用现有文档ID
                const documentId = taskData.document_id || appStore.currentDocument.id
                console.log('使用文档ID:', documentId)
                
                appStore.updateCurrentDocument({
                  id: documentId,
                  content: content.value,
                  processedInEditor: true,  // 标记为在编辑器中处理过
                  ...processedResult
                })
                
                // 添加阅读历史
                appStore.addReadingHistory({
                  id: Date.now(),
                  title: appStore.currentDocument.title || '未命名文档',
                  document_id: documentId,
                  content: content.value,
                  processedContent: processedResult.processedContent,
                  simplifiedContent: processedResult.simplifiedContent,
                  segments: JSON.stringify(processedResult.segments),
                  simplifiedSegments: JSON.stringify(processedResult.simplifiedSegments),
                  pos_tags: JSON.stringify(processedResult.pos_tags),
                  simplified_pos_tags: JSON.stringify(processedResult.simplified_pos_tags),
                  reading_time: 0,
                  last_read_at: new Date().toISOString().slice(0, 19).replace('T', ' ').toString()
                })
                
                // 保存文档到 documents 表
                await appStore.saveCurrentDocument()
                
                router.push('/reader')
                processing.value = false
              } else if (taskStatus.status === 'failed') {
                // 任务失败
                console.error('任务处理失败:', taskStatus.error)
                alert(`处理失败: ${taskStatus.error || '未知错误'}`)
                processing.value = false
              } else {
                // 任务仍在处理中，继续轮询
                setTimeout(checkTaskStatus, 2000) // 每2秒检查一次
              }
            } catch (error) {
              console.error('获取任务状态失败:', error)
              alert('获取处理状态失败，请稍后重试')
              processing.value = false
            }
          }
          
          // 开始轮询
          setTimeout(checkTaskStatus, 2000)
          return
        }
      }
      
      // 转换字段名以匹配前端期望的格式
      const processedResult = {
        processedContent: result.processed_text || '',
        simplifiedContent: result.simplifiedContent || '',
        segments: result.segments || [],
        simplifiedSegments: result.simplified_segments || [],
        pos_tags: result.pos_tags || [],
        simplified_pos_tags: result.simplified_pos_tags || []
      }
      
      console.log('转换后的结果:', processedResult)
      
      // 使用现有的文档ID（如果存在且为真实数据库ID），否则生成新ID
      const existingDocId = appStore.currentDocument.id
      const isRealDocId = existingDocId && existingDocId < 1000000000000 // 真实数据库ID通常小于这个值
      appStore.updateCurrentDocument({
        id: isRealDocId ? existingDocId : Date.now(),
        content: content.value,
        processedInEditor: true,  // 标记为在编辑器中处理过
        ...processedResult
      })
      
      // 添加阅读历史
      appStore.addReadingHistory({
        id: Date.now(),
        title: appStore.currentDocument.title || '未命名文档',
        content: content.value,
        processedContent: processedResult.processedContent,
        simplifiedContent: processedResult.simplifiedContent,
        segments: JSON.stringify(processedResult.segments),
        simplifiedSegments: JSON.stringify(processedResult.simplified_segments),
        pos_tags: JSON.stringify(processedResult.pos_tags),
        simplified_pos_tags: JSON.stringify(processedResult.simplified_pos_tags),
        reading_time: 0,
        last_read_at: new Date().toISOString()
      })
      
      // 保存文档到 documents 表
      await appStore.saveCurrentDocument()
      
      router.push('/reader')
    }
  } catch (error) {
    console.error('处理文本失败:', error)
    console.error('错误详情:', error.response)
    alert('处理文本失败，请稍后重试')
    processing.value = false
  }
}

const clearText = () => {
  content.value = ''
}

const navigateToReader = () => {
  router.push('/reader')
}

const handleFileUpload = async (file) => {
  try {
    console.log('文件对象:', file)
    console.log('文件原始对象:', file.raw)
    
    if (!file.raw) {
      alert('文件对象无效')
      return
    }
    
    const formData = new FormData()
    formData.append('file', file.raw)
    
    // 检查FormData
    console.log('FormData has file:', formData.has('file'))
    
    try {
      const response = await uploadFile(formData)
      console.log('文件上传成功:', response)
      
      // 将文件内容显示在文本编辑框中
      if (response && response.content) {
        content.value = response.content
        
        // 更新当前文档对象，设置正确的标题
        appStore.updateCurrentDocument({
          title: file.raw.name,
          content: response.content
        })
        
        // 自动创建文档记录
        const documentData = {
          title: file.raw.name,
          original_filename: file.raw.name,
          file_type: file.raw.name.split('.').pop().toLowerCase(),
          file_size: file.raw.size,
          content: response.content
        }
        
        console.log('准备创建文档记录:', documentData)
        try {
          const savedDocument = await appStore.saveDocument(documentData)
          console.log('文档记录创建成功:', savedDocument)
          // 更新当前文档ID
          appStore.updateCurrentDocument({ id: savedDocument.id })
          alert('文件上传成功，内容已加载到编辑框，文档记录已保存')
        } catch (saveError) {
          console.error('创建文档记录失败:', saveError)
          alert('文件上传成功，内容已加载到编辑框，但保存文档记录失败')
        }
      } else {
        alert('文件上传成功，但未能读取内容')
      }
    } catch (apiError) {
      console.error('API请求失败:', apiError)
      console.error('错误状态:', apiError.response?.status)
      console.error('错误数据:', apiError.response?.data)
      
      if (apiError.response && apiError.response.status === 422) {
        alert('文件格式错误，请检查文件类型')
      } else {
        alert('文件上传失败，请稍后重试')
      }
    }
  } catch (error) {
    console.error('处理文件上传时出错:', error)
    alert('文件上传失败，请稍后重试')
  }
}

const exportProcessedText = () => {
  const doc = currentDocument.value
  if (!doc.content) {
    alert('没有可导出的内容')
    return
  }
  
  let exportContent = `原文：\n${doc.content}\n\n`
  
  if (doc.simplifiedContent) {
    exportContent += `简化文本：\n${doc.simplifiedContent}\n\n`
  }
  
  if (doc.segments && doc.segments.length > 0) {
    exportContent += `意群划分：\n`
    doc.segments.forEach((segment, index) => {
      exportContent += `[${index + 1}] ${segment.text}\n`
    })
    exportContent += `\n`
  }
  
  const blob = new Blob([exportContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `处理后文本_${Date.now()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  alert('文本导出成功')
}

// 生命周期
onMounted(async () => {
  // 加载阅读器设置
  await appStore.loadReaderSettings()
  // 加载阅读历史
  await appStore.loadReadingHistory()
  
  // 仅在编辑模式下加载内容到编辑框
  // 如果是从阅读历史打开后跳转过来的，不自动加载内容
  if (appStore.currentMode !== 'reading' && appStore.currentDocument && appStore.currentDocument.content) {
    console.log('加载当前文档内容:', appStore.currentDocument)
    content.value = appStore.currentDocument.content
  }
  
  // 重置为编辑模式（下次进入编辑器时可以正常加载）
  appStore.setCurrentMode('editing')
})
</script>

<style scoped>
.editor-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}

.editor-container h2 {
  margin-bottom: 2rem;
  color: #333;
}

.processing-options {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.option-item:last-child {
  margin-bottom: 0;
}

.option-slider {
  width: 200px;
}

.option-select {
  width: 150px;
}

.upload-tip {
  margin-left: 1rem;
  font-size: 14px;
  color: #666;
}

.processing-indicator {
  margin-top: 2rem;
  text-align: center;
}
</style>

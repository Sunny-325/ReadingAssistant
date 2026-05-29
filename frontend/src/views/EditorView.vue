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
          :disabled="appStore.textProcessing.isProcessing"
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
          <el-checkbox 
            v-model="processingOptions.enableChunk"
            :disabled="appStore.textProcessing.isProcessing"
          >启用意群划分</el-checkbox>
          <el-select 
            v-if="processingOptions.enableChunk"
            v-model="processingOptions.chunkLevel" 
            placeholder="选择划分程度"
            class="option-select"
            :disabled="appStore.textProcessing.isProcessing"
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
          <el-checkbox 
            v-model="processingOptions.enableSimplify"
            :disabled="appStore.textProcessing.isProcessing"
          >启用文本简化</el-checkbox>
          <el-select 
            v-if="processingOptions.enableSimplify"
            v-model="processingOptions.simplifyLevel" 
            placeholder="选择简化程度"
            class="option-select"
            :disabled="appStore.textProcessing.isProcessing"
          >
            <el-option label="轻度简化" :value="1" />
            <el-option label="中度简化" :value="2" />
            <el-option label="深度简化" :value="3" />
          </el-select>
        </div>
        
        <div class="option-item">
          <el-checkbox 
            v-model="processingOptions.enableMainContent"
            :disabled="appStore.textProcessing.isProcessing"
          >启用主次内容区分</el-checkbox>
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
          accept=".txt,.pdf,.doc,.docx,.epub"
          :file-list="[]"
        >
          <el-button type="primary" size="small">
            <el-icon><Upload /></el-icon> 选择文件
          </el-button>
        </el-upload>
        <span class="upload-tip">支持 TXT、PDF、Word、EPUB 文件</span>
      </el-form-item>
      
      <el-form-item>
        <el-button 
          type="primary" 
          @click="processText" 
          :loading="appStore.textProcessing.isProcessing"
          :disabled="appStore.textProcessing.isProcessing"
        >
          <el-icon><MagicStick /></el-icon> 
          {{ appStore.textProcessing.isProcessing ? '正在处理...' : '处理文本' }}
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
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/appStore'
import { ElMessage } from 'element-plus'
import { processText as apiProcessText, processTextAsync, processTextGrouped, getGroupedTaskProgress, continueGroupedTask, getUnfinishedTasks, getTaskStatus, uploadFile, pauseTask } from '../utils/api'
import { Upload, Document, MagicStick, Delete, Reading, Download, VideoPause } from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const content = ref('')

const currentDocument = computed(() => appStore.currentDocument)

const processingOptions = reactive({
  enableChunk: true,
  chunkLevel: 2,  // 1=轻度, 2=中度, 3=高度
  enableSimplify: false,
  simplifyLevel: 1,
  enableMainContent: false,
  posTagging: false
})

// 组件挂载时恢复处理状态
onMounted(() => {
  if (appStore.textProcessing.isProcessing && appStore.textProcessing.content) {
    content.value = appStore.textProcessing.content
  }
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

// 获取处理结果并更新 currentDocument
const fetchAndSetProcessedContent = async (documentId) => {
  if (!documentId) return
  
  try {
    const token = localStorage.getItem('token')
    if (!token) return
    
    // 获取文档的最新阅读历史
    const response = await fetch(`/api/documents/${documentId}/history`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      const historyData = result.data
      
      if (historyData) {
        // 解析数据
        const parseData = (data, defaultValue = []) => {
          if (!data) return defaultValue
          if (typeof data === 'object') return data
          try {
            return JSON.parse(data)
          } catch (e) {
            console.error('解析数据失败:', e)
            return defaultValue
          }
        }
        
        console.log('获取到最新处理结果:', historyData)
        
        // 更新 currentDocument - 确保完全替换所有字段
        appStore.updateCurrentDocument({
          id: documentId,
          title: historyData.title || '未命名文档',
          content: historyData.content_snapshot || '',
          processedContent: historyData.content_snapshot || '',
          simplifiedContent: historyData.simplified_content_snapshot || '',
          segments: parseData(historyData.segments_snapshot, []),
          simplifiedSegments: parseData(historyData.simplified_segments_snapshot, []),
          pos_tags: parseData(historyData.pos_tags_snapshot, []),
          simplified_pos_tags: parseData(historyData.simplified_pos_tags_snapshot, []),
          processingSettings: parseData(historyData.processing_settings_snapshot, {}),
          historyId: historyData.id,
          // 强制更新标志
          lastUpdated: Date.now()
        })
        
        console.log('已更新 currentDocument 为最新处理结果')
        
        // 刷新阅读历史列表，确保下次打开历史记录时能看到最新数据
        await appStore.loadReadingHistory()
        console.log('已刷新阅读历史列表')
      }
    } else {
      console.log('获取历史记录失败，状态码:', response.status)
    }
  } catch (error) {
    console.error('获取处理结果失败:', error)
  }
}

const processText = async () => {
  if (!content.value) {
    alert('请输入文本内容')
    return
  }
  
  // 设置全局处理状态
  appStore.startTextProcessing(content.value, processingOptions)
  
  try {
    // 确保用户信息已加载
    const token = localStorage.getItem('token')
    if (!token || !appStore.user) {
      // 如果没有token或用户信息，尝试获取用户信息
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
        // 提示用户需要登录
        alert('请先登录后再处理文本')
        appStore.finishTextProcessing()
        return
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

    // 长文本使用分组处理
    if (content.value.length > 1000) {
      console.log('文本较长，使用分组处理')
      const documentId = appStore.currentDocument.id ? parseInt(appStore.currentDocument.id, 10) : null

      const taskData = await processTextGrouped(content.value, options, documentId)
      console.log('分组任务创建成功:', taskData)

      appStore.setProcessingTaskId(taskData.task_id)

      let retryCount = 0
      const MAX_RETRIES = 5

      const checkGroupedStatus = async () => {
        try {
          const progress = await getGroupedTaskProgress(taskData.task_id)
          console.log('分组任务进度:', progress)

          // 检查状态是否为完成（包含 completed 和 paused，因为单组任务完成后可能显示为 paused）
          const isCompleted = progress.status === 'completed' || 
                            (progress.status === 'paused' && progress.total_groups === 1) ||
                            (progress.status === 'paused' && progress.group_index + 1 >= progress.total_groups)
          
          if (isCompleted) {
            console.log('所有分组处理完成')
            appStore.finishTextProcessing()
            ElMessage.success('文本处理成功！即将跳转到阅读页面...')
            // 获取处理结果并更新 currentDocument
            await fetchAndSetProcessedContent(taskData.document_id)
            router.push('/reader')
          } else if (progress.status === 'paused') {
            console.log('当前组处理完成，准备跳转至阅读界面')
            // 先获取处理结果并更新 currentDocument
            await fetchAndSetProcessedContent(taskData.document_id)
            appStore.finishTextProcessing()

            // 保存当前任务信息到store，以便在阅读界面可以继续处理下一组
            appStore.setProcessingTaskId(taskData.task_id)
            
            ElMessage.success(`第 ${progress.group_index + 1}/${progress.total_groups} 组处理完成，即将跳转到阅读页面...`)
            
            // 延迟跳转，让用户看到提示信息
            setTimeout(() => {
              router.push('/reader')
            }, 1500)
          } else if (progress.status === 'failed') {
            console.error('分组处理失败')
            appStore.finishTextProcessing()
            ElMessage.error('处理失败，请稍后重试')
          } else {
            retryCount = 0
            // 对于单组任务，使用更短的检查间隔
            const checkInterval = taskData.total_groups <= 1 ? 1000 : 3000
            setTimeout(checkGroupedStatus, checkInterval)
          }
        } catch (error) {
          console.error('获取分组任务进度失败:', error)
          retryCount++
          
          if (retryCount < MAX_RETRIES) {
            console.log(`重试获取任务状态，第 ${retryCount} 次`)
            // 指数退避重试
            setTimeout(checkGroupedStatus, Math.pow(2, retryCount) * 1000)
          } else {
            console.error('重试次数已达上限，尝试直接获取文档状态')
            // 重试失败后，尝试直接获取文档处理状态
            try {
              const token = localStorage.getItem('token')
              if (token && taskData.document_id) {
                const response = await fetch(`/api/documents/${taskData.document_id}/processing-status`, {
                  headers: { 'Authorization': `Bearer ${token}` }
                })
                if (response.ok) {
                  const docStatus = await response.json()
                  if (docStatus.data.status === 'completed' || docStatus.data.task_status === 'completed') {
                    console.log('文档处理实际已完成，继续跳转')
                    await fetchAndSetProcessedContent(taskData.document_id)
                    appStore.finishTextProcessing()
                    ElMessage.success('文本处理成功！即将跳转到阅读页面...')
                    router.push('/reader')
                    return
                  }
                }
              }
            } catch (docError) {
              console.error('获取文档状态也失败:', docError)
            }
            
            appStore.finishTextProcessing()
            ElMessage.error('获取处理状态失败，请稍后重试')
          }
        }
      }

      setTimeout(checkGroupedStatus, 2000)
      
      // 长文本异步处理，不立即跳转，等待处理完成后在回调中跳转
      return
    } else {
        // 使用同步处理
        // 获取当前文档的ID
        let documentId = appStore.currentDocument.id
        console.log('当前文档ID:', documentId)
        const result = await apiProcessText(content.value, options, documentId)
        console.log('文本处理API返回结果:', result)
        
        // 使用后端返回的文档ID（这是关键！）
        if (result.document_id) {
          documentId = result.document_id
          console.log('后端返回的文档ID:', documentId)
        }
        
        // 如果后端建议使用异步处理，直接切换到异步处理（不再询问用户）
        if (result.suggest_async) {
          console.log('后端建议使用异步处理，自动切换...')
          // 重新调用，使用异步处理
          const taskData = await processTextAsync(content.value, options, documentId)
          console.log('异步任务创建成功:', taskData)
          
          // 设置任务ID
          appStore.setProcessingTaskId(taskData.task_id)
        
        // 使用闭包确保变量值正确
        const documentIdRef = { value: documentId }
        let retryCount = 0
        const MAX_RETRIES = 5
        
        // 轮询任务状态
        const checkTaskStatus = async () => {
          try {
            console.log(`[轮询] 第${retryCount + 1}次检查任务状态，task_id: ${taskData.task_id}`)
            const response = await getTaskStatus(taskData.task_id)
            // 后端返回的格式是 { message, data: { status, result } }
            const taskStatus = response.data || response
            console.log('[轮询] 任务状态响应:', JSON.stringify(taskStatus))
            
            // 统一转换为小写进行判断
            const status = String(taskStatus.status || '').toLowerCase()
            console.log(`[轮询] 任务状态(小写): ${status}`)
            
            if (status === 'completed') {
              // 任务完成，先从后端获取最新的历史记录数据
              console.log('[轮询] 任务完成，开始获取最新历史记录...')
              
              // 使用后端任务结果中的文档ID
              const currentDocId = taskData.document_id || documentIdRef.value
              console.log('[轮询] 文档ID:', currentDocId)
              
              // 从后端获取最新的处理结果（关键：确保获取最新数据）
              await fetchAndSetProcessedContent(currentDocId)
              
              console.log('[轮询] 已获取最新处理结果')
                
              // 不需要再次保存文档，因为后端已经创建了
              appStore.finishTextProcessing()
              ElMessage.success('文本处理成功！即将跳转到阅读页面...')
              router.push('/reader')
              } else if (status === 'failed') {
                // 任务失败
                console.error('[轮询] 任务处理失败:', taskStatus.error)
                appStore.finishTextProcessing()
                ElMessage.error(`处理失败: ${taskStatus.error || '未知错误'}`)
              } else {
                // 任务仍在处理中，继续轮询
                console.log(`[轮询] 任务仍在处理中，状态: ${status}`)
                setTimeout(checkTaskStatus, 2000) // 每2秒检查一次
              }
            } catch (error) {
              console.error('[轮询] 获取任务状态失败:', error.response?.data || error.message || error)
              retryCount++
              
              if (retryCount < MAX_RETRIES) {
                console.log(`[轮询] 重试获取任务状态，第 ${retryCount} 次`)
                setTimeout(checkTaskStatus, Math.pow(2, retryCount) * 1000)
              } else {
                console.error('[轮询] 重试次数已达上限，尝试直接获取文档状态')
                // 重试失败后，尝试直接获取文档处理状态
                try {
                  const token = localStorage.getItem('token')
                  if (token && taskData.document_id) {
                    const response = await fetch(`/api/documents/${taskData.document_id}/processing-status`, {
                      headers: { 'Authorization': `Bearer ${token}` }
                    })
                    if (response.ok) {
                      const docStatus = await response.json()
                      const docStatusValue = String(docStatus.data?.status || docStatus.data?.task_status || '').toLowerCase()
                      if (docStatusValue === 'completed') {
                        console.log('[轮询] 文档处理实际已完成，继续跳转')
                        await fetchAndSetProcessedContent(taskData.document_id)
                        appStore.finishTextProcessing()
                        ElMessage.success('文本处理成功！即将跳转到阅读页面...')
                        router.push('/reader')
                        return
                      }
                    }
                  }
                } catch (docError) {
                  console.error('[轮询] 获取文档状态也失败:', docError)
                }
                
                appStore.finishTextProcessing()
                ElMessage.error('获取处理状态失败，请稍后重试')
              }
            }
          }
          
          // 开始轮询，异步处理不立即跳转
          setTimeout(checkTaskStatus, 2000)
          return
      } else {
        // 同步处理成功，继续正常流程
        
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
        
        // 确定文档标题（使用后端返回的 documentId）
        let documentTitle = appStore.currentDocument.title || '未命名文档'
        
        // 检查是否为真实的文档ID（后端返回的ID通常较小）
        const isRealDocId = documentId && documentId < 1000000000000
        
        if (!isRealDocId) {
          // 如果不是真实文档ID，应该使用后端返回的ID
          // 但我们已经在前面设置了 documentId = result.document_id
          // 所以这里的逻辑应该已经被前面的赋值处理了
        }
        
        console.log('最终文档ID:', documentId, '是否为真实ID:', isRealDocId)
        
        // 更新当前文档（使用后端返回的 documentId）
        appStore.updateCurrentDocument({
          id: documentId,
          title: documentTitle,
          content: content.value,
          processedInEditor: true,
          fromDocumentRecord: false,
          processingSettings: processingOptions,  // 保存处理设置到 currentDocument
          ...processedResult
        })
        
        // 阅读历史由后端在处理文本时自动创建，不需要前端重复创建
        // 不需要再次保存文档，因为后端已经创建了
        // await appStore.saveCurrentDocument()
        
        // 同步处理完成，显示成功提示并跳转
        appStore.finishTextProcessing()
        ElMessage.success('文本处理成功！即将跳转到阅读页面...')
        router.push('/reader')
      }
    }
  } catch (error) {
    console.error('处理文本失败:', error)
    console.error('错误详情:', error.response)
    appStore.finishTextProcessing()
    ElMessage.error('处理文本失败，请稍后重试')
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
          file_type: file.raw.name.split('.').pop().toLowerCase(),
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
  
  // 检查是否从文档记录打开编辑（编辑模式且有真实文档ID）
  const isFromDocumentEdit = appStore.currentMode === 'editing' && 
                             appStore.currentDocument.id && 
                             appStore.currentDocument.id < 1000000000000
  
  // 仅在从文档记录打开编辑时加载内容到编辑框
  if (isFromDocumentEdit && appStore.currentDocument.content) {
    console.log('从文档记录打开编辑，加载内容:', appStore.currentDocument.title)
    content.value = appStore.currentDocument.content
  }
  
  // 如果是从阅读模式跳转过来的（从文档记录/历史记录打开阅读后回到编辑器），重置当前文档状态
  if (appStore.currentMode === 'reading') {
    console.log('从阅读模式返回编辑器，重置文档状态')
    appStore.updateCurrentDocument({
      id: null,
      title: '',
      content: '',
      processedContent: '',
      simplifiedContent: '',
      segments: [],
      simplifiedSegments: [],
      pos_tags: [],
      simplified_pos_tags: [],
      processedInEditor: false,
      fromDocumentRecord: false,
      fromHistory: false
    })
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

</style>
<template>
  <div class="history-container">
    <h2>阅读历史</h2>
    
    <!-- 搜索和筛选栏 -->
    <div class="history-header">
      <el-input
        v-model="searchQuery"
        placeholder="搜索历史记录"
        class="search-input"
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="header-buttons">
        <el-button type="success" @click="exportSelectedHistory" :disabled="selectedHistory.length === 0">
          <el-icon><Download /></el-icon> 导出选中 ({{ selectedHistory.length }})
        </el-button>
        <el-button type="primary" @click="refreshHistory">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>
    
    <div v-if="filteredHistory.length > 0" class="history-list">
      <el-table :data="paginatedHistory" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="content_snapshot" label="内容预览" show-overflow-tooltip>
          <template #default="scope">
            {{ getContentPreview(scope.row.content_snapshot || scope.row.content) }}...
          </template>
        </el-table-column>
        <el-table-column label="阅读进度" width="150">
          <template #default="scope">
            <div class="progress-info">
              <el-progress 
                :percentage="Math.round((scope.row.reading_progress || 0) * 100)" 
                :stroke-width="8"
                :color="getProgressColor(scope.row.reading_progress || 0)"
              />
              <div class="page-info">
                第 {{ getCurrentPage(scope.row) }} / {{ getTotalPages(scope.row) }} 页
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="阅读时间" width="150">
          <template #default="scope">
            {{ formatReadTime(scope.row.reading_time || scope.row.readTime || 0) }}
          </template>
        </el-table-column>
        <el-table-column label="最后阅读" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.last_read_at || scope.row.lastRead) }}
            </template>
          </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click.stop="openDocument(scope.row)">打开</el-button>
            <el-button size="small" type="danger" @click.stop="deleteHistory(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 批量操作 -->
      <div class="history-actions" v-if="selectedHistory.length > 0">
        <el-button type="danger" @click="deleteSelected">
          删除选中 ({{ selectedHistory.length }})
        </el-button>
      </div>
      
      <!-- 清空按钮 -->
      <div class="history-actions" v-else>
        <el-button type="danger" @click="clearAllHistory">清空历史</el-button>
      </div>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 30, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredHistory.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <div v-else class="no-history">
      <el-empty description="暂无阅读历史" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/appStore'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Refresh, Search, Download } from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedHistory = ref([])

// 从store中获取阅读历史
const readingHistory = computed(() => {
  // 未登录用户显示空历史
  if (!appStore.user) {
    return []
  }
  return appStore.readingHistory
})

// 过滤后的历史记录
const filteredHistory = computed(() => {
  let result = [...readingHistory.value]
  
  // 按搜索词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(history => 
      (history.title || '').toLowerCase().includes(query) ||
      (history.content_snapshot || history.content || '').toLowerCase().includes(query)
    )
  }
  

  
  return result
})

// 分页后的历史记录
const paginatedHistory = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredHistory.value.slice(start, end)
})

// 方法
const handleSearch = () => {
  currentPage.value = 1 // 重置页码
}



const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (current) => {
  currentPage.value = current
}

const refreshHistory = async () => {
  await appStore.loadReadingHistory()
}

const handleSelectionChange = (selection) => {
  selectedHistory.value = selection
}

const getContentPreview = (content) => {
  if (!content) return ''
  return content.substring(0, 100)
}

// 格式化阅读时间（秒 -> 更友好的格式）
const formatReadTime = (seconds) => {
  if (!seconds || seconds <= 0) return '0秒'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 格式化日期时间（UTC时间转换为本地时间）
const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return '未知'
  
  try {
    const date = new Date(dateTimeString)
    if (isNaN(date.getTime())) {
      return dateTimeString
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
  } catch (e) {
    console.error('格式化日期时间失败:', e)
    return dateTimeString
  }
}

const getProgressColor = (progress) => {
  if (progress < 0.3) return '#F56C6C'
  if (progress < 0.7) return '#E6A23C'
  return '#67C23A'
}

// 计算当前阅读页码
const getCurrentPage = (history) => {
  const progress = history.reading_progress || 
                   (history.readingProgress !== undefined && history.readingProgress > 1 
                     ? history.readingProgress / 100 
                     : history.readingProgress || 0)
  const totalPages = getTotalPages(history)
  if (totalPages <= 1 || progress <= 0) return 1
  return Math.min(Math.ceil(progress * totalPages), totalPages)
}

// 计算总页码（基于意群数量）
const getTotalPages = (history) => {
  const segments = history.segments_snapshot || history.segments || []
  const pageSize = 100 // 每页100个意群
  if (!Array.isArray(segments) || segments.length === 0) {
    // 如果没有意群数据，根据内容长度估算
    const content = history.content_snapshot || history.content || ''
    const avgCharsPerSegment = 20 // 平均每个意群约20字符
    const estimatedSegments = Math.max(1, Math.ceil(content.length / avgCharsPerSegment))
    return Math.max(1, Math.ceil(estimatedSegments / pageSize))
  }
  return Math.max(1, Math.ceil(segments.length / pageSize))
}

const openDocument = (history) => {
  // 设置为阅读模式，这样进入编辑器时不会自动加载内容
  appStore.setCurrentMode('reading')
  
  // 解析历史记录数据（支持多种字段名兼容）
  const parseSegments = (data) => {
    if (!data) return []
    if (Array.isArray(data)) return data
    try {
      return typeof data === 'string' ? JSON.parse(data) : data
    } catch (e) {
      return []
    }
  }
  
  const parseProcessingSettings = (data) => {
    if (!data) return {}
    if (typeof data === 'object') return data
    try {
      return typeof data === 'string' ? JSON.parse(data) : data
    } catch (e) {
      return {}
    }
  }
  
  // 数据已在loadReadingHistory中解析完成，直接使用
  appStore.updateCurrentDocument({
    id: history.document_id || history.id,  // 优先使用文档ID，兼容旧数据
    historyId: history.id,  // 保存历史记录ID用于后续更新
    title: history.title,
    content: history.content_snapshot || history.content,
    processedContent: history.content_snapshot || history.content,
    simplifiedContent: history.simplified_content_snapshot || history.simplifiedContent,  // 从历史记录打开时加载简化文本
    segments: parseSegments(history.segments_snapshot || history.segments),
    simplifiedSegments: parseSegments(history.simplified_segments_snapshot || history.simplifiedSegments),
    pos_tags: parseSegments(history.pos_tags_snapshot || history.pos_tags),
    simplified_pos_tags: parseSegments(history.simplified_pos_tags_snapshot || history.simplified_pos_tags),
    processingSettings: parseProcessingSettings(history.processing_settings_snapshot || history.processingSettings),  // 传递处理设置到 currentDocument
    readingProgress: history.reading_progress || history.readingProgress || 0,  // 传递阅读进度
    fromDocumentRecord: false,  // 不是从文档记录打开
    fromHistory: true  // 标记从历史记录打开
  })
  
  // 调试日志：检查数据
  console.log('=== 打开历史记录 ===')
  console.log('历史记录ID:', history.id)
  console.log('阅读进度:', history.reading_progress || history.readingProgress)
  console.log('处理设置:', history.processing_settings_snapshot || history.processingSettings)
  
  // 从历史记录中恢复当时的处理设置
  const processingSettings = parseProcessingSettings(history.processing_settings_snapshot || history.processingSettings)
  if (processingSettings) {
    console.log('恢复处理设置:', processingSettings)
    appStore.updateReaderSettings(processingSettings)
  }
  
  // 导航到阅读器
  router.push('/reader')
}



const deleteHistory = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条历史记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 调用store的方法删除历史记录
    await appStore.deleteReadingHistory(id)
    ElMessage.success('历史记录删除成功')
  } catch (error) {
    // 取消删除或其他错误
    if (error !== 'cancel') {
      console.error('删除历史记录失败:', error)
      ElMessage.error('删除历史记录失败')
    }
  }
}

const deleteSelected = async () => {
  if (selectedHistory.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedHistory.value.length} 条历史记录吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 批量删除历史记录
    for (const history of selectedHistory.value) {
      await appStore.deleteReadingHistory(history.id)
    }
    
    ElMessage.success('批量删除成功')
  } catch (error) {
    // 取消删除或其他错误
    if (error !== 'cancel') {
      console.error('批量删除历史记录失败:', error)
      ElMessage.error('批量删除历史记录失败')
    }
  }
}

const clearAllHistory = () => {
  ElMessageBox.confirm('确定要清空所有阅读历史吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'danger'
  }).then(async () => {
    // 调用store的方法清空历史记录
    await appStore.clearReadingHistory()
    ElMessage.success('历史记录清空成功')
  }).catch(() => {
    // 取消清空
  })
}

const exportSelectedHistory = () => {
  if (selectedHistory.value.length === 0) {
    ElMessage.warning('请先选择要导出的历史记录')
    return
  }

  let exportContent = ''
  
  selectedHistory.value.forEach((history, index) => {
    exportContent += `=== 阅读记录 ${index + 1} ===\n`
    exportContent += `标题：${history.title || '未命名'}\n`
    exportContent += `阅读进度：${Math.round((history.reading_progress || 0) * 100)}%\n`
    exportContent += `阅读时间：${formatReadTime(history.reading_time || history.readTime || 0)}\n`
    exportContent += `最后阅读：${history.last_read_at || '未知'}\n\n`
    
    exportContent += `原文：\n${history.content_snapshot || history.content || '无内容'}\n\n`
    
    if (history.simplified_content_snapshot || history.simplifiedContent) {
      exportContent += `简化文本：\n${history.simplified_content_snapshot || history.simplifiedContent}\n\n`
    }
    
    // 如果有意群划分数据
    const segments = history.segments_snapshot ? JSON.parse(history.segments_snapshot) : history.segments
    if (segments && segments.length > 0) {
      exportContent += `意群划分：\n`
      segments.forEach((segment, segIndex) => {
        exportContent += `[${segIndex + 1}] ${segment.text || segment}\n`
      })
      exportContent += `\n`
    }
    
    exportContent += `\n${'='.repeat(50)}\n\n`
  })

  const blob = new Blob([exportContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `阅读历史导出_${Date.now()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success(`成功导出 ${selectedHistory.value.length} 条阅读记录`)
}

// 生命周期
onMounted(() => {
  // 检查用户登录状态
  if (!appStore.user) {
    // 未登录用户清空历史记录
    appStore.readingHistory = []
    localStorage.removeItem('readingHistory')
  } else {
    // 每次加载页面都重新加载阅读历史，确保数据最新
    appStore.loadReadingHistory()
  }
})
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-container h2 {
  margin-bottom: 2rem;
  color: #333;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.search-input {
  width: 300px;
  margin-right: 1rem;
}

.header-buttons {
  display: flex;
  gap: 1rem;
}

.history-list {
  margin-bottom: 2rem;
}

.history-actions {
  margin-top: 1rem;
  text-align: right;
}

.no-history {
  padding: 4rem 0;
  text-align: center;
}

.pagination {
  margin-top: 2rem;
  text-align: right;
}
</style>

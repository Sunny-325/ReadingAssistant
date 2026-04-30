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

      <el-button type="primary" @click="refreshHistory">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
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
        <el-table-column label="阅读进度" width="120">
          <template #default="scope">
            <el-progress 
              :percentage="Math.round((scope.row.reading_progress || 0) * 100)" 
              :stroke-width="8"
              :color="getProgressColor(scope.row.reading_progress || 0)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="reading_time" label="阅读时间" width="150" />
        <el-table-column prop="last_read_at" label="最后阅读" width="180" />
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
import { Refresh, Search } from '@element-plus/icons-vue'

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

const getProgressColor = (progress) => {
  if (progress < 0.3) return '#F56C6C'
  if (progress < 0.7) return '#E6A23C'
  return '#67C23A'
}

const openDocument = (history) => {
  // 设置为阅读模式，这样进入编辑器时不会自动加载内容
  appStore.setCurrentMode('reading')
  
  // 数据已在loadReadingHistory中解析完成，直接使用
  appStore.updateCurrentDocument({
    id: history.document_id || history.id,  // 优先使用文档ID，兼容旧数据
    historyId: history.id,  // 保存历史记录ID用于后续更新
    title: history.title,
    content: history.content,
    processedContent: history.processedContent,
    simplifiedContent: history.simplifiedContent,
    segments: history.segments || [],
    simplifiedSegments: history.simplifiedSegments || [],
    pos_tags: history.pos_tags || [],
    simplified_pos_tags: history.simplified_pos_tags || []
  })
  
  // 调试日志：检查数据
  console.log('=== 打开历史记录 ===')
  console.log('历史记录ID:', history.id)
  console.log('处理设置:', history.processingSettings)
  console.log('posTagging:', history.processingSettings?.posTagging)
  console.log('pos_tags长度:', (history.pos_tags || []).length)
  
  // 从历史记录中恢复当时的处理设置
  if (history.processingSettings) {
    console.log('恢复处理设置:', history.processingSettings)
    appStore.updateReaderSettings(history.processingSettings)
    console.log('恢复后readerSettings.posTagging:', appStore.readerSettings.posTagging)
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

<template>
  <div class="document-container">
    <!-- 左侧侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h3>文档管理</h3>
      </div>
      
      <!-- 搜索 -->
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文档"
          class="search-input"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <!-- 分组管理 -->
      <div class="group-section">
        <div class="section-header">
          <span>文档分组</span>
          <el-button size="small" type="primary" @click="showCreateGroupDialog">
            <el-icon><Plus /></el-icon> 新建
          </el-button>
        </div>
        <div class="group-list">
          <div class="group-tags">
            <!-- 全部标签支持展开/收起 -->
            <div class="group-item all-group">
              <div class="group-header">
                <div class="group-info" @click="toggleGroup('all')">
                  <el-icon class="group-toggle-icon">
                    <ArrowDown v-if="expandedGroups.includes('all')" />
                    <ArrowRight v-else />
                  </el-icon>
                  <el-tag
                    :type="selectedGroup === 'all' ? 'primary' : ''"
                    @click.stop="() => {
                      selectedGroup = 'all'
                      selectedDocument = null
                    }"
                    class="group-tag all-tag"
                  >
                    全部
                  </el-tag>
                </div>
                <div class="group-actions" v-if="expandedGroups.includes('all') && selectedDocuments.length > 0">
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click.stop="batchDeleteSelected"
                  >
                    <el-icon><Delete /></el-icon> 批量删除
                  </el-button>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click.stop="showBatchMoveDialog"
                  >
                    <el-icon><Right /></el-icon> 批量移动
                  </el-button>
                </div>
              </div>
              <div 
                v-if="expandedGroups.includes('all')" 
                class="group-documents"
              >
                <div 
                  v-for="doc in getAllDocuments()" 
                  :key="doc.id"
                  class="group-document-item"
                  @click="selectDocument(doc.id)"
                >
                  <el-checkbox 
                    v-model="selectedDocuments" 
                    :label="doc.id"
                    class="document-checkbox"
                  />
                  <el-icon class="document-icon"><Document /></el-icon>
                  <span class="document-title">{{ doc.title }}</span>
                  <span class="document-date">{{ formatDate(doc.created_at) }}</span>
                </div>
                <div v-if="getAllDocuments().length === 0" class="no-documents">
                  暂无文档
                </div>
              </div>
            </div>
            
            <div
              v-for="group in documentGroups"
              :key="group.id"
              class="group-item"
            >
              <div class="group-header">
                <div class="group-info" @click="toggleGroup(group.id)">
                  <el-icon class="group-toggle-icon">
                    <ArrowDown v-if="expandedGroups.includes(group.id)" />
                    <ArrowRight v-else />
                  </el-icon>
                  <el-tag
                    :type="selectedGroup === group.id ? 'primary' : ''"
                    @click.stop="() => {
                      selectedGroup = group.id
                      selectedDocument = null
                    }"
                    class="group-tag"
                  >
                    {{ group.name }}
                  </el-tag>
                </div>
                <div class="group-actions">
                  <el-button 
                    size="small" 
                    type="primary" 
                    circle
                    @click.stop="uploadToGroup(group.id)"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-dropdown trigger="click" @command="(command) => handleGroupAction(command, group.id)">
                    <el-button size="small" circle>
                      <el-icon><More /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="rename">重命名</el-dropdown-item>
                        <el-dropdown-item command="delete">删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
              <div 
                v-if="expandedGroups.includes(group.id)" 
                class="group-documents"
              >
                <div 
                  v-for="doc in getGroupDocuments(group.id)" 
                  :key="doc.id"
                  class="group-document-item"
                  @click="selectDocument(doc.id)"
                >
                  <el-checkbox 
                    v-model="selectedDocuments" 
                    :label="doc.id"
                    class="document-checkbox"
                  />
                  <el-icon class="document-icon"><Document /></el-icon>
                  <span class="document-title">{{ doc.title }}</span>
                  <span class="document-date">{{ formatDate(doc.created_at) }}</span>
                </div>
                <div v-if="getGroupDocuments(group.id).length === 0" class="no-documents">
                  该分组暂无文档
                </div>
                <!-- 分组内的批量操作按钮 -->
                <div v-if="getGroupDocuments(group.id).length > 0" class="batch-actions">
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click.stop="batchDeleteSelected"
                    :disabled="selectedDocuments.length === 0"
                  >
                    <el-icon><Delete /></el-icon> 批量删除 ({{ selectedDocuments.length }})
                  </el-button>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click.stop="showBatchMoveDialog"
                    :disabled="selectedDocuments.length === 0"
                  >
                    <el-icon><Right /></el-icon> 批量移动
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 上传文档 -->
      <div class="upload-section">
        <el-upload
          class="upload-demo"
          drag
          action="#"
          :http-request="handleFileUpload"
          :multiple="false"
          :before-upload="beforeUpload"
        >
          <el-icon class="el-icon--upload"><Upload /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">
              支持上传 .txt, .pdf, .doc, .docx 文件
            </div>
          </template>
        </el-upload>
      </div>
    </div>
    
    <!-- 右侧主内容区 -->
    <div class="main-content">
      <div class="content-header">
        <h2>文档记录</h2>
        <div class="header-actions">
          <el-button type="primary" @click="refreshDocuments">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </div>
      
      <!-- 文档详情 -->
      <div v-if="selectedDocument" class="document-detail">
        <div class="detail-header">
          <h2 class="detail-title">{{ selectedDocument.title }}</h2>
          <el-dropdown @command="handleDocumentAction">
            <el-button size="small" circle>
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="{ action: 'rename', id: selectedDocument.id }">
                  <el-icon><Edit /></el-icon> 重命名
                </el-dropdown-item>
                <el-dropdown-item :command="{ action: 'edit', id: selectedDocument.id }">
                  <el-icon><Edit /></el-icon> 编辑
                </el-dropdown-item>
                <el-dropdown-item :command="{ action: 'move', id: selectedDocument.id }">
                  <el-icon><Right /></el-icon> 移动
                </el-dropdown-item>
                <el-dropdown-item :command="{ action: 'download', id: selectedDocument.id }">
                  <el-icon><Download /></el-icon> 下载
                </el-dropdown-item>
                <el-dropdown-item
                  :command="{ action: 'delete', id: selectedDocument.id }"
                  divided
                  type="danger"
                >
                  <el-icon><Delete /></el-icon> 删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="detail-content">
          <div class="content-preview">
            {{ getContentPreview(selectedDocument.content) }}
          </div>
          
          <div class="content-meta">
            <span class="upload-date">{{ formatDate(selectedDocument.created_at) }}</span>
            <span class="file-type" v-if="selectedDocument.file_type">
              {{ selectedDocument.file_type.toUpperCase() }}
            </span>
          </div>
        </div>
        
        <div class="detail-actions">
          <el-button size="small" @click="previewDocument(selectedDocument)">
            预览
          </el-button>
          <el-button size="small" type="primary" @click="openDocument(selectedDocument)">
            打开
          </el-button>
          <el-button size="small" @click="selectedDocument = null">
            返回列表
          </el-button>
        </div>
      </div>
      
      <!-- 文档列表 -->
      <div v-else-if="filteredDocuments.length > 0" class="document-grid">
        <div
          v-for="document in paginatedDocuments"
          :key="document.id"
          class="document-card"
        >
          <div class="card-header">
            <h3 class="document-title">{{ document.title }}</h3>
            <el-dropdown @command="handleDocumentAction">
              <el-button size="small" circle>
                <el-icon><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{ action: 'rename', id: document.id }">
                    <el-icon><Edit /></el-icon> 重命名
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'edit', id: document.id }">
                    <el-icon><Edit /></el-icon> 编辑
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'move', id: document.id }">
                    <el-icon><Right /></el-icon> 移动
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'download', id: document.id }">
                    <el-icon><Download /></el-icon> 下载
                  </el-dropdown-item>
                  <el-dropdown-item
                    :command="{ action: 'delete', id: document.id }"
                    divided
                    type="danger"
                  >
                    <el-icon><Delete /></el-icon> 删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div class="document-preview">
            {{ getContentPreview(document.content) }}
          </div>
          
          <div class="document-meta">
            <span class="upload-date">{{ formatDate(document.created_at) }}</span>
            <span class="file-type" v-if="document.file_type">
              {{ document.file_type.toUpperCase() }}
            </span>
          </div>
          
          <div class="card-footer">
            <el-button size="small" @click="previewDocument(document)">
              预览
            </el-button>
            <el-button size="small" type="primary" @click="openDocument(document)">
              打开
            </el-button>
          </div>
        </div>
      </div>
      
      <div v-else class="no-documents">
        <el-empty description="暂无文档" />
      </div>
      
      <!-- 分页 -->
      <div v-if="!selectedDocument && filteredDocuments.length > 0" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[12, 24, 36, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredDocuments.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 创建分组对话框 -->
    <el-dialog
      v-model="createGroupDialogVisible"
      title="创建文档分组"
      width="30%"
    >
      <el-form :model="newGroup" label-width="80px">
        <el-form-item label="分组名称">
          <el-input v-model="newGroup.name" placeholder="请输入分组名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createGroupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createGroup">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialogVisible"
      :title="renameForm.type === 'group' ? '重命名分组' : '重命名文档'"
      width="30%"
    >
      <el-form :model="renameForm" label-width="80px">
        <el-form-item :label="renameForm.type === 'group' ? '新分组名称' : '新标题'">
          <el-input v-model="renameForm.title" placeholder="请输入新名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="renameDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleRename">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 移动分组对话框 -->
    <el-dialog
      v-model="moveDialogVisible"
      title="移动到分组"
      width="30%"
    >
      <el-form :model="moveForm" label-width="80px">
        <el-form-item label="目标分组">
          <el-select v-model="moveForm.groupId" placeholder="选择分组">
            <el-option
              v-for="group in documentGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="moveDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="moveDocument">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 批量移动文档对话框 -->
    <el-dialog
      v-model="batchMoveDialogVisible"
      title="批量移动文档"
      width="30%"
    >
      <el-form :model="batchMoveForm" label-width="80px">
        <el-form-item label="目标分组">
          <el-select v-model="batchMoveForm.groupId" placeholder="选择分组">
            <el-option
              v-for="group in documentGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="移动数量">
          <span class="move-count">将移动 {{ selectedDocuments.length }} 个文档</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchMoveDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="batchMoveDocuments">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 文档预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      :title="previewDocumentTitle"
      width="80%"
    >
      <div class="document-preview-content">
        <div v-if="previewContent" class="content-pages">
          <div
            v-for="(page, index) in previewPages"
            :key="index"
            class="preview-page"
          >
            {{ page }}
          </div>
        </div>
        <div v-else>
          <el-empty description="预览内容加载中..." />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/appStore'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Document, Delete, Edit, Right, Download, Plus, More, ArrowDown, ArrowRight, Search, Refresh } from '@element-plus/icons-vue'
import { uploadFile } from '../utils/api'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const searchQuery = ref('')
const selectedGroup = ref('all')
const currentPage = ref(1)
const pageSize = ref(12)
const expandedGroups = ref([]) // 存储展开的分组ID
const selectedDocument = ref(null) // 选中的文档
const selectedDocuments = ref([]) // 存储选中的文档ID列表（用于批量操作）
const batchMoveDialogVisible = ref(false) // 批量移动对话框状态
const batchMoveForm = ref({ groupId: '' }) // 批量移动表单数据

// 从本地存储加载分组
const loadGroups = () => {
  const savedGroups = localStorage.getItem('documentGroups')
  if (savedGroups) {
    return JSON.parse(savedGroups)
  }
  return [
    { id: 1, name: '默认分组' },
    { id: 2, name: '工作文档' },
    { id: 3, name: '学习资料' }
  ]
}

// 保存分组到本地存储
const saveGroups = (groups) => {
  localStorage.setItem('documentGroups', JSON.stringify(groups))
}

const documentGroups = ref(loadGroups())

// 对话框状态
const createGroupDialogVisible = ref(false)
const renameDialogVisible = ref(false)
const moveDialogVisible = ref(false)
const previewDialogVisible = ref(false)

// 表单数据
const newGroup = ref({ name: '' })
const renameForm = ref({ title: '', type: 'document', id: null })
const moveForm = ref({ groupId: '' })

// 预览数据
const previewContent = ref('')
const previewDocumentTitle = ref('')
const previewPages = ref([])
const currentDocumentId = ref(null)

// 从store中获取文档列表
const documents = computed(() => {
  if (!appStore.user) {
    return []
  }
  return appStore.documents
})

// 过滤后的文档列表
const filteredDocuments = computed(() => {
  let result = [...documents.value]
  
  // 按搜索词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(doc => 
      doc.title.toLowerCase().includes(query) ||
      doc.content.toLowerCase().includes(query)
    )
  }
  
  // 按分组过滤
  if (selectedGroup.value !== 'all') {
    result = result.filter(doc => doc.group_id === selectedGroup.value)
  }
  
  return result
})

// 分页后的文档列表
const paginatedDocuments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDocuments.value.slice(start, end)
})

// 方法
const handleSearch = () => {
  currentPage.value = 1 // 重置页码
}


const showCreateGroupDialog = () => {
  createGroupDialogVisible.value = true
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (current) => {
  currentPage.value = current
}

const refreshDocuments = async () => {
  await appStore.loadDocuments()
}

const getContentPreview = (content) => {
  if (!content) return ''
  return content.substring(0, 100) + (content.length > 100 ? '...' : '')
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleDocumentAction = (command) => {
  const { action, id } = command
  currentDocumentId.value = id
  
  switch (action) {
    case 'rename':
      const docToRename = documents.value.find(d => d.id === id)
      if (docToRename) {
        // 修复：正确设置重命名表单的类型为文档，并提供完整信息
        renameForm.value = {
          title: docToRename.title,
          type: 'document',
          id: id
        }
        renameDialogVisible.value = true
      }
      break
    case 'edit':
      editDocument(id)
      break
    case 'move':
      moveForm.value.groupId = documentGroups.value[0]?.id || ''
      moveDialogVisible.value = true
      break
    case 'download':
      downloadDocument(id)
      break
    case 'delete':
      deleteDocument(id)
      break
  }
}

const previewDocument = (document) => {
  previewDocumentTitle.value = document.title
  previewContent.value = document.content
  // 简单的分页处理，每500字一页
  const pageSize = 500
  const pages = []
  for (let i = 0; i < document.content.length; i += pageSize) {
    pages.push(document.content.substring(i, i + pageSize))
  }
  previewPages.value = pages
  previewDialogVisible.value = true
}

const openDocument = async (document) => {
  console.log('=== 点击打开文档（阅读模式）===')
  console.log('文档ID:', document.id)
  console.log('文档标题:', document.title)
  
  // 设置为阅读模式
  appStore.setCurrentMode('reading')
  
  try {
    // 先尝试获取文档的最新阅读历史
    let historyData = null
    try {
      const token = localStorage.getItem('token')
      console.log('token:', token ? '已获取' : '未获取')
      if (token) {
        const response = await fetch(`/api/documents/${document.id}/history`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        console.log('API响应状态:', response.status)
        if (response.ok) {
          const result = await response.json()
          historyData = result.data
          console.log('获取到文档的最新阅读历史:', historyData)
        } else if (response.status === 404) {
          console.log('文档没有阅读历史记录，将使用文档原始内容')
        } else {
          console.log('获取阅读历史失败，状态码:', response.status)
        }
      } else {
        console.log('未登录，无法获取阅读历史')
      }
    } catch (error) {
      console.log('获取阅读历史出错:', error)
    }
    
    // 更新当前文档
    const documentData = {
      id: document.id,
      title: historyData?.title || document.title,
      content: historyData?.content_snapshot || document.content,
      historyId: historyData?.id || null,
      fromDocumentRecord: true,  // 标记从文档记录打开（阅读模式）
      fromHistory: false  // 不是从历史记录打开
    }
    
    // 如果有阅读历史，使用处理后的数据
    if (historyData) {
      documentData.processedContent = historyData.processed_content_snapshot || document.content
      // 不加载简化文本相关数据，只加载原文本相关数据（从文档记录打开阅读）
      documentData.simplifiedContent = undefined
      documentData.simplifiedSegments = []
      documentData.simplified_pos_tags = []
      
      // 安全解析数据，先检查是否已经是对象
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
      
      // 使用安全解析，只加载原文本相关数据
      documentData.segments = parseData(historyData.segments_snapshot, [])
      documentData.pos_tags = parseData(historyData.pos_tags_snapshot, [])
      
      // 恢复处理设置
      const settingsData = parseData(historyData.processing_settings_snapshot, null)
      if (settingsData) {
        console.log('=== 从历史记录恢复处理设置 ===')
        console.log('settings:', settingsData)
        
        // 设置文档级别的处理设置（用于主次内容区分）
        documentData.enableMainContent = settingsData.enableMainContent !== undefined ? settingsData.enableMainContent : false
        documentData.enableChunk = settingsData.enableChunk !== undefined ? settingsData.enableChunk : true
        
        // 确保恢复意群划分、主次内容区分、词性标注设置
        appStore.updateReaderSettings({
          enableChunk: settingsData.enableChunk !== undefined ? settingsData.enableChunk : true,
          enableMainContent: settingsData.enableMainContent !== undefined ? settingsData.enableMainContent : false,
          posTagging: settingsData.posTagging !== undefined ? settingsData.posTagging : false,
          chunkLevel: settingsData.chunkLevel !== undefined ? settingsData.chunkLevel : 2,
          simplifyLevel: settingsData.simplifyLevel !== undefined ? settingsData.simplifyLevel : 1,
          selectedPosTags: settingsData.selectedPosTags || ['n', 'v', 'a']
        })
      }
    } else {
      // 没有阅读历史，使用文档原始内容
      documentData.processedContent = undefined
      documentData.simplifiedContent = undefined
      documentData.segments = []
      documentData.simplifiedSegments = []
      documentData.pos_tags = []
      documentData.simplified_pos_tags = []
      documentData.enableMainContent = false
      documentData.enableChunk = true
    }
    
    console.log('=== 更新当前文档 ===')
    console.log('documentData:', documentData)
    console.log('pos_tags 长度:', documentData.pos_tags?.length || 0)
    console.log('simplified_pos_tags 长度:', documentData.simplified_pos_tags?.length || 0)
    appStore.updateCurrentDocument(documentData)
    
    console.log('=== 导航到阅读器 ===')
    router.push('/reader')
    
  } catch (error) {
    console.error('打开文档失败:', error)
    // 显示错误提示
    if (typeof window !== 'undefined') {
      import('element-plus').then(({ ElMessage }) => {
        ElMessage.error('打开文档失败，请稍后重试')
      })
    }
  }
}

const editDocument = async (documentId) => {
  const document = documents.value.find(d => d.id === documentId)
  if (document) {
    // 设置为编辑模式，这样编辑框会自动加载内容
    appStore.setCurrentMode('editing')
    
    // 先尝试获取文档的最新阅读历史
    let processedData = {
      processedContent: null,
      simplifiedContent: null,
      segments: [],
      simplifiedSegments: [],
      pos_tags: [],
      simplified_pos_tags: []
    }
    
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const response = await fetch(
          `/api/documents/${documentId}/history`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        )
        if (response.ok) {
          const result = await response.json()
          if (result.data) {
            const history = result.data
            processedData = {
              processedContent: history.processed_content_snapshot,
              simplifiedContent: history.simplified_content_snapshot,
              segments: history.segments_snapshot || [],
              simplifiedSegments: history.simplified_segments_snapshot || [],
              pos_tags: history.pos_tags_snapshot || [],
              simplified_pos_tags: history.simplified_pos_tags_snapshot || []
            }
            console.log('成功获取文档的最新阅读历史')
          }
        }
      }
    } catch (error) {
      console.error('获取文档历史失败，使用文档原始数据:', error)
    }
    
    // 更新当前文档
    appStore.updateCurrentDocument({
      id: document.id,
      title: document.title,
      content: document.content,
      processedContent: processedData.processedContent || document.content,
      simplifiedContent: processedData.simplifiedContent,
      segments: processedData.segments,
      simplifiedSegments: processedData.simplifiedSegments,
      pos_tags: processedData.pos_tags,
      simplified_pos_tags: processedData.simplified_pos_tags,
      fromDocumentRecord: true  // 标记从文档记录打开编辑
    })
    
    // 导航到编辑器
    router.push('/editor')
  }
}

const downloadDocument = (documentId) => {
  // 查找文档
  const doc = documents.value.find(doc => doc.id === documentId)
  if (!doc) {
    ElMessage.error('文档不存在')
    return
  }

  console.log('准备下载文档:', doc)

  try {
    // 根据文件类型设置 MIME 类型和扩展名
    let mimeType = 'text/plain'
    let extension = 'txt'

    if (doc.file_type === 'pdf') {
      mimeType = 'application/pdf'
      extension = 'pdf'
    } else if (doc.file_type === 'doc') {
      mimeType = 'application/msword'
      extension = 'doc'
    } else if (doc.file_type === 'docx') {
      mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      extension = 'docx'
    }

    console.log('文件类型:', doc.file_type, 'MIME类型:', mimeType, '扩展名:', extension)

    // 确保 content 存在且为字符串
    if (!doc.content || typeof doc.content !== 'string') {
      throw new Error('文档内容无效')
    }

    console.log('文档内容长度:', doc.content.length)

    // 创建 Blob 对象
    const blob = new Blob([doc.content], { type: mimeType })
    console.log('Blob 对象创建成功，大小:', blob.size)

    const url = URL.createObjectURL(blob)
    console.log('创建下载链接:', url)

    // 创建下载链接，使用 window.document 确保获取全局 document 对象
    // 确保标题不包含扩展名，避免下载时出现双后缀
    const titleWithoutExt = doc.title.replace(/\.[^/.]+$/, '')
    
    const link = window.document.createElement('a')
    link.href = url
    link.download = `${titleWithoutExt}.${extension}`
    console.log('下载文件名:', link.download)

    // 模拟点击下载
    link.click()
    console.log('触发下载')

    // 释放 URL 对象
    setTimeout(() => {
      URL.revokeObjectURL(url)
      console.log('释放 URL 对象')
    }, 100)

    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('下载文档失败:', error)
    ElMessage.error('下载失败')
  }
}

const deleteDocument = async (documentId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 调用store的方法删除文档
    await appStore.deleteDocument(documentId)
    ElMessage.success('文档删除成功')
  } catch (error) {
    // 取消删除或其他错误
    if (error !== 'cancel') {
      console.error('删除文档失败:', error)
      ElMessage.error('删除文档失败')
    }
  }
}

const createGroup = () => {
  if (newGroup.value.name) {
    const newId = Math.max(...documentGroups.value.map(g => g.id), 0) + 1
    documentGroups.value.push({
      id: newId,
      name: newGroup.value.name
    })
    // 保存到本地存储
    saveGroups(documentGroups.value)
    newGroup.value.name = ''
    createGroupDialogVisible.value = false
    ElMessage.success('分组创建成功')
  }
}

const deleteGroup = (groupId) => {
  ElMessageBox.confirm('确定要删除这个分组吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    documentGroups.value = documentGroups.value.filter(g => g.id !== groupId)
    if (selectedGroup.value === groupId) {
      selectedGroup.value = 'all'
    }
    // 从展开列表中移除
    expandedGroups.value = expandedGroups.value.filter(id => id !== groupId)
    // 保存到本地存储
    saveGroups(documentGroups.value)
    ElMessage.success('分组删除成功')
  }).catch(() => {
    // 取消删除
  })
}

// 切换分组展开/折叠状态
const toggleGroup = (groupId) => {
  const index = expandedGroups.value.indexOf(groupId)
  if (index > -1) {
    expandedGroups.value.splice(index, 1)
  } else {
    expandedGroups.value.push(groupId)
  }
}

// 获取分组文档
const getGroupDocuments = (groupId) => {
  return appStore.getDocumentsByGroup(groupId)
}

// 获取所有文档（用于"全部"标签）
const getAllDocuments = () => {
  if (!appStore.user) {
    return []
  }
  return appStore.documents
}

// 切换文档选择状态
const toggleDocumentSelection = (documentId) => {
  const index = selectedDocuments.value.indexOf(documentId)
  if (index > -1) {
    selectedDocuments.value.splice(index, 1)
  } else {
    selectedDocuments.value.push(documentId)
  }
}

// 显示批量移动对话框
const showBatchMoveDialog = () => {
  batchMoveForm.value.groupId = ''
  batchMoveDialogVisible.value = true
}

// 批量删除选中的文档
const batchDeleteSelected = async () => {
  if (selectedDocuments.value.length === 0) {
    ElMessage.warning('请先选择要删除的文档')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDocuments.value.length} 个文档吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    for (const docId of selectedDocuments.value) {
      await appStore.deleteDocument(docId)
    }
    
    ElMessage.success(`成功删除 ${selectedDocuments.value.length} 个文档`)
    selectedDocuments.value = []
    await refreshDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量移动文档
const batchMoveDocuments = async () => {
  if (selectedDocuments.value.length === 0) {
    ElMessage.warning('请先选择要移动的文档')
    return
  }
  
  if (!batchMoveForm.value.groupId) {
    ElMessage.warning('请选择目标分组')
    return
  }
  
  try {
    for (const docId of selectedDocuments.value) {
      await appStore.updateDocument(docId, { group_id: batchMoveForm.value.groupId })
    }
    
    ElMessage.success(`成功移动 ${selectedDocuments.value.length} 个文档`)
    selectedDocuments.value = []
    batchMoveDialogVisible.value = false
    await refreshDocuments()
  } catch (error) {
    ElMessage.error('移动失败')
  }
}

// 选择文档
const selectDocument = (documentId) => {
  selectedDocument.value = documents.value.find(doc => doc.id === documentId)
  if (selectedDocument.value && selectedDocument.value.group_id) {
    selectedGroup.value = selectedDocument.value.group_id
  } else {
    selectedGroup.value = 'all'
  }
  console.log('选择文档:', documentId, selectedDocument.value, selectedGroup.value)
}

// 上传文件到指定分组
const uploadToGroup = (groupId) => {
  // 实际项目中，应该打开文件上传对话框，并将文件关联到指定分组
  console.log('上传到分组:', groupId)
  // 这里简化处理，直接触发上传
  const uploadInput = document.createElement('input')
  uploadInput.type = 'file'
  uploadInput.accept = '.txt,.pdf,.doc,.docx'
  uploadInput.onchange = (e) => {
    const file = e.target.files[0]
    if (file) {
      // 构建文件对象
      const fileObj = {
        file: file,
        groupId: groupId
      }
      // 调用上传函数
      handleFileUpload(fileObj)
    }
  }
  uploadInput.click()
}

// 处理分组操作
const handleGroupAction = (command, groupId) => {
  switch (command) {
    case 'rename':
      // 打开重命名分组对话框，正确设置表单类型为分组
      renameForm.value = {
        title: documentGroups.value.find(g => g.id === groupId)?.name || '',
        type: 'group',
        id: groupId
      }
      renameDialogVisible.value = true
      break
    case 'delete':
      deleteGroup(groupId)
      break
  }
}

const handleRename = async () => {
  if (!renameForm.value.title || !renameForm.value.id) {
    return
  }
  
  if (renameForm.value.type === 'group') {
    // 重命名分组
    renameGroup()
  } else {
    // 重命名文档
    await renameDocument()
  }
}

const renameDocument = async () => {
  if (renameForm.value.title && renameForm.value.id) {
    try {
      // 调用 API 更新文档标题
      await appStore.updateDocumentTitle(renameForm.value.id, renameForm.value.title)
      ElMessage.success('文档重命名成功')
    } catch (error) {
      console.error('重命名文档失败:', error)
      ElMessage.error('重命名文档失败，请重试')
    }
    renameDialogVisible.value = false
    await appStore.loadDocuments() // 重新加载文档列表
    // 如果当前选中的文档被重命名，更新选中文档的标题
    if (selectedDocument.value && selectedDocument.value.id === renameForm.value.id) {
      selectedDocument.value.title = renameForm.value.title
    }
  }
}

const renameGroup = () => {
  if (renameForm.value.title && renameForm.value.id) {
    // 找到分组并更新名称
    const group = documentGroups.value.find(g => g.id === renameForm.value.id)
    if (group) {
      group.name = renameForm.value.title
      saveGroups(documentGroups.value)
      ElMessage.success('分组重命名成功')
    }
    renameDialogVisible.value = false
  }
}

const moveDocument = async () => {
  if (moveForm.value.groupId && currentDocumentId.value) {
    try {
      // 调用 appStore 的方法移动文档
      await appStore.moveDocumentToGroup(currentDocumentId.value, moveForm.value.groupId)
      ElMessage.success('文档移动成功')
      moveDialogVisible.value = false
      // 重新加载文档列表
      await appStore.loadDocuments()
    } catch (error) {
      console.error('移动文档失败:', error)
      ElMessage.error('移动文档失败，请重试')
    }
  }
}

const handleFileUpload = async (file) => {
  console.log('开始上传文件:', file.file.name, '大小:', file.file.size, '类型:', file.file.type)
  console.log('目标分组:', file.groupId)
  
  try {
    // 构建表单数据
    const formData = new FormData()
    formData.append('file', file.file)
    console.log('构建表单数据成功')
    
    // 调用文件上传API
    console.log('调用文件上传API: /api/files/upload')
    const uploadResult = await uploadFile(formData)
    console.log('文件上传API响应:', uploadResult)
    
    // 去除文件名中的扩展名
    const filenameWithoutExt = file.file.name.replace(/\.[^/.]+$/, '')
    
    // 调用文档创建API
    const documentData = {
      title: filenameWithoutExt,
      source_type: 'file_upload',
      group_id: file.groupId, // 添加上传文件的分组ID
      original_filename: file.file.name,
      file_type: file.file.name.split('.').pop().toLowerCase(),
      file_size: file.file.size,
      content: uploadResult.content
    }
    console.log('准备创建文档:', documentData)
    
    console.log('调用文档创建API: /api/user/documents')
    await appStore.saveDocument(documentData)
    console.log('文档创建成功')
    
    ElMessage.success('文件上传成功')
  } catch (error) {
    console.error('文件上传失败:', error)
    ElMessage.error('文件上传失败，请重试')
  }
}

const beforeUpload = (file) => {
  const allowedTypes = ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  const allowedExtensions = ['.txt', '.pdf', '.doc', '.docx']
  
  const isTypeAllowed = allowedTypes.includes(file.type)
  const isExtensionAllowed = allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
  
  if (!isTypeAllowed && !isExtensionAllowed) {
    ElMessage.error('只支持上传 .txt, .pdf, .doc, .docx 文件')
    return false
  }
  
  return true
}

// 生命周期
onMounted(() => {
  // 检查用户登录状态
  if (appStore.user) {
    // 每次加载页面都重新加载文档列表，确保数据最新
    appStore.loadDocuments()
  } else {
    // 未登录用户，清空文档列表
    appStore.documents = []
  }
})
</script>

<style scoped>
.document-container {
  display: flex;
  height: 100vh;
  background-color: #f5f7fa;
}

.sidebar {
  width: 300px;
  background-color: white;
  border-right: 1px solid #e4e7ed;
  padding: 20px;
  overflow-y: auto;
}

.sidebar-header {
  margin-bottom: 30px;
}

.sidebar-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.search-section {
  margin-bottom: 30px;
}

.search-input {
  width: 100%;
}

.group-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header span {
  font-weight: 500;
  color: #606266;
}

.group-list {
  margin-top: 10px;
}

.group-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.all-tag {
  width: 100%;
  text-align: center;
  margin-bottom: 5px;
}

.group-item {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f5f7fa;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.group-header:hover {
  background-color: #e6e8eb;
}

.group-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.group-toggle-icon {
  font-size: 14px;
  color: #909399;
  transition: transform 0.3s;
}

.group-tag {
  cursor: pointer;
  padding: 6px 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  flex: 1;
}

.group-tag:hover {
  opacity: 0.8;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.group-documents {
  padding: 10px 12px 10px 32px;
  background-color: #f9fafc;
  border-top: 1px solid #e6e8eb;
  max-height: 300px;
  overflow-y: auto;
}

.group-document-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: all 0.3s;
}

.group-document-item:hover {
  background-color: #f0f2f5;
  padding-left: 8px;
  border-radius: 4px;
}

.document-icon {
  font-size: 16px;
  color: #409eff;
  flex-shrink: 0;
}

.document-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-date {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  flex-shrink: 0;
}

.no-documents {
  text-align: center;
  padding: 20px 0;
  color: #909399;
  font-size: 14px;
}

/* 文档详情样式 */
.document-detail {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 30px;
  margin-bottom: 30px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.detail-title {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.detail-content {
  margin-bottom: 30px;
}

.content-preview {
  font-size: 16px;
  line-height: 1.6;
  color: #606266;
  margin-bottom: 20px;
  white-space: pre-wrap;
  word-break: break-word;
}

.content-meta {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #909399;
  padding-top: 15px;
  border-top: 1px solid #f0f2f5;
}

.detail-actions {
  display: flex;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

/* 分组文档项样式 */
.group-document-item {
  cursor: pointer;
  transition: all 0.3s;
}

.group-document-item:hover {
  background-color: #f0f2f5;
  padding-left: 8px;
  border-radius: 4px;
}

.upload-section {
  margin-top: 30px;
}

.main-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.content-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.document-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  transition: all 0.3s ease;
}

.document-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.document-title {
  margin: 0;
  font-size: 16px;
  color: #303133;
  flex: 1;
  margin-right: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.document-preview {
  margin-bottom: 15px;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
}

.document-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 12px;
  color: #909399;
}

.file-type {
  background-color: #ecf5ff;
  color: #409eff;
  padding: 2px 8px;
  border-radius: 10px;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.no-documents {
  padding: 60px 0;
  text-align: center;
}

.pagination {
  margin-top: 30px;
  text-align: right;
}

.document-preview-content {
  max-height: 600px;
  overflow-y: auto;
}

.preview-page {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.preview-page:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}
</style>
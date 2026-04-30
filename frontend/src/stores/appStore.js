import { defineStore } from 'pinia'
import { getSettings, saveSettings, getReadingHistory, addReadingHistory as addHistoryApi, updateReadingHistory as updateHistoryApi, clearReadingHistory as clearHistoryApi, deleteReadingHistory as deleteHistoryApi, getDocuments, saveDocument as saveDocumentApi, deleteDocument as deleteDocumentApi, updateDocument as updateDocumentApi } from '../utils/api'

// 辅助函数：解析JSON字符串，如果失败则返回默认值
const parseJsonOrReturn = (jsonString, defaultValue = []) => {
  if (!jsonString) return defaultValue
  // 如果已经是对象，直接返回
  if (typeof jsonString === 'object') {
    return jsonString
  }
  try {
    return JSON.parse(jsonString)
  } catch (e) {
    console.error('解析JSON失败:', e)
    return defaultValue
  }
}

// 应用状态管理
export const useAppStore = defineStore('app', {
  state: () => ({
    // 用户信息
    user: null,
    // 用户设置
    readerSettings: {
      fontFamily: 'Arial',
      fontSize: 20,
      lineHeight: 2,
      letterSpacing: 0,
      wordSpacing: 0,
      backgroundColor: '#ffffff',
      textColor: '#333333',
      colorScheme: 'default',
      enableChunk: true,
      chunkLevel: 2,  // 1=轻度, 2=中度, 3=高度
      enableMainContent: false,  // 默认不启用主次内容区分
      enableSimplify: false,
      posTagging: false,
      enableMask: true,
      maskLines: 3,
      maskOpacity: 0.8,
      typesettingMode: 'normal',
      posColors: {
        'n': '#E74C3C',
        'v': '#3498DB',
        'a': '#2ECC71',
        'd': '#F39C12',
        'p': '#9B59B6',
        'c': '#1ABC9C',
        'u': '#95A5A6',
        'r': '#E67E22',
        'm': '#34495E',
        'q': '#16A085',
        't': '#D35400',
        's': '#27AE60',
        'f': '#8E44AD',
        'b': '#C0392B',
        'z': '#2980B9',
        'e': '#F1C40F',
        'y': '#BDC3C7',
        'o': '#7F8C8D',
        'h': '#A569BD',
        'k': '#5DADE2',
        'x': '#566573',
        'w': '#85929E'
      },
      posFontSizes: {
        'n': 16, 'v': 16, 'a': 16, 'd': 16, 'p': 16, 'c': 16, 'u': 16, 'r': 16,
        'm': 16, 'q': 16, 't': 16, 's': 16, 'f': 16, 'b': 16, 'z': 16, 'e': 16,
        'y': 16, 'o': 16, 'h': 16, 'k': 16, 'x': 16, 'w': 16
      },
      // 词性选择 - 默认只标注名词、动词、形容词
      selectedPosTags: ['n', 'v', 'a'],
      // 语音设置
      speechRate: 1.0,
      speechVolume: 1.0,
      ttsProvider: 'pyttsx3',  // 'browser', 'pyttsx3'
      selectedVoice: 'female'  // 'male' 或 'female'（browser）, 'pyttsx3'（使用pyttsx3引擎）
    },
    // 阅读历史
    readingHistory: [],
    // 文档列表
    documents: [],
    // 当前文档
    currentDocument: {
      id: null,
      title: '',
      content: '',
      processedContent: '',
      simplifiedContent: '',
      segments: [],
      simplifiedSegments: [],
      pos_tags: [],
      simplified_pos_tags: [],
      processedInEditor: false  // 标记是否在编辑器中处理过
    },
    // 当前模式：'reading'（阅读）或 'editing'（编辑）
    currentMode: 'editing',
    // 定义面板状态
    definitionPanel: {
      visible: false,
      word: '',
      definition: {}
    },
    // 语音合成状态
    speech: {
      isSpeaking: false,
      currentWordIndex: 0,
      words: []
    }
  }),
  getters: {
    // 获取当前文档的处理选项
    processingOptions: (state) => {
      return {
        enableChunk: state.readerSettings.enableChunk,
        chunkLevel: state.readerSettings.chunkLevel,
        enableMainContent: state.readerSettings.enableMainContent,
        enableSimplify: state.readerSettings.enableSimplify,
        posTagging: state.readerSettings.posTagging
      }
    },
    // 获取阅读历史数量
    historyCount: (state) => state.readingHistory.length,
    // 检查用户是否登录
    isLoggedIn: (state) => !!state.user
  },
  actions: {
    // 设置用户信息
    setUser(user) {
      this.user = user
      // 加载用户的阅读历史
      this.loadReadingHistory()
    },
    // 登出
    logout() {
      this.user = null
      localStorage.removeItem('token')
      // 清空历史记录
      this.readingHistory = []
      localStorage.removeItem('readingHistory')
    },
    // 更新阅读器设置
    async updateReaderSettings(settings) {
      this.readerSettings = { ...this.readerSettings, ...settings }
      // 保存到本地存储
      localStorage.setItem('readerSettings', JSON.stringify(this.readerSettings))
      // 如果用户已登录，同步到后端
      if (this.user) {
        try {
          await saveSettings(this.readerSettings)
        } catch (error) {
          console.error('同步设置失败:', error)
        }
      }
    },
    // 加载阅读器设置
    async loadReaderSettings() {
      // 先从本地存储加载
      const savedSettings = localStorage.getItem('readerSettings')
      if (savedSettings) {
        this.readerSettings = JSON.parse(savedSettings)
      }
      // 如果用户已登录，从后端加载
      if (this.user) {
        try {
          const settings = await getSettings()
          this.readerSettings = { ...this.readerSettings, ...settings }
          // 更新本地存储
          localStorage.setItem('readerSettings', JSON.stringify(this.readerSettings))
        } catch (error) {
          console.error('加载设置失败:', error)
        }
      }
      // 确保行高不小于2
      if (this.readerSettings.lineHeight < 2) {
        this.readerSettings.lineHeight = 2
        // 保存更新后的设置
        localStorage.setItem('readerSettings', JSON.stringify(this.readerSettings))
        // 如果用户已登录，同步到后端
        if (this.user) {
          try {
            await saveSettings(this.readerSettings)
          } catch (error) {
            console.error('同步设置失败:', error)
          }
        }
      }
    },
    // 更新当前文档
    updateCurrentDocument(document) {
      this.currentDocument = { ...this.currentDocument, ...document }
    },
    // 设置当前模式
    setCurrentMode(mode) {
      this.currentMode = mode  // 'reading' 或 'editing'
    },
    // 保存当前文档
    async saveCurrentDocument() {
      if (this.user) {
        try {
          // 检查当前文档是否已经存在且为真实数据库ID
          const existingDocId = this.currentDocument.id
          const isRealDocId = existingDocId && existingDocId < 1000000000000 // 真实数据库ID通常小于这个值
          
          if (isRealDocId) {
            // 更新现有文档 - 只保存基本信息，处理后数据保存在阅读历史中
            console.log('更新现有文档:', this.currentDocument.id)
            const updatedDocument = await updateDocumentApi(this.currentDocument.id, {
              title: this.currentDocument.title || '未命名文档',
              content: this.currentDocument.content
            })
            console.log('文档更新成功:', updatedDocument)
          } else {
            // 创建新文档 - 只保存基本信息
            console.log('创建新文档')
            const newDocument = await saveDocumentApi({
              title: this.currentDocument.title || '未命名文档',
              source_type: 'direct_text',
              content: this.currentDocument.content
            })
            this.currentDocument.id = newDocument.id
            console.log('文档创建成功:', newDocument)
          }
          // 重新加载文档列表
          await this.loadDocuments()
        } catch (error) {
          console.error('保存文档失败:', error)
        }
      }
    },
    // 更新文档标题
    async updateDocumentTitle(documentId, title) {
      if (this.user && documentId && title) {
        try {
          console.log('更新文档标题:', documentId, title)
          await updateDocumentApi(documentId, { title })
          console.log('文档标题更新成功')
        } catch (error) {
          console.error('更新文档标题失败:', error)
          throw error
        }
      }
    },
    // 加载文档列表
    async loadDocuments() {
      if (this.user) {
        try {
          console.log('开始加载文档列表')
          console.log('调用文档列表API: /api/user/documents')
          const documents = await getDocuments()
          console.log('文档列表加载成功，共', documents.length, '个文档')
          console.log('文档列表:', documents)
          this.documents = documents
        } catch (error) {
          console.error('加载文档失败:', error)
        }
      }
    },
    // 保存文档
    async saveDocument(document) {
      if (this.user) {
        try {
          console.log('开始保存文档:', document)
          console.log('调用文档保存API: /api/user/documents')
          const savedDocument = await saveDocumentApi(document)
          console.log('文档保存成功:', savedDocument)
          // 重新加载文档列表
          console.log('重新加载文档列表')
          await this.loadDocuments()
          console.log('文档列表加载成功')
          return savedDocument
        } catch (error) {
          console.error('保存文档失败:', error)
          throw error
        }
      }
    },
    // 根据分组获取文档
    getDocumentsByGroup(groupId) {
      if (groupId === 'all') {
        return this.documents
      }
      return this.documents.filter(doc => doc.group_id === groupId)
    },
    // 移动文档到指定分组
    async moveDocumentToGroup(documentId, groupId) {
      if (this.user) {
        try {
          console.log('开始移动文档:', documentId, '到分组:', groupId)
          console.log('调用文档更新API: /api/user/documents/' + documentId)
          // 调用 API 更新文档的分组
          const response = await fetch(`/api/user/documents/${documentId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ group_id: groupId })
          })

          console.log('API响应状态:', response.status)
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            console.error('更新文档分组失败:', errorData)
            throw new Error('更新文档分组失败')
          }

          const responseData = await response.json()
          console.log('API响应数据:', responseData)

          // 重新加载文档列表，确保数据同步
          console.log('重新加载文档列表')
          await this.loadDocuments()
          console.log('文档列表加载成功')
        } catch (error) {
          console.error('移动文档失败:', error)
          throw error
        }
      }
    },
    // 删除文档
    async deleteDocument(documentId) {
      if (this.user) {
        try {
          await deleteDocumentApi(documentId)
          // 重新加载文档列表
          await this.loadDocuments()
        } catch (error) {
          console.error('删除文档失败:', error)
        }
      }
    },
    // 添加阅读历史
    async addReadingHistory(history) {
      // 未登录用户不添加历史记录
      if (!this.user) {
        return
      }
      
      // 获取内容快照用于比较
      const contentSnapshot = history.content_snapshot || history.content
      
      // 检查是否已经存在相同的阅读历史（基于内容相似度）
      // 使用内容的前500个字符进行比较，避免完全匹配的严格限制
      // 只比较内容，不比较document_id，因为同一文档可能有不同的document_id
      const compareContent = (content) => {
        if (!content || !contentSnapshot) return false
        const content1 = String(content).trim().substring(0, 500)
        const content2 = String(contentSnapshot).trim().substring(0, 500)
        return content1 === content2
      }
      
      // 只根据内容比较来判断是否为同一历史记录
      const existingHistory = this.readingHistory.find(item => 
        compareContent(item.content)
      )
      
      if (existingHistory) {
        // 如果已经存在相同的阅读历史，更新阅读时间、进度和标题，而不是添加新记录
        console.log('阅读历史已存在，更新阅读时间、进度和标题')
        
        // 更新本地历史记录
        existingHistory.lastRead = history.last_read_at || new Date().toISOString()
        // 更新标题（优先使用传入的标题）
        if (history.title && history.title !== '未命名文档') {
          existingHistory.title = history.title
        }
        if (history.reading_time !== undefined) {
          existingHistory.readTime = (existingHistory.readTime || 0) + (history.reading_time || 0)
        }
        if (history.reading_progress !== undefined) {
          existingHistory.readingProgress = history.reading_progress
        }
        
        // 保存到本地存储
        const storageKey = `readingHistory_${this.user.id}`
        localStorage.setItem(storageKey, JSON.stringify(this.readingHistory))
        localStorage.setItem('readingHistory', JSON.stringify(this.readingHistory)) // 兼容旧版本
        
        // 同步到后端（更新现有记录）
        try {
          await updateHistoryApi(existingHistory.id, {
            title: history.title || existingHistory.title,
            reading_progress: history.reading_progress || existingHistory.readingProgress || 0.0,
            current_position: history.current_position || 0,
            reading_time: existingHistory.readTime || 0,
            last_read_at: existingHistory.lastRead ? new Date(existingHistory.lastRead).toISOString().slice(0, 19).replace('T', ' ') : new Date().toISOString().slice(0, 19).replace('T', ' ')
          })
        } catch (error) {
          console.error('更新阅读历史失败:', error)
        }
        
        return
      }
      
      // 转换为前端显示所需的格式
      const formattedHistory = {
        id: history.id,
        document_id: history.document_id,
        title: history.title || '未命名文档',
        content: contentSnapshot,
        processedContent: history.processed_content_snapshot || history.processedContent,
        simplifiedContent: history.simplified_content_snapshot || history.simplifiedContent,
        // 解析JSON字符串为对象
        segments: history.segments_snapshot ? parseJsonOrReturn(history.segments_snapshot) : (typeof history.segments === 'string' ? parseJsonOrReturn(history.segments) : history.segments || []),
        simplifiedSegments: history.simplified_segments_snapshot ? parseJsonOrReturn(history.simplified_segments_snapshot) : (typeof history.simplifiedSegments === 'string' ? parseJsonOrReturn(history.simplifiedSegments) : history.simplifiedSegments || []),
        pos_tags: history.pos_tags_snapshot ? parseJsonOrReturn(history.pos_tags_snapshot) : (typeof history.pos_tags === 'string' ? parseJsonOrReturn(history.pos_tags) : history.pos_tags || []),
        simplified_pos_tags: history.simplified_pos_tags_snapshot ? parseJsonOrReturn(history.simplified_pos_tags_snapshot) : (typeof history.simplified_pos_tags === 'string' ? parseJsonOrReturn(history.simplified_pos_tags) : history.simplified_pos_tags || []),
        // 解析处理设置
        processingSettings: history.processing_settings_snapshot ? parseJsonOrReturn(history.processing_settings_snapshot) : this.processingOptions,
        readTime: history.reading_time || 0,
        lastRead: history.last_read_at || new Date().toISOString()
      }
      
      this.readingHistory.unshift(formattedHistory)
      // 保存到本地存储，使用与用户相关的键
      const storageKey = `readingHistory_${this.user.id}`
      localStorage.setItem(storageKey, JSON.stringify(this.readingHistory))
      localStorage.setItem('readingHistory', JSON.stringify(this.readingHistory)) // 兼容旧版本
      // 同步到后端
      try {
        // 构建后端所需的格式
        const backendHistory = {
          title: history.title || '未命名文档',
          document_id: history.document_id,
          content_snapshot: contentSnapshot,
          processed_content_snapshot: history.processed_content_snapshot || history.processedContent,
          simplified_content_snapshot: history.simplified_content_snapshot || history.simplifiedContent,
          // 检查segments是否已经是JSON字符串，如果是则直接使用，否则进行序列化
          segments_snapshot: history.segments_snapshot || (typeof history.segments === 'string' ? history.segments : JSON.stringify(history.segments || [])),
          simplified_segments_snapshot: history.simplified_segments_snapshot || (typeof history.simplifiedSegments === 'string' ? history.simplifiedSegments : JSON.stringify(history.simplifiedSegments || [])),
          pos_tags_snapshot: history.pos_tags_snapshot || (typeof history.pos_tags === 'string' ? history.pos_tags : JSON.stringify(history.pos_tags || [])),
          simplified_pos_tags_snapshot: history.simplified_pos_tags_snapshot || (typeof history.simplified_pos_tags === 'string' ? history.simplified_pos_tags : JSON.stringify(history.simplified_pos_tags || [])),
          processing_settings_snapshot: history.processing_settings_snapshot || JSON.stringify(this.processingOptions),
          reading_progress: history.reading_progress || 0.0,
          current_position: history.current_position || 0,
          reading_time: history.reading_time || 0,
          last_read_at: history.last_read_at ? new Date(history.last_read_at).toISOString().slice(0, 19).replace('T', ' ') : new Date().toISOString().slice(0, 19).replace('T', ' '),
        }
        await addHistoryApi(backendHistory)
      } catch (error) {
        console.error('同步阅读历史失败:', error)
      }
    },
    // 加载阅读历史
    async loadReadingHistory() {
      // 未登录用户不加载历史记录
      if (!this.user) {
        this.readingHistory = []
        localStorage.removeItem('readingHistory')
        return
      }
      
      try {
        // 从后端加载
        const historyFromBackend = await getReadingHistory()
        // 转换后端返回的数据格式为前端所需格式
        this.readingHistory = historyFromBackend.map(item => ({
          id: item.id,
          document_id: item.document_id,  // 添加文档ID
          title: item.title,
          content: item.content_snapshot,
          processedContent: item.processed_content_snapshot,
          simplifiedContent: item.simplified_content_snapshot,
          // 解析JSON字符串为对象
          segments: parseJsonOrReturn(item.segments_snapshot, []),
          simplifiedSegments: parseJsonOrReturn(item.simplified_segments_snapshot, []),
          pos_tags: parseJsonOrReturn(item.pos_tags_snapshot, []),
          simplified_pos_tags: parseJsonOrReturn(item.simplified_pos_tags_snapshot, []),
          // 解析处理设置
          processingSettings: parseJsonOrReturn(item.processing_settings_snapshot, {}),
          readTime: item.reading_time || 0,
          lastRead: item.last_read_at || item.created_at
        }))
        // 更新本地存储，使用与用户相关的键
        const storageKey = `readingHistory_${this.user.id}`
        localStorage.setItem(storageKey, JSON.stringify(this.readingHistory))
      } catch (error) {
        console.error('加载阅读历史失败:', error)
        // 如果后端加载失败，从本地存储加载，使用与用户相关的键
        const storageKey = `readingHistory_${this.user.id}`
        const savedHistory = localStorage.getItem(storageKey)
        if (savedHistory) {
          this.readingHistory = JSON.parse(savedHistory)
        } else {
          this.readingHistory = []
        }
      }
    },
    // 清空阅读历史
    async clearReadingHistory() {
      this.readingHistory = []
      // 使用与用户相关的键
      if (this.user) {
        const storageKey = `readingHistory_${this.user.id}`
        localStorage.removeItem(storageKey)
      }
      localStorage.removeItem('readingHistory') // 兼容旧版本
      // 如果用户已登录，同步到后端
      if (this.user) {
        try {
          await clearHistoryApi()
        } catch (error) {
          console.error('清空阅读历史失败:', error)
        }
      }
    },
    // 删除单个阅读历史记录
    async deleteReadingHistory(id) {
      // 先从前端列表中删除
      const updatedHistory = this.readingHistory.filter(item => item.id !== id)
      
      // 更新前端状态
      this.readingHistory = updatedHistory
      // 更新本地存储，使用与用户相关的键
      if (this.user) {
        const storageKey = `readingHistory_${this.user.id}`
        localStorage.setItem(storageKey, JSON.stringify(this.readingHistory))
      }
      localStorage.setItem('readingHistory', JSON.stringify(this.readingHistory)) // 兼容旧版本
      
      // 如果用户已登录，同步到后端
      if (this.user) {
        try {
          await deleteHistoryApi(id)
        } catch (error) {
          console.error('删除历史记录失败:', error)
          // 后端删除失败，前端状态已经更新，用户至少看到记录被删除了
        }
      }
    },
    // 显示定义面板
    showDefinitionPanel(word, definition) {
      this.definitionPanel = {
        visible: true,
        word,
        definition
      }
    },
    // 隐藏定义面板
    hideDefinitionPanel() {
      this.definitionPanel.visible = false
    },
    // 开始语音合成
    startSpeech(words) {
      this.speech = {
        isSpeaking: true,
        currentWordIndex: 0,
        words
      }
    },
    // 停止语音合成
    stopSpeech() {
      this.speech = {
        isSpeaking: false,
        currentWordIndex: 0,
        words: []
      }
    },
    // 更新当前语音合成的单词索引
    updateSpeechIndex(index) {
      this.speech.currentWordIndex = index
    }
  }
})

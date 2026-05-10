import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 300000, // 增加超时时间到300秒（5分钟）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器，添加认证令牌
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器，处理认证失败
apiClient.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 处理 401 认证失败
    if (error.response && error.response.status === 401) {
      console.error('登录已过期或未登录，跳转到登录页')
      // 清除本地存储的用户信息
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 显示错误提示
      if (typeof window !== 'undefined') {
        // 动态导入 ElMessage 避免 SSR 问题
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.error('登录已过期，请重新登录')
        })
      }
      // 延迟跳转，让用户看到提示
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    }
    return Promise.reject(error)
  }
)

// 认证API
export const login = async (username, password) => {
  try {
    // OAuth2PasswordRequestForm 需要 form-data 格式
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await apiClient.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  } catch (error) {
    console.error('登录失败:', error)
    throw error
  }
}

export const register = async (username, email, password) => {
  try {
    const response = await apiClient.post('/auth/register', {
      username,
      email,
      password
    })
    return response.data
  } catch (error) {
    console.error('注册失败:', error)
    throw error
  }
}

export const getUserInfo = async () => {
  try {
    const response = await apiClient.get('/auth/me')
    return response.data
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}

// 用户设置API
export const getSettings = async () => {
  try {
    const response = await apiClient.get('/user/settings')
    return response.data
  } catch (error) {
    console.error('获取用户设置失败:', error)
    throw error
  }
}

export const saveSettings = async (settings) => {
  try {
    const response = await apiClient.post('/user/settings', settings)
    return response.data
  } catch (error) {
    console.error('保存用户设置失败:', error)
    throw error
  }
}

// 文档API
export const getDocuments = async () => {
  try {
    console.log('开始获取文档列表')
    console.log('调用API: GET /user/documents')
    const response = await apiClient.get('/user/documents')
    console.log('API响应状态:', response.status)
    console.log('API响应数据:', response.data)
    return response.data
  } catch (error) {
    console.error('获取文档列表失败:', error)
    throw error
  }
}

export const saveDocument = async (document) => {
  try {
    console.log('开始保存文档')
    console.log('调用API: POST /user/documents')
    console.log('请求数据:', document)
    const response = await apiClient.post('/user/documents', document)
    console.log('API响应状态:', response.status)
    console.log('API响应数据:', response.data)
    return response.data
  } catch (error) {
    console.error('保存文档失败:', error)
    throw error
  }
}

export const deleteDocument = async (documentId) => {
  try {
    const response = await apiClient.delete(`/user/documents/${documentId}`)
    return response.data
  } catch (error) {
    console.error('删除文档失败:', error)
    throw error
  }
}

export const updateDocument = async (documentId, documentData) => {
  try {
    console.log('开始更新文档:', documentId)
    console.log('调用API: PUT /user/documents/' + documentId)
    console.log('请求数据:', documentData)
    const response = await apiClient.put(`/user/documents/${documentId}`, documentData)
    console.log('API响应状态:', response.status)
    console.log('API响应数据:', response.data)
    return response.data
  } catch (error) {
    console.error('更新文档失败:', error)
    throw error
  }
}

// 阅读历史API
export const getReadingHistory = async () => {
  try {
    const response = await apiClient.get('/user/history')
    return response.data
  } catch (error) {
    console.error('获取阅读历史失败:', error)
    throw error
  }
}

export const addReadingHistory = async (history) => {
  try {
    const response = await apiClient.post('/user/history', history)
    return response.data
  } catch (error) {
    console.error('添加阅读历史失败:', error)
    throw error
  }
}

export const clearReadingHistory = async () => {
  try {
    const response = await apiClient.delete('/user/history')
    return response.data
  } catch (error) {
    console.error('清空阅读历史失败:', error)
    throw error
  }
}

export const deleteReadingHistory = async (historyId) => {
  try {
    const response = await apiClient.delete(`/user/history/${historyId}`)
    return response.data
  } catch (error) {
    console.error('删除历史记录失败:', error)
    throw error
  }
}

export const updateReadingHistory = async (historyId, updates) => {
  try {
    const response = await apiClient.put(`/user/history/${historyId}`, updates)
    return response.data
  } catch (error) {
    console.error('更新阅读历史失败:', error)
    throw error
  }
}

// 文本处理API（同步）
export const processText = async (text, options, documentId) => {
  try {
    const response = await apiClient.post('/text/process', {
      text,
      options,
      document_id: documentId
    })
    console.log('文本处理API响应:', response.data)
    // 返回完整的响应数据，包括 document_id
    return {
      ...response.data.data,
      document_id: response.data.document_id
    }
  } catch (error) {
    console.error('文本处理失败:', error)
    throw error
  }
}

// 文本处理API（异步）
export const processTextAsync = async (text, options, documentId) => {
  try {
    const response = await apiClient.post('/text/process/async', {
      text,
      options,
      document_id: documentId
    })
    console.log('异步文本处理API响应:', response.data)
    return response.data.data
  } catch (error) {
    console.error('异步文本处理失败:', error)
    throw error
  }
}

// 获取任务状态API
export const getTaskStatus = async (taskId) => {
  try {
    const response = await apiClient.get(`/text/process/async/${taskId}`)
    console.log('任务状态API响应:', response.data)
    return response.data.data
  } catch (error) {
    console.error('获取任务状态失败:', error)
    throw error
  }
}

// 获取词语释义API
export const getWordDefinition = async (word, context = '') => {
  try {
    const response = await apiClient.get(`/text/definition/${word}`, {
      params: { context }
    })
    return response.data.data
  } catch (error) {
    console.error('获取词语释义失败:', error)
    throw error
  }
}

// 文本简化API
export const simplifyText = async (text, level = 1) => {
  try {
    const response = await apiClient.post('/text/simplify', {
      text,
      level
    })
    return response.data.data
  } catch (error) {
    console.error('文本简化失败:', error)
    throw error
  }
}

// 意群划分API
export const chunkText = async (text, chunkSize = 5) => {
  try {
    const response = await apiClient.post('/text/chunk', {
      text,
      chunk_size: chunkSize
    })
    return response.data.data
  } catch (error) {
    console.error('意群划分失败:', error)
    throw error
  }
}

// 文件上传API
export const uploadFile = async (formData) => {
  try {
    console.log('开始上传文件')
    console.log('调用API: POST /files/upload')
    // 获取文件信息
    const file = formData.get('file')
    console.log('上传文件信息:', file.name, file.size, file.type)
    
    // 创建一个新的axios实例，避免使用默认的Content-Type
    const fileUploadClient = axios.create({
      baseURL: '/api',
      timeout: 30000
    })
    
    // 添加认证令牌
    const token = localStorage.getItem('token')
    if (token) {
      fileUploadClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
      console.log('添加认证令牌')
    }
    
    // 不设置Content-Type，让浏览器自动处理（包括边界）
    console.log('发送文件上传请求')
    const response = await fileUploadClient.post('/files/upload', formData)
    console.log('API响应状态:', response.status)
    console.log('文件上传API响应:', response.data)
    return response.data
  } catch (error) {
    console.error('文件上传失败:', error)
    throw error
  }
}

// 文件导出API
export const exportFile = async (fileId) => {
  try {
    const response = await apiClient.get(`/files/export/${fileId}`)
    return response.data
  } catch (error) {
    console.error('文件导出失败:', error)
    throw error
  }
}

<template>
  <div class="settings-container">
    <h2>设置</h2>
    
    <!-- 用户信息 -->
    <el-divider>用户信息</el-divider>
    
    <el-form label-width="120px" class="user-info-form">
      <!-- 当前用户名 -->
      <el-form-item label="当前用户名">
        <span class="setting-value">{{ user?.username }}</span>
      </el-form-item>
      
      <!-- 修改用户名 -->
      <el-form-item label="修改用户名">
        <el-input 
          v-model="userForm.newUsername" 
          placeholder="输入新用户名"
        />
        <el-button type="primary" size="small" @click="handleUpdateUsername" :loading="updatingUsername">
          修改
        </el-button>
      </el-form-item>
      
      <!-- 修改密码 -->
      <el-form-item label="旧密码">
        <el-input 
          v-model="userForm.oldPassword" 
          type="password"
          placeholder="输入旧密码"
        />
      </el-form-item>
      
      <el-form-item label="新密码">
        <el-input 
          v-model="userForm.newPassword" 
          type="password"
          placeholder="输入新密码"
        />
      </el-form-item>
      
      <el-form-item label="确认新密码">
        <el-input 
          v-model="userForm.confirmPassword" 
          type="password"
          placeholder="再次输入新密码"
        />
        <el-button type="primary" size="small" @click="handleUpdatePassword" :loading="updatingPassword">
          修改密码
        </el-button>
      </el-form-item>
    </el-form>
    
    <!-- 阅读器设置 -->
    <el-divider>阅读器设置</el-divider>
    
    <el-form label-width="120px">
      <!-- 字体设置 -->
      <el-form-item label="字体">
        <el-select v-model="localSettings.fontFamily" placeholder="选择字体">
          <el-option label="Arial" value="Arial" />
          <el-option label="微软雅黑" value="Microsoft YaHei" />
          <el-option label="宋体" value="SimSun" />
          <el-option label="黑体" value="SimHei" />
          <el-option label="楷体" value="KaiTi" />
        </el-select>
      </el-form-item>
      
      <!-- 字号设置 -->
      <el-form-item label="字号">
        <el-slider 
          v-model="localSettings.fontSize" 
          :min="14" 
          :max="96" 
          :step="1"
          show-input
        />
      </el-form-item>
      
      <!-- 行高设置 -->
      <el-form-item label="行高">
        <el-slider 
          v-model="localSettings.lineHeight" 
          :min="2" 
          :max="4" 
          :step="0.1"
          show-input
        />
      </el-form-item>
      
      <!-- 字间距设置 -->
      <el-form-item label="字间距">
        <el-slider 
          v-model="localSettings.letterSpacing" 
          :min="0" 
          :max="2" 
          :step="0.1"
          show-input
        />
      </el-form-item>
      
      <!-- 意群间距设置 -->
      <el-form-item label="意群间距">
        <el-slider 
          v-model="localSettings.wordSpacing" 
          :min="50" 
          :max="120" 
          :step="1"
          show-input
        />
      </el-form-item>
      
      <!-- 背景颜色设置 -->
      <el-form-item label="背景颜色">
        <el-color-picker v-model="localSettings.backgroundColor" />
      </el-form-item>
      
      <!-- 文本颜色设置 -->
      <el-form-item label="文本颜色">
        <el-color-picker v-model="localSettings.textColor" />
      </el-form-item>
      
      <!-- 配色方案 -->
      <el-form-item label="配色方案">
        <el-radio-group v-model="localSettings.colorScheme">
          <el-radio label="default">默认</el-radio>
          <el-radio label="eye">护眼模式</el-radio>
          <el-radio label="high-contrast">高对比度</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 功能设置 -->
      <el-form-item label="功能设置">
        <el-checkbox-group v-model="functionSettings">
          <el-checkbox label="posTagging">词性标注</el-checkbox>
          <el-checkbox label="enableMask">蒙版功能</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      
      <!-- 蒙版设置 -->
      <el-form-item label="蒙版行数" v-if="localSettings.enableMask">
        <el-slider 
          v-model="localSettings.maskLines" 
          :min="1" 
          :max="5" 
          :step="1"
          show-input
        />
        <div class="setting-hint">设置全屏模式下中央可见的文本行数</div>
      </el-form-item>
      
      <el-form-item label="蒙版透明度" v-if="localSettings.enableMask">
        <el-slider 
          v-model="localSettings.maskOpacity" 
          :min="0.5" 
          :max="0.9" 
          :step="0.1"
          show-input
        />
      </el-form-item>
      
      <!-- 排版模式 -->
      <el-form-item label="排版模式">
        <el-radio-group v-model="localSettings.typesettingMode">
          <el-radio label="normal">整齐排版</el-radio>
          <el-radio label="staggered">错落排版</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 词性标注设置 -->
      <template v-if="localSettings.posTagging">
        <el-divider>词性标注设置</el-divider>
        
        <!-- 词性选择 -->
        <el-form-item label="选择标注词性">
          <el-checkbox-group v-model="localSettings.selectedPosTags">
            <el-checkbox label="n">名词</el-checkbox>
            <el-checkbox label="v">动词</el-checkbox>
            <el-checkbox label="a">形容词</el-checkbox>
            <el-checkbox label="d">副词</el-checkbox>
            <el-checkbox label="p">介词</el-checkbox>
            <el-checkbox label="c">连词</el-checkbox>
            <el-checkbox label="u">助词</el-checkbox>
            <el-checkbox label="r">代词</el-checkbox>
            <el-checkbox label="m">数词</el-checkbox>
            <el-checkbox label="q">量词</el-checkbox>
            <el-checkbox label="t">时间词</el-checkbox>
            <el-checkbox label="s">处所词</el-checkbox>
            <el-checkbox label="f">方位词</el-checkbox>
            <el-checkbox label="b">区别词</el-checkbox>
            <el-checkbox label="z">状态词</el-checkbox>
            <el-checkbox label="e">叹词</el-checkbox>
            <el-checkbox label="y">语气词</el-checkbox>
            <el-checkbox label="o">拟声词</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <!-- 选中词性的颜色和字号设置 -->
        <div class="pos-settings">
          <div v-for="key in localSettings.selectedPosTags" :key="key" class="pos-setting-item">
            <span class="pos-label">{{ posTypes[key] }}</span>
            <div class="pos-controls">
              <el-color-picker 
                v-model="localSettings.posColors[key]" 
                size="small"
                show-alpha
              />
              <el-slider 
                v-model="localSettings.posFontSizes[key]" 
                :min="12" 
                :max="24" 
                :step="1"
                show-input
                class="pos-size-slider"
              />
            </div>
          </div>
        </div>
      </template>
      
      <!-- 语音设置 -->
      <el-divider>语音设置</el-divider>
      
      <el-form-item label="TTS提供商">
        <span class="setting-value">pyttsx3</span>
        <div class="setting-hint">
          pyttsx3：免费、离线可用，响应速度快，语音质量良好
        </div>
      </el-form-item>
      
      <el-form-item label="语音速度">
        <el-slider 
          v-model="localSettings.speechRate" 
          :min="0.5" 
          :max="2" 
          :step="0.1"
          show-input
        />
        <span class="setting-hint">0.5x - 2.0x</span>
      </el-form-item>
      
      <el-form-item label="语音音量">
        <el-slider 
          v-model="localSettings.speechVolume" 
          :min="0" 
          :max="1" 
          :step="0.1"
          show-input
        />
        <span class="setting-hint">0 - 1.0</span>
      </el-form-item>
      
      <el-divider>快捷键说明</el-divider>
      
      <div class="shortcuts-section">
        <h4>常用快捷键</h4>
        <el-table :data="shortcuts" border style="width: 100%">
          <el-table-column prop="key" label="快捷键" width="120" />
          <el-table-column prop="description" label="功能描述" />
        </el-table>
      </div>
      
      <el-form-item>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
        <el-button @click="resetSettings">重置默认</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '../stores/appStore'
import { ElMessage } from 'element-plus'
import { updateUsername, updatePassword } from '../utils/api'

const appStore = useAppStore()

// 用户信息
const user = computed(() => appStore.user)

// 用户表单
const userForm = ref({
  newUsername: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 加载状态
const updatingUsername = ref(false)
const updatingPassword = ref(false)

// 快捷键列表
const shortcuts = [
  { key: 'Ctrl+S', description: '保存当前文档' },
  { key: 'Ctrl+O', description: '打开文件' },
  { key: 'Ctrl+E', description: '导出文件' },
  { key: 'Ctrl+P', description: '开始/暂停朗读' },
  { key: 'Ctrl+Q', description: '停止朗读' },
  { key: 'Ctrl++', description: '增大字体' },
  { key: 'Ctrl+-', description: '减小字体' },
  { key: 'Ctrl+0', description: '恢复默认字体大小' },
  { key: 'F1', description: '打开帮助文档' },
  { key: 'F2', description: '打开设置面板' },
  { key: 'F3', description: '切换全屏阅读模式' }
]

// 词性类型
const posTypes = ref({
  'n': '名词',
  'v': '动词',
  'a': '形容词',
  'd': '副词',
  'p': '介词',
  'c': '连词',
  'u': '助词',
  'r': '代词',
  'm': '数词',
  'q': '量词',
  't': '时间词',
  's': '处所词',
  'f': '方位词',
  'b': '区别词',
  'z': '状态词',
  'e': '叹词',
  'y': '语气词',
  'o': '拟声词',
  'h': '前缀',
  'k': '后缀',
  'x': '标点符号',
  'w': '其他'
})

// 默认词性颜色
const defaultPosColors = {
  'n': '#E74C3C',  // 名词 - 红色
  'v': '#3498DB',  // 动词 - 蓝色
  'a': '#2ECC71',  // 形容词 - 绿色
  'd': '#F39C12',  // 副词 - 橙色
  'p': '#9B59B6',  // 介词 - 紫色
  'c': '#1ABC9C',  // 连词 - 青色
  'u': '#95A5A6',  // 助词 - 灰色
  'r': '#E67E22',  // 代词 - 深橙色
  'm': '#34495E',  // 数词 - 深蓝灰
  'q': '#16A085',  // 量词 - 深青色
  't': '#D35400',  // 时间词 - 深橙色
  's': '#27AE60',  // 处所词 - 深绿色
  'f': '#8E44AD',  // 方位词 - 深紫色
  'b': '#C0392B',  // 区别词 - 深红色
  'z': '#2980B9',  // 状态词 - 深蓝色
  'e': '#F1C40F',  // 叹词 - 黄色
  'y': '#BDC3C7',  // 语气词 - 浅灰色
  'o': '#7F8C8D',  // 拟声词 - 灰色
  'h': '#A569BD',  // 前缀 - 浅紫色
  'k': '#5DADE2',  // 后缀 - 浅蓝色
  'x': '#566573',  // 标点符号 - 深灰
  'w': '#85929E'   // 其他 - 中灰色
}

// 本地设置
const localSettings = ref({
  fontFamily: 'Arial',
  fontSize: 20,
  lineHeight: 1.5,
  letterSpacing: 0,
  wordSpacing: 0,
  backgroundColor: '#ffffff',
  textColor: '#333333',
  colorScheme: 'default',
  enableChunk: true,
  chunkLevel: 2,  // 1=轻度, 2=中度, 3=高度
  enableMainContent: true,
  enableSimplify: false,
  posTagging: false,
  enableMask: false,
  maskLines: 3,
  maskOpacity: 0.7,
  typesettingMode: 'normal',
  posColors: { ...defaultPosColors },
  posFontSizes: {
    'n': 16, 'v': 16, 'a': 16, 'd': 16, 'p': 16, 'c': 16, 'u': 16, 'r': 16,
    'm': 16, 'q': 16, 't': 16, 's': 16, 'f': 16, 'b': 16, 'z': 16, 'e': 16,
    'y': 16, 'o': 16, 'h': 16, 'k': 16, 'x': 16, 'w': 16
  },
  selectedPosTags: ['n', 'v', 'a'],
  speechRate: 1.0,
  speechVolume: 1.0,
  ttsProvider: 'browser',
  selectedVoice: 'female',
  edgeVoice: 'zh-CN-XiaoxiaoNeural'
})

// 功能设置
const functionSettings = computed({
  get: () => {
    const settings = []
    if (localSettings.value.posTagging) settings.push('posTagging')
    if (localSettings.value.enableMask) settings.push('enableMask')
    return settings
  },
  set: (value) => {
    localSettings.value.posTagging = value.includes('posTagging')
    localSettings.value.enableMask = value.includes('enableMask')
  }
})

// 监听配色方案变化
watch(() => localSettings.value.colorScheme, (newScheme) => {
  switch (newScheme) {
    case 'eye':
      localSettings.value.backgroundColor = '#e8f4ea'
      localSettings.value.textColor = '#2d5a36'
      break
    case 'high-contrast':
      localSettings.value.backgroundColor = '#000000'
      localSettings.value.textColor = '#ffffff'
      break
    default:
      localSettings.value.backgroundColor = '#ffffff'
      localSettings.value.textColor = '#333333'
      break
  }
})

// 修改用户名
const handleUpdateUsername = async () => {
  if (!userForm.value.newUsername.trim()) {
    ElMessage.error('请输入新用户名')
    return
  }
  
  if (userForm.value.newUsername === user.value?.username) {
    ElMessage.warning('新用户名与当前用户名相同')
    return
  }
  
  updatingUsername.value = true
  try {
    await updateUsername(userForm.value.newUsername)
    ElMessage.success('用户名修改成功')
    // 更新本地用户信息
    appStore.user = { ...appStore.user, username: userForm.value.newUsername }
    // 清空输入
    userForm.value.newUsername = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改用户名失败')
  } finally {
    updatingUsername.value = false
  }
}

// 修改密码
const handleUpdatePassword = async () => {
  if (!userForm.value.oldPassword) {
    ElMessage.error('请输入旧密码')
    return
  }
  
  if (!userForm.value.newPassword) {
    ElMessage.error('请输入新密码')
    return
  }
  
  if (userForm.value.newPassword !== userForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  updatingPassword.value = true
  try {
    await updatePassword(userForm.value.oldPassword, userForm.value.newPassword)
    ElMessage.success('密码修改成功')
    // 清空输入
    userForm.value.oldPassword = ''
    userForm.value.newPassword = ''
    userForm.value.confirmPassword = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    updatingPassword.value = false
  }
}

// 方法
const saveSettings = () => {
  appStore.updateReaderSettings(localSettings.value)
  ElMessage.success('设置保存成功')
}

const resetSettings = () => {
  localSettings.value = {
    fontFamily: 'Arial',
    fontSize: 20,
    lineHeight: 1.5,
    letterSpacing: 0,
    wordSpacing: 0,
    backgroundColor: '#ffffff',
    textColor: '#333333',
    colorScheme: 'default',
    enableChunk: true,
    chunkLevel: 2,  // 1=轻度, 2=中度, 3=高度
    enableMainContent: true,
    enableSimplify: false,
    posTagging: false,
    enableMask: false,
    maskLines: 3,
    maskOpacity: 0.7,
    typesettingMode: 'normal',
    posColors: { ...defaultPosColors },
    posFontSizes: {
      'n': 16, 'v': 16, 'a': 16, 'd': 16, 'p': 16, 'c': 16, 'u': 16, 'r': 16,
      'm': 16, 'q': 16, 't': 16, 's': 16, 'f': 16, 'b': 16, 'z': 16, 'e': 16,
      'y': 16, 'o': 16, 'h': 16, 'k': 16, 'x': 16, 'w': 16
    },
    selectedPosTags: ['n', 'v', 'a'],
    speechRate: 1.0,
    speechVolume: 1.0,
    ttsProvider: 'pyttsx3',
    selectedVoice: 'female'
  }
  ElMessage.info('已重置为默认设置')
}

// 生命周期
onMounted(async () => {
  // 加载阅读器设置（先从localStorage加载，再从后端同步）
  const localStorageSettings = localStorage.getItem('readerSettings')
  let initialSettings = {}
  
  // 优先使用localStorage中的设置
  if (localStorageSettings) {
    try {
      initialSettings = JSON.parse(localStorageSettings)
    } catch (e) {
      console.error('解析localStorage设置失败:', e)
    }
  }
  
  // 从后端加载设置
  try {
    await appStore.loadReaderSettings()
    // 合并后端设置，但不覆盖localStorage中的设置
    const backendSettings = { ...appStore.readerSettings }
    
    // 只有当localStorage中没有对应设置时，才使用后端设置
    for (const key of Object.keys(backendSettings)) {
      if (initialSettings[key] === undefined) {
        initialSettings[key] = backendSettings[key]
      }
    }
  } catch (e) {
    console.error('从后端加载设置失败:', e)
    // 如果后端加载失败，继续使用localStorage中的设置
  }
  
  // 更新本地设置
  localSettings.value = { ...initialSettings }
  
  // 确保posColors存在（仅当未定义时）
  if (typeof localSettings.value.posColors === 'undefined') {
    localSettings.value.posColors = { ...defaultPosColors }
  }
  
  // 确保posFontSizes存在（仅当未定义时）
  if (typeof localSettings.value.posFontSizes === 'undefined') {
    localSettings.value.posFontSizes = {
      'n': 16, 'v': 16, 'a': 16, 'd': 16, 'p': 16, 'c': 16, 'u': 16, 'r': 16,
      'm': 16, 'q': 16, 't': 16, 's': 16, 'f': 16, 'b': 16, 'z': 16, 'e': 16,
      'y': 16, 'o': 16, 'h': 16, 'k': 16, 'x': 16, 'w': 16
    }
  }
  
  // 确保selectedPosTags存在（仅当未定义时）
  if (typeof localSettings.value.selectedPosTags === 'undefined') {
    localSettings.value.selectedPosTags = ['n', 'v', 'a']
  }
  
  // 确保其他必要字段存在（仅当未定义时）
  if (typeof localSettings.value.fontFamily === 'undefined') localSettings.value.fontFamily = 'Arial'
  if (typeof localSettings.value.fontSize === 'undefined') localSettings.value.fontSize = 16
  if (typeof localSettings.value.lineHeight === 'undefined') localSettings.value.lineHeight = 1.5
  if (typeof localSettings.value.letterSpacing === 'undefined') localSettings.value.letterSpacing = 0
  if (typeof localSettings.value.wordSpacing === 'undefined') localSettings.value.wordSpacing = 0
  if (typeof localSettings.value.backgroundColor === 'undefined') localSettings.value.backgroundColor = '#ffffff'
  if (typeof localSettings.value.textColor === 'undefined') localSettings.value.textColor = '#333333'
  
  // 确保TTS提供商不为browser（已删除）
  if (typeof localSettings.value.ttsProvider === 'undefined' || localSettings.value.ttsProvider === 'browser') {
    localSettings.value.ttsProvider = 'pyttsx3'
  }
  
  if (typeof localSettings.value.colorScheme === 'undefined') localSettings.value.colorScheme = 'default'
  if (typeof localSettings.value.enableChunk === 'undefined') localSettings.value.enableChunk = true
  if (typeof localSettings.value.chunkLevel === 'undefined') localSettings.value.chunkLevel = 2  // 1=轻度, 2=中度, 3=高度
  if (typeof localSettings.value.enableMainContent === 'undefined') localSettings.value.enableMainContent = false
  if (typeof localSettings.value.enableSimplify === 'undefined') localSettings.value.enableSimplify = false
  if (typeof localSettings.value.posTagging === 'undefined') localSettings.value.posTagging = false
  if (typeof localSettings.value.enableMask === 'undefined') localSettings.value.enableMask = false
  if (typeof localSettings.value.maskLines === 'undefined') localSettings.value.maskLines = 3
  if (typeof localSettings.value.maskOpacity === 'undefined') localSettings.value.maskOpacity = 0.7
  if (typeof localSettings.value.typesettingMode === 'undefined') localSettings.value.typesettingMode = 'normal'
  if (typeof localSettings.value.speechRate === 'undefined') localSettings.value.speechRate = 1.0
  if (typeof localSettings.value.speechVolume === 'undefined') localSettings.value.speechVolume = 1.0
  if (typeof localSettings.value.selectedVoice === 'undefined') localSettings.value.selectedVoice = 'female'
})
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.settings-container h2 {
  margin-bottom: 2rem;
  color: #333;
}

.el-form {
  max-width: 600px;
}

.user-info-form {
  margin-bottom: 1rem;
}

.setting-value {
  color: #666;
  font-size: 14px;
}

.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.el-checkbox {
  margin-right: 1rem;
  margin-bottom: 0.5rem;
}

.pos-settings {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.pos-setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.pos-setting-item:last-child {
  margin-bottom: 0;
}

.pos-label {
  width: 80px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.pos-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.pos-size-slider {
  width: 200px;
}
</style>
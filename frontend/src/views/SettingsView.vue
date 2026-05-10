<template>
  <div class="settings-container">
    <h2>设置</h2>
    
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

const appStore = useAppStore()

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
  // 加载阅读器设置
  await appStore.loadReaderSettings()
  // 更新本地设置
  localSettings.value = { ...appStore.readerSettings }
  // 确保posColors存在
  if (!localSettings.value.posColors) {
    localSettings.value.posColors = { ...defaultPosColors }
  }
  // 确保posFontSizes存在
  if (!localSettings.value.posFontSizes) {
    localSettings.value.posFontSizes = {
      'n': 16, 'v': 16, 'a': 16, 'd': 16, 'p': 16, 'c': 16, 'u': 16, 'r': 16,
      'm': 16, 'q': 16, 't': 16, 's': 16, 'f': 16, 'b': 16, 'z': 16, 'e': 16,
      'y': 16, 'o': 16, 'h': 16, 'k': 16, 'x': 16, 'w': 16
    }
  }
  // 确保selectedPosTags存在
  if (!localSettings.value.selectedPosTags) {
    localSettings.value.selectedPosTags = ['n', 'v', 'a']
  }
  // 确保其他必要字段存在
  if (!localSettings.value.fontFamily) localSettings.value.fontFamily = 'Arial'
  if (!localSettings.value.fontSize) localSettings.value.fontSize = 16
  if (!localSettings.value.lineHeight) localSettings.value.lineHeight = 1.5
  if (!localSettings.value.letterSpacing) localSettings.value.letterSpacing = 0
  if (!localSettings.value.wordSpacing) localSettings.value.wordSpacing = 0
  if (!localSettings.value.backgroundColor) localSettings.value.backgroundColor = '#ffffff'
  if (!localSettings.value.textColor) localSettings.value.textColor = '#333333'
  // 确保TTS提供商不为browser（已删除）
  if (!localSettings.value.ttsProvider || localSettings.value.ttsProvider === 'browser') {
    localSettings.value.ttsProvider = 'pyttsx3'
  }
  if (!localSettings.value.colorScheme) localSettings.value.colorScheme = 'default'
  if (!localSettings.value.enableChunk) localSettings.value.enableChunk = true
  if (!localSettings.value.chunkLevel) localSettings.value.chunkLevel = 2  // 1=轻度, 2=中度, 3=高度
  if (!localSettings.value.enableMainContent) localSettings.value.enableMainContent = false
  if (!localSettings.value.enableSimplify) localSettings.value.enableSimplify = false
  if (!localSettings.value.posTagging) localSettings.value.posTagging = false
  if (!localSettings.value.enableMask) localSettings.value.enableMask = false
  if (!localSettings.value.maskLines) localSettings.value.maskLines = 3
  if (!localSettings.value.maskOpacity) localSettings.value.maskOpacity = 0.7
  if (!localSettings.value.typesettingMode) localSettings.value.typesettingMode = 'normal'
  if (!localSettings.value.speechRate) localSettings.value.speechRate = 1.0
  if (!localSettings.value.speechVolume) localSettings.value.speechVolume = 1.0
  if (!localSettings.value.ttsProvider) localSettings.value.ttsProvider = 'pyttsx3'
  if (!localSettings.value.selectedVoice) localSettings.value.selectedVoice = 'female'
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

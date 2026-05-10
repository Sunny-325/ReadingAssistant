<template>
  <div class="reader-container">
    <h2>阅读器</h2>
    
    <!-- 词语查询输入 -->
    <div class="word-query">
      <el-input
        v-model="queryWord"
        placeholder="输入词语查询释义"
        @keyup.enter="handleQueryWord"
      >
        <template #append>
          <el-button @click="handleQueryWord">查询</el-button>
        </template>
      </el-input>
    </div>
    
    <!-- 阅读器主体 -->
    <div class="reader-main">
      <!-- 原文本面板 -->
      <div class="reader-panel">
        <div class="panel-header">
          <h3>原文本</h3>
          <div class="panel-controls">
            <el-button size="small" @click="isSpeakingOriginal ? stopOriginalSpeech() : startOriginalSpeech()" :disabled="false">
              <el-icon v-if="!isSpeakingOriginal"><Microphone /></el-icon>
              <el-icon v-else><Close /></el-icon>
              {{ isSpeakingOriginal ? ' 暂停' : ' 播放' }}
            </el-button>
            <el-button size="small" @click="toggleFullScreen('original')">
              <el-icon><FullScreen /></el-icon> 全屏
            </el-button>
          </div>
        </div>
        <div class="progress-container">
          <el-slider 
            v-model="originalProgress" 
            :min="0" 
            :max="100" 
            :disabled="!isSpeakingOriginal"
            @change="seekOriginalSpeech"
            :format-tooltip="(val) => val.toFixed(2) + '%'"
          />
        </div>
        <div 
          ref="originalContentRef"
          class="reader-content"
          :class="{ 'mask-active': isOriginalFullScreen && readerSettings.enableMask }"
          :style="{
            fontFamily: readerSettings.fontFamily,
            fontSize: readerSettings.fontSize + 'px',
            lineHeight: readerSettings.lineHeight,
            letterSpacing: readerSettings.letterSpacing + 'px',
            backgroundColor: readerSettings.backgroundColor,
            color: readerSettings.textColor,
            '--bg-color': readerSettings.backgroundColor,
            '--text-color': readerSettings.textColor
          }"
        >
          <!-- 蒙版覆盖层 - 只在全屏模式下显示 -->
          <div 
            v-if="isOriginalFullScreen && readerSettings.enableMask"
            class="reader-mask"
            :style="{ 
              '--mask-height': maskHeight, 
              '--mask-opacity': readerSettings.maskOpacity,
              '--bg-color': readerSettings.backgroundColor,
              '--text-color': readerSettings.textColor
            }"
          ></div>
          
          <!-- 全屏控制按钮 - 只在全屏模式下显示 -->
          <div v-if="isOriginalFullScreen" class="fullscreen-top-controls">
            <el-button size="small" @click.stop="toggleFullScreenSettings">
              <el-icon><Setting /></el-icon> 设置
            </el-button>
            <el-button size="small" @click="toggleFullScreen('original')">
              <el-icon><Close /></el-icon> 退出
            </el-button>
          </div>
          
          <!-- 全屏播放按钮 - 底部中央 -->
          <div v-if="isOriginalFullScreen" class="fullscreen-play-control">
            <el-button 
              circle 
              size="large" 
              @click="isSpeakingOriginal ? stopOriginalSpeech() : startOriginalSpeech()"
              class="play-button"
            >
              <el-icon v-if="!isSpeakingOriginal" :size="24"><VideoPlay /></el-icon>
              <el-icon v-else :size="24"><VideoPause /></el-icon>
            </el-button>
          </div>
          
          <!-- 上下滚动按钮 - 只在全屏模式且开启蒙版时显示 -->
          <div v-if="isOriginalFullScreen && readerSettings.enableMask" class="scroll-controls">
            <el-button size="small" @click="scrollUp('original')" class="scroll-button scroll-button-up" :style="scrollButtonStyles">
              <el-icon><ArrowUp /></el-icon>
            </el-button>
            <el-button size="small" @click="scrollDown('original')" class="scroll-button scroll-button-down" :style="scrollButtonStyles">
              <el-icon><ArrowDown /></el-icon>
            </el-button>
          </div>
          
          <!-- 全屏设置面板 -->
          <div v-if="isOriginalFullScreen && showFullScreenSettings" class="fullscreen-settings-panel">
            <h3>阅读设置</h3>
            
            <!-- 字体设置 -->
            <div class="setting-item">
              <label>字体</label>
              <select :value="appStore.readerSettings.fontFamily" @change="appStore.updateReaderSettings({ fontFamily: $event.target.value })" class="font-select">
                <option value="Arial">Arial</option>
                <option value="Microsoft YaHei">微软雅黑</option>
                <option value="SimSun">宋体</option>
                <option value="SimHei">黑体</option>
                <option value="KaiTi">楷体</option>
              </select>
            </div>
            
            <!-- 字号设置 -->
            <div class="setting-item">
              <label>字号: {{ readerSettings.fontSize }}px</label>
              <el-slider 
                v-model="readerSettings.fontSize" 
                :min="14" 
                :max="96" 
                :step="1"
              />
            </div>
            
            <!-- 行高设置 -->
            <div class="setting-item">
              <label>行高: {{ readerSettings.lineHeight }}</label>
              <el-slider 
                v-model="readerSettings.lineHeight" 
                :min="2" 
                :max="4" 
                :step="0.1"
              />
            </div>
            
            <!-- 字间距设置 -->
            <div class="setting-item">
              <label>字间距: {{ readerSettings.letterSpacing }}px</label>
              <el-slider 
                v-model="readerSettings.letterSpacing" 
                :min="0" 
                :max="2" 
                :step="0.1"
              />
            </div>
            
            <!-- 意群间距设置 -->
            <div class="setting-item">
              <label>意群间距: {{ readerSettings.wordSpacing }}px</label>
              <el-slider 
                v-model="readerSettings.wordSpacing" 
                :min="50" 
                :max="120" 
                :step="1"
              />
            </div>
            
            <!-- 背景颜色设置 -->
            <div class="setting-item">
              <label>背景颜色</label>
              <el-color-picker v-model="readerSettings.backgroundColor" size="small" />
            </div>
            
            <!-- 文本颜色设置 -->
            <div class="setting-item">
              <label>文本颜色</label>
              <el-color-picker v-model="readerSettings.textColor" size="small" />
            </div>
            
            <!-- 配色方案 -->
            <div class="setting-item">
              <label>配色方案</label>
              <el-radio-group v-model="readerSettings.colorScheme" size="small">
                <el-radio label="default">默认</el-radio>
                <el-radio label="eye">护眼模式</el-radio>
                <el-radio label="high-contrast">高对比度</el-radio>
              </el-radio-group>
            </div>
            
            <!-- 功能设置 -->
            <div class="setting-item">
              <label>功能设置</label>
              <el-checkbox v-model="readerSettings.enableMask">蒙版功能</el-checkbox>
              <el-checkbox v-model="readerSettings.posTagging">词性标注</el-checkbox>
            </div>
            
            <!-- 蒙版设置 -->
            <div class="setting-item" v-if="readerSettings.enableMask">
              <label>可见行数: {{ readerSettings.maskLines }}</label>
              <el-slider 
                v-model="readerSettings.maskLines" 
                :min="1" 
                :max="5" 
                :step="1"
              />
            </div>
            
            <div class="setting-item" v-if="readerSettings.enableMask">
              <label>蒙版透明度: {{ readerSettings.maskOpacity }}</label>
              <el-slider 
                v-model="readerSettings.maskOpacity" 
                :min="0.5" 
                :max="0.9" 
                :step="0.1"
              />
            </div>
            
            <!-- 排版模式 -->
            <div class="setting-item">
              <label>排版模式</label>
              <el-radio-group v-model="readerSettings.typesettingMode" size="small">
                <el-radio label="normal">整齐排版</el-radio>
                <el-radio label="staggered">错落排版</el-radio>
              </el-radio-group>
            </div>
            
            <!-- 语音设置 -->
            <div class="setting-item">
              <label>TTS提供商</label>
              <span class="setting-value">pyttsx3</span>
            </div>
            
            <div class="setting-item">
              <label>语音速度: {{ readerSettings.speechRate }}x</label>
              <el-slider 
                v-model="readerSettings.speechRate" 
                :min="0.5" 
                :max="2" 
                :step="0.1"
              />
            </div>
          </div>
          
          <!-- 直接显示文档中已有的处理结果 -->
          <template v-if="currentOriginalSegments.length > 0">
            <span 
              v-for="(segment, index) in currentOriginalSegments" 
              :key="segment.id"
              class="text-segment"
              :data-segment-id="segment.id"
              :class="{
                'primary-content': readerSettings.enableMainContent && segment.is_primary === true,
                'secondary-content': readerSettings.enableMainContent && segment.is_primary === false,
                'staggered-item': readerSettings.typesettingMode === 'staggered',
                'highlighted-segment': currentOriginalSegment === segment.id
              }"
              :style="{
                marginLeft: readerSettings.typesettingMode === 'staggered' ? (index % 2 === 0 ? '0px' : '30px') : '0',
                textAlign: 'left',
                marginRight: readerSettings.wordSpacing + 'px'
              }"
              @click="handleSegmentClick(segment)"
            >
              <!-- 显示带有词性标注的文本 -->
              <template v-if="readerSettings.posTagging && currentDocument.pos_tags && currentDocument.pos_tags.length > 0">
                <span 
                  v-for="word in getSegmentWords(segment.text, segment.start_pos || 0, false)" 
                  :key="word.position"
                  :class="['word-tag', getPosClass(word.text, word.position)]"
                  :style="getPosFontSize(word.text, word.position)"
                >
                  {{ word.text }}
                </span>
              </template>
              <template v-else>
                {{ segment.text || ' ' }}
              </template>
            </span>
          </template>
          <template v-else-if="segments.length > 0">
            <!-- 如果currentOriginalSegments为空但segments有数据，直接显示segments -->
            <span 
              v-for="(segment, index) in segments" 
              :key="segment.id"
              class="text-segment"
              :data-segment-id="segment.id"
              :class="{
                'primary-content': readerSettings.enableMainContent && segment.is_primary === true,
                'secondary-content': readerSettings.enableMainContent && segment.is_primary === false,
                'staggered-item': readerSettings.typesettingMode === 'staggered',
                'highlighted-segment': currentOriginalSegment === segment.id
              }"
              :style="{
                marginLeft: readerSettings.typesettingMode === 'staggered' ? (index % 2 === 0 ? '0px' : '30px') : '0',
                textAlign: 'left',
                marginRight: readerSettings.wordSpacing + 'px'
              }"
              @click="handleSegmentClick(segment)"
            >
              <!-- 显示带有词性标注的文本 -->
              <template v-if="readerSettings.posTagging && currentDocument.pos_tags && currentDocument.pos_tags.length > 0">
                <span 
                  v-for="word in getSegmentWords(segment.text, segment.start_pos || 0, false)" 
                  :key="word.position"
                  :class="['word-tag', getPosClass(word.text, word.position)]"
                  :style="getPosFontSize(word.text, word.position)"
                >
                  {{ word.text }}
                </span>
              </template>
              <template v-else>
                {{ segment.text || ' ' }}
              </template>
            </span>
          </template>
          <template v-else-if="readerSettings.posTagging && currentDocument.pos_tags && currentDocument.pos_tags.length > 0">
            <span>
              <span 
                v-for="(tag, index) in currentDocument.pos_tags" 
                :key="index"
                :class="['word-tag', getPosClass(tag.word, tag.start_pos)]"
                :style="getPosFontSize(tag.word, tag.start_pos)"
              >
                {{ tag.word }}
              </span>
            </span>
          </template>
          <template v-else>
            <span>{{ currentDocument.content }}</span>
          </template>
          
          <!-- 分页控制 -->
          <div class="pagination-controls">
            <el-button 
              size="small" 
              :disabled="paginationState.original.currentPage === 1" 
              @click="prevPage('original')"
            >
              <el-icon><ArrowLeft /></el-icon> 上一页
            </el-button>
            <span class="page-info">
              {{ paginationState.original.currentPage }} / {{ paginationState.original.totalPages }}
            </span>
            <el-button 
              size="small" 
              :disabled="paginationState.original.currentPage === paginationState.original.totalPages" 
              @click="nextPage('original')"
            >
              下一页 <el-icon><ArrowRight /></el-icon>
            </el-button>
            <el-button 
              size="small" 
              @click="openTocDialog('original')"
            >
              <el-icon><List /></el-icon> 目录
            </el-button>
          </div>
          
          <!-- 目录对话框 - 用于全屏模式 -->
          <el-dialog
            v-model="showTocDialog"
            title="目录"
            width="400px"
            class="toc-dialog"
          >
            <div class="toc-container">
              <div class="toc-header">
                <span>共 {{ paginationState[currentTocType].totalPages }} 页</span>
                <span class="toc-progress">{{ Math.round(paginationState[currentTocType].currentPage / paginationState[currentTocType].totalPages * 100) }}%</span>
              </div>
              <div class="toc-list">
                <div 
                  v-for="page in paginationState[currentTocType].totalPages" 
                  :key="page"
                  class="toc-item"
                  :class="{ 'active': page === paginationState[currentTocType].currentPage }"
                  @click="jumpToPage(currentTocType, page)"
                >
                  <span class="toc-page">第 {{ page }} 页</span>
                  <span v-if="page === paginationState[currentTocType].currentPage" class="toc-current">当前</span>
                </div>
              </div>
            </div>
          </el-dialog>
        </div>
      </div>
      
      <!-- 简化文本面板 - 如果有简化文本内容就显示 -->
      <div v-if="currentDocument.simplifiedContent" class="reader-panel">
        <div class="panel-header">
          <h3>简化文本</h3>
          <div class="panel-controls">
            <el-button size="small" @click="isSpeakingSimplified ? stopSimplifiedSpeech() : startSimplifiedSpeech()" :disabled="false">
              <el-icon v-if="!isSpeakingSimplified"><Microphone /></el-icon>
              <el-icon v-else><Close /></el-icon>
              {{ isSpeakingSimplified ? ' 暂停' : ' 播放' }}
            </el-button>
            <el-button size="small" @click="toggleFullScreen('simplified')">
              <el-icon><FullScreen /></el-icon> 全屏
            </el-button>
          </div>
        </div>
        <div class="progress-container">
          <el-slider 
            v-model="simplifiedProgress" 
            :min="0" 
            :max="100" 
            :disabled="!isSpeakingSimplified"
            @change="seekSimplifiedSpeech"
            :format-tooltip="(val) => val.toFixed(2) + '%'"
          />
        </div>
        <div 
          ref="simplifiedContentRef"
          class="reader-content"
          :class="{ 'mask-active': isSimplifiedFullScreen && readerSettings.enableMask }"
          :style="{
            fontFamily: readerSettings.fontFamily,
            fontSize: readerSettings.fontSize + 'px',
            lineHeight: readerSettings.lineHeight,
            letterSpacing: readerSettings.letterSpacing + 'px',
            backgroundColor: readerSettings.backgroundColor,
            color: readerSettings.textColor,
            '--bg-color': readerSettings.backgroundColor,
            '--text-color': readerSettings.textColor
          }"
        >
          <!-- 蒙版覆盖层 - 只在全屏模式下显示 -->
          <div 
            v-if="isSimplifiedFullScreen && readerSettings.enableMask"
            class="reader-mask"
            :style="{ 
              '--mask-height': maskHeight, 
              '--mask-opacity': readerSettings.maskOpacity,
              '--bg-color': readerSettings.backgroundColor,
              '--text-color': readerSettings.textColor
            }"
          ></div>
          
          <!-- 全屏控制按钮 - 只在全屏模式下显示 -->
          <div v-if="isSimplifiedFullScreen" class="fullscreen-top-controls">
            <el-button size="small" @click.stop="toggleFullScreenSettings">
              <el-icon><Setting /></el-icon> 设置
            </el-button>
            <el-button size="small" @click="toggleFullScreen('simplified')">
              <el-icon><Close /></el-icon> 退出
            </el-button>
          </div>
          
          <!-- 全屏播放按钮 - 底部中央 -->
          <div v-if="isSimplifiedFullScreen" class="fullscreen-play-control">
            <el-button 
              circle 
              size="large" 
              @click="isSpeakingSimplified ? stopSimplifiedSpeech() : startSimplifiedSpeech()"
              class="play-button"
            >
              <el-icon v-if="!isSpeakingSimplified" :size="24"><VideoPlay /></el-icon>
              <el-icon v-else :size="24"><VideoPause /></el-icon>
            </el-button>
          </div>
          
          <!-- 上下滚动按钮 - 只在全屏模式且开启蒙版时显示 -->
          <div v-if="isSimplifiedFullScreen && readerSettings.enableMask" class="scroll-controls">
            <el-button size="small" @click="scrollUp('simplified')" class="scroll-button scroll-button-up" :style="scrollButtonStyles">
              <el-icon><ArrowUp /></el-icon>
            </el-button>
            <el-button size="small" @click="scrollDown('simplified')" class="scroll-button scroll-button-down" :style="scrollButtonStyles">
              <el-icon><ArrowDown /></el-icon>
            </el-button>
          </div>
          
          <!-- 全屏设置面板 -->
          <div v-if="isSimplifiedFullScreen && showFullScreenSettings" class="fullscreen-settings-panel">
            <h3>阅读设置</h3>
            
            <!-- 字体设置 -->
            <div class="setting-item">
              <label>字体</label>
              <select :value="appStore.readerSettings.fontFamily" @change="appStore.updateReaderSettings({ fontFamily: $event.target.value })" class="font-select">
                <option value="Arial">Arial</option>
                <option value="Microsoft YaHei">微软雅黑</option>
                <option value="SimSun">宋体</option>
                <option value="SimHei">黑体</option>
                <option value="KaiTi">楷体</option>
              </select>
            </div>
            
            <!-- 字号设置 -->
            <div class="setting-item">
              <label>字号: {{ readerSettings.fontSize }}px</label>
              <el-slider 
                v-model="readerSettings.fontSize" 
                :min="14" 
                :max="96" 
                :step="1"
              />
            </div>
            
            <!-- 行高设置 -->
            <div class="setting-item">
              <label>行高: {{ readerSettings.lineHeight }}</label>
              <el-slider 
                v-model="readerSettings.lineHeight" 
                :min="2" 
                :max="4" 
                :step="0.1"
              />
            </div>
            
            <!-- 字间距设置 -->
            <div class="setting-item">
              <label>字间距: {{ readerSettings.letterSpacing }}px</label>
              <el-slider 
                v-model="readerSettings.letterSpacing" 
                :min="0" 
                :max="2" 
                :step="0.1"
              />
            </div>
            
            <!-- 意群间距设置 -->
            <div class="setting-item">
              <label>意群间距: {{ readerSettings.wordSpacing }}px</label>
              <el-slider 
                v-model="readerSettings.wordSpacing" 
                :min="50" 
                :max="120" 
                :step="1"
              />
            </div>
            
            <!-- 背景颜色设置 -->
            <div class="setting-item">
              <label>背景颜色</label>
              <el-color-picker v-model="readerSettings.backgroundColor" size="small" />
            </div>
            
            <!-- 文本颜色设置 -->
            <div class="setting-item">
              <label>文本颜色</label>
              <el-color-picker v-model="readerSettings.textColor" size="small" />
            </div>
            
            <!-- 配色方案 -->
            <div class="setting-item">
              <label>配色方案</label>
              <el-radio-group v-model="readerSettings.colorScheme" size="small">
                <el-radio label="default">默认</el-radio>
                <el-radio label="eye">护眼模式</el-radio>
                <el-radio label="high-contrast">高对比度</el-radio>
              </el-radio-group>
            </div>
            
            <!-- 功能设置 -->
            <div class="setting-item">
              <label>功能设置</label>
              <el-checkbox v-model="readerSettings.enableMask">蒙版功能</el-checkbox>
              <el-checkbox v-model="readerSettings.posTagging">词性标注</el-checkbox>
            </div>
            
            <!-- 蒙版设置 -->
            <div class="setting-item" v-if="readerSettings.enableMask">
              <label>可见行数: {{ readerSettings.maskLines }}</label>
              <el-slider 
                v-model="readerSettings.maskLines" 
                :min="1" 
                :max="5" 
                :step="1"
              />
            </div>
            
            <div class="setting-item" v-if="readerSettings.enableMask">
              <label>蒙版透明度: {{ readerSettings.maskOpacity }}</label>
              <el-slider 
                v-model="readerSettings.maskOpacity" 
                :min="0.5" 
                :max="0.9" 
                :step="0.1"
              />
            </div>
            
            <!-- 排版模式 -->
            <div class="setting-item">
              <label>排版模式</label>
              <el-radio-group v-model="readerSettings.typesettingMode" size="small">
                <el-radio label="normal">整齐排版</el-radio>
                <el-radio label="staggered">错落排版</el-radio>
              </el-radio-group>
            </div>
            
            <!-- 语音设置 -->
            <div class="setting-item">
              <label>TTS提供商</label>
              <span class="setting-value">pyttsx3</span>
            </div>
            
            <div class="setting-item">
              <label>语音速度: {{ readerSettings.speechRate }}x</label>
              <el-slider 
                v-model="readerSettings.speechRate" 
                :min="0.5" 
                :max="2" 
                :step="0.1"
              />
            </div>
          </div>
          
          <!-- 直接显示文档中已有的处理结果 -->
          <!-- 只有当启用了意群划分时才显示意群划分的样式 -->
          <template v-if="currentSimplifiedSegments.length > 0">
            <span 
              v-for="(segment, index) in currentSimplifiedSegments" 
              :key="segment.id"
              class="simplified-text-segment"
              :data-segment-id="segment.id"
              :class="{
                'primary-content': readerSettings.enableMainContent && segment.is_primary === true,
                'secondary-content': readerSettings.enableMainContent && segment.is_primary === false,
                'staggered-item': readerSettings.typesettingMode === 'staggered',
                'highlighted-segment': currentSimplifiedSegment === segment.id
              }"
              :style="{
                marginLeft: readerSettings.typesettingMode === 'staggered' ? (index % 2 === 0 ? '0px' : '30px') : '0',
                textAlign: 'left',
                marginRight: readerSettings.wordSpacing + 'px'
              }"
              @click="handleSegmentClick(segment)"
            >
              <!-- 显示带有词性标注的文本 -->
              <template v-if="readerSettings.posTagging && currentDocument.simplified_pos_tags && currentDocument.simplified_pos_tags.length > 0">
                <span 
                  v-for="word in getSegmentWords(segment.text, segment.start_pos || 0, true)" 
                  :key="word.position"
                  :class="['word-tag', getPosClass(word.text, word.position, true)]"
                  :style="getPosFontSize(word.text, word.position, true)"
                >
                  {{ word.text }}
                </span>
              </template>
              <template v-else>
                {{ segment.text || ' ' }}
              </template>
            </span>
          </template>
          <template v-else-if="simplifiedSegments.length > 0">
            <!-- 如果currentSimplifiedSegments为空但simplifiedSegments有数据，直接显示simplifiedSegments -->
            <span 
              v-for="(segment, index) in simplifiedSegments" 
              :key="segment.id"
              class="simplified-text-segment"
              :data-segment-id="segment.id"
              :class="{
                'primary-content': readerSettings.enableMainContent && segment.is_primary === true,
                'secondary-content': readerSettings.enableMainContent && segment.is_primary === false,
                'staggered-item': readerSettings.typesettingMode === 'staggered',
                'highlighted-segment': currentSimplifiedSegment === segment.id
              }"
              :style="{
                marginLeft: readerSettings.typesettingMode === 'staggered' ? (index % 2 === 0 ? '0px' : '30px') : '0',
                textAlign: 'left',
                marginRight: readerSettings.wordSpacing + 'px'
              }"
              @click="handleSegmentClick(segment)"
            >
              <!-- 显示带有词性标注的文本 -->
              <template v-if="readerSettings.posTagging && currentDocument.simplified_pos_tags && currentDocument.simplified_pos_tags.length > 0">
                <span 
                  v-for="word in getSegmentWords(segment.text, segment.start_pos || 0, true)" 
                  :key="word.position"
                  :class="['word-tag', getPosClass(word.text, word.position, true)]"
                  :style="getPosFontSize(word.text, word.position, true)"
                >
                  {{ word.text }}
                </span>
              </template>
              <template v-else>
                {{ segment.text || ' ' }}
              </template>
            </span>
          </template>
          <template v-else-if="readerSettings.posTagging && currentDocument.simplified_pos_tags && currentDocument.simplified_pos_tags.length > 0">
            <span>
              <span 
                v-for="(tag, index) in currentDocument.simplified_pos_tags" 
                :key="index"
                :class="['word-tag', getPosClass(tag.word, tag.start_pos, true)]"
                :style="getPosFontSize(tag.word, tag.start_pos, true)"
              >
                {{ tag.word }}
              </span>
            </span>
          </template>
          <template v-else>
            <span>{{ currentDocument.simplifiedContent }}</span>
          </template>
          
          <!-- 分页控制 -->
          <div class="pagination-controls">
            <el-button 
              size="small" 
              :disabled="paginationState.simplified.currentPage === 1" 
              @click="prevPage('simplified')"
            >
              <el-icon><ArrowLeft /></el-icon> 上一页
            </el-button>
            <span class="page-info">
              {{ paginationState.simplified.currentPage }} / {{ paginationState.simplified.totalPages }}
            </span>
            <el-button 
              size="small" 
              :disabled="paginationState.simplified.currentPage === paginationState.simplified.totalPages" 
              @click="nextPage('simplified')"
            >
              下一页 <el-icon><ArrowRight /></el-icon>
            </el-button>
            <el-button 
              size="small" 
              @click="openTocDialog('simplified')"
            >
              <el-icon><List /></el-icon> 目录
            </el-button>
          </div>
          
          <!-- 目录对话框 - 用于全屏模式 -->
          <el-dialog
            v-model="showTocDialog"
            title="目录"
            width="400px"
            class="toc-dialog"
          >
            <div class="toc-container">
              <div class="toc-header">
                <span>共 {{ paginationState[currentTocType].totalPages }} 页</span>
                <span class="toc-progress">{{ Math.round(paginationState[currentTocType].currentPage / paginationState[currentTocType].totalPages * 100) }}%</span>
              </div>
              <div class="toc-list">
                <div 
                  v-for="page in paginationState[currentTocType].totalPages" 
                  :key="page"
                  class="toc-item"
                  :class="{ 'active': page === paginationState[currentTocType].currentPage }"
                  @click="jumpToPage(currentTocType, page)"
                >
                  <span class="toc-page">第 {{ page }} 页</span>
                  <span v-if="page === paginationState[currentTocType].currentPage" class="toc-current">当前</span>
                </div>
              </div>
            </div>
          </el-dialog>
        </div>
      </div>
    </div>
    
    <!-- 词语释义面板 -->
    <el-drawer
      v-model="definitionPanel.visible"
      title="词语释义"
      direction="rtl"
      size="30%"
    >
      <div v-if="definitionPanel.loading" class="loading-content">
        <el-spinner size="large" />
        <p>正在搜索，请稍后...</p>
      </div>
      <div v-else-if="definitionPanel.word" class="definition-content">
        <h4>{{ definitionPanel.word }}</h4>
        <p v-if="definitionPanel.definition.phonetic" class="phonetic">
          {{ definitionPanel.definition.phonetic }}
        </p>
        <div class="definitions">
          <h5>释义：</h5>
          <ul>
            <li v-for="(def, index) in definitionPanel.definition.definitions" :key="index">
              {{ def }}
            </li>
          </ul>
        </div>
        <div v-if="definitionPanel.definition.contextual_meaning" class="contextual-meaning">
          <h5>文中含义：</h5>
          <p>{{ definitionPanel.definition.contextual_meaning }}</p>
        </div>
        <div v-if="definitionPanel.definition.examples && definitionPanel.definition.examples.length > 0" class="examples">
          <h5>例句：</h5>
          <ul>
            <li v-for="(example, index) in definitionPanel.definition.examples" :key="index">
              {{ example }}
            </li>
          </ul>
        </div>
      </div>
      <div v-else class="no-definition">
        <p>请选择要查询的词语</p>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, reactive } from 'vue'
import { useAppStore } from '../stores/appStore'
import { getWordDefinition } from '../utils/api'
import { Microphone, Close, FullScreen, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Setting, VideoPlay, VideoPause, List, Loading } from '@element-plus/icons-vue'
import { pyttsx3, playPyttsx3 } from '../utils/pyttsx3'

const appStore = useAppStore()

// 从store中获取状态
const currentDocument = computed(() => appStore.currentDocument)
const readerSettings = computed(() => {
  const settings = appStore.readerSettings
  console.log('=== 阅读器设置 ===')
  console.log('posTagging:', settings.posTagging)
  console.log('selectedPosTags:', settings.selectedPosTags)
  return settings
})
const definitionPanel = computed(() => appStore.definitionPanel)

// 音频元素
const originalAudio = ref(null)
const simplifiedAudio = ref(null)

// 内容引用
const originalContentRef = ref(null)
const simplifiedContentRef = ref(null)

// 计算属性
const segments = computed(() => {
  return currentDocument.value.segments || []
})

const simplifiedSegments = computed(() => {
  return currentDocument.value.simplifiedSegments || []
})

// 计算蒙版高度
const maskHeight = computed(() => {
  const lineHeight = readerSettings.value.lineHeight || 1.5
  const maskLines = readerSettings.value.maskLines || 3
  // maskHeight 应该是可见区域高度的一半，因为 CSS 中使用了 calc(50vh - var(--mask-height))
  // 所以实际可见区域高度是 2 * maskHeight
  // 使用实际的字体大小来计算可见区域高度
  const fontSize = readerSettings.value.fontSize || 16
  // 计算可见区域高度，应该是 maskLines 行文字的高度
  // 动态获取 HTML 根元素的 font-size
  const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16
  // 计算可见区域的高度，直接使用可见行数乘以单行高度
  const visibleHeight = lineHeight * maskLines * fontSize
  // 返回可见区域高度的一半
  return `${visibleHeight / 2}px`
})

// 计算上下按钮位置
const scrollButtonStyles = computed(() => {
  const lineHeight = readerSettings.value.lineHeight || 1.5
  const maskLines = readerSettings.value.maskLines || 3
  const fontSize = readerSettings.value.fontSize || 16

  // 计算可见区域的高度，直接使用可见行数乘以单行高度
  const visibleHeight = lineHeight * maskLines * fontSize
  // 可见区域顶部位置 = 视口高度/2 - 可见区域高度/2
  const viewportHeight = window.innerHeight
  const visibleAreaTop = (viewportHeight - visibleHeight) / 2
  
  // 按钮高度的一半，用于调整按钮位置
  const buttonHalfHeight = 24 // 48px / 2
  
  return {
    // 上按钮位于可见区域顶部上方（外部）
    '--scroll-button-up-top': `${visibleAreaTop - buttonHalfHeight}px`,
    // 下按钮位于可见区域底部下方（外部）
    '--scroll-button-down-top': `${visibleAreaTop + visibleHeight + buttonHalfHeight}px`
  }
})

// 响应式数据
const queryWord = ref('')
const originalProgress = ref(0)
const simplifiedProgress = ref(0)
const isSpeakingOriginal = ref(false)
const isSpeakingSimplified = ref(false)
const currentOriginalSegment = ref(null)
const currentSimplifiedSegment = ref(null)

const showFullScreenSettings = ref(false)
const showTocDialog = ref(false)
const currentTocType = ref('original')

// 分页状态 - 使用 ref 包装复杂对象
const paginationState = reactive({
  original: {
    currentPage: 1,
    totalPages: 1,
    pageSize: 10,
    loadedPages: [1],  // 使用数组替代 Set
    pageCache: {},
    nextPageLoading: false
  },
  simplified: {
    currentPage: 1,
    totalPages: 1,
    pageSize: 10,
    loadedPages: [1],  // 使用数组替代 Set
    pageCache: {},
    nextPageLoading: false
  }
})

// 当前页的意群
const currentOriginalSegments = computed(() => {
  const state = paginationState.original
  if (state.pageCache[state.currentPage]) {
    return state.pageCache[state.currentPage]
  }
  // 返回全部意群（兼容旧模式）
  return segments.value.slice(0, state.pageSize)
})

const currentSimplifiedSegments = computed(() => {
  const state = paginationState.simplified
  if (state.pageCache[state.currentPage]) {
    return state.pageCache[state.currentPage]
  }
  return simplifiedSegments.value.slice(0, state.pageSize)
})

// 朗读位置记录
const originalSpeechPosition = ref(0)
const simplifiedSpeechPosition = ref(0)

// 全屏状态
const isOriginalFullScreen = ref(false)
const isSimplifiedFullScreen = ref(false)

// 分页相关方法
const fetchSegments = async (documentId, page, pageSize, type) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      console.error('未登录，跳转到登录页')
      ElMessage.error('请先登录')
      setTimeout(() => {
        window.location.href = '/login'
      }, 1000)
      return null
    }
    
    const response = await fetch(
      `/api/documents/${documentId}/segments?page=${page}&page_size=${pageSize}&type=${type}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    
    // 处理认证失败
    if (response.status === 401) {
      console.error('登录已过期，跳转到登录页')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.error('登录已过期，请重新登录')
      setTimeout(() => {
        window.location.href = '/login'
      }, 1000)
      return null
    }
    
    // 处理404错误（文档没有关联的阅读历史）
    if (response.status === 404) {
      console.warn(`文档 ${documentId} 没有关联的阅读历史，将使用本地数据`)
      return null
    }
    
    const result = await response.json()
    if (result.data) {
      return result.data
    }
    return null
  } catch (error) {
    console.error('获取分页意群失败:', error)
    return null
  }
}

const loadPage = async (type, page) => {
  const state = paginationState[type]
  
  if (state.loadedPages.includes(page)) {
    state.currentPage = page
    // 更新阅读进度
    updateReadingProgress(type, page)
    return
  }
  
  const documentId = currentDocument.value.id
  // 后端期望1-based页码
  const result = await fetchSegments(documentId, page, state.pageSize, type)
  
  if (result) {
    state.pageCache[page] = result.segments
    state.loadedPages.push(page)
    // 更新总页数（后端返回的是实际总页数，保持1-based显示）
    state.totalPages = result.total_pages
    state.currentPage = page
    
    // 更新阅读进度
    updateReadingProgress(type, page)
    
    // 预加载下一页
    if (page < state.totalPages) {
      preloadNextPage(type)
    }
  }
}

// 更新阅读进度
const updateReadingProgress = (type, page) => {
  const state = paginationState[type]
  const progress = Math.round((page / state.totalPages) * 100)
  
  // 更新对应类型的进度
  if (type === 'original') {
    originalProgress.value = progress
  } else {
    simplifiedProgress.value = progress
  }
  
  // 更新阅读历史
  updateReadingHistory(type, page, progress)
}

// 更新阅读历史记录
const updateReadingHistory = (type, page, progress) => {
  if (!currentDocument.value.content) {
    return
  }
  
  // 找到对应的阅读历史记录
  const existingHistory = appStore.readingHistory.find(item => 
    item.document_id === currentDocument.value.id || item.content === currentDocument.value.content
  )
  
  if (existingHistory) {
    // 更新阅读进度
    existingHistory.readingProgress = progress
    // 更新最后阅读时间
    existingHistory.lastRead = new Date().toISOString().slice(0, 19).replace('T', ' ')
    // 更新阅读时间（累加）
    existingHistory.readTime += Math.floor((Date.now() - readingStartTime.value) / 1000)
    
    // 保存到本地存储和后端
    saveReadingHistoryToStorage()
  }
}

// 保存阅读历史到存储
const saveReadingHistoryToStorage = () => {
  if (appStore.user) {
    const storageKey = `readingHistory_${appStore.user.id}`
    localStorage.setItem(storageKey, JSON.stringify(appStore.readingHistory))
  }
  localStorage.setItem('readingHistory', JSON.stringify(appStore.readingHistory)) // 兼容旧版本
}

// 恢复上次阅读位置
const restoreReadingPosition = () => {
  if (!currentDocument.value.content) {
    return
  }
  
  // 找到对应的阅读历史记录
  const existingHistory = appStore.readingHistory.find(item => 
    item.document_id === currentDocument.value.id || item.content === currentDocument.value.content
  )
  
  if (existingHistory && existingHistory.readingProgress > 0) {
    // 根据阅读进度计算页码
    const progress = existingHistory.readingProgress / 100
    const totalPages = paginationState.original.totalPages || 1
    const targetPage = Math.max(1, Math.ceil(progress * totalPages))
    
    // 跳转到上次阅读的页面
    setTimeout(() => {
      loadPage('original', targetPage)
    }, 500)
  }
}

const preloadNextPage = async (type) => {
  const state = paginationState[type]
  if (state.nextPageLoading || state.currentPage >= state.totalPages) {
    return
  }
  
  const nextPage = state.currentPage + 1
  if (state.loadedPages.includes(nextPage)) {
    return
  }
  
  state.nextPageLoading = true
  const documentId = currentDocument.value.id
  // 后端期望1-based页码
  const result = await fetchSegments(documentId, nextPage, state.pageSize, type)
  
  if (result) {
    state.pageCache[nextPage] = result.segments
    state.loadedPages.push(nextPage)
    state.totalPages = result.total_pages
  }
  
  state.nextPageLoading = false
}

const nextPage = (type) => {
  const state = paginationState[type]
  if (state.currentPage < state.totalPages) {
    loadPage(type, state.currentPage + 1)
  }
}

const prevPage = (type) => {
  const state = paginationState[type]
  if (state.currentPage > 1) {
    loadPage(type, state.currentPage - 1)
  }
}

const goToPage = (type, page) => {
  const state = paginationState[type]
  if (page >= 1 && page <= state.totalPages) {
    loadPage(type, page)
  }
}

const jumpToPage = (type, page) => {
  goToPage(type, page)
  showTocDialog.value = false
}

const openTocDialog = (type = 'original') => {
  currentTocType.value = type
  console.log('目录按钮点击，type:', type, 'showTocDialog:', showTocDialog.value)
  showTocDialog.value = true
  console.log('点击后showTocDialog:', showTocDialog.value)
}

// 初始化分页数据
const initPagination = async () => {
  console.log('initPagination called, document id:', currentDocument.value.id)
  console.log('document content:', currentDocument.value.content)
  console.log('document segments:', currentDocument.value.segments)
  
  if (!currentDocument.value.id) {
    console.log('No document id, returning')
    return
  }
  
  // 重置分页状态（后端限制 page_size 最大为50）
  paginationState.original = {
    currentPage: 1,
    totalPages: 1,
    pageSize: 50,
    loadedPages: [],
    pageCache: {},
    nextPageLoading: false
  }
  paginationState.simplified = {
    currentPage: 1,
    totalPages: 1,
    pageSize: 50,
    loadedPages: [],
    pageCache: {},
    nextPageLoading: false
  }
  
  // 检查文档是否已有预计算的意群数据
  const hasOriginalSegments = currentDocument.value.segments && currentDocument.value.segments.length > 0
  const hasSimplifiedSegments = currentDocument.value.simplifiedSegments && currentDocument.value.simplifiedSegments.length > 0
  
  if (hasOriginalSegments) {
    // 使用文档中已有的意群数据进行分页
    const allSegments = currentDocument.value.segments
    paginationState.original.totalPages = Math.ceil(allSegments.length / paginationState.original.pageSize)
    paginationState.original.pageCache[1] = allSegments.slice(0, paginationState.original.pageSize)
    paginationState.original.loadedPages = [1]
    paginationState.original.currentPage = 1
    
    // 如果有更多页，预加载下一页
    if (paginationState.original.totalPages > 1) {
      paginationState.original.pageCache[2] = allSegments.slice(paginationState.original.pageSize, paginationState.original.pageSize * 2)
      paginationState.original.loadedPages.push(2)
    }
  } else {
    // 从后端获取分页数据（后端期望1-based页码）
    const originalResult = await fetchSegments(
      currentDocument.value.id, 
      1, 
      paginationState.original.pageSize, 
      'original'
    )
    if (originalResult) {
      paginationState.original.pageCache[1] = originalResult.segments
      paginationState.original.totalPages = originalResult.total_pages
      paginationState.original.loadedPages = [1]
      paginationState.original.currentPage = 1
      
      // 预加载下一页
      if (originalResult.total_pages > 1) {
        preloadNextPage('original')
      }
    } else {
      // 如果后端请求失败，使用原始内容作为后备
      paginationState.original.pageCache[1] = []
      paginationState.original.totalPages = 1
      paginationState.original.loadedPages = [1]
      paginationState.original.currentPage = 1
    }
  }
  
  // 初始化简化文本分页
  if (currentDocument.value.simplifiedContent) {
    if (hasSimplifiedSegments) {
      // 使用文档中已有的简化意群数据进行分页
      const allSegments = currentDocument.value.simplifiedSegments
      paginationState.simplified.totalPages = Math.ceil(allSegments.length / paginationState.simplified.pageSize)
      paginationState.simplified.pageCache[1] = allSegments.slice(0, paginationState.simplified.pageSize)
      paginationState.simplified.loadedPages = [1]
      paginationState.simplified.currentPage = 1
      
      // 如果有更多页，预加载下一页
      if (paginationState.simplified.totalPages > 1) {
        paginationState.simplified.pageCache[2] = allSegments.slice(paginationState.simplified.pageSize, paginationState.simplified.pageSize * 2)
        paginationState.simplified.loadedPages.push(2)
      }
    } else {
      // 从后端获取分页数据（后端期望1-based页码）
      const simplifiedResult = await fetchSegments(
        currentDocument.value.id, 
        1, 
        paginationState.simplified.pageSize, 
        'simplified'
      )
      if (simplifiedResult) {
        paginationState.simplified.pageCache[1] = simplifiedResult.segments
        paginationState.simplified.totalPages = simplifiedResult.total_pages
        paginationState.simplified.loadedPages = [1]
        paginationState.simplified.currentPage = 1
        
        // 预加载下一页
        if (simplifiedResult.total_pages > 1) {
          preloadNextPage('simplified')
        }
      } else {
        // 如果后端请求失败，使用原始内容作为后备
        paginationState.simplified.pageCache[1] = []
        paginationState.simplified.totalPages = 1
        paginationState.simplified.loadedPages = [1]
        paginationState.simplified.currentPage = 1
      }
    }
  }
}

// 方法

const handleSegmentClick = (segment) => {
  // 处理意群点击
  console.log('点击了意群:', segment)
}

const handleQueryWord = async () => {
  if (!queryWord.value) {
    return
  }
  
  try {
    appStore.setDefinitionLoading(true)
    // 获取当前文档内容作为上下文
    const context = currentDocument.value.content || ''
    const definition = await getWordDefinition(queryWord.value, context)
    appStore.showDefinitionPanel(queryWord.value, definition)
  } catch (error) {
    console.error('获取词语释义失败:', error)
    appStore.hideDefinitionPanel()
    alert('获取词语释义失败，请稍后重试')
  }
}

const getPosClass = (word, position, isSimplified = false) => {
  const posTags = isSimplified ? currentDocument.value.simplified_pos_tags : currentDocument.value.pos_tags
  if (!posTags) return ''
  
  const tag = posTags.find(tag => tag.start_pos === position)
  if (!tag) return ''
  
  // 检查该词性是否在用户选中的标注列表中
  const selectedPosTags = readerSettings.value.selectedPosTags || ['n', 'v', 'a']
  if (!selectedPosTags.includes(tag.pos)) return ''
  
  // 根据词性返回不同的类名
  const posMap = {
    'n': 'pos-noun',
    'v': 'pos-verb',
    'a': 'pos-adj',
    'd': 'pos-adv',
    'p': 'pos-prep',
    'c': 'pos-conj',
    'u': 'pos-aux',
    'r': 'pos-pron',
    'm': 'pos-num',
    'q': 'pos-quant',
    't': 'pos-time',
    's': 'pos-place',
    'f': 'pos-dir',
    'b': 'pos-dist',
    'z': 'pos-state',
    'e': 'pos-interj',
    'y': 'pos-modal',
    'o': 'pos-onom',
    'h': 'pos-prefix',
    'k': 'pos-suffix',
    'x': 'pos-punct',
    'w': 'pos-other'
  }
  
  return posMap[tag.pos] || ''
}

const getPosFontSize = (word, position, isSimplified = false) => {
  const posTags = isSimplified ? currentDocument.value.simplified_pos_tags : currentDocument.value.pos_tags
  if (!posTags) return {}
  
  const tag = posTags.find(tag => tag.start_pos === position)
  if (!tag) return {}
  
  // 检查该词性是否在用户选中的标注列表中
  const selectedPosTags = readerSettings.value.selectedPosTags || ['n', 'v', 'a']
  if (!selectedPosTags.includes(tag.pos)) return {}
  
  // 返回空对象，使用基础字体大小（与普通文字一致）
  return {}
}

const getSegmentWords = (segmentText, segmentStartPos, isSimplified = false) => {
  const posTags = isSimplified ? currentDocument.value.simplified_pos_tags : currentDocument.value.pos_tags
  if (!posTags || !segmentText) return []
  
  const endPos = segmentStartPos + segmentText.length
  const words = []
  
  for (let i = 0; i < posTags.length; i++) {
    const tag = posTags[i]
    if (tag.start_pos >= segmentStartPos && tag.start_pos < endPos) {
      words.push({
        text: tag.word,
        position: tag.start_pos
      })
    }
  }
  
  return words
}


// 原文本朗读方法
const startOriginalSpeech = async (startFromPosition = null) => {
  // 先停止任何正在播放的音频
  if (isSpeakingOriginal.value) {
    stopOriginalSpeech()
  }
  
  const fullText = currentDocument.value.content
  const ttsProvider = readerSettings.value.ttsProvider || 'pyttsx3' // 默认使用pyttsx3
  
  // 确定从哪个位置开始朗读
  let startPosition = startFromPosition !== null ? startFromPosition : originalSpeechPosition.value
  
  // 如果没有指定位置，且当前有页码信息，从当前页面开始
  if (startFromPosition === null && originalSpeechPosition.value === 0) {
    const currentPage = paginationState.original.currentPage
    const pageSize = paginationState.original.pageSize
    // 计算当前页面的起始字符位置（每页pageSize个意群，每个意群平均约20字符）
    const estimatedCharsPerSegment = 20
    startPosition = (currentPage - 1) * pageSize * estimatedCharsPerSegment
    // 确保不超过文本长度
    startPosition = Math.min(startPosition, fullText.length - 1)
  }
  
  // 如果上次朗读已完成，从头开始
  if (startPosition >= fullText.length) {
    startPosition = 0
    originalSpeechPosition.value = 0
  }
  
  // 截取从指定位置开始的文本
  const text = fullText.substring(startPosition)
  
  isSpeakingOriginal.value = true
  originalProgress.value = (startPosition / fullText.length) * 100
  
  // 在蒙版模式下，滚动到当前位置
  if (isOriginalFullScreen.value && readerSettings.value.enableMask && originalContentRef.value) {
    nextTick(() => {
      if (startPosition === 0) {
        // 从头开始朗读，滚动到第一行可见位置
        scrollToFirstVisibleLine(originalContentRef.value, 'original')
      } else {
        // 找到对应位置的意群并滚动
        const segment = segments.value.find(s => s.start_pos <= startPosition && s.end_pos > startPosition)
        if (segment) {
          const targetElement = originalContentRef.value.querySelector(`[data-segment-id="${segment.id}"]`)
          if (targetElement) {
            scrollToElement(originalContentRef.value, targetElement, 'original')
          }
        } else {
          // 如果找不到对应意群，滚动到第一个意群（从头开始）
          scrollToFirstVisibleLine(originalContentRef.value, 'original')
        }
      }
    })
  }
  
  // 使用pyttsx3进行文本转语音
  try {
    const audioBlob = await pyttsx3(
      text,
      Math.round((readerSettings.value.speechRate || 1.0) * 150), // 转换为pyttsx3的语速
      readerSettings.value.speechVolume || 1.0
    )
    
    originalAudio.value = playPyttsx3(audioBlob, () => {
      isSpeakingOriginal.value = false
      currentOriginalSegment.value = null
      originalAudio.value = null
    })
    
    // 监听音频元素的durationchange事件，获取真实时长
    originalAudio.value.addEventListener('durationchange', () => {
      if (originalAudio.value.duration > 0) {
        // 基于真实时长更新进度
        const interval = setInterval(() => {
          if (isSpeakingOriginal.value && originalAudio.value) {
            originalProgress.value = (originalAudio.value.currentTime / originalAudio.value.duration) * 100
            if (originalAudio.value.currentTime >= originalAudio.value.duration) {
              clearInterval(interval)
              originalProgress.value = 100
            }
          } else {
            clearInterval(interval)
          }
        }, 100)
      }
    })
    
    // 开始高亮意群
    highlightOriginalSegments()
  } catch (error) {
    console.error('pyttsx3调用失败:', error)
    alert(`pyttsx3调用失败: ${error.message}\n请检查后端服务是否正常`)
    isSpeakingOriginal.value = false
  }
}

const stopOriginalSpeech = () => {
  // 先记录当前朗读位置（字符索引），避免被后续操作重置
  let currentPosition = originalSpeechPosition.value
  
  // 尝试通过音频元素的当前时间计算更精确的位置
  if (originalAudio.value && originalAudio.value.duration > 0) {
    const fullText = currentDocument.value.content || ''
    const progress = originalAudio.value.currentTime / originalAudio.value.duration
    currentPosition = Math.floor(progress * fullText.length)
  } else if (currentOriginalSegment.value && segments.value.length > 0) {
    // 如果没有音频元素，使用当前意群的位置
    const segment = segments.value.find(s => s.id === currentOriginalSegment.value)
    if (segment) {
      currentPosition = segment.start_pos || 0
    }
  }
  
  if (originalAudio.value) {
    // 停止音频播放（适用于Edge-TTS和pyttsx3）
    originalAudio.value.pause()
    originalAudio.value.currentTime = 0
    // 移除所有事件监听器
    originalAudio.value.removeEventListener('timeupdate', () => {})
    originalAudio.value.removeEventListener('ended', () => {})
    originalAudio.value = null
  }
  
  if ('speechSynthesis' in window) {
    speechSynthesis.cancel()
  }
  
  // 保存当前位置
  originalSpeechPosition.value = currentPosition
  
  isSpeakingOriginal.value = false
  // 不要清除当前高亮，保持在原位置
  // currentOriginalSegment.value = null
}

const seekOriginalSpeech = (value) => {
  const fullText = currentDocument.value.content
  
  // 计算目标字符位置
  const targetPosition = Math.floor((value / 100) * fullText.length)
  
  // 更新朗读位置
  originalSpeechPosition.value = targetPosition
  
  // 更新高亮
  const segment = segments.value.find(s => s.start_pos <= targetPosition && s.end_pos > targetPosition)
  if (segment) {
    currentOriginalSegment.value = segment.id
    
    // 自动跳转到目标意群所在的页面
    const pageSize = paginationState.original.pageSize
    const targetPage = Math.ceil(segment.id / pageSize)
    
    // 如果目标页面与当前页面不同，先加载目标页面
    if (targetPage !== paginationState.original.currentPage) {
      loadPage('original', targetPage).then(() => {
        // 页面加载完成后，滚动到目标意群
        scrollToSegment(segment.id, 'original')
      })
    } else {
      // 已经在目标页面，直接滚动
      scrollToSegment(segment.id, 'original')
    }
  }
  
  // 如果正在播放，更新音频位置
  if (originalAudio.value && isSpeakingOriginal.value) {
    const targetTime = (value / 100) * originalAudio.value.duration
    originalAudio.value.currentTime = targetTime
  } else if (!isSpeakingOriginal.value) {
    // 如果没有播放，从当前位置开始播放
    startOriginalSpeech(targetPosition)
  }
}

// 滚动到指定意群
const scrollToSegment = (segmentId, type = 'original') => {
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  if (!element) return
  
  const targetElement = element.querySelector(`[data-segment-id="${segmentId}"]`)
  if (!targetElement) return
  
  // 判断是否在蒙版模式下
  const isMaskEnabled = type === 'original' 
    ? (isOriginalFullScreen.value && readerSettings.value.enableMask)
    : (isSimplifiedFullScreen.value && readerSettings.value.enableMask)
  
  if (isMaskEnabled) {
    // 蒙版模式：滚动到中央可见区域
    scrollToElement(element, targetElement, type)
  } else {
    // 普通模式：滚动到元素可见
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// 简化文本朗读方法
const startSimplifiedSpeech = async (startFromPosition = null) => {
  // 先停止任何正在播放的音频
  if (isSpeakingSimplified.value) {
    stopSimplifiedSpeech()
  }
  
  const fullText = currentDocument.value.simplifiedContent
  const ttsProvider = readerSettings.value.ttsProvider || 'pyttsx3' // 默认使用pyttsx3
  
  // 确定从哪个位置开始朗读
  let startPosition = startFromPosition !== null ? startFromPosition : simplifiedSpeechPosition.value
  
  // 如果没有指定位置，且当前有页码信息，从当前页面开始
  if (startFromPosition === null && simplifiedSpeechPosition.value === 0) {
    const currentPage = paginationState.simplified.currentPage
    const pageSize = paginationState.simplified.pageSize
    // 计算当前页面的起始字符位置（每页pageSize个意群，每个意群平均约20字符）
    const estimatedCharsPerSegment = 20
    startPosition = (currentPage - 1) * pageSize * estimatedCharsPerSegment
    // 确保不超过文本长度
    startPosition = Math.min(startPosition, fullText.length - 1)
  }
  
  // 如果上次朗读已完成，从头开始
  if (startPosition >= fullText.length) {
    startPosition = 0
    simplifiedSpeechPosition.value = 0
  }
  
  // 截取从指定位置开始的文本
  const text = fullText.substring(startPosition)
  
  isSpeakingSimplified.value = true
  simplifiedProgress.value = (startPosition / fullText.length) * 100
  
  // 在蒙版模式下，滚动到当前位置
  if (isSimplifiedFullScreen.value && readerSettings.value.enableMask && simplifiedContentRef.value) {
    nextTick(() => {
      if (startPosition === 0) {
        // 从头开始朗读，滚动到第一行可见位置
        scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
      } else {
        // 找到对应位置的意群并滚动
        const segment = simplifiedSegments.value.find(s => s.start_pos <= startPosition && s.end_pos > startPosition)
        if (segment) {
          const targetElement = simplifiedContentRef.value.querySelector(`[data-segment-id="${segment.id}"]`)
          if (targetElement) {
            scrollToElement(simplifiedContentRef.value, targetElement, 'simplified')
          }
        } else {
          // 如果找不到对应意群，滚动到第一个意群（从头开始）
          scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
        }
      }
    })
  }
  
  // 使用pyttsx3进行文本转语音
  try {
    const audioBlob = await pyttsx3(
      text,
      Math.round((readerSettings.value.speechRate || 1.0) * 150), // 转换为pyttsx3的语速
      readerSettings.value.speechVolume || 1.0
    )
    
    simplifiedAudio.value = playPyttsx3(audioBlob, () => {
      isSpeakingSimplified.value = false
      currentSimplifiedSegment.value = null
      simplifiedAudio.value = null
    })
    
    // 监听音频元素的durationchange事件，获取真实时长
    simplifiedAudio.value.addEventListener('durationchange', () => {
      if (simplifiedAudio.value.duration > 0) {
        // 基于真实时长更新进度
        const interval = setInterval(() => {
          if (isSpeakingSimplified.value && simplifiedAudio.value) {
            simplifiedProgress.value = (simplifiedAudio.value.currentTime / simplifiedAudio.value.duration) * 100
            if (simplifiedAudio.value.currentTime >= simplifiedAudio.value.duration) {
              clearInterval(interval)
              simplifiedProgress.value = 100
            }
          } else {
            clearInterval(interval)
          }
        }, 100)
      }
    })
    
    // 开始高亮意群
    highlightSimplifiedSegments()
  } catch (error) {
    console.error('pyttsx3调用失败:', error)
    alert(`pyttsx3调用失败: ${error.message}\n请检查后端服务是否正常`)
    isSpeakingSimplified.value = false
  }
}

const stopSimplifiedSpeech = () => {
  // 先记录当前朗读位置（字符索引），避免被后续操作重置
  let currentPosition = simplifiedSpeechPosition.value
  
  // 尝试通过音频元素的当前时间计算更精确的位置
  if (simplifiedAudio.value && simplifiedAudio.value.duration > 0) {
    const fullText = currentDocument.value.simplifiedContent || ''
    const progress = simplifiedAudio.value.currentTime / simplifiedAudio.value.duration
    currentPosition = Math.floor(progress * fullText.length)
  } else if (currentSimplifiedSegment.value && simplifiedSegments.value.length > 0) {
    // 如果没有音频元素，使用当前意群的位置
    const segment = simplifiedSegments.value.find(s => s.id === currentSimplifiedSegment.value)
    if (segment) {
      currentPosition = segment.start_pos || 0
    }
  }
  
  if (simplifiedAudio.value) {
    // 停止音频播放（适用于Edge-TTS和pyttsx3）
    simplifiedAudio.value.pause()
    simplifiedAudio.value.currentTime = 0
    // 移除所有事件监听器
    simplifiedAudio.value.removeEventListener('timeupdate', () => {})
    simplifiedAudio.value.removeEventListener('ended', () => {})
    simplifiedAudio.value = null
  }
  
  if ('speechSynthesis' in window) {
    speechSynthesis.cancel()
  }
  
  // 保存当前位置
  simplifiedSpeechPosition.value = currentPosition
  
  isSpeakingSimplified.value = false
  // 不要清除当前高亮，保持在原位置
  // currentSimplifiedSegment.value = null
}

const seekSimplifiedSpeech = (value) => {
  const fullText = currentDocument.value.simplifiedContent
  
  // 计算目标字符位置
  const targetPosition = Math.floor((value / 100) * fullText.length)
  
  // 更新朗读位置
  simplifiedSpeechPosition.value = targetPosition
  
  // 更新高亮
  const segment = simplifiedSegments.value.find(s => s.start_pos <= targetPosition && s.end_pos > targetPosition)
  if (segment) {
    currentSimplifiedSegment.value = segment.id
    
    // 自动跳转到目标意群所在的页面
    const pageSize = paginationState.simplified.pageSize
    const targetPage = Math.ceil(segment.id / pageSize)
    
    // 如果目标页面与当前页面不同，先加载目标页面
    if (targetPage !== paginationState.simplified.currentPage) {
      loadPage('simplified', targetPage).then(() => {
        // 页面加载完成后，滚动到目标意群
        scrollToSegment(segment.id, 'simplified')
      })
    } else {
      // 已经在目标页面，直接滚动
      scrollToSegment(segment.id, 'simplified')
    }
  }
  
  // 如果正在播放，更新音频位置
  if (simplifiedAudio.value && isSpeakingSimplified.value) {
    const targetTime = (value / 100) * simplifiedAudio.value.duration
    simplifiedAudio.value.currentTime = targetTime
  } else if (!isSpeakingSimplified.value) {
    // 如果没有播放，从当前位置开始播放
    startSimplifiedSpeech(targetPosition)
  }
}

// 更新原文本高亮
const updateOriginalHighlight = () => {
  if (originalAudio.value && originalAudio.value.duration > 0) {
    const fullText = currentDocument.value.content
    const currentTime = originalAudio.value.currentTime
    const totalDuration = originalAudio.value.duration
    const segmentId = getCurrentSegmentByProgress(segments.value, fullText, currentTime, totalDuration)
    
    if (segmentId !== currentOriginalSegment.value) {
      currentOriginalSegment.value = segmentId
      // 滚动到当前高亮的意群
      if (isOriginalFullScreen.value) {
        const element = originalContentRef.value
        const targetElement = document.querySelector(`.text-segment[data-segment-id="${segmentId}"]`)
        scrollToElement(element, targetElement)
      }
    }
  }
}

// 更新简化文本高亮
const updateSimplifiedHighlight = () => {
  if (simplifiedAudio.value && simplifiedAudio.value.duration > 0) {
    const fullText = currentDocument.value.simplifiedContent
    const currentTime = simplifiedAudio.value.currentTime
    const totalDuration = simplifiedAudio.value.duration
    const segmentId = getCurrentSegmentByProgress(simplifiedSegments.value, fullText, currentTime, totalDuration)
    
    if (segmentId !== currentSimplifiedSegment.value) {
      currentSimplifiedSegment.value = segmentId
      // 滚动到当前高亮的意群
      if (isSimplifiedFullScreen.value) {
        const element = simplifiedContentRef.value
        const targetElement = document.querySelector(`.simplified-text-segment[data-segment-id="${segmentId}"]`)
        scrollToElement(element, targetElement)
      }
    }
  }
}

// 全屏功能
const toggleFullScreen = (type) => {
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  
  if (element) {
    if (!document.fullscreenElement) {
      element.requestFullscreen().catch(err => {
        console.error(`全屏请求失败: ${err.message}`)
      })
    } else {
      document.exitFullscreen()
    }
  }
}

// 检查全屏状态
const checkFullScreenStatus = () => {
  if (!document.fullscreenElement) {
    // 退出全屏时，清除样式并滚动到顶部
    if (originalContentRef.value) {
      originalContentRef.value.style.marginTop = ''
      originalContentRef.value.style.paddingTop = ''
      originalContentRef.value.style.paddingBottom = ''
      originalContentRef.value.scrollTop = 0
    }
    if (simplifiedContentRef.value) {
      simplifiedContentRef.value.style.marginTop = ''
      simplifiedContentRef.value.style.paddingTop = ''
      simplifiedContentRef.value.style.paddingBottom = ''
      simplifiedContentRef.value.scrollTop = 0
    }
    isOriginalFullScreen.value = false
    isSimplifiedFullScreen.value = false
  } else {
    isOriginalFullScreen.value = document.fullscreenElement === originalContentRef.value || 
                                originalContentRef.value?.contains(document.fullscreenElement)
isSimplifiedFullScreen.value = document.fullscreenElement === simplifiedContentRef.value || 
                                  simplifiedContentRef.value?.contains(document.fullscreenElement)
    
    // 当进入全屏模式且启用蒙版时，自动滚动到文字开始位置
    if (readerSettings.value.enableMask) {
      if (isOriginalFullScreen.value && originalContentRef.value) {
        // 使用setTimeout确保DOM完全更新后再滚动
        setTimeout(() => {
          // 滚动到原文本开始位置，使文字开始部分显示在可见区域内
          scrollToFirstVisibleLine(originalContentRef.value, 'original')
        }, 200)
      }
      if (isSimplifiedFullScreen.value && simplifiedContentRef.value) {
        // 使用setTimeout确保DOM完全更新后再滚动
        setTimeout(() => {
          // 滚动到简化文本开始位置，使文字开始部分显示在可见区域内
          scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
        }, 200)
      }
    }
  }
}

// 向上滚动
const scrollUp = (type) => {
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  if (element) {
    // 计算实际的文字行高，使用实际的字体大小和行高
    const lineHeight = readerSettings.value.lineHeight || 1.5
    const maskLines = readerSettings.value.maskLines || 3
    const fontSize = readerSettings.value.fontSize || 16
  
    // 计算可见区域的高度，直接使用可见行数乘以单行高度
    const visibleHeight = lineHeight * maskLines * fontSize
    
    // 每次滚动的距离应该是可见区域高度
    const scrollAmount = visibleHeight
    
    // 计算新的滚动位置
    let newScrollTop = element.scrollTop - scrollAmount
    
    // 确保滚动位置不小于0
    newScrollTop = Math.max(0, newScrollTop)
    
    // 应用滚动位置
    element.scrollTop = newScrollTop
  }
}

// 向下滚动
const scrollDown = (type) => {
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  if (element) {
    // 计算实际的文字行高，使用实际的字体大小和行高
    const lineHeight = readerSettings.value.lineHeight || 1.5
    const maskLines = readerSettings.value.maskLines || 3
    const fontSize = readerSettings.value.fontSize || 16
   
    // 计算可见区域的高度，直接使用可见行数乘以单行高度
    const visibleHeight = lineHeight * maskLines * fontSize
    
    // 每次滚动的距离应该是可见区域高度
    const scrollAmount = visibleHeight 
    
    // 考虑paddingTop的影响
    const computedStyle = getComputedStyle(element)
    const paddingTop = parseFloat(computedStyle.paddingTop) || 0
    const contentHeight = element.scrollHeight - paddingTop * 2 // 减去上下padding
    
    // 计算最大滚动位置，确保能够滚动到最后一行文字的开始位置
    const maxScrollTop = contentHeight - lineHeight * maskLines * fontSize
    
    // 计算新的滚动位置
    let newScrollTop = element.scrollTop + scrollAmount
    
    // 确保滚动位置不超过最大滚动位置
    newScrollTop = Math.min(maxScrollTop, newScrollTop)
    
    // 应用滚动位置
    element.scrollTop = newScrollTop
  }
}

// 滚动到指定元素
const scrollToElement = (element, targetElement, type = 'original') => {
  if (element && targetElement) {
    // 在蒙版模式下，让目标元素位于可见区域中央
    const isMaskEnabled = type === 'original' 
      ? (isOriginalFullScreen.value && readerSettings.value.enableMask)
      : (isSimplifiedFullScreen.value && readerSettings.value.enableMask)
    
    if (isMaskEnabled) {
      // 计算实际的文字行高，使用实际的字体大小和行高
      const lineHeight = readerSettings.value.lineHeight || 1.5
      const maskLines = readerSettings.value.maskLines || 3
      const fontSize = readerSettings.value.fontSize || 16
    
      // 计算可见区域的高度，直接使用可见行数乘以单行高度
      const visibleHeight = lineHeight * maskLines * fontSize
      
      // 获取元素的paddingTop值
      const computedStyle = getComputedStyle(element)
      const paddingTop = parseFloat(computedStyle.paddingTop) || 0
      
      // 滚动到元素位于可见区域中央的位置
      const targetOffsetTop = targetElement.offsetTop - paddingTop // 减去paddingTop
      const scrollPosition = targetOffsetTop - visibleHeight / 2
      
      // 计算最大滚动位置，确保能够滚动到最后一行文字的开始位置
      const contentHeight = element.scrollHeight - paddingTop * 2 // 减去上下padding
      const maxScrollTop = contentHeight - lineHeight * maskLines * fontSize
      
      element.scrollTop = Math.max(0, Math.min(maxScrollTop, scrollPosition))
    } else {
      // 普通模式：原来的逻辑
      const elementRect = element.getBoundingClientRect()
      const targetRect = targetElement.getBoundingClientRect()
      const scrollPosition = targetRect.top - elementRect.top + element.scrollTop - elementRect.height / 2 + targetRect.height / 2
      element.scrollTop = scrollPosition
    }
  }
}

// 滚动到第一行可见位置（蒙版模式下）
const scrollToFirstVisibleLine = (element, type = 'original') => {
  if (!element) return
  
  const isMaskEnabled = type === 'original' 
    ? (isOriginalFullScreen.value && readerSettings.value.enableMask)
    : (isSimplifiedFullScreen.value && readerSettings.value.enableMask)
  
  if (isMaskEnabled) {
    // 清除所有样式
    element.style.marginTop = ''
    element.style.paddingTop = ''
    element.style.paddingBottom = ''
    
    // 确保DOM更新后再计算
    nextTick(() => {
      // 计算实际的文字行高，使用实际的字体大小和行高
      const lineHeight = readerSettings.value.lineHeight || 1.5
      const maskLines = readerSettings.value.maskLines || 3
      const fontSize = readerSettings.value.fontSize || 16
    
      // 计算可见区域的高度，直接使用可见行数乘以单行高度
      const visibleHeight = lineHeight * maskLines * fontSize
      
      // 可见区域永远居中于画面
      // 可见区域顶部位置 = 视口高度/2 - 可见区域高度/2
      // 使用window.innerHeight获取视口高度
      const viewportHeight = window.innerHeight
      const visibleAreaTop = (viewportHeight - visibleHeight) / 2
      
      // 关键点：我们需要让内容向下移动，使得第一行文字显示在可见区域
      // 这里使用paddingTop来调整内容的位置，确保第一行文字完全显示在可见区域内
      // 计算paddingTop的值，使得第一行文字上端刚好贴合可见区域上边缘
      // 在全屏模式下，容器没有内边距
      element.style.paddingTop = `${visibleAreaTop }px`
      element.style.paddingBottom = `${visibleAreaTop}px`
      
      // 滚动到顶部，确保第一行文字从paddingTop的位置开始显示
      element.scrollTop = 0
    })
  } else {
    // 非蒙版模式，清除样式并滚动到顶部
    element.style.marginTop = ''
    element.style.paddingTop = ''
    element.style.paddingBottom = ''
    element.scrollTop = 0
  }
}

// 检查并自动滚动高亮意群到可见区域（蒙版模式下）
const autoScrollToHighlightedSegment = (segmentId, type = 'original') => {
  if (!segmentId) return
  
  const isMaskEnabled = type === 'original' 
    ? (isOriginalFullScreen.value && readerSettings.value.enableMask)
    : (isSimplifiedFullScreen.value && readerSettings.value.enableMask)
  
  if (!isMaskEnabled) return
  
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  if (!element) return
  
  const targetElement = element.querySelector(`[data-segment-id="${segmentId}"]`)
  if (!targetElement) return
  
  // 获取元素的paddingTop值
  const computedStyle = getComputedStyle(element)
  const paddingTop = parseFloat(computedStyle.paddingTop) || 0
  
  // 计算实际的文字行高，不包括缓冲值
  const lineHeight = readerSettings.value.lineHeight || 1.5
  const maskLines = readerSettings.value.maskLines || 3
  const fontSize = readerSettings.value.fontSize || 16
  
  // 计算可见区域的高度，直接使用可见行数乘以单行高度
  const visibleHeight = lineHeight * maskLines * fontSize
  
  // 滚动到元素位于可见区域中央的位置（与手动滚动逻辑一致）
  const targetOffsetTop = targetElement.offsetTop - paddingTop // 减去paddingTop
  const scrollPosition = targetOffsetTop - visibleHeight / 2
  
  // 计算最大滚动位置，确保能够滚动到最后一行文字的开始位置
  const contentHeight = element.scrollHeight - paddingTop * 2 // 减去上下padding
  const maxScrollTop = contentHeight - lineHeight * maskLines * fontSize
  
  element.scrollTop = Math.max(0, Math.min(maxScrollTop, scrollPosition))
}

// 切换全屏设置面板
const toggleFullScreenSettings = () => {
  showFullScreenSettings.value = !showFullScreenSettings.value
}

// 监听滚动事件，当用户滚动时，从滚动位置开始朗读
const handleUserScroll = (type) => {
  // 计算滚动到的可见区域内的第一行意群
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  if (element) {
    // 获取可见区域的边界
    const rect = element.getBoundingClientRect()
    const visibleTop = rect.top
    const visibleBottom = rect.bottom

    // 找到可见区域内的第一个意群
    const segmentElements = type === 'original' 
      ? element.querySelectorAll('.text-segment')
      : element.querySelectorAll('.simplified-text-segment')
    
    let firstVisibleSegment = null
    for (const segment of segmentElements) {
      const segmentRect = segment.getBoundingClientRect()
      if (segmentRect.top < visibleBottom && segmentRect.bottom > visibleTop) {
        firstVisibleSegment = segment
        break
      }
    }

    // 如果找到可见区域内的意群，从该意群开始朗读
    if (firstVisibleSegment) {
      const segmentId = firstVisibleSegment.getAttribute('data-segment-id')
      if (segmentId) {
        // 计算该意群对应的文本位置
        const segmentsList = type === 'original' ? segments.value : simplifiedSegments.value
        const segment = segmentsList.find(s => s.id === segmentId)
        if (segment) {
          const startPosition = segment.start_pos || 0
          // 从该位置开始朗读
          if (type === 'original') {
            // 停止当前播放
            if (isSpeakingOriginal.value) {
              if (originalAudio.value) {
                originalAudio.value.pause()
                originalAudio.value = null
              }
              isSpeakingOriginal.value = false
            }
            // 从新位置开始朗读
            startSpeech(startPosition, 'original')
          } else {
            // 停止当前播放
            if (isSpeakingSimplified.value) {
              if (simplifiedAudio.value) {
                simplifiedAudio.value.pause()
                simplifiedAudio.value = null
              }
              isSpeakingSimplified.value = false
            }
            // 从新位置开始朗读
            startSimplifiedSpeech(startPosition, 'simplified')
          }
        }
      }
    }
  }
}

// 鼠标滚动事件处理
const handleScroll = (event, type) => {
  event.preventDefault()
  const delta = event.deltaY > 0 ? 1 : -1
  if (delta > 0) {
    scrollDown(type)
  } else {
    scrollUp(type)
  }
  // 调用用户滚动处理函数
  handleUserScroll(type)
}

// 计算意群在文本中的位置映射
const calculateSegmentPositions = (segments, fullText) => {
  if (!segments || !segments.length || !fullText) return []
  
  // 首先尝试使用意群的原始位置信息
  const segmentsWithPositions = segments.map(segment => ({
    ...segment,
    startIndex: segment.start_pos || 0,
    endIndex: segment.end_pos || (segment.start_pos || 0) + segment.text.length
  }))
  
  // 对意群按起始位置排序，确保顺序正确
  return segmentsWithPositions.sort((a, b) => a.startIndex - b.startIndex)
}

// 根据音频进度计算当前应该高亮的意群
const getCurrentSegmentByProgress = (segments, fullText, currentTime, totalDuration) => {
  if (!segments || !segments.length || !fullText || totalDuration <= 0) return null
  
  // 计算当前进度比例
  const progress = Math.min(currentTime / totalDuration, 1)
  
  // 根据进度计算当前应该朗读到的字符位置
  const targetCharIndex = Math.floor(progress * fullText.length)
  
  // 找到包含该字符位置的意群
  for (const segment of segments) {
    if (targetCharIndex >= segment.startIndex && targetCharIndex < segment.endIndex) {
      return segment.id
    }
  }
  
  // 如果找不到，返回最接近的意群
  let closestSegment = null
  let minDistance = Infinity
  
  for (const segment of segments) {
    const distance = Math.abs(segment.startIndex - targetCharIndex)
    if (distance < minDistance) {
      minDistance = distance
      closestSegment = segment.id
    }
  }
  
  return closestSegment
}

// 高亮原文本意群 - 基于音频帧时间戳
const highlightOriginalSegments = () => {
  if (!segments.value.length) return
  
  // 获取完整文本
  const fullText = currentDocument.value.content || ''
  
  // 计算意群位置映射
  const segmentsWithPositions = calculateSegmentPositions(segments.value, fullText)
  
  // 对于Edge-TTS，使用音频元素的timeupdate事件
  if (originalAudio.value) {
    const audioElement = originalAudio.value
    
    // 立即设置当前高亮位置，避免从头开始
    if (isSpeakingOriginal.value && originalSpeechPosition.value > 0) {
      // 根据当前位置计算应该高亮的意群
      const targetCharIndex = originalSpeechPosition.value
      
      // 找到包含该字符位置的意群
      for (const segment of segmentsWithPositions) {
        if (targetCharIndex >= segment.startIndex && targetCharIndex < segment.endIndex) {
          currentOriginalSegment.value = segment.id
          break
        }
      }
    }
    
    // 使用requestAnimationFrame实现更精确的实时同步
    const syncHighlight = () => {
      if (!isSpeakingOriginal.value || !audioElement) {
        return
      }
      
      // 获取音频总时长
      const totalDuration = audioElement.duration || ((fullText.length - originalSpeechPosition.value) * 0.15 / (readerSettings.value.speechRate || 1.0))
      // 获取当前播放位置
      const currentTime = audioElement.currentTime
      
      // 计算当前在完整文本中的位置
      const progress = Math.min(currentTime / totalDuration, 1)
      const targetCharIndex = originalSpeechPosition.value + Math.floor(progress * (fullText.length - originalSpeechPosition.value))
      
      // 找到包含该字符位置的意群
      let currentSegmentId = null
      for (const segment of segmentsWithPositions) {
        if (targetCharIndex >= segment.startIndex && targetCharIndex < segment.endIndex) {
          currentSegmentId = segment.id
          break
        }
      }
      
      // 如果找不到，使用最接近的意群
      if (!currentSegmentId) {
        currentSegmentId = getCurrentSegmentByProgress(segmentsWithPositions, fullText, currentTime, totalDuration)
      }
      
      if (currentSegmentId !== currentOriginalSegment.value) {
        currentOriginalSegment.value = currentSegmentId
        // 自动滚动到高亮意群
        autoScrollToHighlightedSegment(currentSegmentId, 'original')
      }
      
      // 继续同步
      if (isSpeakingOriginal.value && currentTime < totalDuration) {
        requestAnimationFrame(syncHighlight)
      }
    }
    
    // 监听timeupdate事件作为备用
    const handleTimeUpdate = () => {
      if (!isSpeakingOriginal.value) {
        audioElement.removeEventListener('timeupdate', handleTimeUpdate)
        return
      }
    }
    
    // 监听ended事件
    const handleEnded = () => {
      audioElement.removeEventListener('timeupdate', handleTimeUpdate)
      audioElement.removeEventListener('ended', handleEnded)
      
      // 检查是否需要自动翻页
      const currentPage = paginationState.original.currentPage
      const totalPages = paginationState.original.totalPages
      
      if (currentPage < totalPages) {
        // 自动翻到下一页
        nextPage('original')
        
        // 延迟一段时间后继续朗读新页面
        setTimeout(() => {
          // 从新页面开始朗读
          originalSpeechPosition.value = 0
          startOriginalSpeech()
        }, 500) // 等待页面切换完成
      } else {
        // 已经是最后一页，结束朗读
        isSpeakingOriginal.value = false
        currentOriginalSegment.value = null
        originalSpeechPosition.value = 0
      }
    }
    
    // 先移除可能存在的旧监听器，避免重复添加
    audioElement.removeEventListener('timeupdate', handleTimeUpdate)
    audioElement.removeEventListener('ended', handleEnded)
    
    // 添加事件监听器
    audioElement.addEventListener('timeupdate', handleTimeUpdate)
    audioElement.addEventListener('ended', handleEnded)
    
    // 使用requestAnimationFrame开始实时同步（比timeupdate更精确）
    requestAnimationFrame(syncHighlight)
  } else {
    // 对于浏览器内置TTS，使用基于时间的估算
    const speechRate = readerSettings.value.speechRate || 1.0
    const totalDuration = fullText.length * 0.15 / speechRate // 每个字符0.15秒
    
    // 存储开始时间
    const startTime = Date.now()
    
    // 实时更新高亮
    const updateHighlight = () => {
      if (!isSpeakingOriginal.value) {
        currentOriginalSegment.value = null
        return
      }
      
      // 计算当前播放时间
      const currentPlayTime = (Date.now() - startTime) / 1000 // 转换为秒
      
      // 获取当前应该高亮的意群
      const segmentId = getCurrentSegmentByProgress(
        segmentsWithPositions, 
        fullText, 
        currentPlayTime, 
        totalDuration
      )
      
      if (segmentId !== currentOriginalSegment.value) {
        currentOriginalSegment.value = segmentId
        // 自动滚动到高亮意群
        autoScrollToHighlightedSegment(segmentId, 'original')
      }
      
      // 继续更新
      if (isSpeakingOriginal.value && currentPlayTime < totalDuration) {
        requestAnimationFrame(updateHighlight)
      } else {
        currentOriginalSegment.value = null
        originalSpeechPosition.value = 0 // 朗读完成，重置位置
      }
    }
    
    // 开始实时更新
    requestAnimationFrame(updateHighlight)
  }
}

// 高亮简化文本意群 - 基于音频帧时间戳
const highlightSimplifiedSegments = () => {
  if (!simplifiedSegments.value.length) return
  
  // 获取完整文本
  const fullText = currentDocument.value.simplifiedContent || ''
  
  // 计算意群位置映射
  const segmentsWithPositions = calculateSegmentPositions(simplifiedSegments.value, fullText)
  
  // 对于Edge-TTS，使用音频元素的timeupdate事件
  if (simplifiedAudio.value) {
    const audioElement = simplifiedAudio.value
    
    // 立即设置当前高亮位置，避免从头开始
    if (isSpeakingSimplified.value && simplifiedSpeechPosition.value > 0) {
      // 根据当前位置计算应该高亮的意群
      const targetCharIndex = simplifiedSpeechPosition.value
      
      // 找到包含该字符位置的意群
      for (const segment of segmentsWithPositions) {
        if (targetCharIndex >= segment.startIndex && targetCharIndex < segment.endIndex) {
          currentSimplifiedSegment.value = segment.id
          break
        }
      }
    }
    
    // 使用requestAnimationFrame实现更精确的实时同步
    const syncHighlight = () => {
      if (!isSpeakingSimplified.value || !audioElement) {
        return
      }
      
      // 获取音频总时长
      const totalDuration = audioElement.duration || ((fullText.length - simplifiedSpeechPosition.value) * 0.15 / (readerSettings.value.speechRate || 1.0))
      // 获取当前播放位置
      const currentTime = audioElement.currentTime
      
      // 计算当前在完整文本中的位置
      const progress = Math.min(currentTime / totalDuration, 1)
      const targetCharIndex = simplifiedSpeechPosition.value + Math.floor(progress * (fullText.length - simplifiedSpeechPosition.value))
      
      // 找到包含该字符位置的意群
      let currentSegmentId = null
      for (const segment of segmentsWithPositions) {
        if (targetCharIndex >= segment.startIndex && targetCharIndex < segment.endIndex) {
          currentSegmentId = segment.id
          break
        }
      }
      
      // 如果找不到，使用最接近的意群
      if (!currentSegmentId) {
        currentSegmentId = getCurrentSegmentByProgress(segmentsWithPositions, fullText, currentTime, totalDuration)
      }
      
      if (currentSegmentId !== currentSimplifiedSegment.value) {
        currentSimplifiedSegment.value = currentSegmentId
        // 自动滚动到高亮意群
        autoScrollToHighlightedSegment(currentSegmentId, 'simplified')
      }
      
      // 继续同步
      if (isSpeakingSimplified.value && currentTime < totalDuration) {
        requestAnimationFrame(syncHighlight)
      }
    }
    
    // 监听timeupdate事件作为备用
    const handleTimeUpdate = () => {
      if (!isSpeakingSimplified.value) {
        audioElement.removeEventListener('timeupdate', handleTimeUpdate)
        return
      }
    }
    
    // 监听ended事件
    const handleEnded = () => {
      audioElement.removeEventListener('timeupdate', handleTimeUpdate)
      audioElement.removeEventListener('ended', handleEnded)
      
      // 检查是否需要自动翻页
      const currentPage = paginationState.simplified.currentPage
      const totalPages = paginationState.simplified.totalPages
      
      if (currentPage < totalPages) {
        // 自动翻到下一页
        nextPage('simplified')
        
        // 延迟一段时间后继续朗读新页面
        setTimeout(() => {
          // 从新页面开始朗读
          simplifiedSpeechPosition.value = 0
          startSimplifiedSpeech()
        }, 500) // 等待页面切换完成
      } else {
        // 已经是最后一页，结束朗读
        isSpeakingSimplified.value = false
        currentSimplifiedSegment.value = null
        simplifiedSpeechPosition.value = 0
      }
    }
    
    // 先移除可能存在的旧监听器，避免重复添加
    audioElement.removeEventListener('timeupdate', handleTimeUpdate)
    audioElement.removeEventListener('ended', handleEnded)
    
    // 添加事件监听器
    audioElement.addEventListener('timeupdate', handleTimeUpdate)
    audioElement.addEventListener('ended', handleEnded)
    
    // 使用requestAnimationFrame开始实时同步（比timeupdate更精确）
    requestAnimationFrame(syncHighlight)
  } else {
    // 对于浏览器内置TTS，使用基于时间的估算
    const speechRate = readerSettings.value.speechRate || 1.0
    const totalDuration = fullText.length * 0.15 / speechRate // 每个字符0.15秒
    
    // 存储开始时间
    const startTime = Date.now()
    
    // 实时更新高亮
    const updateHighlight = () => {
      if (!isSpeakingSimplified.value) {
        currentSimplifiedSegment.value = null
        return
      }
      
      // 计算当前播放时间
      const currentPlayTime = (Date.now() - startTime) / 1000 // 转换为秒
      
      // 获取当前应该高亮的意群
      const segmentId = getCurrentSegmentByProgress(
        segmentsWithPositions, 
        fullText, 
        currentPlayTime, 
        totalDuration
      )
      
      if (segmentId !== currentSimplifiedSegment.value) {
        currentSimplifiedSegment.value = segmentId
        // 自动滚动到高亮意群
        autoScrollToHighlightedSegment(segmentId, 'simplified')
      }
      
      // 继续更新
      if (isSpeakingSimplified.value && currentPlayTime < totalDuration) {
        requestAnimationFrame(updateHighlight)
      } else {
        currentSimplifiedSegment.value = null
        simplifiedSpeechPosition.value = 0 // 朗读完成，重置位置
      }
    }
    
    // 开始实时更新
    requestAnimationFrame(updateHighlight)
  }
}

// 鼠标滚轮处理函数引用
const originalWheelHandler = (e) => handleScroll(e, 'original')
const simplifiedWheelHandler = (e) => handleScroll(e, 'simplified')

// 键盘事件处理函数
const handleKeyDown = (e) => {
  // 只在全屏模式下处理上下键
  if (isOriginalFullScreen.value || isSimplifiedFullScreen.value) {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (isOriginalFullScreen.value) {
        scrollUp('original')
      } else if (isSimplifiedFullScreen.value) {
        scrollUp('simplified')
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (isOriginalFullScreen.value) {
        scrollDown('original')
      } else if (isSimplifiedFullScreen.value) {
        scrollDown('simplified')
      }
    }
  }
}

// 生命周期
// 点击其他地方自动收起设置
const handleClickOutside = (event) => {
  // 检查是否点击了设置按钮（通过按钮文本内容检测）
  let isClickOnSettingButton = false
  const buttons = document.querySelectorAll('.el-button')
  buttons.forEach(button => {
    // 检查按钮是否包含"设置"文本
    if (button.textContent.includes('设置') && button.contains(event.target)) {
      isClickOnSettingButton = true
    }
  })
  
  // 如果点击了设置按钮，不做处理，因为toggleFullScreenSettings函数会处理
  if (isClickOnSettingButton) {
    return
  }
  
  // 检查是否点击了设置面板
  const settingPanel = document.querySelector('.fullscreen-settings-panel')
  const isClickOnSettingPanel = settingPanel && settingPanel.contains(event.target)
  
  // 检查是否点击了 el-select 的下拉菜单
  const selectDropdown = document.querySelector('.el-select-dropdown')
  const isClickOnSelectDropdown = selectDropdown && selectDropdown.contains(event.target)
  
  // 如果点击在设置面板外，且不在下拉菜单上，且设置面板是打开的，则收起设置
  if (!isClickOnSettingPanel && !isClickOnSelectDropdown && showFullScreenSettings.value) {
    showFullScreenSettings.value = false
  }
}

// 阅读时间记录
const readingStartTime = ref(Date.now())
const readingTime = ref(0)

onMounted(() => {
  // 加载阅读器设置
  appStore.loadReaderSettings()
  
  // 添加调试日志：检查词性标注数据
  console.log('=== 阅读器初始化 ===')
  console.log('当前文档ID:', currentDocument.value.id)
  console.log('pos_tags:', currentDocument.value.pos_tags)
  console.log('pos_tags 长度:', currentDocument.value.pos_tags?.length || 0)
  console.log('simplified_pos_tags:', currentDocument.value.simplified_pos_tags)
  console.log('simplified_pos_tags 长度:', currentDocument.value.simplified_pos_tags?.length || 0)
  console.log('posTagging 设置:', readerSettings.value.posTagging)
  
  // 如果没有文档内容，显示提示
  if (!currentDocument.value.content) {
    appStore.updateCurrentDocument({
      id: 1,
      content: '这是一个示例文档，用于测试阅读器功能。\n\n阅读障碍是一种常见的学习障碍，影响着许多人的阅读能力。我们的工具旨在通过各种辅助功能，帮助有阅读障碍的用户更轻松地阅读和理解中文文本。\n\n主要功能包括：意群划分、主次内容区分、文本简化、词语释义和文本转语音等。',
      segments: [
        { id: 1, text: '这是一个示例文档，', start_pos: 0, end_pos: 8, importance: 0.8, is_primary: true },
        { id: 2, text: '用于测试阅读器功能。', start_pos: 8, end_pos: 19, importance: 0.6, is_primary: false },
        { id: 3, text: '阅读障碍是一种常见的学习障碍，', start_pos: 21, end_pos: 36, importance: 0.8, is_primary: true },
        { id: 4, text: '影响着许多人的阅读能力。', start_pos: 36, end_pos: 49, importance: 0.7, is_primary: false },
        { id: 5, text: '我们的工具旨在通过各种辅助功能，', start_pos: 51, end_pos: 68, importance: 0.9, is_primary: true },
        { id: 6, text: '帮助有阅读障碍的用户更轻松地阅读和理解中文文本。', start_pos: 68, end_pos: 97, importance: 0.8, is_primary: true },
        { id: 7, text: '主要功能包括：', start_pos: 99, end_pos: 107, importance: 0.7, is_primary: false },
        { id: 8, text: '意群划分、', start_pos: 107, end_pos: 112, importance: 0.6, is_primary: false },
        { id: 9, text: '主次内容区分、', start_pos: 112, end_pos: 119, importance: 0.6, is_primary: false },
        { id: 10, text: '文本简化、', start_pos: 119, end_pos: 124, importance: 0.6, is_primary: false },
        { id: 11, text: '词语释义和文本转语音等。', start_pos: 124, end_pos: 140, importance: 0.6, is_primary: false }
      ],
      simplifiedContent: '这是一个示例文档，用来测试阅读器功能。\n\n阅读障碍是一种常见的学习问题，很多人都有。我们的工具通过各种辅助功能，帮助有阅读障碍的人更容易地读中文。\n\n主要功能有：把文章分成小块、标出重要内容、把复杂的话变简单、解释词语意思、把文字读出来等。',
      simplifiedSegments: [
        { id: 1, text: '这是一个示例文档，', start_pos: 0, end_pos: 8, importance: 0.8, is_primary: true },
        { id: 2, text: '用来测试阅读器功能。', start_pos: 8, end_pos: 19, importance: 0.6, is_primary: false },
        { id: 3, text: '阅读障碍是一种常见的学习问题，', start_pos: 21, end_pos: 36, importance: 0.8, is_primary: true },
        { id: 4, text: '很多人都有。', start_pos: 36, end_pos: 42, importance: 0.7, is_primary: false },
        { id: 5, text: '我们的工具通过各种辅助功能，', start_pos: 44, end_pos: 61, importance: 0.9, is_primary: true },
        { id: 6, text: '帮助有阅读障碍的人更容易地读中文。', start_pos: 61, end_pos: 84, importance: 0.8, is_primary: true },
        { id: 7, text: '主要功能有：', start_pos: 86, end_pos: 94, importance: 0.7, is_primary: false },
        { id: 8, text: '把文章分成小块、', start_pos: 94, end_pos: 102, importance: 0.6, is_primary: false },
        { id: 9, text: '标出重要内容、', start_pos: 102, end_pos: 109, importance: 0.6, is_primary: false },
        { id: 10, text: '把复杂的话变简单、', start_pos: 109, end_pos: 118, importance: 0.6, is_primary: false },
        { id: 11, text: '解释词语意思、', start_pos: 118, end_pos: 125, importance: 0.6, is_primary: false },
        { id: 12, text: '把文字读出来等。', start_pos: 125, end_pos: 134, importance: 0.6, is_primary: false }
      ],
      pos_tags: [
        { word: '这', pos: 'r', start_pos: 0, end_pos: 1 },
        { word: '是', pos: 'v', start_pos: 1, end_pos: 2 },
        { word: '一个', pos: 'm', start_pos: 2, end_pos: 4 },
        { word: '示例', pos: 'n', start_pos: 4, end_pos: 6 },
        { word: '文档', pos: 'n', start_pos: 6, end_pos: 8 }
      ],
      simplified_pos_tags: [
        { word: '这', pos: 'r', start_pos: 0, end_pos: 1 },
        { word: '是', pos: 'v', start_pos: 1, end_pos: 2 },
        { word: '一个', pos: 'm', start_pos: 2, end_pos: 4 },
        { word: '示例', pos: 'n', start_pos: 4, end_pos: 6 },
        { word: '文档', pos: 'n', start_pos: 6, end_pos: 8 }
      ]
    })
  }
  
  // 阅读历史已在编辑器处理完成后添加，此处不再重复添加
  // 如果需要更新阅读进度，会通过其他机制处理
  
  // 恢复上次阅读位置
  restoreReadingPosition()
  
  // 添加全屏状态变化监听器
  document.addEventListener('fullscreenchange', checkFullScreenStatus)
  
  // 添加键盘事件监听器
  document.addEventListener('keydown', handleKeyDown)
  
  // 添加点击事件监听器，用于自动收起设置
  document.addEventListener('click', handleClickOutside)
  
  // 在DOM更新后添加鼠标滚动事件监听器
  nextTick(() => {
    if (originalContentRef.value) {
      originalContentRef.value.addEventListener('wheel', originalWheelHandler, { passive: false })
    }
    if (simplifiedContentRef.value) {
      simplifiedContentRef.value.addEventListener('wheel', simplifiedWheelHandler, { passive: false })
    }
    
    // 在DOM更新后再初始化分页数据，确保文档数据已经更新
    initPagination()
  })
  
  // 开始计时
  readingStartTime.value = Date.now()
  readingTime.value = 0
})

// 生命周期 - 组件卸载时移除监听器
onUnmounted(() => {
  // 计算阅读时间
  const sessionReadTime = Math.floor((Date.now() - readingStartTime.value) / 1000) // 转换为秒
  
  // 更新阅读历史的阅读时间和进度
  if (currentDocument.value.content) {
    // 找到对应的阅读历史记录
    const existingHistory = appStore.readingHistory.find(item => 
      item.document_id === currentDocument.value.id || item.content === currentDocument.value.content
    )
    
    if (existingHistory) {
      // 累加阅读时间
      existingHistory.readTime += sessionReadTime
      // 更新最后阅读时间
      existingHistory.lastRead = new Date().toISOString().slice(0, 19).replace('T', ' ')
      // 更新阅读进度（使用当前页码）
      existingHistory.readingProgress = Math.round((paginationState.original.currentPage / (paginationState.original.totalPages || 1)) * 100)
      
      // 保存到本地存储
      saveReadingHistoryToStorage()
    }
  }
  
  document.removeEventListener('fullscreenchange', checkFullScreenStatus)
  
  // 移除键盘事件监听器
  document.removeEventListener('keydown', handleKeyDown)
  
  // 移除点击事件监听器
  document.removeEventListener('click', handleClickOutside)
  
  // 移除鼠标滚动事件监听器
  if (originalContentRef.value) {
    originalContentRef.value.removeEventListener('wheel', originalWheelHandler)
  }
  if (simplifiedContentRef.value) {
    simplifiedContentRef.value.removeEventListener('wheel', simplifiedWheelHandler)
  }
})

// 监听设置变化并保存
watch(() => readerSettings.value, (newSettings) => {
  localStorage.setItem('readerSettings', JSON.stringify(newSettings))
}, { deep: true })

// 监听配色方案变化，自动设置背景色和文字色
watch(() => readerSettings.value.colorScheme, (newScheme) => {
  switch (newScheme) {
    case 'eye':
      readerSettings.value.backgroundColor = '#e8f4ea'
      readerSettings.value.textColor = '#2d5a36'
      break
    case 'high-contrast':
      readerSettings.value.backgroundColor = '#000000'
      readerSettings.value.textColor = '#ffffff'
      break
    default:
      readerSettings.value.backgroundColor = '#ffffff'
      readerSettings.value.textColor = '#333333'
      break
  }
})

// 监听原文本高亮变化，自动滚动到当前意群
watch(() => currentOriginalSegment.value, (segmentId) => {
  if (segmentId && originalContentRef.value) {
    const targetElement = originalContentRef.value.querySelector(`[data-segment-id="${segmentId}"]`)
    if (targetElement) {
      scrollToElement(originalContentRef.value, targetElement, 'original')
    }
  }
})

// 监听简化文本高亮变化，自动滚动到当前意群
watch(() => currentSimplifiedSegment.value, (segmentId) => {
  if (segmentId && simplifiedContentRef.value) {
    const targetElement = simplifiedContentRef.value.querySelector(`[data-segment-id="${segmentId}"]`)
    if (targetElement) {
      scrollToElement(simplifiedContentRef.value, targetElement, 'simplified')
    }
  }
})

// 监听文档变化，重新初始化分页
watch(() => currentDocument.value.id, (newId) => {
  if (newId) {
    nextTick(() => {
      initPagination()
    })
  }
})

// 监听蒙版设置变化，当关闭蒙版时清除marginTop
watch(() => readerSettings.value.enableMask, (newValue, oldValue) => {
  if (oldValue === true && newValue === false) {
    // 蒙版被关闭，恢复原来的布局
    if (originalContentRef.value) {
      scrollToFirstVisibleLine(originalContentRef.value, 'original')
    }
    if (simplifiedContentRef.value) {
      scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
    }
  } else if (oldValue === false && newValue === true) {
    // 蒙版被开启，如果是全屏模式则滚动到第一行
    if (isOriginalFullScreen.value && originalContentRef.value) {
      nextTick(() => {
        scrollToFirstVisibleLine(originalContentRef.value, 'original')
      })
    }
    if (isSimplifiedFullScreen.value && simplifiedContentRef.value) {
      nextTick(() => {
        scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
      })
    }
  }
})

// 监听行高变化，重新计算蒙版高度和滚动位置
watch(() => readerSettings.value.lineHeight, () => {
  // 当行高变化时，重新计算蒙版高度和滚动位置
  if (isOriginalFullScreen.value && readerSettings.value.enableMask && originalContentRef.value) {
    nextTick(() => {
      scrollToFirstVisibleLine(originalContentRef.value, 'original')
    })
  }
  if (isSimplifiedFullScreen.value && readerSettings.value.enableMask && simplifiedContentRef.value) {
    nextTick(() => {
      scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
    })
  }
})

// 监听可见行数变化，重新计算蒙版高度和滚动位置
watch(() => readerSettings.value.maskLines, () => {
  // 当可见行数变化时，重新计算蒙版高度和滚动位置
  if (isOriginalFullScreen.value && readerSettings.value.enableMask && originalContentRef.value) {
    nextTick(() => {
      scrollToFirstVisibleLine(originalContentRef.value, 'original')
    })
  }
  if (isSimplifiedFullScreen.value && readerSettings.value.enableMask && simplifiedContentRef.value) {
    nextTick(() => {
      scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
    })
  }
})

// 监听字号变化，重新计算蒙版高度和滚动位置
watch(() => readerSettings.value.fontSize, () => {
  // 当字号变化时，重新计算蒙版高度和滚动位置
  if (isOriginalFullScreen.value && readerSettings.value.enableMask && originalContentRef.value) {
    nextTick(() => {
      scrollToFirstVisibleLine(originalContentRef.value, 'original')
    })
  }
  if (isSimplifiedFullScreen.value && readerSettings.value.enableMask && simplifiedContentRef.value) {
    nextTick(() => {
      scrollToFirstVisibleLine(simplifiedContentRef.value, 'simplified')
    })
  }
})
</script>

<style scoped>
/* 全局样式 */
:root {
  overflow-x: hidden;
}

body {
  overflow-x: hidden;
}

.reader-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 0 1rem;
  box-sizing: border-box;
  overflow-x: hidden;
}

.reader-container h2 {
  margin-bottom: 2rem;
  color: #333;
}

.reader-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.speech-controls {
  display: flex;
  gap: 0.5rem;
}

.reader-main {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
}

@media (min-width: 768px) {
  .reader-main {
    flex-wrap: nowrap;
  }
}

.reader-panel {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex: 1 1 0;
  min-width: 0;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}

@media (min-width: 768px) {
  .reader-panel {
    width: calc(50% - 0.5rem);
    flex: 1 1 calc(50% - 0.5rem);
  }
}

.reader-panel h3 {
  margin-bottom: 1rem;
  color: #333;
}

.reader-content {
  min-height: 400px;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  line-height: 1.6;
  position: relative;
  overflow-x: auto;
  overflow-y: auto;
  width: 100%;
  box-sizing: border-box;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
  white-space: normal;
  word-break: break-all;
}

@media (min-width: 768px) {
  .reader-content {
    padding: 1.5rem;
  }
}

@media (min-width: 1024px) {
  .reader-content {
    padding: 2rem;
  }
}

/* 防止长URL和代码撑宽容器 */
.reader-content * {
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-all;
  max-width: 100%;
  box-sizing: border-box;
}

/* 特别处理超长URL */
.reader-content a[href] {
  word-break: break-all !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  display: inline-block !important;
}

/* 处理纯文本URL（非链接形式） */
.reader-content :not(a) {
  word-break: break-all !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* 蒙版样式 */
.reader-content.mask-active {
  position: relative;
  overflow: auto;
  /* 确保内容在蒙版下方正确显示 */
  z-index: 1;
}

.reader-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  pointer-events: none;
  transition: all 0.3s ease;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, var(--mask-opacity, 0.8)) 0%,
    rgba(0, 0, 0, var(--mask-opacity, 0.8)) calc(50vh - var(--mask-height, 48px)),
    transparent calc(50vh - var(--mask-height, 48px)),
    transparent calc(50vh + var(--mask-height, 48px)),
    rgba(0, 0, 0, var(--mask-opacity, 0.8)) calc(50vh + var(--mask-height, 48px)),
    rgba(0, 0, 0, var(--mask-opacity, 0.8)) 100%
  );
}

/* 全屏模式下的内容容器 */
.reader-content:fullscreen {
  background-color: var(--bg-color, #ffffff) !important;
  color: var(--text-color, #333333) !important;
}

/* 确保滚动条在全屏模式下可见 */
.reader-content:fullscreen::-webkit-scrollbar {
  width: 8px;
}

.reader-content:fullscreen::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.reader-content:fullscreen::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
}

/* 意群样式 */
.text-segment,
.simplified-text-segment {
  display: inline;
  padding: 0 0.4rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  word-break: break-word;
  background-color: rgba(82, 134, 105, 0.25); /* 浅灰色背景，区分意群 */
  color: inherit; /* 继承文字颜色 */
  opacity: 1; /* 默认完全不透明 */
  font-size: inherit; /* 继承字体大小 */
  font-weight: normal; /* 默认正常字重 */
  border: none; /* 无边框 */
  border-bottom: none; /* 无下划线 */
}

.text-segment:hover,
.simplified-text-segment:hover {
  background-color: #f0f0f0;
}

/* 主要内容样式 - 更加明显 */
.primary-content {
  font-weight: bold;
  color: inherit; /* 继承文字颜色 */
  background-color: rgba(82, 134, 105, 0.25); /* 更明显的背景色 */
  border-left: 3px solid #40826d; /* 左侧实心边框 */
  padding: 0.2em 0.5em;
  border-radius: 4px;
  display: inline-block;
  vertical-align: middle;
  line-height: normal;
}

/* 次要内容样式 - 更加淡化 */
.secondary-content {
  opacity: 0.55; /* 更低的透明度 */
  color: #666666; /* 浅灰色文字 */
  background-color: rgba(128, 128, 128, 0.08); /* 淡淡的灰色背景 */
  border-bottom: 1px dotted #999999; /* 点状下划线 */
  padding: 0.1em 0.3em;
  display: inline-block;
  vertical-align: middle;
  line-height: normal;
}

/* 高亮意群样式 */
.highlighted-segment {
  background-color: rgba(255, 215, 0, 0.3) !important;
  border: 1px solid #ffd700;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(255, 215, 0, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 215, 0, 0);
  }
}

/* 面板头部样式 */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-controls {
  display: flex;
  gap: 0.5rem;
}

/* 进度条容器样式 */
.progress-container {
  margin-bottom: 1rem;
}

/* 全屏顶部控制按钮 */
.fullscreen-top-controls {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 0.5rem;
  z-index: 100;
}

.fullscreen-top-controls .el-button {
  background: rgba(255, 255, 255, 0.9) !important;
  border: none !important;
  color: #333 !important;
}

.fullscreen-top-controls .el-button:hover {
  background: rgba(255, 255, 255, 1) !important;
}

/* 全屏播放按钮 - 底部中央 */
.fullscreen-play-control {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
}

.play-button {
  width: 64px !important;
  height: 64px !important;
  background: rgba(255, 255, 255, 0.95) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

.play-button:hover {
  background: rgba(255, 255, 255, 1) !important;
  transform: scale(1.05);
}

.play-button .el-icon {
  font-size: 28px;
  color: #333;
}

/* 全屏设置面板 */
.fullscreen-settings-panel {
  position: fixed;
  top: 60px;
  right: 90px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 1rem;
  border-radius: 4px;
  z-index: 1000;
  min-width: 300px;
  max-height: 80vh;
  overflow-y: auto;
  /* 固定字体大小和行高，不受readerSettings影响 */
  font-size: 14px !important;
  line-height: 1.4 !important;
  letter-spacing: normal !important;
  word-spacing: normal !important;
}

.fullscreen-settings-panel h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 16px;
  text-align: center;
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-item label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 14px;
}

.fullscreen-settings-panel .el-slider {
  width: 100%;
}

.fullscreen-settings-panel .el-select {
  width: 100%;
  pointer-events: auto !important;
}

.fullscreen-settings-panel .el-select .el-select__input {
  pointer-events: auto !important;
}

.fullscreen-settings-panel .el-select .el-select__caret {
  pointer-events: auto !important;
}

/* 字体选择器样式 */
.font-select {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  color: #333;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
}

.font-select:hover {
  border-color: #c0c4cc;
}

.font-select:focus {
  outline: none;
  border-color: #40826d;
  box-shadow: 0 0 0 2px rgba(64, 130, 109, 0.2);
}

.font-select option {
  padding: 8px;
}

/* 全屏设置面板中的字体选择器 */
.fullscreen-settings-panel .font-select {
  background-color: rgba(255, 255, 255, 0.95);
  color: #333;
}

/* 全局下拉菜单样式 - 确保全屏模式下下拉菜单能正常显示 */
:deep(.el-select-dropdown) {
  z-index: 99999 !important;
  position: fixed !important;
  pointer-events: auto !important;
}

/* 全屏模式下的 el-select 下拉菜单 */
:deep(.reader-content:fullscreen) ~ .el-select-dropdown {
  z-index: 99999 !important;
  position: fixed !important;
}

/* 确保下拉菜单的遮罩层也能正常显示 */
:deep(.el-select-dropdown__wrap) {
  pointer-events: auto !important;
}

/* 确保 el-overlay 不会阻止交互 */
:deep(.el-overlay) {
  z-index: 99998 !important;
}

/* 全屏模式下的下拉菜单容器 */
:deep(.el-select-dropdown.el-popper) {
  z-index: 99999 !important;
  position: fixed !important;
  top: auto !important;
  left: auto !important;
  transform: none !important;
}

/* 确保全屏模式下下拉菜单能在最顶层显示 */
.fullscreen-settings-panel + .el-select-dropdown {
  z-index: 99999 !important;
}

/* 上下滚动按钮 */
.scroll-controls {
  position: fixed;
  right: 20px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.scroll-button {
  background: rgba(255, 255, 255, 0.95) !important;
  border: none !important;
  color: #333 !important;
  width: 48px !important;
  height: 48px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 50% !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
  margin: 0 !important;
}

.scroll-button:hover {
  background: rgba(255, 255, 255, 1) !important;
  transform: translateY(-50%) scale(1.05);
}

.scroll-button .el-icon {
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 上下按钮定位 */
.scroll-button-up {
  position: fixed;
  right: 20px;
  top: var(--scroll-button-up-top, 20px);
  transform: translateY(-50%);
}

.scroll-button-down {
  position: fixed;
  right: 20px;
  top: var(--scroll-button-down-top, 20px);
  transform: translateY(-50%);
}

/* 词性高亮样式 */
.word-tag {
  transition: all 0.3s;
}

.pos-noun {
  color: #409EFF;
}

.pos-verb {
  color: #67C23A;
}

.pos-adj {
  color: #E6A23C;
}

.pos-adv {
  color: #909399;
}

.pos-prep {
  color: #C0C4CC;
}

.pos-conj {
  color: #909399;
}

.pos-aux {
  color: #C0C4CC;
}

.pos-pron {
  color: #67C23A;
}

.pos-num {
  color: #E6A23C;
}

.pos-quant {
  color: #909399;
}

.pos-time {
  color: #409EFF;
}

.pos-place {
  color: #409EFF;
}

.pos-dir {
  color: #909399;
}

.pos-dist {
  color: #909399;
}

.pos-state {
  color: #E6A23C;
}

.pos-interj {
  color: #F56C6C;
}

.pos-modal {
  color: #909399;
}

.pos-onom {
  color: #F56C6C;
}

.pos-prefix {
  color: #909399;
}

.pos-suffix {
  color: #909399;
}

.pos-punct {
  color: #C0C4CC;
}

.pos-other {
  color: #909399;
}

/* 错落排版样式 */
.staggered-item {
  transition: all 0.3s;
}

/* 词语查询样式 */
.word-query {
  margin-top: 2rem;
  max-width: 400px;
}

.definition-content {
  padding: 1rem;
}

.definition-content h4 {
  margin-bottom: 0.5rem;
  color: #333;
}

.phonetic {
  color: #666;
  margin-bottom: 1rem;
}

.definitions,
.examples {
  margin-top: 1rem;
}

.definitions h5,
.examples h5,
.contextual-meaning h5 {
  margin-bottom: 0.5rem;
  color: #333;
}

.definitions ul,
.examples ul {
  margin: 0;
  padding-left: 1.5rem;
}

.definitions li,
.examples li {
  margin-bottom: 0.5rem;
  color: #666;
}

.contextual-meaning {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.contextual-meaning p {
  margin: 0;
  color: #409EFF;
  line-height: 1.6;
}

.no-definition {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.loading-content {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.loading-content p {
  margin-top: 1rem;
}

/* 分页控制样式 */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.pagination-controls .el-button {
  min-width: 80px;
}

.page-info {
  font-size: 14px;
  color: #666;
  min-width: 60px;
  text-align: center;
}

/* 进度条样式 */
.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 1rem;
  padding: 0 1rem;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: #eee;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #409eff;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
  min-width: 40px;
  text-align: right;
}

/* 目录样式 */
.toc-container {
  padding: 10px;
}

.toc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.toc-progress {
  font-weight: bold;
  color: #40826D;
}

.toc-list {
  max-height: 300px;
  overflow-y: auto;
}

.toc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.toc-item:hover {
  background-color: #f5f7fa;
}

.toc-item.active {
  background-color: #c2d9d3;
}

.toc-page {
  font-size: 14px;
  color: #333;
}

.toc-current {
  font-size: 12px;
  color: #40826D;
  font-weight: bold;
}

/* 全屏模式下的分页控制 */
:deep(.reader-content:fullscreen) .pagination-controls {
  position: fixed;
  bottom : 20px;
  left: 20px;
  transform : translateX(0);
  background: rgba(255, 255, 255, 0.9);
  padding: 5px 20px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 99;
  display: flex;
  gap: 1px;
  align-items: center;
}

/* 全屏模式下的分页按钮 */
:deep(.reader-content:fullscreen) .pagination-controls .el-button {
  padding: 6px 14px;
  font-size: 13px;
  min-width: auto;
}

/* 全屏模式下的页码信息 */
:deep(.reader-content:fullscreen) .pagination-controls .page-info {
  font-size: 13px;
  min-width: 50px;
}

/* 全屏模式下的目录对话框 */
:deep(.reader-content:fullscreen) .el-dialog.toc-dialog {
  z-index: 2147483647 !important;
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
}

/* 全屏模式下的目录对话框遮罩 */
:deep(.reader-content:fullscreen) .el-overlay.el-dialog__wrapper {
  z-index: 2147483646 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background-color: rgba(0, 0, 0, 0.5) !important;
}

/* 目录对话框基础样式 */
.el-dialog.toc-dialog {
  z-index: 1000 !important;
}

/* 目录对话框遮罩 */
.el-overlay.el-dialog__wrapper {
  z-index: 999 !important;
}
</style>
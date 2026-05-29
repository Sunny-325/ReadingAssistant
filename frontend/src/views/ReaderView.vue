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
            <el-button size="small" @click="handleOriginalPlayPause" :disabled="false">
              <el-icon v-if="isSpeakingOriginal"><VideoPause /></el-icon>
              <el-icon v-else-if="isOriginalPaused"><VideoPlay /></el-icon>
              <el-icon v-else><Microphone /></el-icon>
              {{ isSpeakingOriginal ? ' 暂停' : (isOriginalPaused ? ' 继续' : ' 播放') }}
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
              @click="handleOriginalPlayPause"
              class="play-button"
            >
              <el-icon v-if="isSpeakingOriginal" :size="24"><VideoPause /></el-icon>
              <el-icon v-else-if="isOriginalPaused" :size="24"><VideoPlay /></el-icon>
              <el-icon v-else :size="24"><VideoPlay /></el-icon>
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
              <select v-model="appStore.readerSettings.fontFamily" class="font-select">
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
              <template v-if="readerSettings.posTagging && (segment.pos_tags || (currentDocument.pos_tags && currentDocument.pos_tags.length > 0))">
                <span 
                  v-for="(word, index) in getSegmentWords(segment.text, segment.start_pos || 0, false, segment)" 
                  :key="word.position + '-' + index"
                  :class="word.isPlainText ? '' : ['word-tag', getPosClassByTag(word.tag)]"
                  :style="word.isPlainText ? {} : getPosStyleByTag(word.tag)"
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
              <template v-if="readerSettings.posTagging && (segment.pos_tags || (currentDocument.pos_tags && currentDocument.pos_tags.length > 0))">
                <span 
                  v-for="(word, index) in getSegmentWords(segment.text, segment.start_pos || 0, false, segment)" 
                  :key="word.position + '-' + index"
                  :class="word.isPlainText ? '' : ['word-tag', getPosClassByTag(word.tag)]"
                  :style="word.isPlainText ? {} : getPosStyleByTag(word.tag)"
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
                :style="getPosStyle(tag.word, tag.start_pos)"
              >
                {{ tag.word }}
              </span>
            </span>
          </template>
          <template v-else-if="currentDocument.content && currentDocument.content.length > 0">
            <!-- 未处理文档：直接显示原文本，支持分页 -->
            <div class="plain-text-content">
              {{ getCurrentPageContent() }}
            </div>
          </template>
          <template v-else>
            <div class="empty-content">
              <p>暂无内容</p>
            </div>
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
            <el-button size="small" @click="handleSimplifiedPlayPause" :disabled="false">
              <el-icon v-if="isSpeakingSimplified"><VideoPause /></el-icon>
              <el-icon v-else-if="isSimplifiedPaused"><VideoPlay /></el-icon>
              <el-icon v-else><Microphone /></el-icon>
              {{ isSpeakingSimplified ? ' 暂停' : (isSimplifiedPaused ? ' 继续' : ' 播放') }}
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
              @click="handleSimplifiedPlayPause"
              class="play-button"
            >
              <el-icon v-if="isSpeakingSimplified" :size="24"><VideoPause /></el-icon>
              <el-icon v-else-if="isSimplifiedPaused" :size="24"><VideoPlay /></el-icon>
              <el-icon v-else :size="24"><VideoPlay /></el-icon>
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
              <template v-if="readerSettings.posTagging && (segment.pos_tags || (currentDocument.simplified_pos_tags && currentDocument.simplified_pos_tags.length > 0))">
                <span 
                  v-for="word in getSegmentWords(segment.text, segment.start_pos || 0, true, segment)" 
                  :key="word.position"
                  :class="word.isPlainText ? '' : ['word-tag', getPosClass(word.text, word.position, true)]"
                  :style="word.isPlainText ? {} : getPosStyle(word.text, word.position, true)"
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
              <template v-if="readerSettings.posTagging && (segment.pos_tags || (currentDocument.simplified_pos_tags && currentDocument.simplified_pos_tags.length > 0))">
                <span 
                  v-for="word in getSegmentWords(segment.text, segment.start_pos || 0, true, segment)" 
                  :key="word.position"
                  :class="word.isPlainText ? '' : ['word-tag', getPosClass(word.text, word.position, true)]"
                  :style="word.isPlainText ? {} : getPosStyle(word.text, word.position, true)"
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
                :style="getPosStyle(tag.word, tag.start_pos, true)"
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

// 用于取消正在进行的请求
const abortController = ref(null)

// 从store中获取状态
const currentDocument = computed(() => appStore.currentDocument)
const readerSettings = computed(() => {
  const settings = appStore.readerSettings
  console.log('=== 阅读器设置 ===')
  console.log('posTagging:', settings.posTagging)
  console.log('selectedPosTags:', settings.selectedPosTags)
  return settings
})

// 更新设置并保存
const updateSetting = (key, value) => {
  console.log(`更新设置: ${key} = ${value}`)
  appStore.updateReaderSettings({ [key]: value })
}
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
    pageSize: 100,
    loadedPages: [1],  // 使用数组替代 Set
    pageCache: {},
    nextPageLoading: false
  },
  simplified: {
    currentPage: 1,
    totalPages: 1,
    pageSize: 100,
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

// 获取当前页的文本内容（用于未处理文档的分页显示）
const getCurrentPageContent = () => {
  const content = currentDocument.value.content || ''
  const state = paginationState.original
  const currentPage = state.currentPage
  
  // 未处理文档使用更大的分页尺寸（按段落分页，约1000字符/页）
  const plainTextPageSize = 1000
  
  // 按段落边界分页
  const pages = []
  let currentPageContent = ''
  
  // 按换行符分割段落
  const paragraphs = content.split(/\n\n|\n/)
  
  for (const paragraph of paragraphs) {
    // 如果当前页加上这个段落超过限制，就新建一页
    if (currentPageContent.length + paragraph.length > plainTextPageSize && currentPageContent.length > 0) {
      pages.push(currentPageContent.trim())
      currentPageContent = paragraph + '\n'
    } else {
      currentPageContent += paragraph + '\n'
    }
  }
  
  // 添加最后一页
  if (currentPageContent.trim()) {
    pages.push(currentPageContent.trim())
  }
  
  // 更新总页数
  state.totalPages = Math.max(1, pages.length)
  
  // 返回当前页内容（处理越界情况）
  const pageIndex = Math.max(0, Math.min(currentPage - 1, pages.length - 1))
  return pages[pageIndex] || content
}

// 朗读位置记录
const originalSpeechPosition = ref(0)
const simplifiedSpeechPosition = ref(0)

// 暂停状态记录（用于真正的暂停/恢复功能）
const originalPausedPosition = ref(0)  // 暂停时的位置
const simplifiedPausedPosition = ref(0)  // 暂停时的位置
const isOriginalPaused = ref(false)     // 是否处于暂停状态
const isSimplifiedPaused = ref(false)    // 是否处于暂停状态

// 全屏状态
const isOriginalFullScreen = ref(false)
const isSimplifiedFullScreen = ref(false)

// 页面停留时间跟踪
const pageVisitTime = ref({
  original: { page: 0, timestamp: 0 },
  simplified: { page: 0, timestamp: 0 }
})

// 阅读进度更新定时器
const progressUpdateTimer = ref(null)

// 最小阅读停留时间（秒），超过此时间才计入阅读进度
const MIN_READING_TIME = 30

// 分页相关方法
const fetchSegments = async (documentId, page, pageSize, type) => {
  try {
    // 在发送新请求前取消之前的请求
    if (abortController.value) {
      abortController.value.abort()
    }
    
    // 创建新的 abort controller
    abortController.value = new AbortController()
    
    // 在发送请求前记录当前文档ID
    const requestDocumentId = documentId
    
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
        },
        signal: abortController.value.signal
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
    
    // 检查文档是否已切换，如果已切换则忽略此响应
    if (currentDocument.value.id !== requestDocumentId) {
      console.log(`文档已切换，忽略旧请求的响应 (requestId: ${requestDocumentId}, currentId: ${currentDocument.value.id})`)
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
    // 处理请求被取消的情况
    if (error.name === 'AbortError') {
      console.log('请求已被取消（文档切换）')
      return null
    }
    console.error('获取分页意群失败:', error)
    return null
  }
}

const loadPage = async (type, page) => {
  const state = paginationState[type]
  
  // 记录上一页的停留时间
  const prevPage = state.currentPage
  const prevTimestamp = pageVisitTime.value[type].timestamp
  
  if (prevPage > 0 && prevTimestamp > 0) {
    const stayDuration = Math.floor((Date.now() - prevTimestamp) / 1000)
    
    // 如果停留时间超过最小阅读时间，更新阅读进度
    if (stayDuration >= MIN_READING_TIME) {
      updateReadingProgress(type, prevPage, stayDuration)
    }
  }
  
  if (state.loadedPages.includes(page)) {
    state.currentPage = page
    // 记录页面访问时间
    pageVisitTime.value[type] = { page, timestamp: Date.now() }
    return Promise.resolve()
  }
  
  // 检查是否是未处理文档（没有segments数据，使用纯文本分页）
  const hasSegments = type === 'original' 
    ? (currentDocument.value.segments && currentDocument.value.segments.length > 0)
    : (currentDocument.value.simplifiedSegments && currentDocument.value.simplifiedSegments.length > 0)
  
  if (!hasSegments) {
    // 未处理文档：直接更新页码，使用纯文本分页逻辑
    state.currentPage = page
    state.loadedPages.push(page)
    // 记录页面访问时间
    pageVisitTime.value[type] = { page, timestamp: Date.now() }
    return Promise.resolve()
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
    
    // 记录页面访问时间
    pageVisitTime.value[type] = { page, timestamp: Date.now() }
    
    // 预加载下一页
    if (page < state.totalPages) {
      preloadNextPage(type)
    }
  }
  
  return Promise.resolve()
}

// 更新阅读进度
const updateReadingProgress = (type, page, stayDuration = 0) => {
  const state = paginationState[type]
  const progress = Math.round((page / state.totalPages) * 100)
  
  // 更新对应类型的进度
  if (type === 'original') {
    originalProgress.value = progress
  } else {
    simplifiedProgress.value = progress
  }
  
  // 更新阅读历史（包含停留时间）
  updateReadingHistory(type, page, progress, stayDuration)
}

// 更新阅读历史记录
const updateReadingHistory = (type, page, progress, stayDuration = 0) => {
  if (!currentDocument.value.content) {
    return
  }
  
  // 找到对应的阅读历史记录
  const existingHistory = appStore.readingHistory.find(item => 
    item.document_id === currentDocument.value.id || item.content === currentDocument.value.content
  )
  
  if (existingHistory) {
    // 检查是否启用了文本简化
    // 优先从 currentDocument 中获取 processingSettings（当前实际使用的设置）
    const processingSettings = currentDocument.value.processingSettings || 
                               existingHistory.processingSettings || {}
    const enableSimplify = processingSettings.enableSimplify || false
    
    // 确定记录哪种文本类型的进度
    // 如果启用了文本简化，记录简化文本的进度；否则记录原文本的进度
    const shouldRecord = enableSimplify ? (type === 'simplified') : (type === 'original')
    
    if (shouldRecord) {
      // 更新阅读进度（同时更新两种字段名格式）
      existingHistory.readingProgress = progress
      existingHistory.reading_progress = progress / 100  // 后端期望小数形式 (0-1)
      
      // 更新最后阅读时间（同时更新两种字段名格式）
      const now = new Date()
      // 使用正确的格式：YYYY-MM-DD HH:mm:ss
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')
      const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
      existingHistory.lastRead = formattedTime
      existingHistory.last_read_at = formattedTime
      
      // 更新阅读时间（累加停留时间）
      if (stayDuration > 0) {
        existingHistory.readTime += stayDuration
        existingHistory.reading_time = existingHistory.readTime
      }
      
      // 更新当前阅读位置（字符索引）
      // 如果启用了文本简化，记录简化文本的位置；否则记录原文本的位置
      let currentPosition = 0
      if (type === 'original') {
        currentPosition = originalSpeechPosition.value
      } else {
        currentPosition = simplifiedSpeechPosition.value
      }
      existingHistory.current_position = currentPosition
      
      // 保存到本地存储和后端
      saveReadingHistoryToStorage()
      
      // 同步到后端
      syncReadingHistoryToBackend(existingHistory)
    }
  }
}

// 同步阅读历史到后端
const syncReadingHistoryToBackend = async (history) => {
  if (!appStore.user || !history.id) {
    return
  }
  
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      return
    }
    
    const response = await fetch(`/api/user/history/${history.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        reading_progress: history.reading_progress || history.readingProgress / 100,
        reading_time: history.reading_time || history.readTime,
        last_read_at: history.last_read_at || history.lastRead,
        current_position: history.current_position || 0
      })
    })
    
    if (!response.ok) {
      console.error('同步阅读历史失败:', response.status)
    }
  } catch (error) {
    console.error('同步阅读历史失败:', error)
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
  
  if (existingHistory) {
    // 检查是否启用了文本简化
    // 优先从 currentDocument 中获取 processingSettings（当前实际使用的设置）
    // 如果不存在，则从历史记录中获取
    const processingSettings = currentDocument.value.processingSettings || 
                               existingHistory.processingSettings || {}
    const enableSimplify = processingSettings.enableSimplify || false
    
    console.log('恢复阅读位置，processingSettings:', processingSettings)
    console.log('enableSimplify:', enableSimplify)
    console.log('simplifiedContent 是否存在:', !!currentDocument.value.simplifiedContent)
    
    // 根据设置决定恢复哪种文本类型的阅读位置
    if (enableSimplify && currentDocument.value.simplifiedContent) {
      // 恢复简化文本的阅读位置
      console.log('恢复简化文本阅读位置')
      restoreSimplifiedReadingPosition(existingHistory)
    } else {
      // 恢复原文本的阅读位置
      console.log('恢复原文本阅读位置')
      restoreOriginalReadingPosition(existingHistory)
    }
  }
}

// 恢复原文本阅读位置
const restoreOriginalReadingPosition = (history) => {
  if (!currentDocument.value.content) {
    return
  }
  
  let targetPosition = 0
  
  // 优先使用 current_position（字符索引）
  if (history.current_position && history.current_position > 0) {
    targetPosition = history.current_position
  } else if (history.readingProgress && history.readingProgress > 0) {
    // 使用阅读进度计算位置
    const progress = history.readingProgress / 100
    const fullText = currentDocument.value.content
    targetPosition = Math.floor(progress * fullText.length)
  }
  
  // 恢复朗读位置
  originalSpeechPosition.value = targetPosition
  
  // 计算目标页码
  const segment = segments.value.find(s => s.start_pos <= targetPosition && s.end_pos > targetPosition)
  if (segment) {
    const segmentIndex = segments.value.findIndex(s => s.id === segment.id)
    const pageSize = paginationState.original.pageSize
    const targetPage = Math.ceil((segmentIndex + 1) / pageSize)
    
    // 跳转到上次阅读的页面
    setTimeout(() => {
      loadPage('original', targetPage).then(() => {
        // 页面加载完成后，滚动到目标意群并设置高亮
        nextTick(() => {
          scrollToSegment(segment.id, 'original')
          currentOriginalSegment.value = segment.id
        })
      })
    }, 500)
  }
}

// 恢复简化文本阅读位置
const restoreSimplifiedReadingPosition = (history) => {
  if (!currentDocument.value.simplifiedContent) {
    return
  }
  
  let targetPosition = 0
  
  // 优先使用 current_position（字符索引）
  if (history.current_position && history.current_position > 0) {
    targetPosition = history.current_position
  } else if (history.readingProgress && history.readingProgress > 0) {
    // 使用阅读进度计算位置
    const progress = history.readingProgress / 100
    const fullText = currentDocument.value.simplifiedContent
    targetPosition = Math.floor(progress * fullText.length)
  }
  
  // 恢复朗读位置
  simplifiedSpeechPosition.value = targetPosition
  
  // 计算目标页码
  const segment = simplifiedSegments.value.find(s => s.start_pos <= targetPosition && s.end_pos > targetPosition)
  if (segment) {
    const segmentIndex = simplifiedSegments.value.findIndex(s => s.id === segment.id)
    const pageSize = paginationState.simplified.pageSize
    const targetPage = Math.ceil((segmentIndex + 1) / pageSize)
    
    // 跳转到上次阅读的页面
    setTimeout(() => {
      loadPage('simplified', targetPage).then(() => {
        // 页面加载完成后，滚动到目标意群并设置高亮
        nextTick(() => {
          scrollToSegment(segment.id, 'simplified')
          currentSimplifiedSegment.value = segment.id
        })
      })
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
    // 如果正在朗读，暂停朗读并记录当前位置
    if (type === 'original' && isSpeakingOriginal.value) {
      pauseOriginalSpeech()
    } else if (type === 'simplified' && isSpeakingSimplified.value) {
      pauseSimplifiedSpeech()
    }
    
    loadPage(type, state.currentPage + 1).then(() => {
      // 翻页后，更新高亮为当前页第一个意群，并设置朗读位置
      updateHighlightOnPageChange(type)
      // 设置朗读位置为当前页第一个意群（但不开始朗读）
      setSpeechPositionToCurrentPage(type)
      
      // 只重置暂停状态，不重置位置（位置已经被 setSpeechPositionToCurrentPage 设置为正确的值）
      if (type === 'original') {
        isOriginalPaused.value = false
      } else if (type === 'simplified') {
        isSimplifiedPaused.value = false
      }
    })
  }
}

const prevPage = (type) => {
  const state = paginationState[type]
  if (state.currentPage > 1) {
    // 如果正在朗读，暂停朗读并记录当前位置
    if (type === 'original' && isSpeakingOriginal.value) {
      pauseOriginalSpeech()
    } else if (type === 'simplified' && isSpeakingSimplified.value) {
      pauseSimplifiedSpeech()
    }
    
    loadPage(type, state.currentPage - 1).then(() => {
      // 翻页后，更新高亮为当前页第一个意群，并设置朗读位置
      updateHighlightOnPageChange(type)
      // 设置朗读位置为当前页第一个意群（但不开始朗读）
      setSpeechPositionToCurrentPage(type)
      
      // 只重置暂停状态，不重置位置（位置已经被 setSpeechPositionToCurrentPage 设置为正确的值）
      if (type === 'original') {
        isOriginalPaused.value = false
      } else if (type === 'simplified') {
        isSimplifiedPaused.value = false
      }
    })
  }
}

const goToPage = (type, page) => {
  const state = paginationState[type]
  if (page >= 1 && page <= state.totalPages) {
    // 如果正在朗读，暂停朗读并记录当前位置
    if (type === 'original' && isSpeakingOriginal.value) {
      pauseOriginalSpeech()
    } else if (type === 'simplified' && isSpeakingSimplified.value) {
      pauseSimplifiedSpeech()
    }
    
    loadPage(type, page).then(() => {
      // 翻页后，更新高亮为当前页第一个意群，并设置朗读位置
      updateHighlightOnPageChange(type)
      // 设置朗读位置为当前页第一个意群（但不开始朗读）
      setSpeechPositionToCurrentPage(type)
      
      // 只重置暂停状态，不重置位置（位置已经被 setSpeechPositionToCurrentPage 设置为正确的值）
      if (type === 'original') {
        isOriginalPaused.value = false
      } else if (type === 'simplified') {
        isSimplifiedPaused.value = false
      }
    })
  }
}

// 翻页时更新意群高亮
const updateHighlightOnPageChange = (type) => {
  const state = paginationState[type]
  const currentPage = state.currentPage
  const pageSize = state.pageSize
  
  // 计算当前页面第一个意群的索引
  const firstSegmentIndex = (currentPage - 1) * pageSize
  
  // 获取当前页面的意群列表
  const allSegments = type === 'original' ? segments.value : simplifiedSegments.value
  
  if (allSegments.length > firstSegmentIndex) {
    const firstSegment = allSegments[firstSegmentIndex]
    if (type === 'original') {
      currentOriginalSegment.value = firstSegment.id
    } else {
      currentSimplifiedSegment.value = firstSegment.id
    }
  }
}

// 设置朗读位置为当前页第一个意群（但不开始朗读）
const setSpeechPositionToCurrentPage = (type) => {
  const state = paginationState[type]
  const currentPage = state.currentPage
  const pageSize = state.pageSize
  
  // 计算当前页面第一个意群的索引
  const firstSegmentIndex = (currentPage - 1) * pageSize
  
  // 获取当前页面的意群列表
  const allSegments = type === 'original' ? segments.value : simplifiedSegments.value
  const fullText = type === 'original' ? currentDocument.value.content : currentDocument.value.simplifiedContent
  
  if (allSegments.length > firstSegmentIndex) {
    const firstSegment = allSegments[firstSegmentIndex]
    const targetPosition = firstSegment.start_pos || 0
    
    if (type === 'original') {
      originalSpeechPosition.value = targetPosition
      // 如果是暂停状态，恢复也从此位置开始
      originalPausedPosition.value = targetPosition
    } else {
      simplifiedSpeechPosition.value = targetPosition
      simplifiedPausedPosition.value = targetPosition
    }
  } else {
    // 如果没有意群数据，使用估算值
    const estimatedCharsPerSegment = 20
    const targetPosition = firstSegmentIndex * estimatedCharsPerSegment
    
    if (type === 'original') {
      originalSpeechPosition.value = Math.min(targetPosition, fullText.length - 1)
      originalPausedPosition.value = Math.min(targetPosition, fullText.length - 1)
    } else {
      simplifiedSpeechPosition.value = Math.min(targetPosition, fullText.length - 1)
      simplifiedPausedPosition.value = Math.min(targetPosition, fullText.length - 1)
    }
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
  
  if (!currentDocument.value.id) {
    console.log('No document id, returning')
    return
  }
  
  // 获取历史记录的阅读进度（如果有）
  let historyProgress = currentDocument.value.reading_progress || 0
  // 如果 readingProgress 是百分比形式（0-100），转换为小数形式（0-1）
  if (currentDocument.value.readingProgress !== undefined && currentDocument.value.readingProgress > 1) {
    historyProgress = currentDocument.value.readingProgress / 100
  }
  console.log('历史阅读进度（小数形式）:', historyProgress)
  
  // 重置分页状态（后端限制 page_size 最大为100）
  paginationState.original = {
    currentPage: 1,
    totalPages: 1,
    pageSize: 100, // 每页100个意群
    loadedPages: [],
    pageCache: {},
    nextPageLoading: false
  }
  paginationState.simplified = {
    currentPage: 1,
    totalPages: 1,
    pageSize: 100,
    loadedPages: [],
    pageCache: {},
    nextPageLoading: false
  }
  
  // 检查文档是否已有预计算的意群数据
  const hasOriginalSegments = currentDocument.value.segments && currentDocument.value.segments.length > 0
  const hasSimplifiedSegments = currentDocument.value.simplifiedSegments && currentDocument.value.simplifiedSegments.length > 0
  
  // 并行处理原文本和简化文本的分页初始化
  const promises = []
  
  if (hasOriginalSegments) {
    // 使用文档中已有的意群数据进行分页（同步处理，最快）
    const allSegments = currentDocument.value.segments
    paginationState.original.totalPages = Math.ceil(allSegments.length / paginationState.original.pageSize)
    paginationState.original.pageCache[1] = allSegments.slice(0, paginationState.original.pageSize)
    paginationState.original.loadedPages = [1]
    
    // 根据历史进度设置当前页码
    if (historyProgress > 0 && historyProgress <= 1) {
      const targetPage = Math.max(1, Math.ceil(historyProgress * paginationState.original.totalPages))
      paginationState.original.currentPage = Math.min(targetPage, paginationState.original.totalPages)
      console.log('根据历史进度设置原文本页码:', paginationState.original.currentPage)
      
      // 加载目标页的数据
      const startIndex = (paginationState.original.currentPage - 1) * paginationState.original.pageSize
      paginationState.original.pageCache[paginationState.original.currentPage] = allSegments.slice(startIndex, startIndex + paginationState.original.pageSize)
      if (!paginationState.original.loadedPages.includes(paginationState.original.currentPage)) {
        paginationState.original.loadedPages.push(paginationState.original.currentPage)
      }
    } else {
      paginationState.original.currentPage = 1
    }
    
    // 如果有更多页，预加载下一页（异步，不阻塞）
    if (paginationState.original.totalPages > 1) {
      setTimeout(() => {
        paginationState.original.pageCache[2] = allSegments.slice(paginationState.original.pageSize, paginationState.original.pageSize * 2)
        paginationState.original.loadedPages.push(2)
      }, 100)
    }
  } else {
    // 从后端获取分页数据（后端期望1-based页码）
    promises.push(fetchSegments(
      currentDocument.value.id, 
      1, 
      paginationState.original.pageSize, 
      'original'
    ).then(originalResult => {
      if (originalResult) {
        paginationState.original.pageCache[1] = originalResult.segments
        paginationState.original.totalPages = originalResult.total_pages
        paginationState.original.loadedPages = [1]
        
        // 根据历史进度设置当前页码
        if (historyProgress > 0 && historyProgress <= 1) {
          const targetPage = Math.max(1, Math.ceil(historyProgress * paginationState.original.totalPages))
          paginationState.original.currentPage = Math.min(targetPage, paginationState.original.totalPages)
          console.log('根据历史进度设置原文本页码:', paginationState.original.currentPage)
        } else {
          paginationState.original.currentPage = 1
        }
      }
    }).catch(err => {
      console.error('Failed to fetch original segments:', err)
    }))
  }
  
  if (hasSimplifiedSegments) {
    // 使用文档中已有的简化意群数据进行分页（同步处理）
    const allSimplifiedSegments = currentDocument.value.simplifiedSegments
    paginationState.simplified.totalPages = Math.ceil(allSimplifiedSegments.length / paginationState.simplified.pageSize)
    paginationState.simplified.pageCache[1] = allSimplifiedSegments.slice(0, paginationState.simplified.pageSize)
    paginationState.simplified.loadedPages = [1]
    
    // 根据历史进度设置当前页码
    if (historyProgress > 0 && historyProgress <= 1) {
      const targetPage = Math.max(1, Math.ceil(historyProgress * paginationState.simplified.totalPages))
      paginationState.simplified.currentPage = Math.min(targetPage, paginationState.simplified.totalPages)
      console.log('根据历史进度设置简化文本页码:', paginationState.simplified.currentPage)
      
      // 加载目标页的数据
      const startIndex = (paginationState.simplified.currentPage - 1) * paginationState.simplified.pageSize
      paginationState.simplified.pageCache[paginationState.simplified.currentPage] = allSimplifiedSegments.slice(startIndex, startIndex + paginationState.simplified.pageSize)
      if (!paginationState.simplified.loadedPages.includes(paginationState.simplified.currentPage)) {
        paginationState.simplified.loadedPages.push(paginationState.simplified.currentPage)
      }
    } else {
      paginationState.simplified.currentPage = 1
    }
    
    // 如果有更多页，预加载下一页（异步，不阻塞）
    if (paginationState.simplified.totalPages > 1) {
      setTimeout(() => {
        paginationState.simplified.pageCache[2] = allSimplifiedSegments.slice(paginationState.simplified.pageSize, paginationState.simplified.pageSize * 2)
        paginationState.simplified.loadedPages.push(2)
      }, 100)
    }
  } else if (currentDocument.value.simplifiedContent) {
    // 如果有简化文本但没有预计算的意群，从后端获取
    promises.push(fetchSegments(
      currentDocument.value.id, 
      1, 
      paginationState.simplified.pageSize, 
      'simplified'
    ).then(simplifiedResult => {
      if (simplifiedResult) {
        paginationState.simplified.pageCache[1] = simplifiedResult.segments
        paginationState.simplified.totalPages = simplifiedResult.total_pages
        paginationState.simplified.loadedPages = [1]
        
        // 根据历史进度设置当前页码
        if (historyProgress > 0 && historyProgress <= 1) {
          const targetPage = Math.max(1, Math.ceil(historyProgress * paginationState.simplified.totalPages))
          paginationState.simplified.currentPage = Math.min(targetPage, paginationState.simplified.totalPages)
          console.log('根据历史进度设置简化文本页码:', paginationState.simplified.currentPage)
        } else {
          paginationState.simplified.currentPage = 1
        }
      }
    }).catch(err => {
      console.error('Failed to fetch simplified segments:', err)
    }))
  }
  
  // 设置朗读位置为当前页
  setTimeout(() => {
    setSpeechPositionToCurrentPage('original')
    setSpeechPositionToCurrentPage('simplified')
  }, 200)
  
  // 等待所有异步操作完成（但不阻塞UI）
  if (promises.length > 0) {
    Promise.all(promises).then(() => {
      console.log('All segment fetching completed')
      // 异步加载完成后再次设置朗读位置
      setSpeechPositionToCurrentPage('original')
      setSpeechPositionToCurrentPage('simplified')
    }).catch(err => {
      console.error('Error during pagination init:', err)
    })
  }
  
  // 立即返回，不等待异步操作完成
  return
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
    // 获取词语附近的部分上下文（避免发送整篇文章）
    const fullContent = currentDocument.value.content || ''
    const context = getPartialContext(fullContent, queryWord.value, 200)
    const definition = await getWordDefinition(queryWord.value, context)
    appStore.showDefinitionPanel(queryWord.value, definition)
  } catch (error) {
    console.error('获取词语释义失败:', error)
    appStore.hideDefinitionPanel()
    alert('获取词语释义失败，请稍后重试')
  }
}

// 获取词语附近的部分上下文（改进版：在句子边界截取，保证语义完整）
const getPartialContext = (content, word, contextLength = 200) => {
  if (!content || !word) return ''

  const index = content.indexOf(word)
  if (index === -1) {
    return content.substring(0, Math.min(contextLength * 2, content.length))
  }

  // 句子结束标记（包括中文标点和英文标点）
  const sentenceEndChars = new Set(['。', '！', '？', '.', '!', '?', '；', ';'])
  // 句子内的小停顿（可以在此处截断但不打断语义）
  const pauseChars = new Set(['，', ',', '、', '：', ':'])

  // 向前查找：找到词语所在句子的开始
  let sentenceStart = index
  let charsFromPause = 0
  let charsFromSentenceEnd = 0

  while (sentenceStart > 0) {
    const char = content[sentenceStart - 1]

    // 如果遇到句子结束符，检查是否达到了足够的上下文
    if (sentenceEndChars.has(char)) {
      break
    }

    // 计算到词语的距离
    charsFromPause++
    charsFromSentenceEnd++

    // 如果已经向后扩展了足够多的内容（超过contextLength），强制截断
    if (charsFromPause >= contextLength && charsFromSentenceEnd >= contextLength) {
      break
    }

    // 如果在小停顿处且距离已够，向前扩展一点点就停止
    if (pauseChars.has(char) && charsFromPause > 20) {
      break
    }

    sentenceStart--
  }

  // 向后查找：找到词语所在句子的结束
  let sentenceEnd = index + word.length
  charsFromPause = 0
  charsFromSentenceEnd = 0

  while (sentenceEnd < content.length) {
    const char = content[sentenceEnd]

    // 遇到句子结束符，在这个位置截断（包含结束符）
    if (sentenceEndChars.has(char)) {
      sentenceEnd++
      break
    }

    // 计算到词语的距离
    charsFromPause++
    charsFromSentenceEnd++

    // 如果已经扩展了足够多的内容，强制截断
    if (charsFromPause >= contextLength && charsFromSentenceEnd >= contextLength) {
      break
    }

    // 如果在小停顿处且距离已够，可以选择在此截断（但不强制）
    if (pauseChars.has(char) && charsFromPause > 50) {
      // 不在这里截断，继续走到句子结束
    }

    sentenceEnd++
  }

  // 确保不超出文本范围
  sentenceStart = Math.max(0, sentenceStart)
  sentenceEnd = Math.min(content.length, sentenceEnd)

  // 提取结果
  let result = content.substring(sentenceStart, sentenceEnd)

  // 如果上下文太短，向前后扩展到合理长度
  if (result.length < contextLength) {
    // 向前扩展
    let expandStart = sentenceStart
    while (expandStart > 0 && result.length < contextLength) {
      const char = content[expandStart - 1]
      expandStart--
      result = char + result

      // 在句子结束符处停止
      if (sentenceEndChars.has(char)) {
        break
      }
    }
    sentenceStart = expandStart

    // 向后扩展
    let expandEnd = sentenceEnd
    while (expandEnd < content.length && result.length < contextLength) {
      const char = content[expandEnd]
      result += char
      expandEnd++

      // 在句子结束符处停止
      if (sentenceEndChars.has(char)) {
        break
      }
    }
    sentenceEnd = expandEnd
  }

  // 如果上下文仍然太短，继续扩展（不限制在句子边界）
  while (result.length < contextLength && (sentenceStart > 0 || sentenceEnd < content.length)) {
    // 交替向前向后扩展
    if (sentenceStart > 0 && result.length < contextLength) {
      sentenceStart--
      result = content[sentenceStart] + result
    }
    if (sentenceEnd < content.length && result.length < contextLength) {
      result += content[sentenceEnd]
      sentenceEnd++
    }
  }

  // 添加省略号标记
  if (sentenceStart > 0) {
    result = '...' + result
  }
  if (sentenceEnd < content.length) {
    result = result + '...'
  }

  return result
}

// 缓存词性标注索引以提高性能
let posTagsIndex = null
let simplifiedPosTagsIndex = null

const buildPosTagsIndex = () => {
  // 为原始文本构建索引
  posTagsIndex = {}
  if (currentDocument.value.pos_tags) {
    for (const tag of currentDocument.value.pos_tags) {
      posTagsIndex[tag.start_pos] = tag
    }
  }
  
  // 为简化文本构建索引
  simplifiedPosTagsIndex = {}
  if (currentDocument.value.simplified_pos_tags) {
    for (const tag of currentDocument.value.simplified_pos_tags) {
      simplifiedPosTagsIndex[tag.start_pos] = tag
    }
  }
}

const getPosClass = (word, position, isSimplified = false) => {
  // 延迟构建索引
  if (!posTagsIndex || !simplifiedPosTagsIndex) {
    buildPosTagsIndex()
  }
  
  const index = isSimplified ? simplifiedPosTagsIndex : posTagsIndex
  if (!index) return ''
  
  // 使用索引快速查找
  const tag = index[position]
  
  // 如果精确匹配失败，尝试使用词匹配
  if (!tag && word) {
    const posTags = isSimplified ? currentDocument.value.simplified_pos_tags : currentDocument.value.pos_tags
    if (posTags) {
      const matchingTag = posTags.find(t => t.word === word && Math.abs(t.start_pos - position) < 5)
      if (matchingTag) {
        return getPosClassByTag(matchingTag)
      }
    }
    return ''
  }
  
  if (!tag) return ''
  
  return getPosClassByTag(tag)
}

// 检查词性标签是否匹配（支持前缀匹配，如'nr'匹配'n'）
const matchesPosTag = (tag, selectedTags) => {
  if (!tag || !selectedTags || selectedTags.length === 0) return false
  // 如果精确匹配，直接返回true
  if (selectedTags.includes(tag)) {
    return true
  }
  // 检查前缀匹配（如'nr'匹配'n'，'vd'匹配'v'）
  return selectedTags.some(selected => tag.startsWith(selected))
}

const getPosClassByTag = (tag) => {
  // 检查该词性是否在用户选中的标注列表中（支持前缀匹配）
  const selectedPosTags = readerSettings.value.selectedPosTags || ['n', 'v', 'a']
  if (!matchesPosTag(tag.pos, selectedPosTags)) {
    // 未选中的词性不显示
    return ''
  }
  return 'word-tag-highlight'
}

const getPosStyle = (word, position, isSimplified = false) => {
  // 延迟构建索引
  if (!posTagsIndex || !simplifiedPosTagsIndex) {
    buildPosTagsIndex()
  }
  
  const index = isSimplified ? simplifiedPosTagsIndex : posTagsIndex
  if (!index) return {}
  
  // 使用索引快速查找
  const tag = index[position]
  
  // 如果精确匹配失败，尝试使用词匹配
  if (!tag && word) {
    const posTags = isSimplified ? currentDocument.value.simplified_pos_tags : currentDocument.value.pos_tags
    if (posTags) {
      const matchingTag = posTags.find(t => t.word === word && Math.abs(t.start_pos - position) < 5)
      if (matchingTag) {
        return getPosStyleByTag(matchingTag)
      }
    }
    return {}
  }
  
  if (!tag) return {}
  
  return getPosStyleByTag(tag)
}

const getPosStyleByTag = (tag) => {
  // 检查该词性是否在用户选中的标注列表中
  const selectedPosTags = readerSettings.value.selectedPosTags || ['n', 'v', 'a']
  
  // 获取用户设置的词性颜色
  const posColors = readerSettings.value.posColors || {}
  const color = posColors[tag.pos] || readerSettings.value.textColor
  
  // 返回样式对象：只设置颜色，字号保持与用户设置一致（不单独设置字号）
  // 无论是否在选中列表中，都返回样式
  return {
    color: color
  }
}

const getPosFontSize = (word, position, isSimplified = false) => {
  // 不再单独设置字号，字号由父元素控制
  return {}
}

const getSegmentWords = (segmentText, segmentStartPos, isSimplified = false, segment = null) => {
  // 优先使用segment自己的词性标注（位置基于segment内部，从0开始）
  // 如果segment没有单独的词性标注，回退到全局词性标注（位置基于整个文档）
  const segmentPosTags = segment ? segment.pos_tags : null
  const isUsingSegmentPosTags = segmentPosTags && segmentPosTags.length > 0
  const posTags = isUsingSegmentPosTags 
    ? segmentPosTags 
    : (isSimplified ? currentDocument.value.simplified_pos_tags : currentDocument.value.pos_tags)
  const selectedPosTags = readerSettings.value.selectedPosTags || ['n', 'v', 'a']
  
  // 如果没有词性标注，直接返回整个意群文本作为一个普通文本块
  if (!posTags || !segmentText || posTags.length === 0) {
    return [{
      text: segmentText,
      position: segmentStartPos,
      isPlainText: true
    }]
  }
  
  // 关键：根据使用的是segment.pos_tags还是全局pos_tags，使用不同的文本进行匹配
  // segment.pos_tags是基于segment.text生成的，所以直接使用segmentText
  // 全局pos_tags是基于整个文档生成的，所以需要从原文本中截取对应位置的内容
  let textToProcess
  if (isUsingSegmentPosTags) {
    // 使用segment自己的词性标注时，直接使用segmentText
    textToProcess = segmentText
  } else {
    // 使用全局词性标注时，从原文本中截取对应位置的内容
    const sourceText = isSimplified 
      ? (currentDocument.value.simplifiedContent || currentDocument.value.content)
      : currentDocument.value.content
    textToProcess = sourceText 
      ? sourceText.substring(segmentStartPos, segmentStartPos + segmentText.length)
      : segmentText
  }
    
  // 根据使用的pos_tags类型，计算segment的结束位置
  const segmentEndPos = isUsingSegmentPosTags 
    ? textToProcess.length  // segment内部位置，从0开始
    : segmentStartPos + textToProcess.length  // 全局位置
    
  // 过滤出在当前segment范围内且用户选中的词性标注
  const tagsInSegment = posTags
    .filter(tag => {
      // 根据使用的pos_tags类型，使用不同的位置判断逻辑
      let positionMatch
      if (isUsingSegmentPosTags) {
        // segment.pos_tags的位置是基于segment内部的（从0开始）
        positionMatch = tag.start_pos >= 0 && tag.start_pos + tag.word.length <= textToProcess.length
      } else {
        // 全局pos_tags的位置是基于整个文档的
        positionMatch = tag.start_pos >= segmentStartPos && tag.start_pos + tag.word.length <= segmentEndPos
      }
      return positionMatch &&
             tag.word && tag.word.trim() &&
             matchesPosTag(tag.pos, selectedPosTags)
    })
    .sort((a, b) => {
      if (a.start_pos !== b.start_pos) {
        return a.start_pos - b.start_pos
      }
      return b.word.length - a.word.length
    })
  
  // 如果没有选中的词性标注，直接返回整个意群
  if (tagsInSegment.length === 0) {
    return [{
      text: textToProcess,
      position: segmentStartPos,
      isPlainText: true
    }]
  }
  
  const words = []
  let currentPos = 0
  
  while (currentPos < textToProcess.length) {
    // 根据使用的pos_tags类型，计算当前位置
    const currentMatchPos = isUsingSegmentPosTags 
      ? currentPos  // segment.pos_tags: 使用相对位置
      : segmentStartPos + currentPos  // 全局pos_tags: 使用绝对位置
    
    // 查找从当前位置开始的标注词
    const matchingTag = tagsInSegment.find(tag => tag.start_pos === currentMatchPos)
    
    if (matchingTag) {
      // 计算这个标注词在segment中的相对结束位置
      const tagRelativeEnd = isUsingSegmentPosTags 
        ? matchingTag.start_pos + matchingTag.word.length  // segment.pos_tags: 直接相加
        : matchingTag.start_pos + matchingTag.word.length - segmentStartPos  // 全局pos_tags: 转换为相对位置
      
      // 确保不超出segment范围
      if (tagRelativeEnd <= textToProcess.length) {
        // 获取segment中对应位置的文本
        const actualText = textToProcess.substring(currentPos, tagRelativeEnd)
        
        if (actualText === matchingTag.word) {
          // 匹配成功，添加标注词
          words.push({
            text: matchingTag.word,
            position: matchingTag.start_pos,
            tag: matchingTag
          })
          currentPos = tagRelativeEnd
          continue
        }
      }
    }
    
    // 如果没有找到匹配的标注词，或者匹配失败，添加普通文本字符
    const charPosition = isUsingSegmentPosTags 
      ? currentPos  // segment.pos_tags: 使用相对位置
      : segmentStartPos + currentPos  // 全局pos_tags: 使用绝对位置
    
    words.push({
      text: textToProcess[currentPos],
      position: charPosition,
      isPlainText: true
    })
    currentPos++
  }
  
  return words
}


// 获取当前可见区域的第一个意群
const getFirstVisibleSegment = (type) => {
  const element = type === 'original' ? originalContentRef.value : simplifiedContentRef.value
  if (!element) return null
  
  // 获取可见区域的边界
  const rect = element.getBoundingClientRect()
  const visibleTop = rect.top
  const visibleBottom = rect.bottom

  // 找到可见区域内的第一个意群
  const segmentElements = type === 'original' 
    ? element.querySelectorAll('.text-segment')
    : element.querySelectorAll('.simplified-text-segment')
  
  for (const segmentElement of segmentElements) {
    const segmentRect = segmentElement.getBoundingClientRect()
    // 检查意群是否在可见区域内
    if (segmentRect.top < visibleBottom && segmentRect.bottom > visibleTop) {
      // 获取意群ID并查找对应的意群数据
      const segmentId = segmentElement.getAttribute('data-segment-id')
      if (segmentId) {
        const segmentsList = type === 'original' ? segments.value : simplifiedSegments.value
        return segmentsList.find(s => s.id === segmentId) || null
      }
    }
  }
  
  return null
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
  let startPosition = 0
  
  if (startFromPosition !== null) {
    // 如果传入了指定位置，使用传入的位置（如拖动音频条）
    startPosition = startFromPosition
  } else {
    // 用户主动点击播放，从当前可见区域的第一个意群开始
    // 先尝试获取当前可见区域的第一个意群
    const visibleSegment = getFirstVisibleSegment('original')
    
    if (visibleSegment) {
      // 使用可见区域的第一个意群位置
      startPosition = visibleSegment.start_pos || 0
    } else {
      // 如果无法获取可见意群，使用分页状态作为备选
      const currentPage = paginationState.original.currentPage
      const pageSize = paginationState.original.pageSize
      
      // 计算当前页面的起始意群索引
      const startSegmentIndex = (currentPage - 1) * pageSize
      
      // 获取当前页面的第一个意群
      if (segments.value.length > 0 && startSegmentIndex < segments.value.length) {
        const firstSegment = segments.value[startSegmentIndex]
        startPosition = firstSegment.start_pos || 0
      } else {
        // 如果没有意群数据，使用估算值
        const estimatedCharsPerSegment = 20
        startPosition = startSegmentIndex * estimatedCharsPerSegment
      }
    }
    
    // 确保不超过文本长度
    startPosition = Math.min(startPosition, fullText.length - 1)
    
    // 更新朗读位置为当前页面开始位置
    originalSpeechPosition.value = startPosition
  }
  
  // 如果上次朗读已完成，从头开始
  if (startPosition >= fullText.length) {
    startPosition = 0
    originalSpeechPosition.value = 0
  }
  
  // 获取从当前位置开始的所有意群文本（确保从完整的意群开始朗读）
  let text = ''
  const startSegmentIndex = segments.value.findIndex(s => s.start_pos <= startPosition && s.end_pos > startPosition)
  
  if (startSegmentIndex >= 0) {
    // 从当前意群开始，拼接所有后续意群的文本
    for (let i = startSegmentIndex; i < segments.value.length; i++) {
      text += segments.value[i].text
    }
  } else {
    // 如果找不到对应意群，使用字符截取作为备选
    text = fullText.substring(startPosition)
  }
  
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

// 暂停原文本朗读（保持位置，可恢复）
const pauseOriginalSpeech = () => {
  if (!isSpeakingOriginal.value && !isOriginalPaused.value) {
    return
  }
  
  // 记录当前朗读位置
  let currentPosition = originalSpeechPosition.value
  
  // 尝试通过音频元素的当前时间计算更精确的位置
  if (originalAudio.value && originalAudio.value.duration > 0) {
    const fullText = currentDocument.value.content || ''
    const progress = originalAudio.value.currentTime / originalAudio.value.duration
    currentPosition = originalSpeechPosition.value + Math.floor(progress * (fullText.length - originalSpeechPosition.value))
  } else if (currentOriginalSegment.value && segments.value.length > 0) {
    const segment = segments.value.find(s => s.id === currentOriginalSegment.value)
    if (segment) {
      currentPosition = segment.start_pos || 0
    }
  }
  
  // 保存暂停位置
  originalPausedPosition.value = currentPosition
  originalSpeechPosition.value = currentPosition
  
  if (originalAudio.value) {
    originalAudio.value.pause()
  }
  
  if ('speechSynthesis' in window) {
    speechSynthesis.pause()
  }
  
  isSpeakingOriginal.value = false
  isOriginalPaused.value = true
  // 保持高亮在当前位置
}

// 恢复原文本朗读（从暂停位置继续）
const resumeOriginalSpeech = async () => {
  if (!isOriginalPaused.value) {
    // 如果不是暂停状态，正常开始朗读
    startOriginalSpeech()
    return
  }
  
  // 从暂停位置恢复朗读
  const startPosition = originalPausedPosition.value
  originalSpeechPosition.value = startPosition
  isOriginalPaused.value = false
  isSpeakingOriginal.value = true
  
  const fullText = currentDocument.value.content
  
  // 获取从暂停位置开始的所有意群文本（确保从完整的意群开始朗读）
  let text = ''
  let resumeSegmentId = null
  const startSegmentIndex = segments.value.findIndex(s => s.start_pos <= startPosition && s.end_pos > startPosition)
  
  if (startSegmentIndex >= 0) {
    // 从当前意群开始，拼接所有后续意群的文本
    for (let i = startSegmentIndex; i < segments.value.length; i++) {
      text += segments.value[i].text
    }
    // 记录恢复时的起始意群ID，用于正确计算高亮
    resumeSegmentId = segments.value[startSegmentIndex].id
  } else {
    // 如果找不到对应意群，使用字符截取作为备选
    text = fullText.substring(startPosition)
  }
  
  // 在蒙版模式下，滚动到当前位置
  if (isOriginalFullScreen.value && readerSettings.value.enableMask && originalContentRef.value) {
    nextTick(() => {
      const segment = segments.value.find(s => s.start_pos <= startPosition && s.end_pos > startPosition)
      if (segment) {
        const targetElement = originalContentRef.value.querySelector(`[data-segment-id="${segment.id}"]`)
        if (targetElement) {
          scrollToElement(originalContentRef.value, targetElement, 'original')
        }
      }
    })
  }
  
  try {
    const audioBlob = await pyttsx3(
      text,
      Math.round((readerSettings.value.speechRate || 1.0) * 150),
      readerSettings.value.speechVolume || 1.0
    )
    
    originalAudio.value = playPyttsx3(audioBlob, () => {
      isSpeakingOriginal.value = false
      isOriginalPaused.value = false
      currentOriginalSegment.value = null
      originalAudio.value = null
    })
    
    // 立即设置高亮为恢复时的起始意群（避免等待音频加载）
    if (resumeSegmentId) {
      currentOriginalSegment.value = resumeSegmentId
    } else {
      // 尝试根据位置找到对应意群
      const segment = segments.value.find(s => s.start_pos <= startPosition && s.end_pos > startPosition)
      if (segment) {
        currentOriginalSegment.value = segment.id
      }
    }
    
    // 开始高亮意群
    highlightOriginalSegments()
  } catch (error) {
    console.error('pyttsx3调用失败:', error)
    isSpeakingOriginal.value = false
    isOriginalPaused.value = false
  }
}

// 停止原文本朗读（完全停止，重置位置）
const stopOriginalSpeech = () => {
  // 记录当前位置以备恢复（如果是暂停状态）
  const wasPaused = isOriginalPaused.value
  const pausedPos = originalPausedPosition.value
  
  // 清除暂停状态
  isOriginalPaused.value = false
  
  if (originalAudio.value) {
    originalAudio.value.pause()
    originalAudio.value.currentTime = 0
    originalAudio.value.removeEventListener('timeupdate', () => {})
    originalAudio.value.removeEventListener('ended', () => {})
    originalAudio.value = null
  }
  
  if ('speechSynthesis' in window) {
    speechSynthesis.cancel()
  }
  
  // 重置位置
  originalSpeechPosition.value = 0
  originalPausedPosition.value = 0
  isSpeakingOriginal.value = false
  
  // 如果是从暂停状态停止，保持高亮在原位；否则清除高亮
  if (!wasPaused) {
    currentOriginalSegment.value = null
  }
}

// 处理原文本播放/暂停按钮点击
const handleOriginalPlayPause = () => {
  if (isSpeakingOriginal.value) {
    // 正在播放 -> 暂停
    pauseOriginalSpeech()
  } else if (isOriginalPaused.value) {
    // 暂停状态 -> 恢复播放
    resumeOriginalSpeech()
  } else {
    // 停止状态 -> 开始播放（从当前页开始）
    startOriginalSpeech()
  }
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
    // 使用意群在数组中的索引来计算页码（更准确）
    const segmentIndex = segments.value.findIndex(s => s.id === segment.id)
    const targetPage = Math.ceil((segmentIndex + 1) / pageSize)
    
    // 如果目标页面与当前页面不同，先加载目标页面
    if (targetPage !== paginationState.original.currentPage) {
      loadPage('original', targetPage).then(() => {
        // 页面加载完成后，等待DOM更新再滚动
        nextTick(() => {
          scrollToSegment(segment.id, 'original')
          // 开始朗读
          startOriginalSpeech(targetPosition)
        })
      })
    } else {
      // 已经在目标页面，直接滚动
      scrollToSegment(segment.id, 'original')
      // 如果没有播放，从当前位置开始播放
      if (!isSpeakingOriginal.value) {
        startOriginalSpeech(targetPosition)
      }
    }
  } else {
    // 如果找不到意群，从指定位置开始朗读
    if (!isSpeakingOriginal.value) {
      startOriginalSpeech(targetPosition)
    }
  }
  
  // 如果正在播放，更新音频位置
  if (originalAudio.value && isSpeakingOriginal.value) {
    const targetTime = (value / 100) * originalAudio.value.duration
    originalAudio.value.currentTime = targetTime
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
  let startPosition = 0
  
  if (startFromPosition !== null) {
    // 如果传入了指定位置，使用传入的位置（如拖动音频条）
    startPosition = startFromPosition
  } else {
    // 用户主动点击播放，从当前可见区域的第一个意群开始
    // 先尝试获取当前可见区域的第一个意群
    const visibleSegment = getFirstVisibleSegment('simplified')
    
    if (visibleSegment) {
      // 使用可见区域的第一个意群位置
      startPosition = visibleSegment.start_pos || 0
    } else {
      // 如果无法获取可见意群，使用分页状态作为备选
      const currentPage = paginationState.simplified.currentPage
      const pageSize = paginationState.simplified.pageSize
      
      // 计算当前页面的起始意群索引
      const startSegmentIndex = (currentPage - 1) * pageSize
      
      // 获取当前页面的第一个意群
      if (simplifiedSegments.value.length > 0 && startSegmentIndex < simplifiedSegments.value.length) {
        const firstSegment = simplifiedSegments.value[startSegmentIndex]
        startPosition = firstSegment.start_pos || 0
      } else {
        // 如果没有意群数据，使用估算值
        const estimatedCharsPerSegment = 20
        startPosition = startSegmentIndex * estimatedCharsPerSegment
      }
    }
    
    // 确保不超过文本长度
    startPosition = Math.min(startPosition, fullText.length - 1)
    
    // 更新朗读位置为当前页面开始位置
    simplifiedSpeechPosition.value = startPosition
  }
  
  // 如果上次朗读已完成，从头开始
  if (startPosition >= fullText.length) {
    startPosition = 0
    simplifiedSpeechPosition.value = 0
  }
  
  // 获取从当前位置开始的所有意群文本（确保从完整的意群开始朗读）
  let text = ''
  const startSegmentIndex = simplifiedSegments.value.findIndex(s => s.start_pos <= startPosition && s.end_pos > startPosition)
  
  if (startSegmentIndex >= 0) {
    // 从当前意群开始，拼接所有后续意群的文本
    for (let i = startSegmentIndex; i < simplifiedSegments.value.length; i++) {
      text += simplifiedSegments.value[i].text
    }
  } else {
    // 如果找不到对应意群，使用字符截取作为备选
    text = fullText.substring(startPosition)
  }
  
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
  // 记录当前位置以备恢复（如果是暂停状态）
  const wasPaused = isSimplifiedPaused.value
  
  // 清除暂停状态
  isSimplifiedPaused.value = false
  
  if (simplifiedAudio.value) {
    simplifiedAudio.value.pause()
    simplifiedAudio.value.currentTime = 0
    simplifiedAudio.value.removeEventListener('timeupdate', () => {})
    simplifiedAudio.value.removeEventListener('ended', () => {})
    simplifiedAudio.value = null
  }
  
  if ('speechSynthesis' in window) {
    speechSynthesis.cancel()
  }
  
  // 重置位置
  simplifiedSpeechPosition.value = 0
  simplifiedPausedPosition.value = 0
  isSpeakingSimplified.value = false
  
  // 如果是从暂停状态停止，保持高亮在原位；否则清除高亮
  if (!wasPaused) {
    currentSimplifiedSegment.value = null
  }
}

// 暂停简化文本朗读（保持位置，可恢复）
const pauseSimplifiedSpeech = () => {
  if (!isSpeakingSimplified.value && !isSimplifiedPaused.value) {
    return
  }
  
  // 记录当前朗读位置
  let currentPosition = simplifiedSpeechPosition.value
  
  // 尝试通过音频元素的当前时间计算更精确的位置
  if (simplifiedAudio.value && simplifiedAudio.value.duration > 0) {
    const fullText = currentDocument.value.simplifiedContent || ''
    const progress = simplifiedAudio.value.currentTime / simplifiedAudio.value.duration
    currentPosition = simplifiedSpeechPosition.value + Math.floor(progress * (fullText.length - simplifiedSpeechPosition.value))
  } else if (currentSimplifiedSegment.value && simplifiedSegments.value.length > 0) {
    const segment = simplifiedSegments.value.find(s => s.id === currentSimplifiedSegment.value)
    if (segment) {
      currentPosition = segment.start_pos || 0
    }
  }
  
  // 保存暂停位置
  simplifiedPausedPosition.value = currentPosition
  simplifiedSpeechPosition.value = currentPosition
  
  if (simplifiedAudio.value) {
    simplifiedAudio.value.pause()
  }
  
  if ('speechSynthesis' in window) {
    speechSynthesis.pause()
  }
  
  isSpeakingSimplified.value = false
  isSimplifiedPaused.value = true
  // 保持高亮在当前位置
}

// 恢复简化文本朗读（从暂停位置继续）
const resumeSimplifiedSpeech = async () => {
  if (!isSimplifiedPaused.value) {
    // 如果不是暂停状态，正常开始朗读
    startSimplifiedSpeech()
    return
  }
  
  // 从暂停位置恢复朗读
  const startPosition = simplifiedPausedPosition.value
  simplifiedSpeechPosition.value = startPosition
  isSimplifiedPaused.value = false
  isSpeakingSimplified.value = true
  
  const fullText = currentDocument.value.simplifiedContent
  
  // 获取从暂停位置开始的所有意群文本（确保从完整的意群开始朗读）
  let text = ''
  let resumeSegmentId = null
  const startSegmentIndex = simplifiedSegments.value.findIndex(s => s.start_pos <= startPosition && s.end_pos > startPosition)
  
  if (startSegmentIndex >= 0) {
    // 从当前意群开始，拼接所有后续意群的文本
    for (let i = startSegmentIndex; i < simplifiedSegments.value.length; i++) {
      text += simplifiedSegments.value[i].text
    }
    // 记录恢复时的起始意群ID，用于正确计算高亮
    resumeSegmentId = simplifiedSegments.value[startSegmentIndex].id
  } else {
    // 如果找不到对应意群，使用字符截取作为备选
    text = fullText.substring(startPosition)
  }
  
  // 在蒙版模式下，滚动到当前位置
  if (isSimplifiedFullScreen.value && readerSettings.value.enableMask && simplifiedContentRef.value) {
    nextTick(() => {
      const segment = simplifiedSegments.value.find(s => s.start_pos <= startPosition && s.end_pos > startPosition)
      if (segment) {
        const targetElement = simplifiedContentRef.value.querySelector(`[data-segment-id="${segment.id}"]`)
        if (targetElement) {
          scrollToElement(simplifiedContentRef.value, targetElement, 'simplified')
        }
      }
    })
  }
  
  try {
    const audioBlob = await pyttsx3(
      text,
      Math.round((readerSettings.value.speechRate || 1.0) * 150),
      readerSettings.value.speechVolume || 1.0
    )
    
    simplifiedAudio.value = playPyttsx3(audioBlob, () => {
      isSpeakingSimplified.value = false
      isSimplifiedPaused.value = false
      currentSimplifiedSegment.value = null
      simplifiedAudio.value = null
    })
    
    // 立即设置高亮为恢复时的起始意群（避免等待音频加载）
    if (resumeSegmentId) {
      currentSimplifiedSegment.value = resumeSegmentId
    } else {
      // 尝试根据位置找到对应意群
      const segment = simplifiedSegments.value.find(s => s.start_pos <= startPosition && s.end_pos > startPosition)
      if (segment) {
        currentSimplifiedSegment.value = segment.id
      }
    }
    
    // 开始高亮意群
    highlightSimplifiedSegments()
  } catch (error) {
    console.error('pyttsx3调用失败:', error)
    isSpeakingSimplified.value = false
    isSimplifiedPaused.value = false
  }
}

// 处理简化文本播放/暂停按钮点击
const handleSimplifiedPlayPause = () => {
  if (isSpeakingSimplified.value) {
    // 正在播放 -> 暂停
    pauseSimplifiedSpeech()
  } else if (isSimplifiedPaused.value) {
    // 暂停状态 -> 恢复播放
    resumeSimplifiedSpeech()
  } else {
    // 停止状态 -> 开始播放（从当前页开始）
    startSimplifiedSpeech()
  }
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
    // 使用意群在数组中的索引来计算页码（更准确）
    const segmentIndex = simplifiedSegments.value.findIndex(s => s.id === segment.id)
    const targetPage = Math.ceil((segmentIndex + 1) / pageSize)
    
    // 如果目标页面与当前页面不同，先加载目标页面
    if (targetPage !== paginationState.simplified.currentPage) {
      loadPage('simplified', targetPage).then(() => {
        // 页面加载完成后，等待DOM更新再滚动
        nextTick(() => {
          scrollToSegment(segment.id, 'simplified')
          // 开始朗读
          startSimplifiedSpeech(targetPosition)
        })
      })
    } else {
      // 已经在目标页面，直接滚动
      scrollToSegment(segment.id, 'simplified')
      // 如果没有播放，从当前位置开始播放
      if (!isSpeakingSimplified.value) {
        startSimplifiedSpeech(targetPosition)
      }
    }
  } else {
    // 如果找不到意群，从指定位置开始朗读
    if (!isSpeakingSimplified.value) {
      startSimplifiedSpeech(targetPosition)
    }
  }
  
  // 如果正在播放，更新音频位置
  if (simplifiedAudio.value && isSpeakingSimplified.value) {
    const targetTime = (value / 100) * simplifiedAudio.value.duration
    simplifiedAudio.value.currentTime = targetTime
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
    let firstVisibleSegmentIndex = -1
    for (let i = 0; i < segmentElements.length; i++) {
      const segmentRect = segmentElements[i].getBoundingClientRect()
      if (segmentRect.top < visibleBottom && segmentRect.bottom > visibleTop) {
        firstVisibleSegment = segmentElements[i]
        firstVisibleSegmentIndex = i
        break
      }
    }

    // 如果找到可见区域内的意群，从该意群开始朗读
    if (firstVisibleSegment && firstVisibleSegmentIndex >= 0) {
      const segmentId = firstVisibleSegment.getAttribute('data-segment-id')
      if (segmentId) {
        // 计算该意群对应的文本位置
        const segmentsList = type === 'original' ? segments.value : simplifiedSegments.value
        const segment = segmentsList.find(s => s.id === segmentId)
        
        // 更新当前页码（根据可见的第一个意群计算）
        const pageSize = paginationState[type].pageSize
        const targetPage = Math.ceil((firstVisibleSegmentIndex + 1) / pageSize)
        if (targetPage !== paginationState[type].currentPage) {
          paginationState[type].currentPage = targetPage
        }
        
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
            startOriginalSpeech(startPosition)
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
            startSimplifiedSpeech(startPosition)
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
    
    // 使用requestAnimationFrame实现更精确的实时同步（意群级同步）
    const syncHighlight = () => {
      if (!isSpeakingOriginal.value || !audioElement) {
        return
      }
      
      // 获取音频总时长
      const totalDuration = audioElement.duration || ((fullText.length - originalSpeechPosition.value) * 0.15 / (readerSettings.value.speechRate || 1.0))
      // 获取当前播放位置
      const currentTime = audioElement.currentTime
      
      // 找到朗读起始位置对应的意群索引（起始意群是从该位置开始的第一个完整意群）
      let startSegmentIndex = 0
      for (let i = 0; i < segmentsWithPositions.length; i++) {
        if (originalSpeechPosition.value >= segmentsWithPositions[i].startIndex && 
            originalSpeechPosition.value < segmentsWithPositions[i].endIndex) {
          startSegmentIndex = i
          break
        }
      }
      
      // 计算起始意群内的字符偏移（恢复时可能在意群中间开始）
      const startSegment = segmentsWithPositions[startSegmentIndex]
      const charOffsetInStartSegment = originalSpeechPosition.value - startSegment.startIndex
      
      // 计算从起始意群开始的所有意群的总字符数
      let totalCharsFromStart = 0
      for (let i = startSegmentIndex; i < segmentsWithPositions.length; i++) {
        totalCharsFromStart += segmentsWithPositions[i].text.length
      }
      
      // 计算当前应该读到的字符位置（在意群范围内，加上起始意群内的偏移）
      const progress = Math.min(currentTime / totalDuration, 1)
      const currentCharOffset = Math.floor(progress * totalCharsFromStart) + charOffsetInStartSegment
      
      // 找到当前正在朗读的意群（意群级同步）
      let currentSegmentId = null
      let accumulatedChars = 0
      for (let i = startSegmentIndex; i < segmentsWithPositions.length; i++) {
        const segment = segmentsWithPositions[i]
        if (currentCharOffset < accumulatedChars + segment.text.length) {
          currentSegmentId = segment.id
          break
        }
        accumulatedChars += segment.text.length
      }
      
      if (currentSegmentId !== currentOriginalSegment.value) {
        currentOriginalSegment.value = currentSegmentId
        
        // 检查当前意群是否在当前页面上
        const currentSegment = segmentsWithPositions.find(s => s.id === currentSegmentId)
        if (currentSegment) {
          const segmentIndex = segmentsWithPositions.findIndex(s => s.id === currentSegmentId)
          const pageSize = paginationState.original.pageSize
          const targetPage = Math.ceil((segmentIndex + 1) / pageSize)
          
          if (targetPage !== paginationState.original.currentPage) {
            // 意群不在当前页面，需要翻页
            loadPage('original', targetPage).then(() => {
              // 页面加载完成后，滚动到目标意群
              nextTick(() => {
                scrollToSegment(currentSegmentId, 'original')
              })
            })
          } else {
            // 意群在当前页面，检查是否需要滚动（仅蒙版模式下自动滚动）
            const isMaskEnabled = isOriginalFullScreen.value && readerSettings.value.enableMask
            if (isMaskEnabled) {
              autoScrollToHighlightedSegment(currentSegmentId, 'original')
            }
          }
        }
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
    
    // 使用requestAnimationFrame实现更精确的实时同步（意群级同步）
    const syncHighlight = () => {
      if (!isSpeakingSimplified.value || !audioElement) {
        return
      }
      
      // 获取音频总时长
      const totalDuration = audioElement.duration || ((fullText.length - simplifiedSpeechPosition.value) * 0.15 / (readerSettings.value.speechRate || 1.0))
      // 获取当前播放位置
      const currentTime = audioElement.currentTime
      
      // 找到朗读起始位置对应的意群索引（起始意群是从该位置开始的第一个完整意群）
      let startSegmentIndex = 0
      for (let i = 0; i < segmentsWithPositions.length; i++) {
        if (simplifiedSpeechPosition.value >= segmentsWithPositions[i].startIndex && 
            simplifiedSpeechPosition.value < segmentsWithPositions[i].endIndex) {
          startSegmentIndex = i
          break
        }
      }
      
      // 计算起始意群内的字符偏移（恢复时可能在意群中间开始）
      const startSegment = segmentsWithPositions[startSegmentIndex]
      const charOffsetInStartSegment = simplifiedSpeechPosition.value - startSegment.startIndex
      
      // 计算从起始意群开始的所有意群的总字符数
      let totalCharsFromStart = 0
      for (let i = startSegmentIndex; i < segmentsWithPositions.length; i++) {
        totalCharsFromStart += segmentsWithPositions[i].text.length
      }
      
      // 计算当前应该读到的字符位置（在意群范围内，加上起始意群内的偏移）
      const progress = Math.min(currentTime / totalDuration, 1)
      const currentCharOffset = Math.floor(progress * totalCharsFromStart) + charOffsetInStartSegment
      
      // 找到当前正在朗读的意群（意群级同步）
      let currentSegmentId = null
      let accumulatedChars = 0
      for (let i = startSegmentIndex; i < segmentsWithPositions.length; i++) {
        const segment = segmentsWithPositions[i]
        if (currentCharOffset < accumulatedChars + segment.text.length) {
          currentSegmentId = segment.id
          break
        }
        accumulatedChars += segment.text.length
      }
      
      if (currentSegmentId !== currentSimplifiedSegment.value) {
        currentSimplifiedSegment.value = currentSegmentId
        
        // 检查当前意群是否在当前页面上
        const currentSegment = segmentsWithPositions.find(s => s.id === currentSegmentId)
        if (currentSegment) {
          const segmentIndex = segmentsWithPositions.findIndex(s => s.id === currentSegmentId)
          const pageSize = paginationState.simplified.pageSize
          const targetPage = Math.ceil((segmentIndex + 1) / pageSize)
          
          if (targetPage !== paginationState.simplified.currentPage) {
            // 意群不在当前页面，需要翻页
            loadPage('simplified', targetPage).then(() => {
              // 页面加载完成后，滚动到目标意群
              nextTick(() => {
                scrollToSegment(currentSegmentId, 'simplified')
              })
            })
          } else {
            // 意群在当前页面，检查是否需要滚动（仅蒙版模式下自动滚动）
            const isMaskEnabled = isSimplifiedFullScreen.value && readerSettings.value.enableMask
            if (isMaskEnabled) {
              autoScrollToHighlightedSegment(currentSegmentId, 'simplified')
            }
          }
        }
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

onMounted(() => {
  // 加载阅读器设置
  appStore.loadReaderSettings()
  
  // 从processingSettings恢复相关设置
  const processingSettings = currentDocument.value.processingSettings
  if (processingSettings) {
    console.log('从processingSettings恢复设置:', processingSettings)
    // 恢复enableMainContent设置
    if (processingSettings.enableMainContent !== undefined) {
      appStore.updateReaderSettings({ enableMainContent: processingSettings.enableMainContent })
    }
    // 恢复enableChunk设置
    if (processingSettings.enableChunk !== undefined) {
      appStore.updateReaderSettings({ enableChunk: processingSettings.enableChunk })
    }
    // 恢复enableSimplify设置
    if (processingSettings.enableSimplify !== undefined) {
      appStore.updateReaderSettings({ enableSimplify: processingSettings.enableSimplify })
    }
    // 恢复posTagging设置
    if (processingSettings.posTagging !== undefined) {
      appStore.updateReaderSettings({ posTagging: processingSettings.posTagging })
    }
  }
  
  // 添加调试日志：检查词性标注数据
  console.log('=== 阅读器初始化 ===')
  console.log('当前文档ID:', currentDocument.value.id)
  console.log('segments:', currentDocument.value.segments)
  console.log('segments第一个元素:', currentDocument.value.segments?.[0])
  console.log('pos_tags:', currentDocument.value.pos_tags)
  console.log('pos_tags 长度:', currentDocument.value.pos_tags?.length || 0)
  console.log('simplified_pos_tags:', currentDocument.value.simplified_pos_tags)
  console.log('simplified_pos_tags 长度:', currentDocument.value.simplified_pos_tags?.length || 0)
  console.log('posTagging 设置:', readerSettings.value.posTagging)
  console.log('enableMainContent 设置:', readerSettings.value.enableMainContent)
  
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
})

// 生命周期 - 组件卸载时移除监听器
onUnmounted(() => {
  // 记录当前页面的停留时间
  ['original', 'simplified'].forEach(type => {
    const currentPage = paginationState[type].currentPage
    const timestamp = pageVisitTime.value[type].timestamp
    
    if (currentPage > 0 && timestamp > 0) {
      const stayDuration = Math.floor((Date.now() - timestamp) / 1000)
      
      // 如果停留时间超过最小阅读时间，更新阅读进度
      if (stayDuration >= MIN_READING_TIME) {
        updateReadingProgress(type, currentPage, stayDuration)
      }
    }
  })
  
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

/* 纯文本内容样式（未处理文档） */
.plain-text-content {
  width: 100%;
  min-height: 300px;
  padding: 1rem;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
  overflow-wrap: break-word;
}

/* 空内容样式 */
.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #999;
  text-align: center;
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
  background-color: rgba(82, 134, 105, 0.25); /* 浅绿色背景，区分意群 */
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
  border: none !important;        /* 移除所有边框，避免与阴影动画重叠 */
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
  font-family: Arial, sans-serif !important;
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
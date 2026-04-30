<template>
  <div class="app-container">
    <header class="app-header">
      <nav class="app-nav">
        <router-link to="/editor">编辑器</router-link>
        <router-link to="/reader">阅读器</router-link>
        <router-link to="/history">阅读历史</router-link>
        <router-link to="/documents">文档记录</router-link>
        <router-link to="/settings">设置</router-link>
      </nav>
      <div class="user-actions">
        <template v-if="!isLoggedIn">
          <el-button type="primary" size="small" @click="goToLogin">登录</el-button>
          <el-button size="small" @click="goToRegister">注册</el-button>
        </template>
        <template v-else>
          <el-dropdown @command="handleCommand">
            <span class="user-name">
              {{ user?.username || '用户' }}
              <el-icon><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>
    </header>
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from './stores/appStore'
import { ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const isLoggedIn = computed(() => appStore.isLoggedIn)
const user = computed(() => appStore.user)

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

const handleCommand = (command) => {
  if (command === 'settings') {
    router.push('/settings')
  } else if (command === 'logout') {
    appStore.logout()
    router.push('/editor')
  }
}

// 快捷键处理函数
const handleKeydown = (event) => {
  // 检查是否按下了Ctrl键
  const isCtrlPressed = event.ctrlKey || event.metaKey // metaKey for Mac
  
  // 检查是否按下了功能键
  if (event.key === 'F1') {
    event.preventDefault()
    // 打开帮助文档（这里可以跳转到帮助页面或显示帮助对话框）
    window.open('https://github.com/your-repo/docs/用户手册.md', '_blank')
    return
  }
  
  if (event.key === 'F2') {
    event.preventDefault()
    // 打开设置面板
    router.push('/settings')
    return
  }
  
  if (event.key === 'F3') {
    event.preventDefault()
    // 切换全屏阅读模式
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      document.documentElement.requestFullscreen()
    }
    return
  }
  
  // 检查Ctrl组合键
  if (isCtrlPressed) {
    switch (event.key) {
      case 's':
        event.preventDefault()
        // 保存当前文档
        // 这里需要根据当前页面调用相应的保存方法
        if (router.currentRoute.value.path === '/editor') {
          // 触发编辑器的保存功能
          const editorComponent = document.querySelector('.editor-container')
          if (editorComponent) {
            // 这里可以通过事件或状态管理来触发保存
            console.log('保存当前文档')
          }
        }
        break
        
      case 'o':
        event.preventDefault()
        // 打开文件
        if (router.currentRoute.value.path === '/editor') {
          // 触发文件上传
          const fileInput = document.querySelector('input[type="file"]')
          if (fileInput) {
            fileInput.click()
          }
        }
        break
        
      case 'e':
        event.preventDefault()
        // 导出文件
        if (router.currentRoute.value.path === '/editor') {
          // 触发导出功能
          const exportButton = document.querySelector('.el-button:has(.el-icon-download)')
          if (exportButton) {
            exportButton.click()
          }
        }
        break
        
      case 'p':
        event.preventDefault()
        // 开始/暂停朗读
        if (router.currentRoute.value.path === '/reader') {
          // 触发朗读功能
          const speechButton = document.querySelector('.speech-controls .el-button:has(.el-icon-mics)')
          if (speechButton) {
            speechButton.click()
          }
        }
        break
        
      case 'q':
        event.preventDefault()
        // 停止朗读
        if (router.currentRoute.value.path === '/reader') {
          // 触发停止朗读功能
          const stopButton = document.querySelector('.speech-controls .el-button:has(.el-icon-close)')
          if (stopButton) {
            stopButton.click()
          }
        }
        break
        
      case '=':
      case '+':
        event.preventDefault()
        // 增大字体
        appStore.updateReaderSettings({
          fontSize: Math.min(appStore.readerSettings.fontSize + 2, 36)
        })
        break
        
      case '-':
        event.preventDefault()
        // 减小字体
        appStore.updateReaderSettings({
          fontSize: Math.max(appStore.readerSettings.fontSize - 2, 12)
        })
        break
        
      case '0':
        event.preventDefault()
        // 恢复默认字体大小
        appStore.updateReaderSettings({
          fontSize: 16
        })
        break
    }
  }
}

// 生命周期
onMounted(() => {
  // 添加键盘事件监听器
  window.addEventListener('keydown', handleKeydown)
  
  // 检查登录状态
  const token = localStorage.getItem('token')
  if (token && !appStore.user) {
    // 如果有token但没有用户信息，尝试获取用户信息
    import('./utils/api').then(({ getUserInfo }) => {
      getUserInfo().then(userInfo => {
        appStore.setUser(userInfo)
      }).catch(() => {
        // 获取用户信息失败，清除token
        localStorage.removeItem('token')
      })
    })
  }
})

onUnmounted(() => {
  // 移除键盘事件监听器
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #40826D;
  color: white;
  padding: 0.75rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-nav {
  display: flex;
  gap: 0.5rem;
}

.app-nav a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
  font-size: 14px;
}

.app-nav a:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.app-nav a.router-link-active {
  background-color: rgba(255, 255, 255, 0.3);
  font-weight: bold;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.user-name {
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 14px;
}

.app-main {
  flex: 1;
  padding: 2rem;
  background-color: #f5f7fa;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

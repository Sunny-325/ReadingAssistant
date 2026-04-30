import { createApp } from 'vue'
import { createPinia } from 'pinia'
// 导入Element Plus，包含所有组件
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 导入自定义主题
import './styles/theme.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册Element Plus组件
app.use(ElementPlus)

app.use(createPinia())
app.use(router)

app.mount('#app')

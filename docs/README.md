# 中文文本阅读障碍辅助工具

## 项目简介

中文文本阅读障碍辅助工具是一个基于Python 3.12 + FastAPI + Vue 3 + Element Plus开发的Web应用，专为中文阅读障碍用户设计，集成了Qwen大模型（通过阿里云通义千问API调用），提供12项核心阅读辅助功能。

## 技术栈

### 后端
- Python 3.12
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Requests 2.32.4
- MySQL 8.0
- jieba (用于中文分词和词性标注)
- dashscope 1.17.0 (阿里云通义千问SDK)
- pyttsx3 2.90 (文本转语音)

### 前端
- Vue 3.4.21+
- Vue Router 4.3.0+
- Pinia 2.1.7+
- Axios 1.6.7+
- Element Plus 2.5.3+
- Vite 5.2.0+

## 核心功能

1. **文本输入/上传/导出**
   - 支持PDF/Word文件解析
   - 自动文本编码处理
   - 多种格式导出

2. **意群划分**
   - 基于规则和模型的混合方法
   - 可配置的分块大小
   - 支持重新划分

3. **阅读模式+语音朗读**
   - 实时语音合成（使用pyttsx3）
   - 文本高亮同步
   - 播放控制（播放/暂停/停止）

4. **蒙版功能**
   - 可配置行数（1-10行）
   - 透明度调节
   - 键盘和鼠标滚动支持

5. **间距调节**
   - 字间距/行间距/词间距
   - 实时预览效果

6. **词性高亮**
   - 基于jieba的词性标注
   - 可配置颜色方案
   - 多词性同时高亮

7. **配色方案**
   - 护眼模式（绿字浅绿底）
   - 高对比度模式（白字黑底）
   - 自定义配色

8. **词性字号设置**
   - 特定词性字号调整
   - 保持整体排版

9. **排版模式**
   - 整齐排版
   - 错落排版（轻微上下错位）

10. **主次内容区分**
    - 基于规则和模型的内容筛选
    - 透明度区分主次

11. **文本简化**
    - 复杂文本自动简化
    - 支持轻度/中度/深度三级简化
    - 简化后的文本在独立面板显示

12. **词语释义查询**
    - 用户查询式词语释义
    - 详细的词语解释和例句
    - 结合上下文提供准确解释

## 项目结构

```
├── backend/                 # 后端代码
│   ├── app/                 # 应用核心代码
│   │   ├── core/            # 核心模块
│   │   │   ├── config.py    # 配置文件
│   │   │   ├── database.py  # 数据库配置
│   │   │   ├── model_manager.py  # 模型管理器基类
│   │   │   ├── qwen_model_manager.py  # Qwen模型管理器
│   │   │   ├── ollama_model_manager.py  # Ollama模型管理器（备用）
│   │   │   └── task_manager.py  # 任务管理器
│   │   ├── models/          # 数据库模型
│   │   ├── routes/          # API路由
│   │   ├── schemas/         # Pydantic模型
│   │   ├── services/        # 业务逻辑服务
│   │   │   ├── text_processor.py  # 文本处理服务
│   │   │   ├── file_service.py  # 文件服务
│   │   │   ├── voice_service.py  # 语音服务（pyttsx3）
│   │   │   └── auth_service.py  # 认证服务
│   │   └── main.py          # 主应用入口
│   ├── requirements.txt     # 依赖列表
│   ├── setup_environment.py # 环境设置脚本
│   └── .env                 # 环境变量配置
├── frontend/                # 前端代码
│   ├── src/                 # 源代码
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # 状态管理
│   │   ├── utils/           # 工具函数
│   │   ├── views/           # 视图组件
│   │   │   ├── EditorView.vue  # 文本编辑器
│   │   │   ├── ReaderView.vue  # 阅读器
│   │   │   ├── HomeView.vue    # 首页
│   │   │   ├── SettingsView.vue # 设置页面
│   │   │   └── HistoryView.vue  # 历史记录
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── index.html           # HTML模板
│   ├── package.json         # 前端依赖
│   └── vite.config.js       # Vite配置
├── docs/                    # 项目文档
│   ├── README.md            # 项目说明
│   ├── 技术文档.md           # 技术文档
│   ├── 开发文档.md           # 开发文档
│   └── 用户手册.md           # 用户手册
├── venv/                    # 虚拟环境
└── test_*.py                # 测试文件
```

## 环境搭建

### 后端环境

1. 安装Python 3.12
2. 安装依赖：
   ```bash
   cd backend
   pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 配置阿里云通义千问API：
   - 前往阿里云官网申请API Key：https://www.aliyun.com/product/dashscope
   - 在`backend/app/core/config.py`中配置`QWEN_API_KEY`

4. 启动后端服务：
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 前端环境

1. 安装Node.js 16+
2. 安装依赖：
   ```bash
   cd frontend
   npm install
   ```
3. 启动前端开发服务器：
   ```bash
   npm run dev
   ```

## 数据库配置

1. 安装MySQL 8.0
2. 创建数据库：
   ```sql
   CREATE DATABASE reading_assistant DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. 配置`backend/app/core/config.py`中的数据库连接信息
4. 启动应用时会自动创建数据库表

## 模型配置

项目通过阿里云通义千问API调用Qwen大模型，无需本地部署模型：

1. **API Key配置**：在`backend/app/core/config.py`中设置`QWEN_API_KEY`
2. **模型名称**：`qwen-long`（长文本模型，适合文本处理任务）
3. **API调用**：通过dashscope SDK进行调用，支持流式生成

## API文档

启动后端服务后，可以通过以下地址访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 部署

### 开发环境

1. 后端：
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. 前端：
   ```bash
   cd frontend
   npm run dev
   ```

### 生产环境

1. 构建前端：
   ```bash
   cd frontend
   npm run build
   ```

2. 使用Gunicorn部署后端：
   ```bash
   cd backend
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
   ```

## 使用说明

1. 启动后端服务：http://localhost:8000
2. 启动前端服务：http://localhost:5173
3. 访问前端应用：http://localhost:5173
4. 通过API接口访问功能（可选）：
   - 处理文本：POST /api/text/process
   - 获取词语释义：GET /api/text/definition/{word}
   - 上传文件：POST /api/files/upload
   - 导出文件：GET /api/files/export/{file_id}
5. 查看API文档：http://localhost:8000/docs

## 功能详解

### 1. 文本输入/上传/导出
- 支持直接输入文本
- 支持上传PDF、Word、TXT文件
- 支持导出为TXT、PDF格式

### 2. 意群划分
- 基于规则和Qwen大模型的混合方法
- 可配置的分块大小（轻度/中度/高度划分）
- 支持重新划分

### 3. 阅读模式+语音朗读
- 实时语音合成（使用pyttsx3）
- 文本高亮同步
- 播放控制（播放/暂停/停止）
- 支持调整语速和音量

### 4. 蒙版功能
- 可配置显示行数（1-10行）
- 可调节蒙版透明度
- 支持键盘和鼠标滚动

### 5. 间距调节
- 字间距调整
- 行间距调整
- 词间距调整
- 实时预览效果

### 6. 词性高亮
- 基于jieba的词性标注
- 可配置不同词性的颜色
- 支持多词性同时高亮

### 7. 配色方案
- 多种预设配色方案
- 护眼模式
- 高对比度模式
- 自定义配色

### 8. 词性字号设置
- 可单独调整特定词性的字号
- 保持整体排版美观

### 9. 排版模式
- 整齐排版
- 错落排版（轻微上下错位，适合阅读障碍用户）

### 10. 主次内容区分
- 基于规则和Qwen大模型的内容筛选
- 通过透明度区分主次内容

### 11. 文本简化
- 复杂文本自动简化（基于规则和Qwen大模型）
- 支持轻度/中度/深度三级简化
- 简化后的文本在独立面板显示，方便对比阅读

### 12. 词语释义查询
- 用户查询式词语释义
- 详细的词语解释和例句
- 结合上下文提供准确解释

## 开发说明

### 代码规范
- 后端使用Black进行代码格式化
- 前端使用ESLint + Prettier进行代码检查和格式化

### 日志记录
- 所有重要操作都有日志记录
- 日志文件位于backend/app.log

### 错误处理
- 完善的错误处理机制
- 详细的错误信息返回

## 测试

### 单元测试
```bash
cd backend
pytest tests/unit/ -v
```

### 集成测试
```bash
cd backend
pytest tests/integration/ -v
```

## 性能优化

1. **API调用优化**：
   - 实现API调用缓存，减少重复请求
   - 优化API调用参数，提高生成质量和速度
   - 实现请求重试机制，提高API调用可靠性

2. **文本处理优化**：
   - 实现缓存机制，提高重复文本处理速度
   - 长文本分块处理，每块1200字
   - 基于规则的快速处理，对短文本（<1000字）进行快速处理
   - 混合处理策略：短文本使用规则方法，长文本使用模型方法

3. **设备适配**：
   - 无需GPU，仅需CPU运行
   - 跨平台支持（Windows/macOS/Linux）

## 安全注意事项

1. 生产环境中应修改SECRET_KEY
2. 配置正确的CORS_ORIGINS
3. 定期更新依赖包
4. 配置合适的文件大小限制
5. 实现用户权限控制
6. 保护API Key，避免泄露

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系：
- 项目负责人：[你的名字]
- 邮箱：[你的邮箱]
- 项目地址：[GitHub链接]

## 更新日志

### v1.0.0 (2026-02-XX)
- 初始版本发布
- 实现12项核心阅读辅助功能
- 集成Qwen大模型（通过阿里云通义千问API）
- 支持文本处理、文件上传/导出、词语释义等功能
- 实现缓存机制和长文本分块处理
- 使用pyttsx3实现文本转语音功能

### v1.0.1 (2026-02-XX)
- 优化文本处理速度
- 改进词语释义功能，改为用户查询式
- 完善模型交互逻辑
- 更新项目文档

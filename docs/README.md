# 中文文本阅读障碍辅助工具

## 项目简介

中文文本阅读障碍辅助工具是一个基于 Python 3.12 + FastAPI + Vue 3 + Element Plus 开发的 Web 应用，专为中文阅读障碍用户设计。项目集成了阿里云通义千问大模型（Qwen），通过 API 调用实现智能文本处理，提供 12 项核心阅读辅助功能，帮助阅读障碍用户更轻松地理解和阅读中文文本。

## 技术栈

### 后端
- **Python 3.12** - 主要编程语言
- **FastAPI 0.104.1** - 现代、高性能的 Web 框架
- **Uvicorn 0.24.0** - ASGI 服务器
- **MySQL 8.0** - 关系型数据库
- **SQLAlchemy 2.0.23** - ORM 框架
- **Redis 5.0.0** - 分布式缓存（任务状态管理、限流）
- **jieba 0.42.1** - 中文分词和词性标注
- **dashscope 1.17.0** - 阿里云通义千问 SDK
- **pyttsx3 2.90** - 文本转语音
- **PyPDF2 3.0.1** - PDF 文件解析
- **python-docx 1.1.0** - Word 文档解析
- **EbookLib 0.20** - EPUB 文件处理

### 前端
- **Vue 3.5.13** - 渐进式 JavaScript 框架
- **Vue Router 4.4.5** - 路由管理
- **Pinia 2.3.0** - 状态管理
- **Element Plus 2.8.6** - UI 组件库
- **Axios 1.7.9** - HTTP 客户端
- **Vite 6.0.5** - 构建工具

## 核心功能

### 1. 文本输入/上传/导出
- 支持直接输入文本
- 支持上传 TXT、PDF、Word、EPUB 文件
- 支持导出为 TXT、PDF 格式
- 自动文本编码检测和处理

### 2. 意群划分
- 基于规则和 Qwen 大模型的混合方法
- 可配置的分块大小（轻度/中度/高度划分）
- 支持重新划分
- 短文本（<1000字）使用规则快速处理
- 长文本使用模型进行语义分析

### 3. 文本简化
- 复杂文本自动简化
- 支持轻度/中度/深度三级简化
- 基于规则和模型的混合方法
- 简化后的文本在独立面板显示，方便对比阅读

### 4. 主次内容区分
- 基于规则和模型的内容筛选
- 通过透明度区分主次内容
- 短文本使用基于位置的规则
- 长文本使用模型分析内容重要性

### 5. 词性高亮
- 基于 jieba 的词性标注
- 可配置不同词性的颜色
- 支持多词性同时高亮
- 用户可选择要标注的词性（默认：名词、动词、形容词）

### 6. 阅读模式 + 语音朗读
- 实时语音合成（使用 pyttsx3）
- 文本高亮同步
- 播放控制（播放/暂停/停止）
- 支持调整语速和音量
- 双面板独立语音控制

### 7. 蒙版功能
- 可配置显示行数（1-10行）
- 可调节蒙版透明度
- 支持键盘和鼠标滚动
- 全屏模式下自动启用

### 8. 间距调节
- 字间距调整
- 行间距调整
- 词间距调整
- 实时预览效果

### 9. 配色方案
- 多种预设配色方案
- 护眼模式（绿字浅绿底）
- 高对比度模式（白字黑底）
- 自定义配色

### 10. 词性字号设置
- 可单独调整特定词性的字号
- 保持整体排版美观
- 不同词性使用不同字号显示

### 11. 排版模式
- 整齐排版
- 错落排版（轻微上下错位，适合阅读障碍用户）

### 12. 词语释义查询
- 用户查询式词语释义
- 详细的词语解释和例句
- 结合上下文提供准确解释
- 通过 Qwen 大模型生成释义

## 项目结构

```
├── backend/                 # 后端代码
│   ├── app/                 # 应用核心代码
│   │   ├── core/            # 核心模块
│   │   │   ├── config.py    # 配置文件
│   │   │   ├── database.py  # 数据库配置
│   │   │   ├── model_manager.py  # 模型管理器基类
│   │   │   ├── qwen_model_manager.py  # Qwen模型管理器
│   │   │   ├── model_params_manager.py  # 模型参数管理器
│   │   │   └── task_manager.py  # 任务管理器
│   │   ├── models/          # 数据库模型
│   │   │   ├── user.py      # 用户模型
│   │   │   ├── document.py  # 文档模型
│   │   │   ├── reading_history.py  # 阅读历史模型
│   │   │   ├── setting.py   # 设置模型
│   │   │   ├── task.py      # 任务模型
│   │   │   └── text_chunk.py  # 文本分块模型
│   │   ├── routes/          # API路由
│   │   │   ├── api.py       # 主要API路由
│   │   │   └── auth.py      # 认证路由
│   │   ├── schemas/         # Pydantic模型
│   │   ├── services/        # 业务逻辑服务
│   │   │   ├── text_processor.py  # 文本处理服务
│   │   │   ├── file_service.py  # 文件服务
│   │   │   ├── voice_service.py  # 语音服务
│   │   │   └── auth_service.py  # 认证服务
│   │   └── main.py          # 主应用入口
│   ├── requirements.txt     # 依赖列表
│   └── docker-compose.yml   # Docker配置
├── frontend/                # 前端代码
│   ├── src/                 # 源代码
│   │   ├── router/          # 路由配置
│   │   │   └── index.js     # 路由定义
│   │   ├── stores/          # 状态管理
│   │   │   └── appStore.js  # 应用状态
│   │   ├── utils/           # 工具函数
│   │   │   ├── api.js       # API调用
│   │   │   └── pyttsx3.js   # 语音工具
│   │   ├── views/           # 视图组件
│   │   │   ├── EditorView.vue  # 文本编辑器
│   │   │   ├── ReaderView.vue  # 阅读器
│   │   │   ├── SettingsView.vue # 设置页面
│   │   │   ├── HistoryView.vue  # 历史记录
│   │   │   ├── DocumentView.vue # 文档管理
│   │   │   ├── LoginView.vue    # 登录页面
│   │   │   └── RegisterView.vue # 注册页面
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── index.html           # HTML模板
│   ├── package.json         # 前端依赖
│   └── vite.config.js       # Vite配置
├── docs/                    # 项目文档
│   ├── README.md            # 项目说明
│   ├── 技术文档.md           # 技术文档
│   └── 用户手册.md           # 用户手册
└── venv/                    # 虚拟环境
```

## 环境搭建

### 后端环境

1. **安装 Python 3.12**
   ```bash
   # 确保Python版本为3.12+
   python --version
   ```

2. **安装依赖**
   ```bash
   cd backend
   pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **配置阿里云通义千问 API**
   - 前往阿里云官网申请 API Key：https://www.aliyun.com/product/dashscope
   - 在 `backend/app/core/config.py` 中配置 `QWEN_API_KEY`

4. **启动后端服务**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 前端环境

1. **安装 Node.js 16+**
   ```bash
   # 确保Node.js版本为16+
   node --version
   ```

2. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

3. **启动前端开发服务器**
   ```bash
   npm run dev
   ```

## 数据库配置

1. **安装 MySQL 8.0**

2. **创建数据库**
   ```sql
   CREATE DATABASE reading_assistant DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **配置数据库连接**
   在 `backend/app/core/config.py` 中配置：
   ```python
   DB_HOST: str = "localhost"
   DB_PORT: int = 3306
   DB_NAME: str = "reading_assistant"
   DB_USER: str = "root"
   DB_PASSWORD: str = "your_password"
   ```

4. **自动创建表**
   启动应用时会自动创建数据库表

## 模型配置

项目通过阿里云通义千问 API 调用 Qwen 大模型，无需本地部署模型：

1. **API Key 配置**：在 `backend/app/core/config.py` 中设置 `QWEN_API_KEY`
2. **模型名称**：`qwen-long`（长文本模型，适合文本处理任务）
3. **API 调用**：通过 dashscope SDK 进行调用

### 模型参数配置

```python
# 通用参数
MODEL_MAX_TOKENS: int = 8192        # 最大生成长度
MODEL_RETRY_ATTEMPTS: int = 3       # 重试次数
MODEL_TEMPERATURE: float = 0.2      # 默认温度参数
MODEL_TOP_P: float = 0.9            # 默认top_p参数

# 意群划分参数
SEGMENT_TEMPERATURE: float = 0.1    # 较低温度，确保划分结果稳定
SEGMENT_TOP_P: float = 0.85         # 较严格的输出控制
SEGMENT_MAX_TOKENS: int = 4096      # 意群划分输出相对简短

# 文本简化参数
SIMPLIFY_TEMPERATURE: float = 0.2   # 适中温度，保持简化后的自然度
SIMPLIFY_TOP_P: float = 0.9         # 适当的输出多样性
SIMPLIFY_MAX_TOKENS: int = 8192     # 可能需要较长的简化输出

# 主次内容区分参数
ANALYZE_TEMPERATURE: float = 0.15   # 较低温度，确保分析结果可靠
ANALYZE_TOP_P: float = 0.85         # 较严格的输出控制
ANALYZE_MAX_TOKENS: int = 4096      # 分析结果相对简短
```

## API 文档

启动后端服务后，可以通过以下地址访问 API 文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 接口

#### 认证相关
- `POST /api/auth/token` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 退出登录
- `PUT /api/auth/update-username` - 修改用户名
- `PUT /api/auth/update-password` - 修改密码
- `DELETE /api/auth/account` - 账号注销（永久删除）

#### 文本处理
- `POST /api/text/process` - 处理文本（短文本）
- `POST /api/text/process/async` - 异步处理文本（长文本）
- `GET /api/text/process/async/{task_id}` - 获取异步任务状态
- `GET /api/text/definition/{word}` - 获取词语释义
- `POST /api/text/simplify` - 简化文本
- `POST /api/text/chunk` - 意群划分

#### 用户设置
- `GET /api/user/settings` - 获取用户设置
- `POST /api/user/settings` - 保存用户设置

#### 文档管理
- `GET /api/user/documents` - 获取用户文档列表
- `POST /api/user/documents` - 创建新文档
- `PUT /api/user/documents/{document_id}` - 更新文档
- `DELETE /api/user/documents/{document_id}` - 删除文档

#### 阅读历史
- `GET /api/user/history` - 获取用户阅读历史
- `POST /api/user/history` - 添加阅读历史

#### 语音服务
- `POST /api/tts/pyttsx3` - 文本转语音（pyttsx3）

#### 文件管理
- `POST /api/files/upload` - 上传文件
- `GET /api/files/export/{file_id}` - 导出文件

#### 系统相关
- `GET /api/system/health` - 健康检查

## 部署

### 开发环境

1. **后端**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **前端**
   ```bash
   cd frontend
   npm run dev
   ```

### 生产环境

1. **构建前端**
   ```bash
   cd frontend
   npm run build
   ```

2. **使用 Gunicorn 部署后端**
   ```bash
   cd backend
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
   ```

3. **配置 Nginx**
   - 配置 Nginx 反向代理 API 请求
   - 将前端 dist 目录部署到 Nginx

## 使用说明

1. 启动后端服务：http://localhost:8000
2. 启动前端服务：http://localhost:3000
3. 访问前端应用：http://localhost:3000
4. 注册/登录账号
5. 在编辑器中输入或上传文本
6. 选择处理选项（意群划分、文本简化、主次内容区分）
7. 点击"处理文本"按钮
8. 在阅读器中查看处理结果
9. 使用各种阅读辅助功能（语音朗读、蒙版、词性高亮等）

## 开发说明

### 代码规范

#### 后端（Python）
- 遵循 PEP 8 编码规范
- 使用 4 个空格缩进
- 每行代码长度不超过 100 个字符
- 函数和方法使用 snake_case 命名
- 类使用 CamelCase 命名
- 使用 Google 风格的文档字符串

#### 前端（JavaScript/Vue）
- 遵循 Vue 3 Composition API
- 组件命名使用 CamelCase
- 使用单文件组件（.vue）
- 脚本部分使用 setup 语法糖
- 模板部分使用 2 个空格缩进
- CSS 使用 scoped 属性

### 日志记录
- 所有重要操作都有日志记录
- 日志文件位于 backend/app.log

### 错误处理
- 完善的错误处理机制
- 详细的错误信息返回
- HTTP 异常使用 HTTPException

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

### 1. API 调用优化
- 实现请求重试机制（最大重试次数：3次）
- 优化 API 调用参数，提高生成质量和速度
- 监控 API 调用状态，确保服务可用性

### 2. 文本处理优化
- 每次请求直接调用模型，确保结果的新鲜度和多样性
- 长文本分块处理，每块 1500 字
- 基于规则的快速处理，对短文本（<1000字）进行快速处理
- 混合处理策略：短文本使用规则方法，长文本使用模型方法

### 3. 并发处理优化
- 使用 FastAPI 的异步处理能力
- 实现线程池处理 CPU 密集型任务
- 最大工作线程数：4

### 4. Redis 缓存优化
- **任务状态查询优先从 Redis 获取**，避免频繁数据库访问
- **Redis 不可用时自动降级到数据库查询**
- **支持实时进度更新，提高响应速度**
- 分布式限流：每分钟最多创建 5 个任务

### 5. 前端优化
- 使用虚拟列表渲染长文本
- 实现懒加载，只渲染可见区域的内容
- 优化 CSS 选择器，提高样式渲染速度

## 安全注意事项

1. **数据安全**
   - 密码使用 bcrypt 加密存储
   - 敏感数据传输使用 HTTPS 协议
   - 数据库连接使用环境变量配置

2. **API 安全**
   - 使用 JWT 进行身份认证
   - 实现请求速率限制
   - 验证请求参数

3. **模型安全**
   - 保护 API Key，避免泄露
   - 监控 API 调用情况
   - 定期更新 SDK 版本

4. **部署安全**
   - 定期更新系统和依赖包
   - 配置防火墙，限制访问端口
   - 监控系统日志

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
- 实现 12 项核心阅读辅助功能
- 集成 Qwen 大模型（通过阿里云通义千问 API）
- 支持文本处理、文件上传/导出、词语释义等功能
- 实现每次请求直接调用模型，确保结果的新鲜度和多样性
- 使用 pyttsx3 实现文本转语音功能
- 支持 EPUB 文件格式

### v1.0.1 (2026-02-XX)
- 优化文本处理速度
- 改进词语释义功能，改为用户查询式
- 完善模型交互逻辑
- 更新项目文档
- 增加模型参数配置

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主应用文件
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import engine, Base

from .routes import api, auth

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 配置静态文件服务
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

# 使用 lifespan event handlers 替代 on_event
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    try:
        from .core.model_manager import get_model_manager
        # 加载模型管理器
        model_manager = get_model_manager()
        # 检查模型状态
        status = model_manager.get_model_status()
        
        # 只在模型状态不健康时记录日志
        if status.get("status") != "healthy":
            logger.warning(f"模型加载状态: {status.get('status')}")
            logger.warning(f"模型错误: {status.get('error', '未知错误')}")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("应用正在关闭...")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="中文文本阅读障碍辅助工具API",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由，统一放在 /api 前缀下
app.include_router(api.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)

# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {"status": "healthy"}

# 挂载静态资源到 /assets 路径
if os.path.exists(frontend_dist_path):
    # 挂载静态资源目录
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    logger.info(f"静态资源服务已配置，路径: {os.path.join(frontend_dist_path, 'assets')}")
else:
    logger.warning(f"前端构建目录不存在: {frontend_dist_path}")

# 捕获所有路径的路由，返回index.html（让前端路由接管）
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """
    捕获所有未匹配的路径，返回index.html
    这样前端路由就能正常工作
    """
    if os.path.exists(frontend_dist_path):
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
    return {"detail": "Not Found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=False
    )

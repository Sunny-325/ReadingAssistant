#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置类"""
    # 应用配置
    APP_NAME: str = "中文文本阅读障碍辅助工具"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "your-secret-key-here"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_DESCRIPTION: str = "为中文文本阅读障碍者提供的辅助工具"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "mysql://root:123456@localhost:3306/reading_assistant"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "reading_assistant"
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_CHARSET: str = "utf8mb4"
    
    # JWT配置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 模型配置
    OLLAMA_API_URL: str = "http://localhost:11434"
    OLLAMA_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "qwen2.5:3b-instruct-q4_K_M"
    AUTO_LOAD_MODEL: bool = False
    USE_CLOUD_MODEL: bool = False
    CLOUD_MODEL_API_URL: str = "http://localhost:11434"
    

    # Qwen模型配置
    QWEN_API_KEY: str = "sk-61b8d06e980541709d02453c6e27eb33"
    QWEN_MODEL_NAME: str = "qwen-long"
    USE_QWEN_MODEL: bool = True
    
    # 文件配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_TEXT_LENGTH: int = 10000
    SUPPORTED_FILE_TYPES: List[str] = [".txt", ".pdf", ".doc", ".docx"]
    
    # 文本处理配置
    CHUNK_SIZE: int = 500
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    
    # 性能配置
    BATCH_SIZE: int = 16
    MAX_WORKERS: int = 4
    
    # 第三方服务配置
    GTTS_LANG: str = "zh-cn"
    
    # 缓存配置
    CACHE_EXPIRE: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# 创建全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

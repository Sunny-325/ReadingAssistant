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
    
    # ========== 长文本处理配置 ==========
    # 分块配置
    CHUNK_SIZE: int = 1500  # 每个文本块的字符数（考虑中文语义完整性）
    CHUNKS_PER_GROUP: int = 4  # 每组处理的块数，配合MAX_WORKERS=4实现并行处理
    
    # 最大文本长度（支持长文档）
    MAX_TEXT_LENGTH: int = 500000  # 增加到50万字符，支持更长文档（如EPUB电子书）
    
    # ========== 通用模型参数配置 ==========
    MODEL_MAX_TOKENS: int = 8192  # 默认生成长度上限
    MODEL_RETRY_ATTEMPTS: int = 3  # 重试次数
    MODEL_TEMPERATURE: float = 0.2  # 默认温度参数
    MODEL_TOP_P: float = 0.9  # 默认top_p参数
    
    # ========== 功能-specific参数配置 ==========
    
    # 意群划分（Segmentation）- 需要较高的准确性和一致性
    SEGMENT_TEMPERATURE: float = 0.1  # 较低温度，确保划分结果稳定一致
    SEGMENT_TOP_P: float = 0.85  # 较严格的输出控制
    SEGMENT_MAX_TOKENS: int = 4096  # 意群划分输出相对简短
    
    # 文本简化（Simplification）- 需要平衡准确性和可读性
    SIMPLIFY_TEMPERATURE: float = 0.2  # 适中温度，保持简化后的自然度
    SIMPLIFY_TOP_P: float = 0.9  # 适当的输出多样性
    SIMPLIFY_MAX_TOKENS: int = 8192  # 可能需要较长的简化输出
    
    # 主次内容区分（Main/Secondary Content）- 需要较高的判断准确性
    ANALYZE_TEMPERATURE: float = 0.15  # 较低温度，确保分析结果可靠
    ANALYZE_TOP_P: float = 0.85  # 较严格的输出控制
    ANALYZE_MAX_TOKENS: int = 4096  # 分析结果相对简短
    
    # ====================================
    
    # 性能配置
    PROCESSING_BATCH_SIZE: int = 16  # 批量处理大小
    MAX_WORKERS: int = 4  # 最大工作线程数（根据CPU核心数调整）
    
    # ====================================
    
    # 文件配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 增加到50MB，支持更大的EPUB文件
    SUPPORTED_FILE_TYPES: List[str] = [".txt", ".pdf", ".doc", ".docx", ".epub"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    
    # 第三方服务配置
    GTTS_LANG: str = "zh-cn"
    
    # 缓存配置
    CACHE_EXPIRE: int = 3600
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        case_sensitive = True
        extra = "allow"


# 创建全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

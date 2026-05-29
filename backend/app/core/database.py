#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# 注册pymysql作为MySQL的驱动
pymysql.install_as_MySQLdb()

from ..core.config import settings

# 创建数据库引擎
# 增加连接池配置，提高并发处理能力
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,              # 增加到20
    max_overflow=50,           # 增加到50
    pool_timeout=30,           # 连接超时时间
    pool_recycle=3600,         # 连接回收时间（1小时）
    echo=False                 # 关闭SQL日志输出，提高性能
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

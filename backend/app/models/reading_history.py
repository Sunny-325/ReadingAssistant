#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阅读历史模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import LONGTEXT, JSON

from ..core.database import Base


class ReadingHistory(Base):
    """
    阅读历史模型
    存储完整的阅读会话数据，包括处理后的文本和意群划分
    """
    __tablename__ = "reading_histories"
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    
    # 原始内容快照（文件上传后经过数据清洗）
    content_snapshot = Column(LONGTEXT, nullable=False)
    
    # 简化后的内容（通俗易懂版）
    simplified_content_snapshot = Column(LONGTEXT, nullable=True)
    
    # 意群划分数据
    segments_snapshot = Column(JSON, nullable=True)
    simplified_segments_snapshot = Column(JSON, nullable=True)
    
    # 词性标注数据
    pos_tags_snapshot = Column(JSON, nullable=True)
    simplified_pos_tags_snapshot = Column(JSON, nullable=True)
    
    # 主次内容区分数据
    primary_content_snapshot = Column(JSON, nullable=True)
    secondary_content_snapshot = Column(JSON, nullable=True)
    
    # 处理设置快照
    processing_settings_snapshot = Column(JSON, nullable=True)
    
    # 阅读状态
    reading_progress = Column(Float, nullable=False, default=0.0)
    current_position = Column(Integer, nullable=False, default=0)
    reading_time = Column(Integer, nullable=False, default=0)
    last_read_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

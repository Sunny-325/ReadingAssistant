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
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    
    # 原始内容快照
    content_snapshot = Column(LONGTEXT, nullable=False)
    
    # 预处理后的内容（去噪、规范化等）
    processed_content_snapshot = Column(LONGTEXT, nullable=True)
    
    # 简化后的内容（通俗易懂版）
    simplified_content_snapshot = Column(LONGTEXT, nullable=True)
    
    # 意群划分数据
    segments_snapshot = Column(JSON, nullable=True)  # 原始文本意群划分
    simplified_segments_snapshot = Column(JSON, nullable=True)  # 简化文本意群划分
    
    # 词性标注数据
    pos_tags_snapshot = Column(JSON, nullable=True)  # 原始文本词性标注
    simplified_pos_tags_snapshot = Column(JSON, nullable=True)  # 简化文本词性标注
    
    # 主次内容区分数据
    primary_content_snapshot = Column(JSON, nullable=True)  # 主要内容标记
    secondary_content_snapshot = Column(JSON, nullable=True)  # 次要内容标记
    
    # 处理设置快照
    processing_settings_snapshot = Column(JSON, nullable=True)
    
    # 阅读状态
    reading_progress = Column(Float, nullable=False, default=0.0)
    current_position = Column(Integer, nullable=False, default=0)
    reading_time = Column(Integer, nullable=False, default=0)
    last_read_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

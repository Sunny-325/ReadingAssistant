#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class FileType(str, enum.Enum):
    txt = "txt"
    pdf = "pdf"
    doc = "doc"
    docx = "docx"
    epub = "epub"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    paused = "paused"


class Document(Base):
    """
    文档模型
    只存储原始文档内容和基本信息，不存储处理后的数据
    """
    __tablename__ = "documents"
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, nullable=True, default=None)
    title = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.pending)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 分组处理相关字段
    processing_task_id = Column(Integer, nullable=True)
    total_groups = Column(Integer, nullable=True, default=0)
    completed_groups = Column(Integer, nullable=True, default=0)

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


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Document(Base):
    """
    文档模型
    只存储原始文档内容和基本信息，不存储处理后的数据
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, nullable=True, default=None)  # 文档分组ID
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=True)
    file_type = Column(Enum(FileType), nullable=True)
    file_size = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)  # 原始文本内容
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.pending)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

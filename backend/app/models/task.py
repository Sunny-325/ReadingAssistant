#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
    @classmethod
    def _missing_(cls, value):
        # 处理大小写不匹配的情况
        for member in cls:
            if member.value == value.lower():
                return member
        return super()._missing_(value)


class Task(Base):
    """
    任务模型
    """
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    task_type = Column(String(50), nullable=False)
    status = Column(Enum('pending', 'processing', 'completed', 'failed'), nullable=False, default='pending')
    input_data = Column(Text, nullable=True)  # JSON格式存储
    result_data = Column(LONGTEXT, nullable=True)  # JSON格式存储
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

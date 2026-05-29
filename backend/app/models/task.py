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
    PAUSED = "paused"

class Task(Base):
    """
    任务模型
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, nullable=True)
    group_index = Column(Integer, nullable=False, default=0)
    total_groups = Column(Integer, nullable=False, default=1)
    total_chunks = Column(Integer, nullable=False, default=0)
    completed_chunks = Column(Integer, nullable=False, default=0)
    is_continuable = Column(Boolean, nullable=False, default=False)
    last_chunk_index = Column(Integer, nullable=False, default=-1)
    task_type = Column(String(50), nullable=False)
    status = Column(Enum(TaskStatus, values_callable=lambda obj: [e.value for e in obj]), 
                    nullable=False, default=TaskStatus.PENDING)
    input_data = Column(Text, nullable=True)
    result_data = Column(LONGTEXT, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

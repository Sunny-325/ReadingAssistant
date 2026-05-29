#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本块模型
用于长文本分组处理，每组4块
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.mysql import LONGTEXT, JSON
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class ChunkStatus(str, enum.Enum):
    """文本块状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TextChunk(Base):
    """
    文本块模型
    存储长文本分割后的每个块及其处理状态
    """
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    group_index = Column(Integer, nullable=False, default=0)
    chunk_index = Column(Integer, nullable=False)
    content = Column(LONGTEXT, nullable=False)
    result = Column(JSON, nullable=True)
    status = Column(Enum(ChunkStatus, values_callable=lambda obj: [e.value for e in obj]), 
                    nullable=False, default=ChunkStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

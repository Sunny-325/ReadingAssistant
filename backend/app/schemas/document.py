#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档Pydantic模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class DocumentBase(BaseModel):
    """
    文档基础模型
    """
    title: str
    content: str


class DocumentCreate(DocumentBase):
    """
    创建文档模型
    """
    pass


class DocumentUpdate(BaseModel):
    """
    更新文档模型
    """
    title: Optional[str] = None
    content: Optional[str] = None
    processed_content: Optional[str] = None
    simplified_content: Optional[str] = None


class Document(DocumentBase):
    """
    文档响应模型
    """
    id: int
    user_id: int
    processed_content: Optional[str] = None
    simplified_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TextProcessRequest(BaseModel):
    """
    文本处理请求模型
    """
    text: str
    options: Optional[Dict[str, Any]] = None


class TextSimplifyRequest(BaseModel):
    """
    文本简化请求模型
    """
    text: str
    level: int = 1  # 简化级别，1-3


class TextChunkRequest(BaseModel):
    """
    意群划分请求模型
    """
    text: str
    chunk_size: int = 5  # 意群大小

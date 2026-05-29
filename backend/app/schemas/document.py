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
    更新文档请求模型
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


class DocumentCreateRequest(BaseModel):
    """
    创建文档请求模型
    """
    title: str = "未命名文档"
    content: str
    file_type: Optional[str] = None
    group_id: Optional[int] = None


class DocumentUpdateRequest(BaseModel):
    """
    更新文档请求模型
    """
    title: Optional[str] = None
    content: Optional[str] = None
    group_id: Optional[int] = None


class DocumentResponse(BaseModel):
    """
    文档响应模型
    """
    id: int
    user_id: int
    group_id: Optional[int] = None
    title: str
    file_type: Optional[str] = None
    content: str
    status: str
    error_message: Optional[str] = None
    processing_task_id: Optional[int] = None
    total_groups: int = 0
    completed_groups: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TextProcessOptions(BaseModel):
    """
    文本处理选项模型
    """
    enableSegmentation: bool = False
    enableSimplify: bool = False
    enablePosTagging: bool = False
    enableMainContent: bool = False
    simplifyLevel: int = 1


class TextProcessRequest(BaseModel):
    """
    文本处理请求模型
    """
    text: str
    options: Optional[Dict[str, Any]] = None
    document_id: Optional[int] = None


class TextProcessResponse(BaseModel):
    """
    文本处理响应模型
    """
    processed_text: str
    simplified_content: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None
    simplified_segments: Optional[List[Dict[str, Any]]] = None
    pos_tags: Optional[List[Dict[str, Any]]] = None
    simplified_pos_tags: Optional[List[Dict[str, Any]]] = None
    document_id: Optional[int] = None

    class Config:
        from_attributes = True


class TextProcessAsyncRequest(BaseModel):
    """
    异步文本处理请求模型
    """
    text: str
    options: Optional[Dict[str, Any]] = None
    document_id: Optional[int] = None


class TextProcessAsyncResponse(BaseModel):
    """
    异步文本处理响应模型
    """
    task_id: int
    document_id: int
    message: str = "任务创建成功"

    class Config:
        from_attributes = True


class TextProcessGroupedRequest(BaseModel):
    """
    分组文本处理请求模型
    """
    text: str
    options: Optional[Dict[str, Any]] = None
    document_id: Optional[int] = None


class TextProcessGroupedResponse(BaseModel):
    """
    分组文本处理响应模型
    """
    task_id: int
    document_id: int
    total_groups: int
    total_chunks: int
    message: str = "任务创建成功"

    class Config:
        from_attributes = True


class TaskProgressResponse(BaseModel):
    """
    任务进度响应模型
    """
    task_id: int
    group_id: Optional[int] = None
    group_index: int
    total_groups: int
    completed_chunks: int
    total_chunks: int
    status: str
    is_continuable: bool

    class Config:
        from_attributes = True


class ContinueTaskResponse(BaseModel):
    """
    继续任务响应模型
    """
    task_id: int
    group_id: Optional[int] = None
    group_index: int
    has_more: bool
    message: str = "继续处理当前组"

    class Config:
        from_attributes = True


class DocumentProcessingStatusResponse(BaseModel):
    """
    文档处理状态响应模型
    """
    document_id: int
    title: str
    status: str
    processing_task_id: Optional[int] = None
    completed_groups: int = 0
    total_groups: int = 0
    progress_percent: float = 0.0
    task_status: Optional[str] = None
    is_continuable: bool = False

    class Config:
        from_attributes = True


class TextSimplifyRequest(BaseModel):
    """
    文本简化请求模型
    """
    text: str
    level: int = 1


class TextSimplifyResponse(BaseModel):
    """
    文本简化响应模型
    """
    simplified_text: str
    original_length: int
    simplified_length: int

    class Config:
        from_attributes = True


class TextChunkRequest(BaseModel):
    """
    意群划分请求模型
    """
    text: str
    chunk_size: int = 5


class TextChunkResponse(BaseModel):
    """
    意群划分响应模型
    """
    chunks: List[str]
    chunk_count: int

    class Config:
        from_attributes = True

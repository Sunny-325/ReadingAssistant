#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阅读历史Pydantic模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReadingHistoryBase(BaseModel):
    """
    阅读历史基础模型
    """
    document_id: int
    last_read_position: int = 0
    read_time: int = 0  # 阅读时间（秒）


class ReadingHistoryCreate(ReadingHistoryBase):
    """
    创建阅读历史模型
    """
    pass


class ReadingHistoryUpdate(BaseModel):
    """
    更新阅读历史模型
    """
    last_read_position: Optional[int] = None
    read_time: Optional[int] = None


class ReadingHistory(ReadingHistoryBase):
    """
    阅读历史响应模型
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

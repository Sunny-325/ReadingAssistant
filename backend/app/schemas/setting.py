#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置Pydantic模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SettingBase(BaseModel):
    """
    设置基础模型
    """
    setting_key: str
    setting_value: str


class SettingCreate(SettingBase):
    """
    创建设置模型
    """
    pass


class SettingUpdate(BaseModel):
    """
    更新设置模型
    """
    setting_value: str


class Setting(SettingBase):
    """
    设置响应模型
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

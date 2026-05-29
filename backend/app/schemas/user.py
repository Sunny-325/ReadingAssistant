#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户Pydantic模型
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """
    用户基础模型
    """
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """
    创建用户模型
    """
    password: str


class UserUpdate(BaseModel):
    """
    更新用户模型
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class User(UserBase):
    """
    用户响应模型
    """
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """
    令牌模型
    """
    access_token: str
    token_type: str
    message: Optional[str] = None


class TokenData(BaseModel):
    """
    令牌数据模型
    """
    username: Optional[str] = None

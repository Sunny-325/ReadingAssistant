#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件服务
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException

from ..core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FileService:
    """
    文件服务类
    """
    
    def __init__(self):
        """
        初始化文件服务
        """
        # 确保上传目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async def save_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        保存上传的文件
        
        :param file: 上传的文件
        :return: 文件信息
        """
        try:
            # 检查文件大小
            file.file.seek(0, 2)  # 移动到文件末尾
            file_size = file.file.tell()  # 获取文件大小
            file.file.seek(0)  # 重置文件指针
            
            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"文件大小超过限制 {settings.MAX_FILE_SIZE / 1024 / 1024}MB")
            
            # 生成文件名
            file_name = f"{os.urandom(8).hex()}_{file.filename}"
            file_path = os.path.join(settings.UPLOAD_DIR, file_name)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return {
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "content_type": file.content_type
            }
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        读取文件内容
        
        :param file_path: 文件路径
        :return: 文件内容
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            # 根据文件扩展名选择读取方式
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.txt':
                # 读取文本文件
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif ext == '.pdf':
                # 读取PDF文件
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                except Exception as e:
                    logger.error(f"读取PDF文件失败: {e}")
                    return None
            elif ext in ['.doc', '.docx']:
                # 读取Word文件
                try:
                    from docx import Document
                    doc = Document(file_path)
                    content = ""
                    for para in doc.paragraphs:
                        content += para.text + "\n"
                except Exception as e:
                    logger.error(f"读取Word文件失败: {e}")
                    return None
            else:
                # 尝试作为文本文件读取
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"读取文件失败: {e}")
                    return None
            
            return content
            
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        :param file_path: 文件路径
        :return: 是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

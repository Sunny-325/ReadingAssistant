#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器
"""
import json
from typing import Dict, Any, Optional
from sqlalchemy.sql import func
from ..models.task import Task
from ..core.database import SessionLocal
from ..services.text_processor import TextProcessor
from ..core.model_manager import get_model_manager


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.model_manager = get_model_manager()
        self.text_processor = TextProcessor(self.model_manager)
    
    def create_task(self, user_id: int, task_type: str, input_data: Dict[str, Any], document_id: Optional[int] = None) -> Task:
        """
        创建任务
        
        :param user_id: 用户ID
        :param task_type: 任务类型
        :param input_data: 输入数据
        :param document_id: 文档ID
        :return: 任务对象
        """
        db = SessionLocal()
        try:
            task = Task(
                user_id=user_id,
                document_id=document_id,
                task_type=task_type,
                input_data=json.dumps(input_data)
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        finally:
            db.close()
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """
        获取任务
        
        :param task_id: 任务ID
        :return: 任务对象
        """
        db = SessionLocal()
        try:
            return db.query(Task).filter(Task.id == task_id).first()
        finally:
            db.close()
    
    async def process_text_task(self, task_id: int):
        """
        处理文本处理任务
        处理结果不再保存到 Document 表，而是在创建阅读历史时保存
        
        :param task_id: 任务ID
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            # 更新任务状态为处理中
            task.status = 'processing'
            
            # 更新关联文档状态为处理中
            if task.document_id:
                from ..models.document import Document, DocumentStatus
                document = db.query(Document).filter(Document.id == task.document_id).first()
                if document:
                    document.status = DocumentStatus.processing
            
            db.commit()

            # 解析输入数据
            input_data = json.loads(task.input_data)
            text = input_data.get('text')
            options = input_data.get('options', {})

            # 处理文本
            try:
                result = await self.text_processor.process_text(text, options)
                
                # 更新任务状态为完成
                task.status = 'completed'
                
                # 存储完整的处理结果到 task.result_data
                # 这些数据将在创建阅读历史时转移到 ReadingHistory 表
                task.result_data = json.dumps({
                    "processed_text": result.get("processed_text", ""),
                    "simplifiedContent": result.get("simplifiedContent", ""),  
                    "segments": result.get("segments", []),
                    "simplified_segments": result.get("simplified_segments", []),
                    "pos_tags": result.get("pos_tags", []),
                    "simplified_pos_tags": result.get("simplified_pos_tags", []),
                    "primary_content": result.get("primary_content", []),
                    "secondary_content": result.get("secondary_content", []),
                    "processing_settings": options
                })

                # 更新关联的文档记录 - 只保存基本状态信息
                if task.document_id:
                    from ..models.document import Document, DocumentStatus
                    document = db.query(Document).filter(Document.id == task.document_id).first()
                    if document:
                        # 更新文档标题
                        if document.title == "处理中的文档":
                            document.title = "未命名文档"
                        
                        # 只更新处理状态，不存储处理后的数据
                        document.status = DocumentStatus.completed
                        document.processed_at = func.now()
                        
            except Exception as e:
                # 更新任务状态为失败
                task.status = 'failed'
                task.error_message = str(e)

                # 更新关联的文档状态为失败
                if task.document_id:
                    from ..models.document import Document, DocumentStatus
                    document = db.query(Document).filter(Document.id == task.document_id).first()
                    if document:
                        document.status = DocumentStatus.failed
                        document.error_message = str(e)

            db.commit()
        finally:
            db.close()


# 创建全局任务管理器实例
task_manager = TaskManager()

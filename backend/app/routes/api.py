#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由
"""

import logging
import json
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.model_manager import get_model_manager
from app.core.config import settings
from app.services.text_processor import TextProcessor
from app.services.file_service import FileService
from app.services.voice_service import VoiceService
from app.services.text_cleaner import TextCleaner
from app.schemas.document import (
    TextProcessRequest,
    TextProcessAsyncRequest, TextProcessAsyncResponse,
    TextProcessGroupedRequest, TextProcessGroupedResponse,
    DocumentCreateRequest, DocumentUpdateRequest, DocumentResponse,
    TextSimplifyRequest,
    TextChunkRequest
)
from app.models.user import User
from app.models.setting import Setting
from app.models.document import Document, DocumentStatus
from app.models.reading_history import ReadingHistory
from app.models.task import Task, TaskStatus
from app.models.text_chunk import TextChunk
from app.core.task_manager import task_manager
from app.routes.auth import get_current_user
from fastapi import UploadFile, File

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def _create_or_update_reading_history(
    db,
    user_id: int,
    document_id: int,
    content: str,
    result: Dict[str, Any],
    options: Dict[str, Any] = None
):
    """
    创建或更新阅读历史记录
    如果同一文档已存在阅读历史，则更新为最新处理结果
    """
    try:
        import json
        
        # 获取文档标题
        document_title = "未命名文档"
        if document_id:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document_title = document.title
        
        # 检查是否已存在同一文档的阅读历史
        existing_history = db.query(ReadingHistory).filter(
            ReadingHistory.user_id == user_id,
            ReadingHistory.document_id == document_id
        ).first()
        
        # 从 segments 中提取主次内容（文本处理器在 segments 中添加了 is_primary 属性）
        segments = result.get("segments", [])
        primary_content = [seg for seg in segments if seg.get("is_primary") is True]
        secondary_content = [seg for seg in segments if seg.get("is_primary") is False]
        
        logger.info(f"主次内容提取: 原意群数={len(segments)}, primary_count={len(primary_content)}, secondary_count={len(secondary_content)}")
        
        simplified_segments = result.get("simplified_segments", [])
        
        if existing_history:
            # 更新现有的阅读历史记录
            existing_history.title = document_title
            existing_history.content_snapshot = content
            existing_history.simplified_content_snapshot = result.get("simplifiedContent")
            existing_history.segments_snapshot = segments
            existing_history.simplified_segments_snapshot = simplified_segments
            existing_history.pos_tags_snapshot = result.get("pos_tags")
            existing_history.simplified_pos_tags_snapshot = result.get("simplified_pos_tags")
            existing_history.primary_content_snapshot = primary_content
            existing_history.secondary_content_snapshot = secondary_content
            # 将处理设置转换为JSON字符串存储
            existing_history.processing_settings_snapshot = json.dumps(options) if options else None
            existing_history.last_read_at = func.now()
            db.commit()
            logger.info(f"更新阅读历史记录: document_id={document_id}, title={document_title}")
        else:
            # 创建新的阅读历史记录
            new_history = ReadingHistory(
                user_id=user_id,
                document_id=document_id,
                title=document_title,
                content_snapshot=content,
                simplified_content_snapshot=result.get("simplifiedContent"),
                segments_snapshot=segments,
                simplified_segments_snapshot=simplified_segments,
                pos_tags_snapshot=result.get("pos_tags"),
                simplified_pos_tags_snapshot=result.get("simplified_pos_tags"),
                primary_content_snapshot=primary_content,
                secondary_content_snapshot=secondary_content,
                # 将处理设置转换为JSON字符串存储
                processing_settings_snapshot=json.dumps(options) if options else None,
                reading_progress=0.0,
                current_position=0,
                reading_time=0,
                last_read_at=func.now()
            )
            db.add(new_history)
            db.commit()
            logger.info(f"创建阅读历史记录: document_id={document_id}, title={document_title}")
            
    except Exception as e:
        logger.error(f"创建或更新阅读历史失败: {e}")
        # 不抛出异常，避免影响文本处理流程

# 创建路由
router = APIRouter()


@router.post("/text/process", response_model=Dict[str, Any])
async def process_text(
    request: TextProcessRequest,
    model_manager=Depends(get_model_manager),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    处理文本，应用各种阅读辅助功能（适用于短文本）
    """
    created_document_id = None

    try:
        # 获取请求数据
        text = request.text
        options = request.options or {}
        document_id = request.document_id
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        if len(text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(status_code=413, detail=f"文本长度超过限制（最大{settings.MAX_TEXT_LENGTH}字符）")
        
        # 解析document_id
        try:
            document_id = int(document_id) if document_id else None
        except (ValueError, TypeError):
            document_id = None
        
        # 创建或更新文档记录（无论文本长短都创建）
        if not document_id:
            # 创建新文档
            new_document = Document(
                user_id=current_user.id,
                title="未命名文档",
                content=text,
                status=DocumentStatus.processing
            )
            db.add(new_document)
            db.commit()
            db.refresh(new_document)
            document_id = new_document.id
            created_document_id = document_id
            logger.info(f"为文本处理创建文档记录: {document_id}")
        else:
            # 验证document_id是否有效
            existing_document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.id
            ).first()
            if existing_document:
                # 更新现有文档内容
                existing_document.content = text
                existing_document.status = DocumentStatus.processing
                db.commit()
                logger.info(f"更新现有文档记录: {document_id}")
            else:
                # document_id无效，创建新文档
                new_document = Document(
                    user_id=current_user.id,
                    title="未命名文档",
                    content=text,
                    status=DocumentStatus.processing
                )
                db.add(new_document)
                db.commit()
                db.refresh(new_document)
                document_id = new_document.id
                created_document_id = document_id
                logger.info(f"document_id无效，创建新文档记录: {document_id}")
        
        # 对于长文本，建议使用异步处理（但仍返回document_id）
        if len(text) > 1000:
            # 更新文档状态为等待异步处理
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = DocumentStatus.pending
                db.commit()
            
            return {
                "message": "文本较长，建议使用异步处理",
                "data": {
                    "suggest_async": True
                },
                "document_id": document_id
            }
        
        # 创建文本处理器
        text_processor = TextProcessor(model_manager)
        
        # 处理文本
        result = await text_processor.process_text(text, options)
        
        # 更新文档状态为已完成
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.completed
            db.commit()
        
        # 自动创建或更新阅读历史记录
        await _create_or_update_reading_history(
            db=db,
            user_id=current_user.id,
            document_id=document_id,
            content=text,
            result=result,
            options=options
        )
        
        logger.info(f"文本处理成功，长度: {len(text)}，文档ID: {document_id}")
        return {
            "message": "文本处理成功",
            "data": result,
            "document_id": document_id
        }
        
    except HTTPException:
        # 如果创建了新文档但处理失败，标记为失败状态
        if created_document_id:
            document = db.query(Document).filter(Document.id == created_document_id).first()
            if document:
                document.status = DocumentStatus.failed
                db.commit()
        raise
    except Exception as e:
        # 如果创建了新文档但处理失败，标记为失败状态
        if created_document_id:
            document = db.query(Document).filter(Document.id == created_document_id).first()
            if document:
                document.status = DocumentStatus.failed
                db.commit()
        
        logger.error(f"文本处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")


@router.post("/text/process/async", response_model=TextProcessAsyncResponse)
async def process_text_async(
    request: TextProcessAsyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    异步处理文本，应用各种阅读辅助功能（适用于长文本）
    """
    try:
        # 获取请求数据
        text = request.text
        options = request.options or {}
        document_id = request.document_id

        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="文本内容不能为空")

        if len(text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(status_code=413, detail=f"文本长度超过限制（最大{settings.MAX_TEXT_LENGTH}字符）")

        # 如果没有提供 document_id 或 document_id 无效，先创建文档记录
        # 尝试将 document_id 转换为整数
        try:
            document_id = int(document_id) if document_id else None
        except (ValueError, TypeError):
            document_id = None
            
        if not document_id:
            new_document = Document(
                user_id=current_user.id,
                title="处理中的文档",
                content=text,
                status=DocumentStatus.processing
            )
            db.add(new_document)
            db.commit()
            db.refresh(new_document)
            document_id = new_document.id
            logger.info(f"为文本处理创建文档记录: {document_id}")
        else:
            # 验证document_id是否有效
            existing_document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.id
            ).first()
            if existing_document:
                # 使用现有的文档记录
                logger.info(f"使用现有文档记录: {document_id}")
            else:
                # 如果document_id无效，创建新的文档记录
                new_document = Document(
                    user_id=current_user.id,
                    title="处理中的文档",
                    content=text,
                    status=DocumentStatus.processing
                )
                db.add(new_document)
                db.commit()
                db.refresh(new_document)
                document_id = new_document.id
                logger.info(f"document_id无效，为文本处理创建新文档记录: {document_id}")

        # 创建任务
        task, error = task_manager.create_task(
            user_id=current_user.id,
            task_type="text_processing",
            input_data={
                "text": text,
                "options": options
            },
            document_id=document_id
        )

        if not task:
            raise HTTPException(status_code=429, detail=error)

        # 异步处理任务
        asyncio.create_task(task_manager.process_text_task(task.id))

        logger.info(f"创建文本处理任务: {task.id}, 长度: {len(text)}, 文档ID: {document_id}")
        return TextProcessAsyncResponse(
            task_id=task.id,
            document_id=document_id,
            message="任务创建成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建文本处理任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建文本处理任务失败: {str(e)}")


@router.get("/text/process/async/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: int
):
    """
    获取异步任务状态
    """
    try:
        # 获取任务
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 构建响应
        response = {
            "message": "获取任务状态成功",
            "data": {
                "task_id": task.id,
                "status": task.status,
                "created_at": task.created_at
            }
        }
        
        # 如果任务完成，返回结果
        if task.status == 'completed' and task.result_data:
            response["data"]["result"] = json.loads(task.result_data)
        
        # 如果任务失败，返回错误信息
        elif task.status == 'failed' and task.error_message:
            response["data"]["error"] = task.error_message
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.post("/text/process/grouped", response_model=TextProcessGroupedResponse)
async def process_text_grouped(
    request: TextProcessGroupedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分组处理长文本（每4块为一组）
    第一组完成后跳转阅读界面，之后询问用户是否继续
    """
    try:
        text = request.text
        options = request.options or {}
        document_id = request.document_id

        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="文本内容不能为空")

        if len(text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(status_code=413, detail=f"文本长度超过限制（最大{settings.MAX_TEXT_LENGTH}字符）")

        try:
            document_id = int(document_id) if document_id else None
        except (ValueError, TypeError):
            document_id = None

        if not document_id:
            new_document = Document(
                user_id=current_user.id,
                title="处理中的文档",
                content=text,
                status=DocumentStatus.processing
            )
            db.add(new_document)
            db.commit()
            db.refresh(new_document)
            document_id = new_document.id
        else:
            existing_document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.id
            ).first()
            if existing_document:
                existing_document.content = text
                existing_document.status = DocumentStatus.processing
                db.commit()
            else:
                new_document = Document(
                    user_id=current_user.id,
                    title="处理中的文档",
                    content=text,
                    status=DocumentStatus.processing
                )
                db.add(new_document)
                db.commit()
                db.refresh(new_document)
                document_id = new_document.id

        task, error = task_manager.create_task(
            user_id=current_user.id,
            task_type="text_processing_grouped",
            input_data={"text": text, "options": options},
            document_id=document_id
        )

        if not task:
            raise HTTPException(status_code=429, detail=error)

        # 更新文档的任务ID和进度信息
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_task_id = task.id
            document.completed_groups = 0
            document.total_groups = task.total_groups
            db.commit()

        asyncio.create_task(task_manager.process_text_grouped(task.id))

        logger.info(f"创建分组文本处理任务: {task.id}, 长度: {len(text)}, 文档ID: {document_id}")
        return TextProcessGroupedResponse(
            task_id=task.id,
            document_id=document_id,
            total_groups=task.total_groups,
            total_chunks=task.total_chunks,
            message="任务创建成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分组任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建分组任务失败: {str(e)}")


@router.get("/text/process/grouped/progress/{task_id}", response_model=Dict[str, Any])
async def get_grouped_task_progress(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取分组任务进度"""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        progress = task_manager.get_task_progress(task_id)
        return {
            "message": "获取进度成功",
            "data": progress
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分组任务进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")


@router.post("/text/process/grouped/{task_id}/continue", response_model=Dict[str, Any])
async def continue_grouped_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """继续处理：如果当前组未完成则恢复，否则创建下一组"""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        if task.status not in ['paused', 'completed']:
            raise HTTPException(status_code=400, detail="任务状态不支持继续处理")

        # 检查当前组是否已完成
        is_current_group_completed = task.completed_chunks >= task.total_chunks
        
        if task.status == 'paused' and not is_current_group_completed:
            # 当前组未完成，恢复当前任务继续处理
            resumed_task = task_manager.resume_task(task_id)
            if not resumed_task:
                raise HTTPException(status_code=500, detail="恢复任务失败")

            # 更新文档状态为处理中
            document = db.query(Document).filter(Document.id == task.document_id).first()
            if document:
                document.status = DocumentStatus.processing
                document.processing_task_id = task_id
                # 先提交数据库
                db.commit()
            # 更新Redis中的任务状态为processing
            task_manager._update_task_status_redis(task_id, TaskStatus.PROCESSING.value, {
                "group_index": task.group_index,
                "total_groups": task.total_groups,
                "completed_chunks": task.completed_chunks,
                "total_chunks": task.total_chunks
             })

             # 最后启动异步任务
            asyncio.create_task(task_manager.process_text_grouped(task_id))

            return {
                "message": "继续处理当前组",
                "data": {
                    "task_id": task_id,
                    "group_id": task.group_id,
                    "group_index": task.group_index,
                    "has_more": True
                }
            }
        else:
            # 当前组已完成，创建下一组任务
            next_task = task_manager.create_next_group_task(task_id)
            if not next_task:
                return {
                    "message": "没有更多组需要处理",
                    "data": {"has_more": False}
                }

            # 更新文档的处理任务ID为新任务ID，并更新状态为处理中
            document = db.query(Document).filter(Document.id == next_task.document_id).first()
            if document:
                document.status = DocumentStatus.processing
                document.processing_task_id = next_task.id  # 关键：更新为新任务ID
                # 先提交数据库
                db.commit()
                # 更新Redis中新任务的状态
            task_manager._update_task_status_redis(next_task.id, TaskStatus.PROCESSING.value, {
                "group_index": next_task.group_index,
                "total_groups": next_task.total_groups,
                "completed_chunks": 0,
                "total_chunks": next_task.total_chunks
            })

            # 最后启动异步任务
            asyncio.create_task(task_manager.process_text_grouped(next_task.id))

            return {
                "message": "继续处理下一组",
                "data": {
                    "task_id": next_task.id,
                    "group_id": next_task.group_id,
                    "group_index": next_task.group_index,
                    "has_more": True
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"继续处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"继续处理失败: {str(e)}")


@router.get("/text/process/unfinished", response_model=Dict[str, Any])
async def get_unfinished_tasks(
    current_user: User = Depends(get_current_user)
):
    """获取用户未完成的任务列表"""
    try:
        unfinished = task_manager.get_unfinished_groups(current_user.id)
        return {
            "message": "获取未完成任务成功",
            "data": unfinished
        }

    except Exception as e:
        logger.error(f"获取未完成任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取未完成任务失败: {str(e)}")


@router.post("/text/process/{task_id}/pause", response_model=Dict[str, Any])
async def pause_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """中断/暂停任务"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权操作此任务")

        success = task_manager.pause_task(task_id)
        if success:
            return {
                "message": "任务已暂停",
                "data": {"task_id": task_id, "status": "paused"}
            }
        else:
            raise HTTPException(status_code=500, detail="暂停任务失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")


@router.get("/text/process/{task_id}/progress", response_model=Dict[str, Any])
async def get_task_progress(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务处理进度"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权查看此任务")

        progress = task_manager.get_task_progress(task_id)
        return {
            "message": "获取进度成功",
            "data": progress
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务进度失败: {str(e)}")


@router.get("/documents/{document_id}/processing-status", response_model=Dict[str, Any])
async def get_document_processing_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文档的处理状态和进度"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        result = {
            "document_id": document.id,
            "title": document.title,
            "status": document.status.value,
            "processing_task_id": document.processing_task_id,
            "completed_groups": document.completed_groups or 0,
            "total_groups": document.total_groups or 0,
            "progress_percent": 0,
            "task_status": None,
            "is_continuable": False
        }

        # 计算进度百分比
        if document.total_groups and document.total_groups > 0:
            result["progress_percent"] = round(
                (document.completed_groups or 0) / document.total_groups * 100
            )

        # 如果有任务ID，优先从Redis获取任务状态
        if document.processing_task_id:
            # 优先从Redis获取实时任务状态
            progress = task_manager.get_task_progress(document.processing_task_id)
            if progress:
                result["task_status"] = progress.get("status")
                # 更新进度信息
                if "group_index" in progress and "total_groups" in progress:
                    result["completed_groups"] = progress["group_index"] + 1 if progress.get("group_index") is not None else result["completed_groups"]
                    result["total_groups"] = progress["total_groups"] or result["total_groups"]
                    if result["total_groups"] > 0:
                        result["progress_percent"] = round(
                            result["completed_groups"] / result["total_groups"] * 100
                        )
            else:
                # Redis不可用时，从数据库获取
                task = db.query(Task).filter(Task.id == document.processing_task_id).first()
                if task:
                    result["task_status"] = task.status.value
                    result["is_continuable"] = task.is_continuable
        else:
            # 如果没有当前任务ID，尝试查找最近的历史任务
            recent_task = db.query(Task).filter(
                Task.document_id == document_id,
                Task.user_id == current_user.id
            ).order_by(Task.created_at.desc()).first()
            if recent_task:
                result["processing_task_id"] = recent_task.id
                result["task_status"] = recent_task.status.value
                result["is_continuable"] = True

        return {
            "message": "获取处理状态成功",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档处理状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档处理状态失败: {str(e)}")


@router.get("/text/definition/{word}", response_model=Dict[str, Any])
async def get_word_definition(
    word: str,
    context: str = Query("", description="词语上下文"),
    model_manager=Depends(get_model_manager)
):
    """
    获取词语释义
    """
    try:
        # 验证词语
        if not word or len(word.strip()) == 0:
            raise HTTPException(status_code=400, detail="词语不能为空")
        
        if len(word) > 50:
            raise HTTPException(status_code=400, detail="词语长度超过限制")
        
        # 创建文本处理器
        text_processor = TextProcessor(model_manager)
        
        # 获取词语释义
        definition = text_processor.get_word_definition(word, context)
        
        logger.info(f"获取词语释义成功: {word}")
        return {
            "message": "获取词语释义成功",
            "data": definition
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取词语释义失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取词语释义失败: {str(e)}")


@router.post("/text/simplify", response_model=Dict[str, Any])
async def simplify_text(
    request: TextSimplifyRequest,
    model_manager=Depends(get_model_manager)
):
    """
    简化文本
    """
    try:
        # 验证文本长度
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        if len(request.text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(status_code=413, detail=f"文本长度超过限制（最大{settings.MAX_TEXT_LENGTH}字符）")
        
        # 创建文本处理器
        text_processor = TextProcessor(model_manager)
        
        # 简化文本，传递简化级别
        simplified_text = text_processor.simplify_text(request.text, request.level)
        
        logger.info(f"文本简化成功，原文长度: {len(request.text)}, 简化后长度: {len(simplified_text)}")
        return {
            "message": "文本简化成功",
            "data": {
                "original_text": request.text,
                "simplifiedContent": simplified_text
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本简化失败: {e}")
        raise HTTPException(status_code=500, detail=f"文本简化失败: {str(e)}")


@router.post("/text/chunk", response_model=Dict[str, Any])
async def chunk_text(
    request: TextChunkRequest,
    model_manager=Depends(get_model_manager)
):
    """
    意群划分
    """
    try:
        # 验证文本长度
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        if len(request.text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(status_code=413, detail=f"文本长度超过限制（最大{settings.MAX_TEXT_LENGTH}字符）")
        
        # 验证分块大小
        if request.chunk_size < 1 or request.chunk_size > 20:
            raise HTTPException(status_code=400, detail="分块大小必须在1-20之间")
        
        # 创建文本处理器
        text_processor = TextProcessor(model_manager)
        
        # 划分意群
        segments = text_processor.segment_text(request.text, {"chunk_size": request.chunk_size})
        
        logger.info(f"意群划分成功，生成 {len(segments)} 个意群")
        return {
            "message": "意群划分成功",
            "data": {
                "text": request.text,
                "segments": segments
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"意群划分失败: {e}")
        raise HTTPException(status_code=500, detail=f"意群划分失败: {str(e)}")


# 用户设置API
@router.get("/user/settings", response_model=Dict[str, Any])
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户设置
    """
    try:
        # 从数据库获取用户设置
        settings = db.query(Setting).filter(Setting.user_id == current_user.id).all()
        
        # 转换为字典
        settings_dict = {}
        for setting in settings:
            try:
                settings_dict[setting.setting_key] = json.loads(setting.setting_value)
            except json.JSONDecodeError:
                settings_dict[setting.setting_key] = setting.setting_value
        
        return settings_dict
        
    except Exception as e:
        logger.error(f"获取用户设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户设置失败: {str(e)}")


@router.post("/user/settings", response_model=Dict[str, Any])
async def save_user_settings(
    settings: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    保存用户设置
    """
    try:
        # 清除用户现有的设置
        db.query(Setting).filter(Setting.user_id == current_user.id).delete()
        
        # 保存新的设置
        for key, value in settings.items():
            setting = Setting(
                user_id=current_user.id,
                setting_key=key,
                setting_value=json.dumps(value)
            )
            db.add(setting)
        
        db.commit()
        return {"message": "设置保存成功"}
        
    except Exception as e:
        logger.error(f"保存用户设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存用户设置失败: {str(e)}")


# 文档API
@router.get("/user/documents", response_model=List[Dict[str, Any]])
async def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户文档列表
    """
    try:
        documents = db.query(Document).filter(Document.user_id == current_user.id).all()
        
        # 转换为字典列表
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "title": doc.title,
                "group_id": doc.group_id,
                "file_type": doc.file_type.value if doc.file_type else None,
                "content": doc.content,
                "status": doc.status.value,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "completed_groups": doc.completed_groups or 0,
                "total_groups": doc.total_groups or 0
            })
        
        return document_list
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@router.post("/user/documents", response_model=DocumentResponse)
async def create_user_document(
    request: DocumentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新文档
    """
    try:
        # 处理 file_type，确保使用正确的小写形式
        file_type = request.file_type
        if file_type:
            file_type = file_type.lower()

        # 清洗文本内容
        text_cleaner = TextCleaner()
        raw_content = request.content
        cleaned_content = text_cleaner.clean_text(raw_content)

        new_document = Document(
            user_id=current_user.id,
            group_id=request.group_id,
            title=request.title,
            file_type=file_type,
            content=cleaned_content,
            status=DocumentStatus.pending
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        logger.info(f"用户 {current_user.username} 保存文档成功: {new_document.id}")

        return DocumentResponse(
            id=new_document.id,
            user_id=new_document.user_id,
            group_id=new_document.group_id,
            title=new_document.title,
            file_type=new_document.file_type.value if new_document.file_type else None,
            content=new_document.content,
            status=new_document.status.value,
            created_at=new_document.created_at,
            updated_at=new_document.updated_at
        )
        
    except Exception as e:
        logger.error(f"创建文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建文档失败: {str(e)}")

@router.delete("/user/documents/{document_id}", response_model=Dict[str, Any])
async def delete_user_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除文档
    """
    try:
        # 查找文档
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除关联的阅读历史
        db.query(ReadingHistory).filter(ReadingHistory.document_id == document_id).delete()
        
        # 删除关联的任务和文本块
        tasks = db.query(Task).filter(Task.document_id == document_id).all()
        for task in tasks:
            # 删除任务关联的文本块
            db.query(TextChunk).filter(TextChunk.task_id == task.id).delete()
            # 安全删除任务（如果任务不存在则跳过）
            existing_task = db.query(Task).filter(Task.id == task.id).first()
            if existing_task:
                db.delete(existing_task)
        
        # 删除文档
        db.delete(document)
        db.commit()
        
        logger.info(f"用户 {current_user.username} 删除文档: {document_id}")

        return {"message": "文档删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.put("/user/documents/{document_id}", response_model=DocumentResponse)
async def update_user_document(
    document_id: int,
    request: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新文档
    """
    try:
        # 查找文档
        db_document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not db_document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 更新文档字段 - 只更新基本信息，处理后数据保存在阅读历史中
        if request.title is not None:
            db_document.title = request.title
            # 同步更新关联的阅读历史标题
            db.query(ReadingHistory).filter(
                ReadingHistory.document_id == document_id,
                ReadingHistory.user_id == current_user.id
            ).update({"title": request.title})
        if request.group_id is not None:
            db_document.group_id = request.group_id
        if request.content is not None:
            # 清洗文本内容
            text_cleaner = TextCleaner()
            cleaned_content = text_cleaner.clean_text(request.content)
            db_document.content = cleaned_content

        db.commit()
        db.refresh(db_document)

        logger.info(f"用户 {current_user.username} 更新文档: {document_id}")

        return DocumentResponse(
            id=db_document.id,
            user_id=db_document.user_id,
            group_id=db_document.group_id,
            title=db_document.title,
            file_type=db_document.file_type.value if db_document.file_type else None,
            content=db_document.content,
            status=db_document.status.value,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新文档失败: {str(e)}")


# 阅读历史API
@router.get("/user/history", response_model=List[Dict[str, Any]])
async def get_user_reading_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户阅读历史
    """
    try:
        history = db.query(ReadingHistory).filter(
            ReadingHistory.user_id == current_user.id
        ).order_by(ReadingHistory.last_read_at.desc()).all()
        
        # 转换为字典列表
        history_list = []
        for item in history:
            history_dict = {
                "id": item.id,
                "document_id": item.document_id,
                "title": item.title,
                "content_snapshot": item.content_snapshot,
                "simplified_content_snapshot": item.simplified_content_snapshot,
                "segments_snapshot": item.segments_snapshot,
                "pos_tags_snapshot": item.pos_tags_snapshot,
                "processing_settings_snapshot": item.processing_settings_snapshot,
                "reading_progress": item.reading_progress,
                "current_position": item.current_position,
                "reading_time": item.reading_time,
                "last_read_at": item.last_read_at,
                "created_at": item.created_at
            }
            # 只添加存在的字段
            if hasattr(item, 'simplified_segments_snapshot') and item.simplified_segments_snapshot:
                history_dict["simplified_segments_snapshot"] = item.simplified_segments_snapshot
            if hasattr(item, 'simplified_pos_tags_snapshot') and item.simplified_pos_tags_snapshot:
                history_dict["simplified_pos_tags_snapshot"] = item.simplified_pos_tags_snapshot
            history_list.append(history_dict)
        
        return history_list
        
    except Exception as e:
        logger.error(f"获取阅读历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取阅读历史失败")


# 初始化语音服务
voice_service = VoiceService()


@router.post("/tts/pyttsx3")
async def text_to_speech_pyttsx3(
    text: str = Body(..., description="要转换的文本"),
    rate: int = Body(150, description="语速"),
    volume: float = Body(1.0, description="音量"),
    voice: str = Body(None, description="语音ID")
):
    """
    使用pyttsx3进行文本转语音
    """
    try:
        result = voice_service.text_to_speech(text, rate=rate, volume=volume, voice=voice)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        # 返回音频数据
        return Response(
            content=result["audio_data"],
            media_type="audio/wav"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"pyttsx3 文本转语音失败: {e}")
        raise HTTPException(status_code=500, detail="文本转语音失败")


@router.post("/user/history", response_model=Dict[str, Any])
async def add_user_reading_history(
    history: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加阅读历史
    接收前端传递的处理后数据，保存到 ReadingHistory 表
    """
    try:
        import json
        
        # 验证document_id是否存在
        document_id = history.get("document_id")
        if document_id:
            # 检查document_id是否存在且属于当前用户
            existing_document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.id
            ).first()
            if not existing_document:
                # 如果document_id不存在，设置为None
                document_id = None
        
        # 处理前端传递的数据
        # 前端可能传递字符串格式的JSON，需要解析
        def parse_json_field(field_value):
            if field_value is None:
                return None
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return field_value
            return field_value
        
        new_history = ReadingHistory(
            user_id=current_user.id,
            document_id=document_id,
            title=history.get("title", "未命名历史"),
            content_snapshot=history.get("content", history.get("content_snapshot", "")),
            simplified_content_snapshot=history.get("simplifiedContent", history.get("simplified_content_snapshot")),
            segments_snapshot=parse_json_field(history.get("segments", history.get("segments_snapshot"))),
            simplified_segments_snapshot=parse_json_field(history.get("simplifiedSegments", history.get("simplified_segments_snapshot"))),
            pos_tags_snapshot=parse_json_field(history.get("pos_tags", history.get("pos_tags_snapshot"))),
            simplified_pos_tags_snapshot=parse_json_field(history.get("simplified_pos_tags", history.get("simplified_pos_tags_snapshot"))),
            primary_content_snapshot=parse_json_field(history.get("primary_content", history.get("primary_content_snapshot"))),
            secondary_content_snapshot=parse_json_field(history.get("secondary_content", history.get("secondary_content_snapshot"))),
            processing_settings_snapshot=parse_json_field(history.get("processing_settings_snapshot")),
            reading_progress=history.get("reading_progress", 0.0),
            current_position=history.get("current_position", 0),
            reading_time=history.get("reading_time", 0),
            last_read_at=history.get("last_read_at") or func.now()
        )
        
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        
        return {
            "id": new_history.id,
            "document_id": new_history.document_id,
            "title": new_history.title,
            "content_snapshot": new_history.content_snapshot,
            "simplified_content_snapshot": new_history.simplified_content_snapshot,
            "segments_snapshot": new_history.segments_snapshot,
            "simplified_segments_snapshot": new_history.simplified_segments_snapshot,
            "pos_tags_snapshot": new_history.pos_tags_snapshot,
            "simplified_pos_tags_snapshot": new_history.simplified_pos_tags_snapshot,
            "primary_content_snapshot": new_history.primary_content_snapshot,
            "secondary_content_snapshot": new_history.secondary_content_snapshot,
            "processing_settings_snapshot": new_history.processing_settings_snapshot,
            "reading_progress": new_history.reading_progress,
            "current_position": new_history.current_position,
            "reading_time": new_history.reading_time,
            "last_read_at": new_history.last_read_at,
            "created_at": new_history.created_at
        }
        
    except Exception as e:
        logger.error(f"添加阅读历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加阅读历史失败: {str(e)}")


@router.delete("/user/history", response_model=Dict[str, Any])
async def clear_user_reading_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清空阅读历史
    """
    try:
        # 获取用户所有阅读历史
        histories = db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id).all()
        
        # 清理关联的任务和文本块（当文档不存在时）
        for history in histories:
            if history.document_id is not None:
                document = db.query(Document).filter(Document.id == history.document_id).first()
                if not document:
                    # 文档已删除，清理关联的任务和文本块
                    tasks = db.query(Task).filter(Task.document_id == history.document_id).all()
                    for task in tasks:
                        db.query(TextChunk).filter(TextChunk.task_id == task.id).delete()
                        db.delete(task)
        
        # 删除用户的所有阅读历史
        db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id).delete()
        db.commit()
        
        return {"message": "阅读历史清空成功"}
        
    except Exception as e:
        logger.error(f"清空阅读历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空阅读历史失败: {str(e)}")


@router.put("/user/history/{history_id}", response_model=Dict[str, Any])
async def update_user_reading_history(
    history_id: int,
    updates: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新阅读历史记录（阅读进度、阅读时间、处理结果等）
    """
    try:
        # 查找指定的阅读历史记录
        history = db.query(ReadingHistory).filter(
            ReadingHistory.id == history_id,
            ReadingHistory.user_id == current_user.id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="历史记录不存在")
        
        # 更新基本字段
        if "title" in updates:
            history.title = updates["title"]
        if "reading_progress" in updates:
            history.reading_progress = updates["reading_progress"]
        if "current_position" in updates:
            history.current_position = updates["current_position"]
        if "reading_time" in updates:
            history.reading_time = updates["reading_time"]
        if "last_read_at" in updates:
            history.last_read_at = updates["last_read_at"]
        
        # 更新处理结果相关字段（当重新处理文档时更新）
        if "content_snapshot" in updates:
            history.content_snapshot = updates["content_snapshot"]
        if "simplified_content_snapshot" in updates:
            history.simplified_content_snapshot = updates["simplified_content_snapshot"]
        if "segments_snapshot" in updates:
            history.segments_snapshot = updates["segments_snapshot"]
        if "simplified_segments_snapshot" in updates:
            history.simplified_segments_snapshot = updates["simplified_segments_snapshot"]
        if "pos_tags_snapshot" in updates:
            history.pos_tags_snapshot = updates["pos_tags_snapshot"]
        if "simplified_pos_tags_snapshot" in updates:
            history.simplified_pos_tags_snapshot = updates["simplified_pos_tags_snapshot"]
        if "primary_content_snapshot" in updates:
            history.primary_content_snapshot = updates["primary_content_snapshot"]
        if "secondary_content_snapshot" in updates:
            history.secondary_content_snapshot = updates["secondary_content_snapshot"]
        if "processing_settings_snapshot" in updates:
            history.processing_settings_snapshot = updates["processing_settings_snapshot"]
        
        db.commit()
        db.refresh(history)
        
        logger.info(f"用户 {current_user.username} 更新阅读历史记录: {history_id}")
        
        return {
            "id": history.id,
            "document_id": history.document_id,
            "title": history.title,
            "reading_progress": history.reading_progress,
            "current_position": history.current_position,
            "reading_time": history.reading_time,
            "last_read_at": history.last_read_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新阅读历史记录失败: {e}")
        raise HTTPException(status_code=500, detail="更新阅读历史记录失败")

@router.delete("/user/history/{history_id}", response_model=Dict[str, Any])
async def delete_user_reading_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除单个阅读历史记录
    """
    try:
        # 查找并删除指定的阅读历史记录
        history = db.query(ReadingHistory).filter(
            ReadingHistory.id == history_id,
            ReadingHistory.user_id == current_user.id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="历史记录不存在")
        
        # 记录删除操作
        logger.info(f"用户 {current_user.username} 删除阅读历史记录: {history_id}")
        
        # 获取关联的文档ID
        document_id = history.document_id
        
        # 清理关联的任务和文本块（无论文档是否存在）
        # 注意：不删除文档，文档应当保留供后续使用
        if document_id is not None:
            tasks = db.query(Task).filter(Task.document_id == document_id).all()
            for task in tasks:
                db.query(TextChunk).filter(TextChunk.task_id == task.id).delete()
                db.delete(task)
            logger.info(f"清理文档 {document_id} 关联的任务和文本块")
        
        db.delete(history)
        db.commit()
        
        logger.info(f"阅读历史记录删除成功: {history_id}")
        
        return {"message": "历史记录删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除历史记录失败: {str(e)}")


# 分页获取意群API
@router.get("/reading-history/{history_id}/segments", response_model=Dict[str, Any])
async def get_reading_history_segments(
    history_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    type: str = Query("original", regex="^(original|simplified)$", description="意群类型"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取阅读历史的意群（分页）
    从 ReadingHistory 模型获取数据
    """
    try:
        # 从 ReadingHistory 模型查找
        history = db.query(ReadingHistory).filter(
            ReadingHistory.id == history_id,
            ReadingHistory.user_id == current_user.id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="阅读历史不存在")
        
        # 获取对应类型的意群数据
        if type == "original":
            segments = history.segments_snapshot
        else:
            segments = history.simplified_segments_snapshot
        
        if not segments:
            raise HTTPException(status_code=404, detail="该阅读历史没有意群数据")
        
        # 计算分页
        total = len(segments)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        
        # 获取当前页的数据
        current_segments = segments[start:end]
        
        return {
            "message": "获取意群成功",
            "data": {
                "segments": current_segments,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取意群失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取意群失败: {str(e)}")


# 获取文档的最新阅读历史
@router.get("/documents/{document_id}/history", response_model=Dict[str, Any])
async def get_document_latest_history(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取文档的最新阅读历史（如果有的话）
    用于编辑文档后重新打开时获取最新处理结果
    """
    try:
        # 查找该文档关联的最新阅读历史
        history = db.query(ReadingHistory).filter(
            ReadingHistory.document_id == document_id,
            ReadingHistory.user_id == current_user.id
        ).order_by(ReadingHistory.last_read_at.desc()).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="该文档没有阅读历史记录")
        
        return {
            "message": "获取成功",
            "data": {
                "id": history.id,
                "document_id": history.document_id,
                "title": history.title,
                "content_snapshot": history.content_snapshot,
                "simplified_content_snapshot": history.simplified_content_snapshot,
                "segments_snapshot": history.segments_snapshot,
                "simplified_segments_snapshot": history.simplified_segments_snapshot,
                "pos_tags_snapshot": history.pos_tags_snapshot,
                "simplified_pos_tags_snapshot": history.simplified_pos_tags_snapshot,
                "processing_settings_snapshot": history.processing_settings_snapshot,
                "last_read_at": history.last_read_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档最新历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# 兼容旧版API - 通过 document_id 获取意群（实际从关联的阅读历史获取）
@router.get("/documents/{document_id}/segments", response_model=Dict[str, Any])
async def get_document_segments(
    document_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    type: str = Query("original", regex="^(original|simplified)$", description="意群类型"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取文档的意群（分页）- 兼容旧版API
    实际从关联的 ReadingHistory 获取数据
    """
    try:
        # 首先尝试通过 document_id 查找关联的阅读历史
        history = db.query(ReadingHistory).filter(
            ReadingHistory.document_id == document_id,
            ReadingHistory.user_id == current_user.id
        ).order_by(ReadingHistory.created_at.desc()).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="该文档没有关联的阅读历史")
        
        # 获取对应类型的意群数据
        if type == "original":
            segments = history.segments_snapshot
        else:
            segments = history.simplified_segments_snapshot
        
        if not segments:
            raise HTTPException(status_code=404, detail="该阅读历史没有意群数据")
        
        # 计算分页
        total = len(segments)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        
        # 获取当前页的数据
        current_segments = segments[start:end]
        
        return {
            "message": "获取意群成功",
            "data": {
                "segments": current_segments,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取意群失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取意群失败: {str(e)}")


# 文件上传API
@router.post("/files/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件并读取内容
    """
    try:
        file_service = FileService()
        file_info = await file_service.save_file(file)
        
        # 读取文件内容
        file_content = file_service.read_file(file_info['file_path'])
        
        # 删除临时文件
        file_service.delete_file(file_info['file_path'])
        
        if file_content is None:
            raise HTTPException(status_code=500, detail="读取文件内容失败")
        
        logger.info(f"文件上传成功: {file_info['file_name']}, 内容长度: {len(file_content)}")
        return {
            "message": "文件上传成功",
            "file_name": file_info['file_name'],
            "content": file_content
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


# 文件导出API
@router.get("/files/export/{file_id}", response_model=Dict[str, Any])
async def export_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出文件
    """
    try:
        # 查找文档
        document = db.query(Document).filter(
            Document.id == file_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 这里可以根据需要实现不同格式的导出
        # 目前返回文档内容
        return {
            "id": document.id,
            "content": document.content,
            "created_at": document.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件导出失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件导出失败: {str(e)}")

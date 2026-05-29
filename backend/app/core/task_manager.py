#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器
支持分组处理、断点续传
使用Redis存储任务状态和实现限流
"""
import json
import re
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.sql import func
import pymysql

from ..models.task import Task, TaskStatus
from ..models.text_chunk import TextChunk, ChunkStatus
from ..core.database import SessionLocal
from ..services.text_processor import TextProcessor
from ..core.model_manager import get_model_manager
from ..core.config import settings
from ..core.redis_manager import redis_manager

logger = logging.getLogger(__name__)

# 从配置文件读取分块参数
CHUNK_SIZE = settings.CHUNK_SIZE
CHUNKS_PER_GROUP = settings.CHUNKS_PER_GROUP


class TaskManager:
    """任务管理器"""

    # 类级别的集合，用于追踪正在处理的组，防止竞态条件导致重复调用
    _processing_groups = set()

    # 限流配置
    RATE_LIMIT_TASKS = 5  # 每分钟最大任务数
    RATE_LIMIT_WINDOW = 60  # 时间窗口（秒）

    def __init__(self):
        self.model_manager = get_model_manager()
        self.text_processor = TextProcessor(self.model_manager)

    def check_rate_limit(self, user_id: int) -> Tuple[bool, int]:
        """
        检查用户任务创建速率限制
        使用Redis实现分布式限流

        :param user_id: 用户ID
        :return: (是否允许, 剩余可创建任务数)
        """
        try:
            key = f"rate_limit:{user_id}"
            current = redis_manager.get(key)
            
            if current is None:
                # 首次请求，设置初始值和过期时间
                redis_manager.set(key, 1, expire=self.RATE_LIMIT_WINDOW)
                return True, self.RATE_LIMIT_TASKS - 1
            else:
                current_count = int(current)
                if current_count >= self.RATE_LIMIT_TASKS:
                    return False, 0
                else:
                    redis_manager.set(key, current_count + 1, expire=self.RATE_LIMIT_WINDOW)
                    return True, self.RATE_LIMIT_TASKS - current_count - 1
        except Exception as e:
            logger.warning(f"Redis限流检查失败，允许请求: {e}")
            # Redis不可用时，允许请求（优雅降级）
            return True, self.RATE_LIMIT_TASKS

    def _update_task_status_redis(self, task_id: int, status: str, progress: Optional[Dict] = None):
        """
        更新任务状态到Redis

        :param task_id: 任务ID
        :param status: 任务状态
        :param progress: 进度信息
        """
        try:
            status_data = {
                "status": status,
                "updated_at": datetime.now().isoformat(),
                "progress": progress or {}
            }
            redis_manager.set(f"task:{task_id}:status", status_data, expire=3600)
            logger.debug(f"任务 {task_id} 状态已更新到Redis: {status}")
        except Exception as e:
            logger.warning(f"更新任务状态到Redis失败: {e}")

    def _get_task_status_redis(self, task_id: int) -> Optional[Dict]:
        """
        从Redis获取任务状态

        :param task_id: 任务ID
        :return: 任务状态信息
        """
        try:
            status = redis_manager.get(f"task:{task_id}:status")
            return status
        except Exception as e:
            logger.warning(f"从Redis获取任务状态失败: {e}")
            return None

    def _clear_task_status_redis(self, task_id: int):
        """
        清除Redis中的任务状态

        :param task_id: 任务ID
        """
        try:
            redis_manager.delete(f"task:{task_id}:status")
            logger.debug(f"任务 {task_id} 状态已从Redis清除")
        except Exception as e:
            logger.warning(f"清除任务状态失败: {e}")

    def create_task(self, user_id: int, task_type: str, input_data: Dict[str, Any],
                   document_id: Optional[int] = None, group_id: Optional[int] = None,
                   check_limit: bool = True) -> Tuple[Optional[Task], str]:
        """
        创建任务

        :param user_id: 用户ID
        :param task_type: 任务类型
        :param input_data: 输入数据
        :param document_id: 文档ID
        :param group_id: 分组ID（用于关联同一文本的多个任务组）
        :param check_limit: 是否检查限流
        :return: (任务对象, 错误信息)
        """
        # 检查限流
        if check_limit:
            allowed, remaining = self.check_rate_limit(user_id)
            if not allowed:
                return None, f"任务创建过于频繁，请稍后再试（每分钟最多{self.RATE_LIMIT_TASKS}个任务）"

        db = SessionLocal()
        try:
            task = Task(
                user_id=user_id,
                document_id=document_id,
                group_id=group_id,
                group_index=0,
                task_type=task_type,
                input_data=json.dumps(input_data)
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            # 更新任务状态到Redis
            self._update_task_status_redis(task.id, TaskStatus.PENDING.value)

            return task, ""
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

    def get_pending_task_by_group(self, user_id: int, group_id: int) -> Optional[Task]:
        """
        获取用户指定分组中未完成的任务

        :param user_id: 用户ID
        :param group_id: 分组ID
        :return: 未完成任务对象
        """
        db = SessionLocal()
        try:
            return db.query(Task).filter(
                Task.user_id == user_id,
                Task.group_id == group_id,
                Task.status.in_(['paused', 'processing', 'pending'])
            ).first()
        finally:
            db.close()

    def get_unfinished_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户所有未完成的任务分组

        :param user_id: 用户ID
        :return: 未完成分组列表
        """
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(
                Task.user_id == user_id,
                Task.is_continuable == True
            ).all()

            result = []
            for task in tasks:
                if task.group_id:
                    result.append({
                        "task_id": task.id,
                        "group_id": task.group_id,
                        "group_index": task.group_index,
                        "total_groups": task.total_groups,
                        "completed_chunks": task.completed_chunks,
                        "total_chunks": task.total_chunks,
                        "last_chunk_index": task.last_chunk_index,
                        "status": task.status.value if isinstance(task.status, TaskStatus) else task.status
                    })
            return result
        finally:
            db.close()

    def _split_text_by_sentence(self, text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
        """
        基于句子边界分割文本

        :param text: 原始文本
        :param chunk_size: 每个块的目标大小
        :return: 文本块列表
        """
        sentence_pattern = r'([。！？.!?])'
        parts = re.split(sentence_pattern, text)
        sentences = []
        for i in range(0, len(parts), 2):
            sentence = parts[i]
            if i + 1 < len(parts):
                sentence += parts[i + 1]
            if sentence:
                sentences.append(sentence)

        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _calculate_groups(self, total_chunks: int, chunks_per_group: int = CHUNKS_PER_GROUP) -> int:
        """计算总组数"""
        return (total_chunks + chunks_per_group - 1) // chunks_per_group

    async def process_text_task(self, task_id: int):
        """
        处理文本任务（简单版本，用于非分组处理场景）
        
        :param task_id: 任务ID
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            # 更新任务状态为处理中
            task.status = TaskStatus.PROCESSING
            task.is_continuable = True
            
            # 更新文档状态为 processing，让文档列表显示正在处理
            if task.document_id:
                from ..models.document import Document, DocumentStatus
                document = db.query(Document).filter(Document.id == task.document_id).first()
                if document:
                    document.status = DocumentStatus.processing
                    document.processing_task_id = task.id
            
            db.commit()

            # 更新任务状态到Redis
            self._update_task_status_redis(task_id, TaskStatus.PROCESSING.value, {
                "group_index": 0,
                "total_groups": 1,
                "completed_chunks": 0,
                "total_chunks": 1
            })

            logger.info(f"开始处理任务 {task_id}")

            # 执行分组处理
            await self.process_text_grouped(task_id)

        except Exception as e:
            logger.error(f"处理任务 {task_id} 失败: {e}")
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                db.commit()
                self._update_task_status_redis(task_id, TaskStatus.FAILED.value, {"error": str(e)})
        finally:
            db.close()

    async def process_text_grouped(self, task_id: int):
        """
        分组处理文本任务
        每4块为一组，完成后保存历史记录

        :param task_id: 任务ID
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            input_data = json.loads(task.input_data)
            text = input_data.get('text')
            options = input_data.get('options', {})

            existing_chunks = db.query(TextChunk).filter(
                TextChunk.task_id == task_id
            ).order_by(TextChunk.chunk_index).all()

            if existing_chunks:
                completed_indices = {c.chunk_index for c in existing_chunks if c.status == ChunkStatus.COMPLETED}
                pending_chunks = [c for c in existing_chunks if c.status == ChunkStatus.PENDING]
                total_chunks = len(existing_chunks)
                # 对于续传任务，显示整个文档的进度（已完成组数/总组数）
                completed_groups = (task.group_index if task.group_index else 0)
                logger.info(f"续传任务 {task_id}: 已完成 {completed_groups}/{task.total_groups} 组 ({len(completed_indices)}/{total_chunks} chunks)")
            else:
                chunks_content = self._split_text_by_sentence(text)
                total_chunks = len(chunks_content)
                total_groups = self._calculate_groups(total_chunks)

                task.total_chunks = total_chunks
                task.total_groups = total_groups
                task.group_id = task.group_id or task.id

                # 更新文档的总组数
                if task.document_id:
                    from ..models.document import Document
                    document = db.query(Document).filter(Document.id == task.document_id).first()
                    if document:
                        document.total_groups = total_groups
                        db.commit()

                # 只创建第0组的chunk（当前任务处理的组）
                current_group_chunks = chunks_content[:CHUNKS_PER_GROUP]
                for i, content in enumerate(current_group_chunks):
                    db.add(TextChunk(
                        task_id=task_id,
                        group_index=0,
                        chunk_index=i,
                        content=content,
                        status=ChunkStatus.PENDING
                    ))
                db.commit()

                pending_chunks = db.query(TextChunk).filter(
                    TextChunk.task_id == task_id,
                    TextChunk.status == ChunkStatus.PENDING
                ).order_by(TextChunk.chunk_index).all()

                logger.info(f"新建分组任务 {task_id}: 第{task.group_index + 1}组，共 {len(current_group_chunks)} 块，总计 {total_chunks} 块，{total_groups} 组")

            task.status = TaskStatus.PROCESSING
            task.is_continuable = True
            
            # 更新文档状态为 processing，让文档列表显示正在处理
            if task.document_id:
                from ..models.document import Document, DocumentStatus
                document = db.query(Document).filter(Document.id == task.document_id).first()
                if document:
                    document.status = DocumentStatus.processing
                    document.processing_task_id = task.id
            
            db.commit()

            # 更新任务状态到Redis
            self._update_task_status_redis(task_id, TaskStatus.PROCESSING.value, {
                "group_index": task.group_index,
                "total_groups": task.total_groups,
                "completed_chunks": 0,
                "total_chunks": task.total_chunks
            })

            # 将任务信息传递给 _process_chunks，让其内部创建独立的数据库连接
            # 不传递 db session，避免跨线程共享导致连接中断
            await asyncio.to_thread(self._process_chunks, task.id, pending_chunks, options)

        except Exception as e:
            logger.error(f"分组任务 {task_id} 处理失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
            # 更新任务状态到Redis
            self._update_task_status_redis(task_id, TaskStatus.FAILED.value, {"error": str(e)})
        finally:
            db.close()

    def _process_chunks(self, task_id: int, pending_chunks: List[TextChunk], options: Dict[str, Any]):
        """
        处理文本块（并行处理）

        :param task_id: 任务ID
        :param pending_chunks: 待处理的块列表
        :param options: 处理选项
        """
        # 在内部创建独立的数据库连接，避免跨线程共享session
        db = SessionLocal()
        
        try:
            # 获取任务对象
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return
            
            max_workers = min(len(pending_chunks), 4)
            results = []

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_chunk, chunk.id, chunk.content, options): chunk
                    for chunk in pending_chunks
                }

                for future in as_completed(futures):
                    chunk = futures[future]
                    try:
                        result = future.result()
                        results.append((chunk.chunk_index, result))

                        task.completed_chunks = db.query(TextChunk).filter(
                            TextChunk.task_id == task.id,
                            TextChunk.status == ChunkStatus.COMPLETED
                        ).count()

                        last_completed = db.query(TextChunk).filter(
                            TextChunk.task_id == task.id,
                            TextChunk.status == ChunkStatus.COMPLETED
                        ).order_by(TextChunk.chunk_index.desc()).first()

                        if last_completed:
                            task.last_chunk_index = last_completed.chunk_index

                        db.commit()

                        # 使用任务的 group_index 而不是通过 chunk_index 计算
                        # 因为续传任务的 chunk_index 从0开始，但属于更高的组
                        current_group_index = task.group_index
                        
                        # 获取当前组的总chunk数
                        total_group_chunks = db.query(TextChunk).filter(
                            TextChunk.task_id == task.id,
                            TextChunk.group_index == current_group_index
                        ).count()
                        
                        completed_group_chunks = db.query(TextChunk).filter(
                            TextChunk.task_id == task.id,
                            TextChunk.group_index == current_group_index,
                            TextChunk.status == ChunkStatus.COMPLETED
                        ).count()

                        # 当该组所有chunk都完成时才触发组完成
                        if completed_group_chunks == total_group_chunks and total_group_chunks > 0:
                            self._on_group_completed(task.id, current_group_index, options)

                    except Exception as e:
                        logger.error(f"处理块 {chunk.chunk_index} 失败: {e}")
                        chunk.status = ChunkStatus.FAILED
                        chunk.error_message = str(e)
                        db.commit()

            all_chunks = db.query(TextChunk).filter(TextChunk.task_id == task.id).all()
            all_completed = all(c.status == ChunkStatus.COMPLETED for c in all_chunks)

            if all_completed:
                task.status = TaskStatus.COMPLETED
                task.is_continuable = False
                # 更新任务状态到Redis
                self._update_task_status_redis(task.id, TaskStatus.COMPLETED.value, {
                    "group_index": task.group_index,
                    "total_groups": task.total_groups,
                    "completed_chunks": task.completed_chunks,
                    "total_chunks": task.total_chunks
                })
                logger.info(f"任务 {task.id} 所有chunks完成，状态设置为 COMPLETED")
            else:
                task.status = TaskStatus.PAUSED
                # 更新任务状态到Redis
                self._update_task_status_redis(task.id, TaskStatus.PAUSED.value, {
                    "group_index": task.group_index,
                    "total_groups": task.total_groups,
                    "completed_chunks": task.completed_chunks,
                    "total_chunks": task.total_chunks
                })
                logger.info(f"任务 {task.id} 当前组处理完成，状态设置为 PAUSED，等待继续处理下一组")

            db.commit()
        except Exception as e:
            logger.error(f"处理块列表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()

    def _process_single_chunk(self, chunk_id: int, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文本块"""
        db = SessionLocal()
        try:
            chunk = db.query(TextChunk).filter(TextChunk.id == chunk_id).first()
            if not chunk:
                return {}

            chunk.status = ChunkStatus.PROCESSING
            db.commit()

            result = self.text_processor._process_short_text(content, options)

            chunk.status = ChunkStatus.COMPLETED
            chunk.result = json.dumps(result)
            db.commit()

            return result
        finally:
            db.close()

    def _on_group_completed(self, task_id: int, group_index: int, options: Dict[str, Any]):
        """
        当一组（4块）处理完成时的回调
        保存该组结果到历史记录

        :param task_id: 任务ID
        :param group_index: 完成的组索引
        :param options: 处理选项
        """
        db = SessionLocal()
        try:
            from ..models.reading_history import ReadingHistory
            
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            # 防止竞态条件：检查该组是否已经在处理中
            group_key = (task_id, group_index)
            if group_key in TaskManager._processing_groups:
                logger.info(f"任务 {task_id} 组 {group_index} 正在处理中，跳过重复调用")
                return
            
            # 标记该组为正在处理
            TaskManager._processing_groups.add(group_key)
            
            # 以下是原有的处理逻辑
            group_chunks = db.query(TextChunk).filter(
                TextChunk.task_id == task_id,
                TextChunk.group_index == group_index
            ).order_by(TextChunk.chunk_index).all()

            # 检查该组是否有任何chunk存在，并且所有chunk都已完成
            if not group_chunks:
                return
            
            completed_chunks = [c for c in group_chunks if c.status == ChunkStatus.COMPLETED]
            if len(completed_chunks) != len(group_chunks):
                logger.warning(f"任务 {task_id} 组 {group_index} 未全部完成 ({len(completed_chunks)}/{len(group_chunks)})，跳过保存")
                return

            all_segments = []
            all_simplified_segments = []
            processed_text = ""
            simplified_text = ""
            all_pos_tags = []
            all_simplified_pos_tags = []

            # 获取之前组的累积长度（用于位置偏移计算）
            prev_length = 0
            prev_simplified_length = 0
            
            # 如果不是第一组，从已有历史记录中获取之前的累积长度
            if group_index > 0 and task.document_id:
                existing_history = db.query(ReadingHistory).filter(
                    ReadingHistory.user_id == task.user_id,
                    ReadingHistory.document_id == task.document_id
                ).first()
                if existing_history and existing_history.content_snapshot:
                    prev_length = len(existing_history.content_snapshot)
                if existing_history and existing_history.simplified_content_snapshot:
                    prev_simplified_length = len(existing_history.simplified_content_snapshot)
            
            # 组内累积长度（用于组内chunk之间的位置偏移）
            current_group_length = 0
            current_group_simplified_length = 0
            
            for i, chunk in enumerate(group_chunks):
                if chunk.result:
                    result = json.loads(chunk.result)
                    chunk_processed_text = result.get('processed_text', '')
                    chunk_simplified_text = result.get('simplifiedContent', '') or ''
                    
                    processed_text += chunk_processed_text
                    simplified_text += chunk_simplified_text
                    
                    # 当前chunk的起始位置 = 组间偏移 + 组内累积长度
                    chunk_start_pos = prev_length + current_group_length
                    chunk_simplified_start_pos = prev_simplified_length + current_group_simplified_length
                    
                    # 为原始文本词性标注添加位置偏移
                    chunk_pos_tags = result.get('pos_tags', [])
                    for tag in chunk_pos_tags:
                        tag['start_pos'] = chunk_start_pos + tag['start_pos']
                        tag['end_pos'] = chunk_start_pos + tag['end_pos']
                        all_pos_tags.append(tag)
                    
                    # 为简化文本词性标注添加位置偏移
                    chunk_sim_pos_tags = result.get('simplified_pos_tags', [])
                    for tag in chunk_sim_pos_tags:
                        tag['start_pos'] = chunk_simplified_start_pos + tag['start_pos']
                        tag['end_pos'] = chunk_simplified_start_pos + tag['end_pos']
                        all_simplified_pos_tags.append(tag)

                    # 调试日志
                    first_seg = result.get('segments', [])[0] if result.get('segments', []) else None
                    logger.info(f"组 {group_index} chunk {i}: content长度={len(chunk.content)}, 第一个seg位置={first_seg}, chunk起始位置={chunk_start_pos}")

                    for seg in result.get('segments', []):
                        seg['start_pos'] = chunk_start_pos + seg['start_pos']
                        seg['end_pos'] = chunk_start_pos + seg['end_pos']
                        seg['id'] = len(all_segments) + 1
                        
                        # 注意：segment内部的pos_tags保持相对位置不变
                        # 前端会根据isUsingSegmentPosTags来使用不同的匹配逻辑
                        
                        all_segments.append(seg)

                    for seg in result.get('simplified_segments', []):
                        seg['start_pos'] = chunk_simplified_start_pos + seg['start_pos']
                        seg['end_pos'] = chunk_simplified_start_pos + seg['end_pos']
                        seg['id'] = len(all_simplified_segments) + 1
                        
                        # 注意：segment内部的pos_tags保持相对位置不变
                        # 前端会根据isUsingSegmentPosTags来使用不同的匹配逻辑
                        
                        all_simplified_segments.append(seg)

                    # 更新组内累积长度（使用处理后文本的长度，而不是原始chunk长度）
                    current_group_length += len(chunk_processed_text)
                    current_group_simplified_length += len(chunk_simplified_text)

            history_id = self._save_reading_history(
                user_id=task.user_id,
                document_id=task.document_id,
                original_text=''.join(c.content for c in group_chunks),
                processed_text=processed_text,
                simplified_text=simplified_text,
                segments=all_segments,
                simplified_segments=all_simplified_segments,
                pos_tags=all_pos_tags,
                simplified_pos_tags=all_simplified_pos_tags,
                options=options,
                task_id=task_id,
                group_index=group_index,
                total_groups=task.total_groups
            )

            # 更新任务的 result_data 字段，保存 history_id
            if history_id:
                result_data = {
                    "history_id": history_id,
                    "group_index": group_index,
                    "completed_at": datetime.now().isoformat()
                }
                task.result_data = json.dumps(result_data)
                db.commit()
                logger.info(f"任务 {task_id} 第 {group_index + 1} 组完成，history_id={history_id} 已保存到 result_data")

            # 更新文档进度信息
            if task.document_id:
                from ..models.document import Document, DocumentStatus
                document = db.query(Document).filter(Document.id == task.document_id).first()
                if document:
                    document.completed_groups = group_index + 1
                    document.total_groups = task.total_groups
                    
                    # 判断是否所有组都已完成
                    if group_index + 1 >= task.total_groups:
                        document.status = DocumentStatus.completed
                    else:
                        # 还有未完成的组，设置为暂停状态
                        document.status = DocumentStatus.paused
                    
                    db.commit()
            
            # 关键修复：确保任务状态被正确更新到Redis
            # 对于单组任务，检查是否所有块都已完成
            all_chunks = db.query(TextChunk).filter(TextChunk.task_id == task_id).all()
            all_completed = all(c.status == ChunkStatus.COMPLETED for c in all_chunks)
            
            # 如果所有块都完成了，设置任务状态为COMPLETED
            if all_completed:
                task.status = TaskStatus.COMPLETED
                task.is_continuable = False
                db.commit()
                logger.info(f"任务 {task_id} 所有块完成，设置状态为 COMPLETED")
            
            # 获取任务状态
            current_status = task.status.value if hasattr(task.status, 'value') else task.status
            
            logger.info(f"任务 {task_id} 完成，当前状态: {current_status}")
            
            # 确保任务状态被正确更新到Redis
            # 对于单组任务，强制设置为COMPLETED状态
            final_status = TaskStatus.COMPLETED.value if all_completed else current_status
            self._update_task_status_redis(
                task.id, 
                final_status,
                {
                    "group_index": group_index,
                    "total_groups": task.total_groups,
                    "completed_groups": group_index + 1,
                    "completed_chunks": task.completed_chunks,
                    "total_chunks": task.total_chunks
                }
            )
            
            logger.info(f"任务 {task_id} 第 {group_index + 1} 组完成，Redis状态已更新为: {final_status}")

            logger.info(f"任务 {task_id} 第 {group_index + 1} 组完成，已保存历史记录")

        except Exception as e:
            logger.error(f"保存第 {group_index} 组历史记录失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # 移除正在处理的标记
            TaskManager._processing_groups.discard(group_key)
            db.close()

    def _save_reading_history(self, user_id: int, document_id: Optional[int],
                            original_text: str, processed_text: str, simplified_text: str,
                            segments: List, simplified_segments: List,
                            pos_tags: List, simplified_pos_tags: List,
                            options: Dict[str, Any], task_id: int, group_index: int,
                            total_groups: int = 1) -> Optional[int]:
        """
        保存阅读历史记录（追加模式，单组时更新模式）

        :param user_id: 用户ID
        :param document_id: 文档ID
        :param original_text: 原始文本
        :param processed_text: 处理后文本
        :param simplified_text: 简化文本
        :param segments: 意群划分
        :param simplified_segments: 简化文本意群划分
        :param pos_tags: 词性标注
        :param simplified_pos_tags: 简化文本词性标注
        :param options: 处理选项
        :param task_id: 任务ID
        :param group_index: 组索引
        :param total_groups: 总组数，用于判断是追加还是更新模式
        :return: 历史记录ID
        """
        # 添加重试机制，防止数据库连接中断
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            db = SessionLocal()
            try:
                # 执行保存操作
                return self._save_reading_history_inner(
                    db, user_id, document_id, original_text, processed_text, 
                    simplified_text, segments, simplified_segments, pos_tags, 
                    simplified_pos_tags, options, task_id, group_index, total_groups
                )
            except pymysql.err.OperationalError as e:
                logger.warning(f"保存历史记录失败（第 {attempt + 1}/{max_retries} 次尝试）: {e}")
                db.close()
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"保存历史记录失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                db.close()
                raise
        return None
    
    def _save_reading_history_inner(self, db, user_id: int, document_id: Optional[int],
                                   original_text: str, processed_text: str, simplified_text: str,
                                   segments: List, simplified_segments: List,
                                   pos_tags: List, simplified_pos_tags: List,
                                   options: Dict[str, Any], task_id: int, group_index: int,
                                   total_groups: int = 1) -> Optional[int]:
        """
        保存阅读历史记录的内部方法（不包含重试逻辑）
        """
        try:
            from ..models.reading_history import ReadingHistory
            from ..models.document import Document

            # 获取文档标题
            document_title = None
            if document_id:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document_title = document.title

            # 尝试查找该文档已有的历史记录
            existing_history = None
            if document_id:
                existing_history = db.query(ReadingHistory).filter(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.document_id == document_id
                ).order_by(ReadingHistory.created_at.desc()).first()

            if existing_history:
                # 已有历史记录
                if total_groups == 1:
                    # 单组处理时，更新历史记录而不是追加
                    existing_history.content_snapshot = original_text
                    existing_history.simplified_content_snapshot = simplified_text if simplified_text else None
                    existing_history.segments_snapshot = segments if segments else None
                    existing_history.simplified_segments_snapshot = simplified_segments if simplified_segments else None
                    existing_history.pos_tags_snapshot = pos_tags if pos_tags else None
                    existing_history.simplified_pos_tags_snapshot = simplified_pos_tags if simplified_pos_tags else None
                    existing_history.processing_settings_snapshot = options
                    
                    from sqlalchemy.orm import attributes
                    attributes.flag_modified(existing_history, 'content_snapshot')
                    if simplified_text:
                        attributes.flag_modified(existing_history, 'simplified_content_snapshot')
                    if segments:
                        attributes.flag_modified(existing_history, 'segments_snapshot')
                    if simplified_segments:
                        attributes.flag_modified(existing_history, 'simplified_segments_snapshot')
                    if pos_tags:
                        attributes.flag_modified(existing_history, 'pos_tags_snapshot')
                    if simplified_pos_tags:
                        attributes.flag_modified(existing_history, 'simplified_pos_tags_snapshot')
                    attributes.flag_modified(existing_history, 'processing_settings_snapshot')
                    
                    existing_history.last_read_at = func.now()
                    db.commit()
                    db.refresh(existing_history)
                    logger.info(f"单组更新历史记录 {existing_history.id}，用于任务 {task_id}")
                    return existing_history.id
                else:
                    # 多组处理时，追加数据
                    offset = len(existing_history.content_snapshot) if existing_history.content_snapshot else 0
                    
                    existing_history.content_snapshot += original_text
                    if simplified_text:
                        if existing_history.simplified_content_snapshot:
                            existing_history.simplified_content_snapshot += simplified_text
                        else:
                            existing_history.simplified_content_snapshot = simplified_text

                    if segments:
                        existing_segments = existing_history.segments_snapshot or []
                        for seg in segments:
                            seg['id'] = len(existing_segments) + 1
                            seg['start_pos'] += offset
                            seg['end_pos'] += offset
                            # segment.pos_tags的位置已经在前面的处理中正确设置，这里不需要再调整
                            existing_segments.append(seg)
                        existing_history.segments_snapshot = existing_segments

                    if simplified_segments:
                        existing_simplified = existing_history.simplified_segments_snapshot or []
                        # 计算简化文本的偏移量（追加前的长度）
                        sim_offset = len(existing_history.simplified_content_snapshot) if existing_history.simplified_content_snapshot else 0
                        for seg in simplified_segments:
                            seg['id'] = len(existing_simplified) + 1
                            seg['start_pos'] += sim_offset
                            seg['end_pos'] += sim_offset
                            # segment.pos_tags的位置已经在前面的处理中正确设置，这里不需要再调整
                            existing_simplified.append(seg)
                        existing_history.simplified_segments_snapshot = existing_simplified

                    if pos_tags:
                        existing_pos = existing_history.pos_tags_snapshot or []
                        # 使用已计算好的offset（追加前的长度）
                        # 为新添加的词性标注添加偏移
                        for tag in pos_tags:
                            tag['start_pos'] += offset
                            tag['end_pos'] += offset
                        existing_pos.extend(pos_tags)
                        existing_history.pos_tags_snapshot = existing_pos

                    if simplified_pos_tags:
                        existing_sim_pos = existing_history.simplified_pos_tags_snapshot or []
                        # 使用简化文本追加前的长度作为偏移量
                        for tag in simplified_pos_tags:
                            tag['start_pos'] += sim_offset
                            tag['end_pos'] += sim_offset
                        existing_sim_pos.extend(simplified_pos_tags)
                        existing_history.simplified_pos_tags_snapshot = existing_sim_pos

                    existing_history.processing_settings_snapshot = options
                    existing_history.last_read_at = func.now()

                    from sqlalchemy.orm import attributes
                    attributes.flag_modified(existing_history, 'content_snapshot')
                    if simplified_text:
                        attributes.flag_modified(existing_history, 'simplified_content_snapshot')
                    if segments:
                        attributes.flag_modified(existing_history, 'segments_snapshot')
                    if simplified_segments:
                        attributes.flag_modified(existing_history, 'simplified_segments_snapshot')
                    if pos_tags:
                        attributes.flag_modified(existing_history, 'pos_tags_snapshot')
                    if simplified_pos_tags:
                        attributes.flag_modified(existing_history, 'simplified_pos_tags_snapshot')
                    attributes.flag_modified(existing_history, 'processing_settings_snapshot')
                    attributes.flag_modified(existing_history, 'last_read_at')

                    db.commit()
                    db.refresh(existing_history)
                    logger.info(f"追加到历史记录 {existing_history.id}，用于任务 {task_id} 第 {group_index} 组")
                    return existing_history.id
            else:
                # 没有历史记录，创建新记录
                history = ReadingHistory(
                    user_id=user_id,
                    document_id=document_id,
                    title=document_title or f"文档 {document_id}",
                    content_snapshot=original_text,
                    simplified_content_snapshot=simplified_text if simplified_text else None,
                    segments_snapshot=segments if segments else None,
                    simplified_segments_snapshot=simplified_segments if simplified_segments else None,
                    pos_tags_snapshot=pos_tags if pos_tags else None,
                    simplified_pos_tags_snapshot=simplified_pos_tags if simplified_pos_tags else None,
                    processing_settings_snapshot=options,
                    last_read_at=func.now()
                )
                db.add(history)
                db.commit()
                db.refresh(history)

                logger.info(f"创建新历史记录 {history.id} 用于任务 {task_id}")
                return history.id

        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        finally:
            db.close()

    def create_next_group_task(self, original_task_id: int) -> Optional[Task]:
        """
        创建下一组任务

        :param original_task_id: 原始任务ID
        :return: 新任务对象
        """
        db = SessionLocal()
        try:
            original_task = db.query(Task).filter(Task.id == original_task_id).first()
            if not original_task:
                return None

            next_group_index = original_task.group_index + 1
            if next_group_index >= original_task.total_groups:
                logger.info(f"任务 {original_task_id} 已无更多组")
                return None

            new_task = Task(
                user_id=original_task.user_id,
                document_id=original_task.document_id,
                group_id=original_task.group_id,
                group_index=next_group_index,
                total_groups=original_task.total_groups,
                total_chunks=original_task.total_chunks,
                completed_chunks=0,
                task_type=original_task.task_type,
                input_data=original_task.input_data
            )
            db.add(new_task)
            # 先提交任务获取ID
            db.commit()
            db.refresh(new_task)

            # 动态创建当前组的chunk（而不是从原任务复制）
            input_data = json.loads(original_task.input_data or '{}')
            text = input_data.get('text', '')
            
            if text:
                chunks_content = self._split_text_by_sentence(text)
                # 计算当前组的chunk范围
                start_index = next_group_index * CHUNKS_PER_GROUP
                end_index = start_index + CHUNKS_PER_GROUP
                current_group_chunks = chunks_content[start_index:end_index]
                
                for i, content in enumerate(current_group_chunks):
                    new_chunk = TextChunk(
                        task_id=new_task.id,
                        group_index=next_group_index,
                        chunk_index=i,
                        content=content,
                        status='pending'
                    )
                    db.add(new_chunk)

            db.commit()
            logger.info(f"为任务 {original_task_id} 创建第 {next_group_index + 1} 组的新任务 {new_task.id}")
            return new_task

        except Exception as e:
            logger.error(f"创建下一组任务失败: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def pause_task(self, task_id: int) -> bool:
        """暂停任务"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False

            task.status = TaskStatus.PAUSED
            task.is_continuable = True
            db.commit()
            logger.info(f"任务 {task_id} 已暂停")
            return True
        finally:
            db.close()

    def resume_task(self, task_id: int) -> Optional[Task]:
        """恢复任务"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return None

            task.status = TaskStatus.PENDING
            db.commit()
            
            # 更新Redis状态
            self._update_task_status_redis(task_id, TaskStatus.PENDING.value, {
                "group_index": task.group_index,
                "total_groups": task.total_groups,
                "completed_chunks": task.completed_chunks,
                "total_chunks": task.total_chunks
            })
            
            logger.info(f"任务 {task_id} 已恢复")
            return task
        finally:
            db.close()

    def get_task_progress(self, task_id: int) -> Dict[str, Any]:
        """获取任务进度
        优先从Redis获取，提高响应速度
        """
        # 优先从Redis获取任务状态
        redis_status = self._get_task_status_redis(task_id)
        if redis_status:
            return {
                "task_id": task_id,
                "status": redis_status.get("status"),
                "updated_at": redis_status.get("updated_at"),
                **redis_status.get("progress", {})
            }

        # Redis不可用时，从数据库获取
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {}

            completed_chunks = db.query(TextChunk).filter(
                TextChunk.task_id == task_id,
                TextChunk.status == ChunkStatus.COMPLETED
            ).count()

            pending_chunks = db.query(TextChunk).filter(
                TextChunk.task_id == task_id,
                TextChunk.status == ChunkStatus.PENDING
            ).count()

            return {
                "task_id": task_id,
                "group_id": task.group_id,
                "group_index": task.group_index,
                "total_groups": task.total_groups,
                "total_chunks": task.total_chunks,
                "completed_chunks": completed_chunks,
                "pending_chunks": pending_chunks,
                "last_chunk_index": task.last_chunk_index,
                "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
                "is_continuable": task.is_continuable
            }
        finally:
            db.close()


task_manager = TaskManager()

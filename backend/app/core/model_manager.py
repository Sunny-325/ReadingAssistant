#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelManager(ABC):
    """
    模型管理器抽象基类
    """
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成文本
        
        :param prompt: 提示文本
        :param kwargs: 其他参数
        :return: 生成的文本
        """
        pass
    
    @abstractmethod
    def get_model_status(self) -> Dict[str, Any]:
        """
        获取模型状态
        
        :return: 模型状态
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> Dict[str, Any]:
        """
        清理资源
        
        :return: 清理结果
        """
        pass


# 创建全局模型管理器实例
model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """
    获取模型管理器实例
    
    :return: 模型管理器实例
    """
    global model_manager
    if model_manager is None:
        # 根据配置选择模型管理器
        if settings.USE_QWEN_MODEL:
            try:
                # 动态导入QwenModelManager，避免循环导入
                from ..core.qwen_model_manager import QwenModelManager
                model_manager = QwenModelManager()
                logger.info("使用Qwen模型管理器")
            except Exception as e:
                logger.error(f"初始化Qwen模型管理器失败: {e}")
                logger.info("自动切换到Ollama模型管理器")
                # 动态导入OllamaModelManager，避免循环导入
                from ..core.ollama_model_manager import OllamaModelManager
                model_manager = OllamaModelManager()
        else:
            # 动态导入OllamaModelManager，避免循环导入
            from ..core.ollama_model_manager import OllamaModelManager
            model_manager = OllamaModelManager()
            logger.info("使用Ollama模型管理器")
    return model_manager


def switch_to_fallback_model() -> ModelManager:
    """
    切换到备用模型（Ollama）
    
    :return: Ollama模型管理器实例
    """
    global model_manager
    try:
        # 清理现有模型管理器资源
        if model_manager:
            model_manager.cleanup()
            logger.info("已清理原模型管理器资源")
        
        # 动态导入OllamaModelManager
        from ..core.ollama_model_manager import OllamaModelManager
        model_manager = OllamaModelManager()
        logger.info("已切换到Ollama模型管理器作为备用")
        
        return model_manager
    except Exception as e:
        logger.error(f"切换到备用模型失败: {e}")
        raise

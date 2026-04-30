#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama模型管理器
"""

import logging
import requests
from typing import Dict, Any, Optional

from .config import settings
from .model_manager import ModelManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OllamaModelManager(ModelManager):
    """
    Ollama模型管理器
    """
    
    def __init__(self):
        """
        初始化Ollama模型管理器
        """
        import time
        start_time = time.time()
        
        # 根据配置选择API地址
        if settings.USE_CLOUD_MODEL:
            self.api_url = settings.CLOUD_MODEL_API_URL
            logger.info(f"使用云端模型服务: {self.api_url}")
        else:
            self.api_url = settings.OLLAMA_API_URL
            logger.info(f"使用本地Ollama服务: {self.api_url}")
        
        self.model_name = settings.MODEL_NAME
        self.session = requests.Session()
        self.session.timeout = 30
        
        # 记录加载时间
        self.load_time = time.time() - start_time
    
    def generate_text(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成文本
        
        :param prompt: 提示文本
        :param kwargs: 其他参数
        :return: 生成的文本
        """
        try:
            endpoint = f"{self.api_url}/api/generate"
            # 默认参数优化
            default_kwargs = {
                "max_length": 1024,  # 增加生成长度
                "temperature": 0.3,
                "top_p": 0.9,
                "stop": ["\n\n"]
            }
            default_kwargs.update(kwargs)
            
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                **default_kwargs
            }
            
            response = self.session.post(endpoint, json=data, timeout=300)  # 增加超时时间到5分钟
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.RequestException as e:
            logger.error(f"生成文本失败: {e}")
            return None
        except Exception as e:
            logger.error(f"生成文本失败: {e}")
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        获取模型状态
        
        :return: 模型状态
        """
        try:
            endpoint = f"{self.api_url}/api/tags"
            response = self.session.get(endpoint)
            response.raise_for_status()
            
            result = response.json()
            models = result.get("models", [])
            
            # 检查模型是否存在
            model_exists = any(model.get("name") == self.model_name for model in models)
            
            return {
                "status": "healthy" if model_exists else "unhealthy",
                "model": self.model_name,
                "model_exists": model_exists,
                "api_url": self.api_url
            }
            
        except requests.RequestException as e:
            logger.error(f"获取模型状态失败: {e}")
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"获取模型状态失败: {e}")
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "error": str(e)
            }
    
    def cleanup(self) -> Dict[str, Any]:
        """
        清理资源
        
        :return: 清理结果
        """
        try:
            # 关闭会话
            self.session.close()
            return {
                "success": True,
                "message": "资源清理成功"
            }
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

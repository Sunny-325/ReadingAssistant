#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen模型管理器
"""

import logging
import time
from typing import Dict, Any, Optional
import dashscope
from dashscope import Generation

from .config import settings
from .model_manager import ModelManager, switch_to_fallback_model

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QwenModelManager(ModelManager):
    """
    Qwen模型管理器
    """
    
    def __init__(self):
        """
        初始化Qwen模型管理器
        """
        start_time = time.time()
        
        # 阿里云通义千问API配置
        self.api_key = settings.QWEN_API_KEY
        self.model_name = settings.QWEN_MODEL_NAME
        
        # 配置dashscope API密钥
        dashscope.api_key = self.api_key
        
        # 缓存配置
        self.cache = {}
        self.max_cache_size = 100
        
        # 重试配置（从配置文件读取）
        self.max_retries = settings.MODEL_RETRY_ATTEMPTS
        self.retry_delay = 1
        
        # 记录加载时间
        self.load_time = time.time() - start_time
        logger.info(f"Qwen模型管理器初始化完成，加载时间: {self.load_time:.2f}秒")
    
    def generate_text(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成文本
        
        :param prompt: 提示文本
        :param kwargs: 其他参数
        :return: 生成的文本
        """
        # 不使用缓存，每次都调用模型获取结果
        # 保持每次处理文本都调用模型，尽管内容一样但是每次模型返回的结果可能不同
        
        # 使用配置文件中的参数，支持长文本处理
        default_kwargs = {
            "max_tokens": settings.MODEL_MAX_TOKENS,  # 从配置文件读取
            "temperature": settings.MODEL_TEMPERATURE,  # 较低温度，保持输出稳定性
            "top_p": settings.MODEL_TOP_P  # nucleus sampling
        }
        default_kwargs.update(kwargs)
        
        logger.info(f"调用Qwen模型: {self.model_name}")
        logger.info(f"提示词长度: {len(prompt)}字符")
        logger.info(f"参数: {default_kwargs}")
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                # 使用dashscope SDK调用API
                logger.info(f"第{attempt+1}次请求模型API")
                
                # 构建messages格式的提示词
                messages = [
                    {"role": "system", "content": "你是一个文本处理助手，负责文本理解、简化和意群划分。"},
                    {"role": "user", "content": prompt}
                ]
                
                # 调用模型（使用官方文档推荐的格式）
                response = Generation.call(
                    model=self.model_name,
                    api_key=self.api_key,
                    messages=messages,
                    temperature=default_kwargs.get("temperature"),
                    top_p=default_kwargs.get("top_p"),
                    max_tokens=default_kwargs.get("max_tokens"),
                    result_format="message"
                )
                
                # 处理响应（按照官方文档格式）
                if response.status_code == 200:
                    # 检查 response.output 是否为 None
                    if response.output is None:
                        logger.error("API响应成功但输出为空")
                        logger.error(f"响应详情: {str(response)}")
                        if attempt < self.max_retries - 1:
                            logger.info(f"等待{self.retry_delay * (2 ** attempt)}秒后重试")
                            time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                            continue
                        else:
                            logger.error("生成文本失败: API响应输出为空")
                            return None
                    
                    # 按照官方文档格式提取文本: response.output.choices[0].message.content
                    generated_text = None
                    
                    try:
                        # 官方推荐的方式
                        if (hasattr(response.output, 'choices') and 
                            response.output.choices and 
                            len(response.output.choices) > 0):
                            choice = response.output.choices[0]
                            if (hasattr(choice, 'message') and 
                                choice.message and 
                                hasattr(choice.message, 'content') and 
                                choice.message.content):
                                generated_text = choice.message.content
                                logger.debug("从 response.output.choices[0].message.content 获取文本")
                    except Exception as e:
                        logger.error(f"提取文本时发生异常: {e}")
                    
                    # 检查是否获取到文本
                    if generated_text is None or generated_text.strip() == "":
                        logger.error("API响应成功但文本为空")
                        logger.error(f"响应输出详情: {str(response.output)}")
                        if attempt < self.max_retries - 1:
                            logger.info(f"等待{self.retry_delay * (2 ** attempt)}秒后重试")
                            time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                            continue
                        else:
                            logger.error("生成文本失败: 响应文本为空")
                            return None
                    
                    logger.info(f"模型响应成功，生成文本长度: {len(generated_text)}字符")
                    
                    # 不缓存模型结果，保持每次调用都获取新结果
                    return generated_text
                else:
                    logger.error(f"API调用失败: {response.message}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"等待{self.retry_delay * (2 ** attempt)}秒后重试")
                        time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                    else:
                        logger.error(f"生成文本失败: {response.message}")
                        return None
                
            except Exception as e:
                logger.error(f"第{attempt+1}次请求失败: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"等待{self.retry_delay * (2 ** attempt)}秒后重试")
                    time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                else:
                    logger.error(f"生成文本失败: {str(e)}")
                    # 尝试切换到备用模型
                    try:
                        logger.info("尝试切换到Ollama备用模型")
                        fallback_manager = switch_to_fallback_model()
                        return fallback_manager.generate_text(prompt, **kwargs)
                    except Exception as fallback_e:
                        logger.error(f"切换到备用模型失败: {str(fallback_e)}")
                        return None
    
    def _update_cache(self, key: str, value: str):
        """
        更新缓存
        
        :param key: 缓存键
        :param value: 缓存值
        """
        if len(self.cache) >= self.max_cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = value
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        获取模型状态
        
        :return: 模型状态
        """
        try:
            # 检查配置是否正确
            is_configured = bool(self.api_key) and bool(self.model_name)
            
            return {
                "status": "healthy" if is_configured else "unhealthy",
                "model": self.model_name,
                "api_key_configured": bool(self.api_key),
                "cache_size": len(self.cache)
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
            # 清空缓存
            self.cache.clear()
        
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


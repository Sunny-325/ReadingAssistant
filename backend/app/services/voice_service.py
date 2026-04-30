#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音服务
"""

import logging
import tempfile
import os
from typing import Optional, Dict, Any


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入pyttsx3
PYTTSX3_AVAILABLE = False
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class VoiceService:
    """
    语音服务类
    """
    
    def __init__(self):
        """
        初始化语音服务
        """
        self.engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                # 设置默认参数
                self.engine.setProperty('rate', 150)  # 语速
                self.engine.setProperty('volume', 1.0)  # 音量
            except Exception as e:
                logger.error(f"pyttsx3 引擎初始化失败: {e}")
                self.engine = None
    
    def text_to_speech(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        文本转语音（pyttsx3）
        
        :param text: 文本
        :param kwargs: 其他参数
        :return: 语音合成结果
        """
        try:
            # 获取参数
            rate = kwargs.get('rate', 150)
            volume = kwargs.get('volume', 1.0)
            
            # 检查pyttsx3是否可用
            if not PYTTSX3_AVAILABLE or self.engine is None:
                return {
                    "text": text,
                    "success": False,
                    "message": "pyttsx3 服务不可用"
                }
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            # 设置参数（使用默认语音，不选择男女声）
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # 合成语音
            self.engine.save_to_file(text, temp_file_path)
            self.engine.runAndWait()
            
            # 读取音频文件
            with open(temp_file_path, 'rb') as f:
                audio_data = f.read()
            
            # 清理临时文件
            os.unlink(temp_file_path)
            
            return {
                "text": text,
                "success": True,
                "message": "文本转语音成功",
                "audio_data": audio_data
            }
        except Exception as e:
            logger.error(f"文本转语音失败: {e}")
            return {
                "text": text,
                "success": False,
                "message": f"文本转语音失败: {str(e)}"
            }

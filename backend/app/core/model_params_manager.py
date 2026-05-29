#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型参数管理器
根据不同功能类型返回最佳参数配置
"""

from typing import Dict, Any
from .config import settings


class ModelParamsManager:
    """
    模型参数管理器
    根据不同的功能类型返回最佳参数配置
    """
    
    @staticmethod
    def get_params_by_function(function_type: str) -> Dict[str, Any]:
        """
        根据功能类型获取对应的模型参数
        
        :param function_type: 功能类型，可选值: 'segment', 'simplify', 'analyze'
        :return: 模型参数字典
        """
        params_map = {
            'segment': {
                'temperature': settings.SEGMENT_TEMPERATURE,
                'top_p': settings.SEGMENT_TOP_P,
                'max_tokens': settings.SEGMENT_MAX_TOKENS
            },
            'simplify': {
                'temperature': settings.SIMPLIFY_TEMPERATURE,
                'top_p': settings.SIMPLIFY_TOP_P,
                'max_tokens': settings.SIMPLIFY_MAX_TOKENS
            },
            'analyze': {
                'temperature': settings.ANALYZE_TEMPERATURE,
                'top_p': settings.ANALYZE_TOP_P,
                'max_tokens': settings.ANALYZE_MAX_TOKENS
            }
        }
        
        # 返回对应功能的参数，如果不存在则返回默认参数
        return params_map.get(function_type, {
            'temperature': settings.SIMPLIFY_TEMPERATURE,
            'top_p': settings.MODEL_TOP_P,
            'max_tokens': settings.MODEL_MAX_TOKENS
        })
    
    @staticmethod
    def get_segment_params() -> Dict[str, Any]:
        """获取意群划分的参数配置"""
        return {
            'temperature': settings.SEGMENT_TEMPERATURE,
            'top_p': settings.SEGMENT_TOP_P,
            'max_tokens': settings.SEGMENT_MAX_TOKENS
        }
    
    @staticmethod
    def get_simplify_params() -> Dict[str, Any]:
        """获取文本简化的参数配置"""
        return {
            'temperature': settings.SIMPLIFY_TEMPERATURE,
            'top_p': settings.SIMPLIFY_TOP_P,
            'max_tokens': settings.SIMPLIFY_MAX_TOKENS
        }
    
    @staticmethod
    def get_analyze_params() -> Dict[str, Any]:
        """获取主次内容区分的参数配置"""
        return {
            'temperature': settings.ANALYZE_TEMPERATURE,
            'top_p': settings.ANALYZE_TOP_P,
            'max_tokens': settings.ANALYZE_MAX_TOKENS
        }

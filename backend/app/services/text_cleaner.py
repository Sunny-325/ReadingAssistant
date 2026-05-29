#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本清洗服务
统一的文本清洗和预处理逻辑
"""
import re
import logging

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    文本清洗器
    提供统一的文本清洗和预处理功能
    """
    
    def clean_text(self, text: str) -> str:
        """
        清洗文本内容
        
        :param text: 原始文本
        :return: 清洗后的文本
        """
        if not text or not text.strip():
            return text
        
        original_length = len(text)
        cleaned = text
        
        # 1. 去除控制字符（除了换行符和制表符）
        cleaned = self._remove_control_chars(cleaned)
        
        # 2. 规范化空白字符
        cleaned = self._normalize_whitespace(cleaned)
        
        # 3. 全角转半角
        cleaned = self._fullwidth_to_halfwidth(cleaned)
        
        # 4. 去除多余换行
        cleaned = self._remove_extra_newlines(cleaned)
        
        # 5. 去除首尾空白
        cleaned = cleaned.strip()
        
        logger.debug(f"文本清洗完成：原始长度={original_length}, 清洗后长度={len(cleaned)}")
        
        return cleaned
    
    def _remove_control_chars(self, text: str) -> str:
        """
        去除控制字符，保留换行符和制表符
        
        :param text: 文本
        :return: 处理后的文本
        """
        # 保留 \n 和 \t，移除其他控制字符
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        规范化空白字符
        
        :param text: 文本
        :return: 处理后的文本
        """
        # 将连续的空白字符（空格、制表符、全角空格等）转换为单个空格
        # 但保留换行符
        result = []
        i = 0
        n = len(text)
        
        while i < n:
            if text[i] == '\n':
                # 保留换行符
                result.append('\n')
                i += 1
            elif text[i].isspace() or ord(text[i]) in [0x00a0, 0x3000] or (0x2000 <= ord(text[i]) <= 0x200b):
                # 连续空白字符合并为单个空格
                result.append(' ')
                i += 1
                while i < n and (text[i].isspace() or ord(text[i]) in [0x00a0, 0x3000] or (0x2000 <= ord(text[i]) <= 0x200b)):
                    if text[i] == '\n':
                        break
                    i += 1
            else:
                result.append(text[i])
                i += 1
        
        return ''.join(result)
    
    def _fullwidth_to_halfwidth(self, text: str) -> str:
        """
        将全角字符转换为半角字符
        
        :param text: 文本
        :return: 处理后的文本
        """
        result = []
        for char in text:
            code = ord(char)
            # 全角空格
            if code == 0x3000:
                result.append(' ')
            # 其他全角字符（ASCII范围内）
            elif 0xFF01 <= code <= 0xFF5E:
                result.append(chr(code - 0xFEE0))
            else:
                result.append(char)
        return ''.join(result)
    
    def _remove_extra_newlines(self, text: str) -> str:
        """
        去除多余换行（连续多个换行变为两个）
        
        :param text: 文本
        :return: 处理后的文本
        """
        return re.sub(r'\n{3,}', '\n\n', text)

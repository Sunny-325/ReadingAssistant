#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件服务
"""

import os
import re
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
            elif ext == '.epub':
                # 读取EPUB文件
                try:
                    from ebooklib import epub
                    from ebooklib.epub import EpubHtml
                    book = epub.read_epub(file_path)
                    content = ""
                    html_items_count = 0
                    total_items_count = 0
                    
                    logger.info(f"EPUB文件开始处理: 书名={book.get_metadata('DC', 'title')}, 总项目数={len(list(book.get_items()))}")
                    
                    # 遍历所有项目，提取HTML内容
                    for item in book.get_items():
                        total_items_count += 1
                        
                        # 使用多种条件判断是否为HTML内容
                        is_html = False
                        
                        # 方法1: 检查是否是EpubHtml类型
                        if isinstance(item, EpubHtml):
                            is_html = True
                        
                        # 方法2: 检查media_type
                        if not is_html and hasattr(item, 'media_type'):
                            if 'html' in item.media_type.lower() or 'xhtml' in item.media_type.lower():
                                is_html = True
                        
                        # 方法3: 检查文件扩展名
                        if not is_html and hasattr(item, 'get_name'):
                            name = item.get_name().lower()
                            if name.endswith(('.html', '.xhtml', '.htm')):
                                is_html = True
                        
                        if is_html:
                            html_items_count += 1
                            try:
                                # 获取章节内容
                                html_content = item.get_content().decode('utf-8', errors='ignore')
                                logger.debug(f"EPUB章节 {item.id}: 原始HTML长度={len(html_content)}")
                                
                                # 提取纯文本并清理
                                text = self._clean_epub_content(html_content)
                                logger.debug(f"EPUB章节 {item.id}: 清理后文本长度={len(text)}")
                                if text:
                                    content += text + "\n\n"
                            except Exception as e:
                                logger.warning(f"解析EPUB章节 {item.id} 失败: {e}")
                                continue
                    
                    logger.info(f"EPUB文件处理完成: 总项目数={total_items_count}, 发现 {html_items_count} 个HTML项目，合并后内容长度={len(content)}")
                    
                    # 如果内容为空，尝试备用解析方法
                    if not content.strip():
                        logger.warning("EPUB文件内容为空，尝试备用解析方法")
                        content = self._parse_epub_fallback(book)
                    
                    # 清理最终内容
                    content = self._clean_final_content(content)
                    logger.info(f"EPUB文件清理后内容长度={len(content)}")
                    
                except Exception as e:
                    logger.error(f"读取EPUB文件失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
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
    
    def _clean_epub_content(self, html_content: str) -> str:
        """
        清理EPUB章节内容，提取纯文本
        
        :param html_content: HTML内容
        :return: 清理后的纯文本
        """
        import re
        from bs4 import BeautifulSoup
        
        if not html_content or not html_content.strip():
            return ""
        
        try:
            # 移除脚本和样式
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除导航、页眉、页脚等非正文内容
            for tag in soup(['nav', 'header', 'footer', 'aside', 'figure', 'figcaption', 'script', 'style']):
                tag.decompose()
            
            # 尝试找到主要内容区域
            main_content = None
            
            # 优先查找 article, main, section 标签
            for tag_name in ['article', 'main']:
                tag = soup.find(tag_name)
                if tag:
                    main_content = tag
                    break
            
            # 如果没有找到，查找 class 包含 content/body/text 的 div
            if not main_content:
                for div in soup.find_all('div'):
                    classes = div.get('class', [])
                    if any(c in str(classes).lower() for c in ['content', 'body', 'text', 'chapter']):
                        main_content = div
                        break
            
            # 如果还是没找到，使用整个 soup
            if not main_content:
                main_content = soup
            
            # 获取纯文本，保持段落结构
            text_parts = []
            for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span']):
                element_text = element.get_text(strip=True)
                if element_text:
                    text_parts.append(element_text)
            
            # 如果没有找到结构化元素，直接获取文本
            if not text_parts:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = '\n'.join(text_parts)
            
            # 清理多余的空白字符
            text = re.sub(r'[ \t]+', ' ', text)  # 合并空格和制表符
            text = re.sub(r'\n\s*\n', '\n\n', text)  # 合并空行
            text = text.strip()
            
            return text
        except Exception as e:
            logger.warning(f"清理EPUB内容失败: {e}")
            return ""
    
    def _parse_epub_fallback(self, book) -> str:
        """
        备用EPUB解析方法，当标准方法失败时使用
        
        :param book: EPUB书籍对象
        :return: 解析后的文本内容
        """
        import re
        from bs4 import BeautifulSoup
        
        content = ""
        
        try:
            # 尝试获取所有文档项
            for item in book.get_items():
                try:
                    # 检查是否有get_content方法
                    if hasattr(item, 'get_content'):
                        raw_content = item.get_content()
                        if raw_content:
                            # 尝试解码
                            try:
                                html_content = raw_content.decode('utf-8', errors='ignore')
                            except:
                                continue
                            
                            # 检查是否是HTML或XML内容
                            if any(keyword in html_content.lower() for keyword in ['<html', '<body', '<div', '<p', '<?xml']):
                                # 使用BeautifulSoup提取文本
                                soup = BeautifulSoup(html_content, 'html.parser')
                                text = soup.get_text(separator='\n', strip=True)
                                
                                # 清理文本
                                text = re.sub(r'\s+', ' ', text).strip()
                                if len(text) > 10:  # 只保留有意义的内容
                                    content += text + "\n\n"
                except Exception as e:
                    logger.debug(f"解析EPUB项目失败: {e}")
                    continue
            
            logger.info(f"备用解析方法完成: 内容长度={len(content)}")
            
        except Exception as e:
            logger.error(f"备用EPUB解析失败: {e}")
        
        return content
    
    def _clean_final_content(self, content: str) -> str:
        """
        清理最终内容，移除出版社版权等信息和目录
        
        :param content: 原始内容
        :return: 清理后的内容
        """
        import re
        
        # 首先按段落分割（双换行符）
        paragraphs = re.split(r'\n\s*\n', content)
        
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            
            if not paragraph:
                continue
            
            # 检查是否是版权/出版信息段落
            if self._is_copyright_or_publish_info(paragraph):
                continue
            
            # 检查是否是目录段落
            if self._is_table_of_contents(paragraph):
                continue
            
            # 保留该段落
            cleaned_paragraphs.append(paragraph)
        
        # 合并段落
        result = '\n\n'.join(cleaned_paragraphs)
        
        # 进一步清理：移除连续的空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    def _is_copyright_or_publish_info(self, text: str) -> bool:
        """
        判断文本是否是版权或出版信息
        
        :param text: 待检查的文本
        :return: 是否是版权/出版信息
        """
        # 版权相关关键词
        copyright_keywords = [
            r'图书在版编目',
            r'CIP数据',
            r'ISBN',
            r'版权所有',
            r'©',
            r'All rights reserved',
            r'中国版本图书馆',
            r'核字',
            r'书名原文',
            r'Original English',
            r'Simplified Chinese translation',
            r'translation edition',
            r'策划推广',
            r'出版发行',
            r'中信出版社官网',
            r'官方微博',
            r'中信飞书',
            r'中信电子书',
            r'责任编辑',
            r'装帧设计',
            r'定价',
            r'版次',
            r'印次',
            r'字数',
            r'开本',
            r'印张',
        ]
        
        # 如果包含多个版权关键词，则认为是版权信息
        match_count = 0
        for pattern in copyright_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                match_count += 1
        
        # 如果匹配到2个或以上关键词，或者文本很短且包含关键标识
        if match_count >= 2:
            return True
        
        if match_count >= 1 and len(text) < 200:
            return True
        
        return False
    
    def _is_table_of_contents(self, text: str) -> bool:
        """
        判断文本是否是目录内容
        
        :param text: 待检查的文本
        :return: 是否是目录
        """
        # 目录特征模式
        toc_patterns = [
            r'^目录\s*$',  # 单独的"目录"标题
            r'^(导读|序言|前言|引言)\s*$',  # 单独的章节名
            r'^(第[一二三四五六七八九十百千万\d]+[章回节篇部])',  # 以章节开头
            r'^\d+\s+[一二三四五六七八九十]',  # 数字+中文序号
            r'^[一二三四五六七八九十]+\s+[^\u4e00-\u9fff]{0,20}$',  # 中文序号+短文本
        ]
        
        # 如果是单行且匹配目录模式
        lines = text.split('\n')
        if len(lines) == 1:
            line = lines[0].strip()
            for pattern in toc_patterns:
                if re.match(pattern, line):
                    return True
        
        # 如果包含多个章节标题（每行都很短且有章节特征）
        if len(lines) > 1:
            short_lines_with_chapter = 0
            for line in lines:
                line = line.strip()
                if len(line) < 50 and re.match(r'^(第[一二三四五六七八九十百千万\d]+[章回节篇部]|^\d+\.)', line):
                    short_lines_with_chapter += 1
            
            # 如果超过一半的行是短章节标题
            if short_lines_with_chapter > len(lines) / 2:
                return True
        
        return False
    
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

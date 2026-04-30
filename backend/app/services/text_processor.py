#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理器
实现12项核心阅读辅助功能
"""

import logging
import jieba
import jieba.posseg as pseg
from typing import Dict, List, Tuple, Optional, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TextProcessor:
    """
    文本处理器类，实现12项核心阅读辅助功能
    """
    
    def __init__(self, model_manager):
        """
        初始化文本处理器
        
        :param model_manager: 模型管理器实例
        """
        self.model_manager = model_manager
        
        # 初始化jieba分词
        jieba.initialize()
        
        # 词性映射表
        self.pos_map = {
            'n': '名词', 'v': '动词', 'a': '形容词', 'd': '副词',
            'p': '介词', 'c': '连词', 'u': '助词', 'r': '代词',
            'm': '数词', 'q': '量词', 't': '时间词', 's': '处所词',
            'f': '方位词', 'b': '区别词', 'z': '状态词', 'e': '叹词',
            'y': '语气词', 'o': '拟声词', 'h': '前缀', 'k': '后缀',
            'x': '标点符号', 'w': '其他'
        }
        
        # 缓存清理
        self._cache = {}
        self._max_cache_size = 100
    
    async def process_text(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理文本，根据选项应用各种功能
        
        :param text: 原始文本
        :param options: 处理选项
        :return: 处理后的文本和元数据
        """
        import time
        total_start_time = time.time()
        
        logger.info(f"开始处理文本，长度: {len(text)}")
        logger.info(f"处理选项: {options}")
        
        # 检查文本长度
        if len(text) > 1000:
            logger.info(f"处理长文本，长度: {len(text)}，将进行分块处理")
            # 长文本分块处理
            result = await self._process_long_text(text, options)
        else:
            # 短文本直接处理
            result = self._process_short_text(text, options)
        
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        # 添加处理时间信息
        result["metadata"]["total_processing_time"] = round(total_duration, 2)
        result["metadata"]["processing_time_ms"] = round(total_duration * 1000, 0)
        result["metadata"]["text_length"] = len(text)
        result["metadata"]["processed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"文本处理完成，总耗时: {total_duration:.2f}秒，结果包含: {list(result.keys())}")
        logger.info(f"处理速率: {len(text)/total_duration:.1f} 字符/秒")
        
        return result
    
    def _process_short_text(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理短文本（小于等于1000字）
        
        :param text: 原始文本
        :param options: 处理选项
        :return: 处理结果
        """
        # 检查缓存
        cache_key = f"process_{hash(text)}_{hash(str(options))}"
        if cache_key in self._cache:
            logger.info(f"从缓存获取处理结果")
            return self._cache[cache_key]
        
        result = {
            "original_text": text,
            "processed_text": text,
            "simplifiedContent": None,  # 初始化为 None，只有在启用文本简化时才设置
            "segments": [],
            "metadata": {},
            "simplified_segments": [],
            "simplified_pos_tags": []
        }
        
        # 1. 意群划分
        if options.get("enableChunk", False):
            chunk_level = options.get("chunkLevel", 2)  # 1=轻度, 2=中度, 3=高度
            result["segments"] = self.segment_text(text, {"chunk_level": chunk_level})
        elif options.get("segmentation", False):
            # 兼容旧格式
            result["segments"] = self.segment_text(text, options.get("segmentation_params", {}))
        
        # 2. 主次内容区分
        if options.get("enableMainContent", False):
            # 如果没有segments，生成默认的segments
            if not result["segments"]:
                result["segments"] = self.segment_text(text, {"chunk_level": 2})  # 使用中度划分作为默认
            result = self.prioritize_content(result, options.get("mainContent_params", {}))
        elif options.get("content_prioritization", False):
            # 兼容旧格式
            # 如果没有segments，生成默认的segments
            if not result["segments"]:
                result["segments"] = self.segment_text(text, {})  # 使用默认参数
            result = self.prioritize_content(result, options.get("prioritization_params", {}))
        
        # 3. 文本简化
        if options.get("enableSimplify", False):
            # 保存原始处理后的文本
            original_processed = result["processed_text"]
            # 获取简化级别，默认为1（轻度简化）
            simplify_level = options.get("simplifyLevel", 1)
            logger.info(f"文本简化级别: {simplify_level}")
            # 简化文本并单独存储
            simplifiedContent = self.simplify_text(original_processed, simplify_level)
            result["simplifiedContent"] = simplifiedContent
            
            # 为简化文本生成独立的segments和pos_tags（只有启用了意群划分时）
            if options.get("enableChunk", False):
                try:
                    # 为简化文本进行意群划分
                    simplified_segments = self.segment_text(result["simplifiedContent"], {"chunk_level": options.get("chunkLevel", 2)})
                    result["simplified_segments"] = simplified_segments
                    
                    # 为简化文本进行词性标注
                    result["simplified_pos_tags"] = self.tag_pos(result["simplifiedContent"])
                    
                    logger.info(f"简化文本处理完成：segments={len(result['simplified_segments'])}, pos_tags={len(result['simplified_pos_tags'])}")
                except Exception as e:
                    logger.error(f"简化文本的segments和pos_tags生成失败: {e}")
                    result["simplified_segments"] = []
                    result["simplified_pos_tags"] = []
            else:
                # 如果没有启用意群划分，清空简化文本的segments
                result["simplified_segments"] = []
                result["simplified_pos_tags"] = []
        elif options.get("simplification", False):
            # 兼容旧格式
            # 保存原始处理后的文本
            original_processed = result["processed_text"]
            # 获取简化级别，默认为1（轻度简化）
            simplify_level = options.get("simplifyLevel", 1)
            logger.info(f"文本简化级别（旧格式）: {simplify_level}")
            # 简化文本并单独存储
            simplifiedContent = self.simplify_text(original_processed, simplify_level)
            result["simplifiedContent"] = simplifiedContent
            # 确保即使简化失败也有合理的返回值
            if result["simplifiedContent"] == original_processed:
                # 如果简化后的文本与原始文本相同，尝试使用更简单的方法
                try:
                    prompt = f"请用更简单的语言重新表达以下内容，保持原意但更易懂：\n\n{original_processed}"
                    simpler_response = self.model_manager.generate_text(prompt, max_length=1024)
                    if simpler_response and simpler_response != original_processed:
                        result["simplifiedContent"] = simpler_response
                except Exception as e:
                    logger.error(f"二次文本简化失败: {e}")
            
            # 为简化文本生成独立的segments和pos_tags
            # 只有当启用了意群划分或主次内容区分时才处理
            if options.get("segmentation", False) or options.get("content_prioritization", False):
                try:
                    # 为简化文本进行意群划分
                    simplified_segments = self.segment_text(result["simplifiedContent"], {})
                    result["simplified_segments"] = simplified_segments
                    
                    # 为简化文本进行主次内容区分
                    if options.get("content_prioritization", False):
                        simplified_result = {
                            "processed_text": result["simplifiedContent"],
                            "segments": simplified_segments
                        }
                        simplified_result = self.prioritize_content(simplified_result, {})
                        result["simplified_segments"] = simplified_result["segments"]
                    
                    # 为简化文本进行词性标注
                    result["simplified_pos_tags"] = self.tag_pos(result["simplifiedContent"])
                    
                    logger.info(f"简化文本处理完成：segments={len(result['simplified_segments'])}, pos_tags={len(result['simplified_pos_tags'])}")
                except Exception as e:
                    logger.error(f"简化文本的segments和pos_tags生成失败: {e}")
                    result["simplified_segments"] = []
                    result["simplified_pos_tags"] = []
            else:
                # 如果没有启用意群划分，清空简化文本的segments
                result["simplified_segments"] = []
        
        # 清理缓存
        self._cleanup_cache()
        
        # 4. 词性标注 - 原始文本
        if options.get("pos_tagging", False):
            result["metadata"]["pos_tags"] = self.tag_pos(result["processed_text"])
            # 同时存储在顶层，方便前端访问
            result["pos_tags"] = result["metadata"]["pos_tags"]
            
            # 为简化文本生成词性标注（如果有简化文本）
            if result.get("simplifiedContent"):
                try:
                    result["simplified_pos_tags"] = self.tag_pos(result["simplifiedContent"])
                    logger.info(f"简化文本词性标注完成：pos_tags={len(result['simplified_pos_tags'])}")
                except Exception as e:
                    logger.error(f"简化文本词性标注失败: {e}")
                    result["simplified_pos_tags"] = []
            else:
                result["simplified_pos_tags"] = []
        
        # 缓存结果
        self._cache[cache_key] = result
        
        return result
    
    async def _process_long_text(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理长文本（大于1000字）
        
        :param text: 原始文本
        :param options: 处理选项
        :return: 处理结果
        """
        # 检查缓存
        cache_key = f"long_text_{hash(text)}_{hash(str(options))}"
        if cache_key in self._cache:
            logger.info(f"从缓存获取长文本处理结果")
            return self._cache[cache_key]
        
        result = {
            "original_text": text,
            "processed_text": text,
            "simplifiedContent": None,  # 初始化为 None，只有在启用文本简化时才设置
            "segments": [],
            "metadata": {
                "is_long_text": True,
                "chunk_count": 0
            },
            "simplified_segments": [],
            "simplified_pos_tags": []
        }
        
        try:
            # 基于句子边界分块，确保意群不被分割
            import re
            # 使用正则表达式分割句子，保留分隔符
            sentence_pattern = r'([。！？.!?])'
            parts = re.split(sentence_pattern, text)
            sentences = []
            for i in range(0, len(parts), 2):
                sentence = parts[i]
                if i + 1 < len(parts):
                    sentence += parts[i + 1]
                if sentence:
                    sentences.append(sentence)
            
            # 重新组合句子，确保每个块大小适中
            # 分块大小设置为1200字符，确保提示词总长度控制在2000字符以内
            chunks = []
            current_chunk = ""
            chunk_size = 1200  # 控制分块大小，确保提示词不会过长
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= chunk_size:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk)
            
            result["metadata"]["chunk_count"] = len(chunks)
            
            logger.info(f"将长文本分为 {len(chunks)} 块，基于句子边界")
            
            # 处理每块文本
            all_segments = []
            all_simplified_chunks = []
            
            # 准备处理任务
            import asyncio
            chunk_tasks = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"准备处理第 {i+1} 块文本，长度: {len(chunk)}")
                
                # 处理当前块
                chunk_options = options.copy()
                # 保持所有原始设置
                chunk_options["pos_tagging"] = options.get("pos_tagging", False)
                chunk_options["enableMainContent"] = options.get("enableMainContent", False)
                chunk_options["enableSimplify"] = options.get("enableSimplify", False)
                chunk_options["enableChunk"] = options.get("enableChunk", True)
                chunk_options["chunkLevel"] = options.get("chunkLevel", 2)  # 1=轻度, 2=中度, 3=高度
                
                # 创建处理任务
                async def process_chunk(i, chunk, chunk_options):
                    chunk_result = self._process_short_text(chunk, chunk_options)
                    return i, chunk_result
                
                chunk_tasks.append(process_chunk(i, chunk, chunk_options))
            
            # 并行处理所有块
            if chunk_tasks:
                logger.info(f"开始并行处理 {len(chunk_tasks)} 个文本块")
                results = await asyncio.gather(*chunk_tasks)
                
                # 按块顺序处理结果
                for i, chunk_result in sorted(results, key=lambda x: x[0]):
                    # 收集意群结果
                    if chunk_result["segments"]:
                        # 调整segments的start_pos和end_pos
                        for segment in chunk_result["segments"]:
                            # 计算实际位置
                            if i == 0:
                                start_pos = segment["start_pos"]
                                end_pos = segment["end_pos"]
                            else:
                                # 计算前面所有块的长度总和
                                prev_length = sum(len(chunks[j]) for j in range(i))
                                start_pos = prev_length + segment["start_pos"]
                                end_pos = prev_length + segment["end_pos"]
                            
                            segment["start_pos"] = start_pos
                            segment["end_pos"] = end_pos
                            segment["id"] = len(all_segments) + 1
                            all_segments.append(segment)
                    
                    # 收集简化文本
                    if options.get("enableSimplify", False) and chunk_result.get("simplifiedContent"):
                        all_simplified_chunks.append(chunk_result["simplifiedContent"])
            
            # 合并结果
            result["segments"] = all_segments
            
            # 合并简化文本
            if options.get("enableSimplify", False) and all_simplified_chunks:
                # 合并简化文本，处理标点符号
                simplified_content = ""
                for i, chunk in enumerate(all_simplified_chunks):
                    if chunk:
                        # 确保每个块以标点符号结尾
                        if not re.search(r'[。！？.!?]$', chunk):
                            chunk += "。"
                        simplified_content += chunk
                
                result["simplifiedContent"] = simplified_content
                
                # 为合并后的简化文本生成segments
                try:
                    simplified_segments = self.segment_text(result["simplifiedContent"], {"chunk_level": options.get("chunkLevel", 2)})
                    result["simplified_segments"] = simplified_segments
                    
                    # 为简化文本进行主次内容区分
                    if options.get("enableMainContent", False):
                        simplified_result = {
                            "processed_text": result["simplifiedContent"],
                            "segments": simplified_segments
                        }
                        simplified_result = self.prioritize_content(simplified_result, {})
                        result["simplified_segments"] = simplified_result["segments"]
                    
                    logger.info(f"简化文本处理完成：segments={len(result['simplified_segments'])}")
                except Exception as e:
                    logger.error(f"简化文本的segments生成失败: {e}")
                    result["simplified_segments"] = []
            
            # 词性标注 - 原始文本
            if options.get("pos_tagging", False):
                result["pos_tags"] = self.tag_pos(text)
                
                # 为简化文本生成词性标注（如果有简化文本）
                if result.get("simplifiedContent"):
                    try:
                        result["simplified_pos_tags"] = self.tag_pos(result["simplifiedContent"])
                        logger.info(f"简化文本词性标注完成：pos_tags={len(result['simplified_pos_tags'])}")
                    except Exception as e:
                        logger.error(f"简化文本词性标注失败: {e}")
                        result["simplified_pos_tags"] = []
                else:
                    result["simplified_pos_tags"] = []
            
            # 缓存结果
            self._cache[cache_key] = result
            
            logger.info(f"长文本处理完成，长度: {len(text)}, 生成 {len(all_segments)} 个意群")
            logger.info(f"文本处理完成，结果包含: {list(result.keys())}")
            
        except Exception as e:
            logger.error(f"长文本处理失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result["metadata"]["error"] = str(e)
        
        return result
    
    def segment_text(self, text: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        意群划分
        
        :param text: 原始文本
        :param params: 划分参数，包含chunk_level（划分程度：1=轻度, 2=中度, 3=高度）
        :return: 划分后的意群列表
        """
        segments = []
        
        try:
            chunk_level = params.get("chunk_level", 2)  # 1=轻度, 2=中度, 3=高度
            
            # 将划分程度转换为描述和词语数量参考
            # 调整后的粒度：更细的划分
            level_descriptions = {
                1: ("轻度划分", "意群较大，约6-7个词语，适合快速阅读", 7),
                2: ("中度划分", "意群适中，约3-4个词语，平衡阅读", 4),
                3: ("高度划分", "意群较小，约1-3个词语，适合细致阅读", 3)
            }
            level_name, level_desc, chunk_size = level_descriptions.get(chunk_level, level_descriptions[2])
            
            # 检查缓存
            cache_key = f"segment_{hash(text)}_{chunk_level}"
            if cache_key in self._cache:
                logger.info(f"从缓存获取意群划分结果")
                return self._cache[cache_key]
            
            # 根据chunk_level动态设置提示词中的划分粒度
            level_prompts = {
                1: "轻度划分，每意群约6-7个词，适合快速阅读",
                2: "中等划分，每意群约3-5个词，平衡阅读",
                3: "高度划分，每意群约1-3个词，适合细致阅读"
            }
            level_prompt = level_prompts.get(chunk_level, level_prompts[2])
            
            # 精简的提示词：只包含必要规则
            prompt = f"""将以下文本按语义划分为意群，每个意群占一行。

规则：
1. 语义连贯优先，主谓/动宾结构不拆分
2. 保留所有标点符号
3. 短句保持完整，不强行拆分
4. {level_prompt}

文本：
{text}

=== 严格输出要求 ===
- 【强制】仅输出划分结果，不输出任何其他内容
- 【禁止】不要输出解释、说明、思考过程、开场白、结束语
- 【禁止】不要输出"好的"、"以下是"、"划分结果"、"完成"等任何前缀或后缀文字
- 【禁止】不要添加任何额外注释或标记
- 【格式】每行一个意群，直接输出文字内容，无编号、无序号

输出："""
            
            response = self.model_manager.generate_text(prompt, max_length=4096, temperature=0.2)
            
            if response:
                # 解析模型输出
                # 记录当前在原始文本中的位置
                current_pos = 0
                
                # 过滤掉模型的解释性文字，只保留实际的意群
                import re
                # 移除可能的HTML标签
                response = re.sub(r'<[^>]+>', '', response)
                
                # 过滤掉解释性文字和规则说明
                # 查找"划分结果"或"结果："之后的内容
                result_start = response.find("划分结果")
                if result_start == -1:
                    result_start = response.find("结果：")
                if result_start == -1:
                    result_start = response.find("结果:")
                if result_start != -1:
                    response = response[result_start:]
                
                # 按行分割
                lines = response.split('\n')
                valid_segments = []
                
                # 定义需要过滤的关键词
                filter_prefixes = [
                    '好的', '以下是', '划分结果', '分析：', '示例', '【', '根据',
                    '规则', '要求', '原则', '关键', '正确', '错误', '语义', '连贯性',
                    '主谓', '动宾', '划分程度', '处理结果', '总结：', '说明：',
                    '返回', '输出', '完成', '处理中', '正在', '开始', '结束',
                    '不要输出', '等前缀', '每行一个意群', '直接输出', '文字即可',
                    '重要：', '输出格式', '仅输出', '不要输出', '不要包含'
                ]
                
                for line in lines:
                    line = line.strip()
                    if line:
                        # 过滤掉解释性文字
                        is_filtered = False
                        
                        # 检查行是否以过滤前缀开头
                        for prefix in filter_prefixes:
                            if line.startswith(prefix):
                                is_filtered = True
                                break
                        
                        # 如果还没被过滤，检查行是否包含这些关键词（处理引号包围的情况）
                        if not is_filtered:
                            filter_keywords = [
                                '不要输出', '等前缀', '每行一个意群', '直接输出',
                                '文字即可', '输出格式', '仅输出', '重要：', '不要包含'
                            ]
                            for keyword in filter_keywords:
                                if keyword in line:
                                    is_filtered = True
                                    break
                        
                        # 过滤只包含特殊字符的行
                        if re.match(r'^[*#=-_~`]+$', line):
                            is_filtered = True
                        
                        # 过滤只有数字和标点的行
                        if re.match(r'^\d*[。，！？；：、]*$', line):
                            is_filtered = True
                        
                        if not is_filtered:
                            # 移除可能的序号前缀，如"1. "、"2. "、"①"等
                            line = re.sub(r'^\d+\.\s*', '', line)
                            line = re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩]+[\s.]*', '', line)
                            line = re.sub(r'^[-•●○◆◇■□▲△▼▽]+[\s]*', '', line)
                            
                            # 移除首尾的引号
                            line = re.sub(r'^["\']+', '', line)
                            line = re.sub(r'["\']+$', '', line)
                            
                            if line.strip():
                                valid_segments.append(line)
                
                for i, segment in enumerate(valid_segments):
                        
                        # 只去除首尾空白，保留内部所有字符
                        clean_segment = segment.strip()
                        
                        # 处理只包含标点符号的意群
                        if re.match(r'^[，。！？；：、]+$', clean_segment):
                            logger.debug(f"处理只包含标点符号的意群: {clean_segment}")
                            if segments:
                                # 与前一个意群合并
                                last_segment = segments[-1]
                                # 检查前一个意群是否已经以标点符号结尾
                                if not re.search(r'[，。！？；：、]$', last_segment["text"]):
                                    merged_text = last_segment["text"] + clean_segment
                                    # 更新前一个意群
                                    segments[-1]["text"] = merged_text
                                    segments[-1]["end_pos"] = current_pos + len(clean_segment)
                            current_pos += len(clean_segment)
                            continue
                        
                        # 处理以标点符号开头的意群
                        if re.match(r'^[，。！？；：、]', clean_segment):
                            logger.debug(f"处理以标点符号开头的意群: {clean_segment}")
                            if segments:
                                # 与前一个意群合并
                                last_segment = segments[-1]
                                # 检查前一个意群是否已经以标点符号结尾
                                if not re.search(r'[，。！？；：、]$', last_segment["text"]):
                                    merged_text = last_segment["text"] + clean_segment
                                    # 更新前一个意群
                                    segments[-1]["text"] = merged_text
                                    segments[-1]["end_pos"] = current_pos + len(clean_segment)
                            else:
                                # 如果是第一个意群，保留标点符号
                                # 使用记录的位置，而不是find方法
                                start_pos = current_pos
                                end_pos = current_pos + len(clean_segment)
                                current_pos = end_pos
                                
                                segments.append({
                                    "id": len(segments) + 1,
                                    "text": clean_segment,  # 保留标点符号
                                    "start_pos": start_pos,
                                    "end_pos": end_pos,
                                    "importance": 1.0  # 默认重要性
                                })
                            current_pos += len(clean_segment)
                            continue
                        
                        # 检查意群的词语数是否符合要求
                        # 计算词语数（使用jieba分词）
                        words = list(jieba.cut(clean_segment))
                        # 过滤标点符号
                        actual_words = [word for word in words if word not in [',', '，', ';', '；', ':', '：', '。', '！', '？']]
                        word_count = len(actual_words)
                        
                        # 根据划分程度检查词语数
                        max_words = 9 if chunk_level == 1 else (6 if chunk_level == 2 else 5)
                        
                        if word_count > max_words:
                            logger.debug(f"意群词语数超过限制（{word_count} > {max_words}），使用基于规则的划分")
                            # 使用基于规则的划分重新处理这个意群
                            # 按chunk_size划分
                            current_sub_chunk = []
                            current_sub_length = 0
                            sub_chunk_start_pos = current_pos
                            
                            for word in words:
                                current_sub_chunk.append(word)
                                # 只计算实际词语的数量
                                if word not in [',', '，', ';', '；', ':', '：', '。', '！', '？']:
                                    current_sub_length += 1
                                current_pos += len(word)
                                
                                # 当达到或超过chunk_size时划分
                                if current_sub_length >= chunk_size:
                                    # 确保在标点处划分
                                    if word in [',', '，', ';', '；', ':', '：', '。', '！', '？']:
                                        sub_chunk_text = ''.join(current_sub_chunk)
                                        if sub_chunk_text:
                                            start_pos = sub_chunk_start_pos
                                            end_pos = current_pos
                                            
                                            segments.append({
                                                "id": len(segments) + 1,
                                                "text": sub_chunk_text,  # 保留标点符号
                                                "start_pos": start_pos,
                                                "end_pos": end_pos,
                                                "importance": 1.0  # 默认重要性
                                            })
                                            
                                            # 重置子意群
                                            current_sub_chunk = []
                                            current_sub_length = 0
                                            sub_chunk_start_pos = current_pos
                                    elif current_sub_length > chunk_size:
                                        # 强制划分
                                        sub_chunk_text = ''.join(current_sub_chunk)
                                        if sub_chunk_text:
                                            start_pos = sub_chunk_start_pos
                                            end_pos = current_pos
                                            
                                            segments.append({
                                                "id": len(segments) + 1,
                                                "text": sub_chunk_text,  # 保留标点符号
                                                "start_pos": start_pos,
                                                "end_pos": end_pos,
                                                "importance": 1.0  # 默认重要性
                                            })
                                            
                                            # 重置子意群
                                            current_sub_chunk = []
                                            current_sub_length = 0
                                            sub_chunk_start_pos = current_pos
                            
                            # 处理最后一个子意群
                            if current_sub_chunk:
                                sub_chunk_text = ''.join(current_sub_chunk)
                                if sub_chunk_text:
                                    start_pos = sub_chunk_start_pos
                                    end_pos = current_pos
                                    
                                    segments.append({
                                        "id": len(segments) + 1,
                                        "text": sub_chunk_text,  # 保留标点符号
                                        "start_pos": start_pos,
                                        "end_pos": end_pos,
                                        "importance": 1.0  # 默认重要性
                                    })
                        else:
                            # 使用记录的位置，而不是find方法
                            start_pos = current_pos
                            end_pos = current_pos + len(clean_segment)
                            current_pos = end_pos
                            
                            segments.append({
                                "id": len(segments) + 1,
                                "text": clean_segment,  # 使用清理后的文本，确保标点符号完整
                                "start_pos": start_pos,
                                "end_pos": end_pos,
                                "importance": 1.0  # 默认重要性
                            })
            else:
                # 如果模型划分失败，使用基于规则的简单划分
                logger.debug(f"模型划分失败，使用基于规则的简单划分")
                import re
                
                # 首先按句子分割（保留标点符号）
                # 使用正则表达式分割，但保留标点符号
                sentences = re.split(r'([。！？\n])', text)
                
                # 记录当前在原始文本中的位置
                current_pos = 0
                
                # 重新组合句子和标点符号
                i = 0
                while i < len(sentences):
                    if i + 1 < len(sentences) and sentences[i+1] in ['。', '！', '？', '\n']:
                        sentence = sentences[i] + sentences[i+1]
                        i += 2
                    else:
                        sentence = sentences[i]
                        i += 1
                    
                        sentence = sentence.strip()
                        if sentence:
                            # 对每个句子，按chunk_size划分词语
                            words = list(jieba.cut(sentence))
                            
                            # 改进的意群划分逻辑：优先考虑语义连贯性
                            current_chunk = []
                            current_length = 0
                            chunk_start_pos = current_pos
                    
                            # 语义单元边界标记
                            semantic_boundaries = [',', '，', ';', '；', ':', '：', '。', '！', '？']
                                
                            for word in words:
                                current_chunk.append(word)
                                # 只计算实际词语的数量，标点符号不计入词语数
                                if word not in semantic_boundaries:
                                    current_length += 1
                                current_pos += len(word)
                                
                                # 优先在语义边界处划分
                                should_split = False
                                
                                # 1. 如果遇到完整的语义边界（句号、感叹号、问号），强制划分
                                if word in ['。', '！', '？']:
                                    should_split = True
                                # 2. 如果遇到逗号等分隔符，且已经达到合理长度，考虑划分
                                elif word in [',', '，', ';', '；', ':', '：'] and current_length >= chunk_size * 0.8:
                                    should_split = True
                                # 3. 如果词语数超过chunk_size的1.5倍，强制划分
                                elif current_length > chunk_size * 1.5:
                                    # 尝试在最近的标点符号处划分
                                    punctuation_found = False
                                    for j in range(len(current_chunk)-1, -1, -1):
                                        if current_chunk[j] in semantic_boundaries:
                                            # 在标点符号处划分
                                            punctuation_chunk = current_chunk[:j+1]
                                            remaining_chunk = current_chunk[j+1:]
                                            
                                            # 处理标点符号结尾的意群
                                            punctuation_text = ''.join(punctuation_chunk)
                                            if punctuation_text:
                                                start_pos = chunk_start_pos
                                                end_pos = chunk_start_pos + len(punctuation_text)
                                                
                                                segments.append({
                                                    "id": len(segments) + 1,
                                                    "text": punctuation_text,  # 保留标点符号
                                                    "start_pos": start_pos,
                                                    "end_pos": end_pos,
                                                    "importance": 1.0
                                                })
                                            
                                            # 重置当前意群为剩余部分
                                            current_chunk = remaining_chunk
                                            current_length = len([w for w in current_chunk if w not in semantic_boundaries])
                                            chunk_start_pos = end_pos
                                            punctuation_found = True
                                            break
                                
                                    if not punctuation_found:
                                        # 如果没有找到标点符号，强制划分
                                        should_split = True
                            
                                if should_split:
                                    chunk_text = ''.join(current_chunk)
                                    if chunk_text:
                                        # 处理以标点符号开头的意群
                                        if re.match(r'^[，。！？；：、]', chunk_text):
                                            # 如果以标点符号开头，尝试与前一个意群合并
                                            if segments:
                                                last_segment = segments[-1]
                                                # 检查前一个意群是否已经以标点符号结尾
                                                if not re.search(r'[，。！？；：、]$', last_segment["text"]):
                                                    merged_text = last_segment["text"] + chunk_text
                                                    # 更新前一个意群
                                                    segments[-1]["text"] = merged_text
                                                    segments[-1]["end_pos"] = current_pos
                                            else:
                                                # 如果是第一个意群，保留标点符号
                                                start_pos = chunk_start_pos
                                                end_pos = current_pos
                                                
                                                segments.append({
                                                    "id": len(segments) + 1,
                                                    "text": chunk_text,  # 保留标点符号
                                                    "start_pos": start_pos,
                                                    "end_pos": end_pos,
                                                    "importance": 1.0
                                                })
                                        else:
                                            # 使用记录的位置
                                            start_pos = chunk_start_pos
                                            end_pos = current_pos
                                            
                                            segments.append({
                                                "id": len(segments) + 1,
                                                "text": chunk_text,  # 保留标点符号
                                                "start_pos": start_pos,
                                                "end_pos": end_pos,
                                                "importance": 1.0
                                            })
                            
                            # 重置当前意群
                            current_chunk = []
                            current_length = 0
                            chunk_start_pos = current_pos
                            
                            # 处理最后一个意群
                            if current_chunk:
                                chunk_text = ''.join(current_chunk)
                                if chunk_text:
                                    # 处理以标点符号开头的意群
                                    if re.match(r'^[，。！？；：、]', chunk_text):
                                        # 如果以标点符号开头，尝试与前一个意群合并
                                        if segments:
                                            last_segment = segments[-1]
                                            # 检查前一个意群是否已经以标点符号结尾
                                            if not re.search(r'[，。！？；：、]$', last_segment["text"]):
                                                merged_text = last_segment["text"] + chunk_text
                                                # 更新前一个意群
                                                segments[-1]["text"] = merged_text
                                                segments[-1]["end_pos"] = current_pos
                                        else:
                                            # 如果是第一个意群，保留标点符号
                                            # 使用记录的位置，而不是find方法
                                            start_pos = chunk_start_pos
                                            end_pos = current_pos
                                            
                                            segments.append({
                                                "id": len(segments) + 1,
                                                "text": chunk_text,  # 保留标点符号
                                                "start_pos": start_pos,
                                                "end_pos": end_pos,
                                                "importance": 1.0
                                            })
                                    else:
                                        # 使用记录的位置，而不是find方法
                                        start_pos = chunk_start_pos
                                        end_pos = current_pos
                                        
                                        segments.append({
                                            "id": len(segments) + 1,
                                            "text": chunk_text,  # 保留标点符号
                                            "start_pos": start_pos,
                                            "end_pos": end_pos,
                                            "importance": 1.0
                                        })
            
            # 如果模型划分失败，使用基于标点和词语数的简单划分
            if not segments:
                import re
                # 首先按句子分割（保留标点符号）
                # 使用正则表达式分割，但保留标点符号
                sentences = re.split(r'([。！？\n])', text)
                
                # 记录当前在原始文本中的位置
                current_pos = 0
                
                # 重新组合句子和标点符号
                i = 0
                while i < len(sentences):
                    if i + 1 < len(sentences) and sentences[i+1] in ['。', '！', '？', '\n']:
                        sentence = sentences[i] + sentences[i+1]
                        i += 2
                    else:
                        sentence = sentences[i]
                        i += 1
                    
                    sentence = sentence.strip()
                    if sentence:
                        # 对每个句子，按chunk_size划分词语
                        words = list(jieba.cut(sentence))
                        
                        # 改进的意群划分逻辑：考虑语义和标点
                        current_chunk = []
                        current_length = 0
                        chunk_start_pos = current_pos
                        
                        for word in words:
                            current_chunk.append(word)
                            current_length += 1
                            current_pos += len(word)
                            
                            # 当达到chunk_size或者遇到标点时，结束当前意群
                            if current_length >= chunk_size or word in [',', '，', ';', '；', ':', '：']:
                                chunk_text = ''.join(current_chunk)
                                if chunk_text:
                                    # 使用记录的位置，而不是find方法
                                    start_pos = chunk_start_pos
                                    end_pos = current_pos
                                    
                                    segments.append({
                                        "id": len(segments) + 1,
                                        "text": chunk_text,  # 保留标点符号
                                        "start_pos": start_pos,
                                        "end_pos": end_pos,
                                        "importance": 1.0
                                    })
                                    
                                    # 重置当前意群
                                    current_chunk = []
                                    current_length = 0
                                    chunk_start_pos = current_pos
                        
                        # 处理最后一个意群
                        if current_chunk:
                            chunk_text = ''.join(current_chunk)
                            if chunk_text:
                                # 确保意群不以标点符号开头
                                if re.match(r'^[，。！？；：、]', chunk_text):
                                    # 如果以标点符号开头，尝试与前一个意群合并
                                    if segments:
                                        last_segment = segments[-1]
                                        merged_text = last_segment["text"] + chunk_text
                                        # 更新前一个意群
                                        segments[-1]["text"] = merged_text
                                        segments[-1]["end_pos"] = current_pos
                                    else:
                                        # 如果是第一个意群，跳过标点符号
                                        chunk_text = re.sub(r'^[，。！？；：、]+', '', chunk_text)
                                        if chunk_text:
                                            # 使用记录的位置，而不是find方法
                                            start_pos = chunk_start_pos
                                            end_pos = current_pos
                                            
                                            segments.append({
                                                "id": len(segments) + 1,
                                                "text": chunk_text,  # 保留标点符号
                                                "start_pos": start_pos,
                                                "end_pos": end_pos,
                                                "importance": 1.0
                                            })
                                else:
                                    # 使用记录的位置，而不是find方法
                                    start_pos = chunk_start_pos
                                    end_pos = current_pos
                                    
                                    segments.append({
                                        "id": len(segments) + 1,
                                        "text": chunk_text,  # 保留标点符号
                                        "start_pos": start_pos,
                                        "end_pos": end_pos,
                                        "importance": 1.0
                                    })
            
            # 如果还是没有划分结果，使用整个文本作为一个意群
            if not segments:
                segments = [{"id": 1, "text": text, "start_pos": 0, "end_pos": len(text), "importance": 1.0}]
            
        except Exception as e:
            logger.error(f"意群划分失败: {e}")
            # fallback到简单划分
            segments = [{"id": 1, "text": text, "start_pos": 0, "end_pos": len(text), "importance": 1.0}]
        
        return segments
    
    def prioritize_content(self, result: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        主次内容区分
        
        :param result: 当前处理结果
        :param params: 优先级参数
        :return: 更新后的结果
        """
        import json
        import re
        
        text = result["processed_text"]
        segments = result["segments"]
        
        try:
            # 检查缓存
            # 使用params参数构建缓存键，确保不同参数有不同缓存
            cache_key = f"prioritize_{hash(text)}_{hash(str(params))}"
            if cache_key in self._cache:
                logger.info(f"从缓存获取主次内容区分结果")
                result["segments"] = self._cache[cache_key]
                return result
            
            # 使用模型识别主次内容
            # 从params中获取优先级参数
            importance_threshold = params.get("importance_threshold", 0.5)
            min_secondary_ratio = params.get("min_secondary_ratio", 0.3)
            
            # 简化提示词，只传递意群ID和文本，不重复传递完整文本
            # 构建简洁的意群列表
            seg_list = "\n".join([f"{seg['id']}. {seg['text'][:50]}..." if len(seg['text']) > 50 else f"{seg['id']}. {seg['text']}" for seg in segments])
            
            prompt = f"""分析意群重要性。

意群：
{seg_list}

=== 严格输出要求 ===
- 【强制】仅输出JSON格式结果，不输出任何其他内容
- 【禁止】不要输出解释、说明、思考过程、开场白、结束语
- 【禁止】不要输出"好的"、"以下是"、"分析结果"、"完成"等任何前缀或后缀文字
- 【禁止】不要添加任何额外注释或标记
- 【格式】严格按照示例格式输出：{{"segments":[{{"id":数字,"importance":0-1之间的小数}}]}}

输出："""
            
            response = self.model_manager.generate_text(prompt, max_length=2048, temperature=0.3)
            
            if response:
                # 尝试从响应中提取JSON
                
                # 移除可能的HTML标签
                response = re.sub(r'<[^>]+>', '', response)
                
                # 记录原始响应长度，用于调试
                logger.debug(f"模型响应长度: {len(response)} 字符")
                
                # 尝试多种方法解析JSON
                parsed_success = False
                
                # 方法1：尝试直接解析
                try:
                    prioritized = json.loads(response)
                    if isinstance(prioritized, dict) and "segments" in prioritized:
                        for seg in prioritized["segments"]:
                            for i, segment in enumerate(segments):
                                if segment["id"] == seg["id"]:
                                    segments[i]["importance"] = float(seg["importance"])
                        parsed_success = True
                        logger.info("JSON解析成功（方法1：直接解析）")
                except json.JSONDecodeError as e:
                    logger.warning(f"直接解析JSON失败: {e}")
                
                # 方法2：提取第一个完整的JSON对象
                if not parsed_success:
                    try:
                        # 寻找第一个 { 和对应的闭合 }
                        json_str = self._extract_first_valid_json(response)
                        if json_str:
                            prioritized = json.loads(json_str)
                            if isinstance(prioritized, dict) and "segments" in prioritized:
                                for seg in prioritized["segments"]:
                                    for i, segment in enumerate(segments):
                                        if segment["id"] == seg["id"]:
                                            segments[i]["importance"] = float(seg["importance"])
                                parsed_success = True
                                logger.info("JSON解析成功（方法2：提取完整JSON对象）")
                    except json.JSONDecodeError as e2:
                        logger.warning(f"提取JSON对象失败: {e2}")
                
                # 方法3：尝试按行解析，查找包含id和importance的行
                if not parsed_success:
                    try:
                        self._parse_semi_structured_response(response, segments)
                        parsed_success = True
                        logger.info("JSON解析成功（方法3：半结构化解析）")
                    except Exception as e3:
                        logger.warning(f"半结构化解析失败: {e3}")
                
                if not parsed_success:
                    logger.error(f"所有JSON解析方法均失败，响应片段: {response[:500]}...")
                
                # 确保所有意群都有importance值
                for segment in segments:
                    if "importance" not in segment:
                        # 如果模型没有返回importance，使用默认值
                        segment["importance"] = 1.0
                        logger.warning(f"意群 {segment['id']} 没有获得importance值，使用默认值1.0")
            
            # 计算平均importance值
            total_importance = sum(seg.get("importance", 1.0) for seg in segments)
            avg_importance = total_importance / len(segments) if segments else 1.0
            
            # 优化的主次内容区分算法
            # 1. 先计算所有意群的重要性分布
            importance_values = [seg.get("importance", 1.0) for seg in segments]
            if importance_values:
                import numpy as np
                # 计算标准差，了解重要性分布的离散程度
                std_importance = np.std(importance_values) if len(importance_values) > 1 else 0
                
                # 2. 动态调整阈值，基于重要性分布
                if std_importance < 0.2:  # 分布过于集中
                    # 强制进行更明显的区分
                    sorted_indices = np.argsort(importance_values)
                    # 确保至少有10%的次要内容
                    secondary_count = max(1, int(len(segments) * 0.1))
                    for i in range(secondary_count):
                        if i < len(sorted_indices):
                            segments[sorted_indices[i]]["is_primary"] = False
                    # 确保至少有60%的主要内容
                    primary_count = max(int(len(segments) * 0.6), len(segments) - secondary_count)
                    for i in range(primary_count):
                        if i < len(sorted_indices):
                            segments[sorted_indices[-i-1]]["is_primary"] = True
                else:
                    # 正常情况下使用绝对阈值
                    secondary_count = 0
                    for segment in segments:
                        importance = segment.get("importance", 1.0)
                        if importance < importance_threshold:
                            segment["is_primary"] = False
                            secondary_count += 1
                        else:
                            segment["is_primary"] = True
                    
                    # 确保有足够的次要内容
                    if secondary_count < max(1, int(len(segments) * min_secondary_ratio)):
                        # 按importance排序
                        sorted_segments = sorted(enumerate(segments), key=lambda x: x[1].get("importance", 1.0))
                        # 计算需要额外标记的次要内容数量
                        needed = max(1, int(len(segments) * min_secondary_ratio)) - secondary_count
                        # 标记额外的次要内容
                        for i in range(secondary_count, secondary_count + needed):
                            if i < len(sorted_segments):
                                idx = sorted_segments[i][0]
                                segments[idx]["is_primary"] = False
                                secondary_count += 1
                        logger.info(f"强制标记了{needed}个意群为次要内容")
            else:
                # 如果没有重要性值，全部标记为主要内容
                for segment in segments:
                    segment["is_primary"] = True
            
            # 缓存结果（只缓存segments部分，避免缓存整个result导致字段缺失）
            self._cache[cache_key] = segments
            logger.info(f"主次内容区分完成，平均重要性: {avg_importance:.2f}")
            
        except Exception as e:
            logger.error(f"主次内容区分失败: {e}")
            # 如果失败，设置默认值
            for segment in segments:
                if "importance" not in segment:
                    segment["importance"] = 1.0
                if "is_primary" not in segment:
                    segment["is_primary"] = True
        
        result["segments"] = segments
        return result
    
    def _extract_first_valid_json(self, text):
        """
        从文本中提取第一个完整的JSON对象
        使用括号匹配算法确保提取完整的JSON
        """
        # 找到第一个 { 的位置
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        # 使用括号匹配找到对应的闭合 }
        brace_count = 1
        end_idx = start_idx + 1
        
        while end_idx < len(text) and brace_count > 0:
            if text[end_idx] == '{':
                brace_count += 1
            elif text[end_idx] == '}':
                brace_count -= 1
            end_idx += 1
        
        if brace_count == 0:
            return text[start_idx:end_idx]
        
        return None
    
    def _parse_semi_structured_response(self, response, segments):
        """
        解析半结构化响应，尝试从非标准格式中提取id和importance信息
        """
        import re
        
        # 按行分割
        lines = response.strip().split('\n')
        
        for line in lines:
            # 尝试匹配包含 id 和 importance 的行
            id_match = re.search(r'(?:["\']?id["\']?\s*[:=]\s*)(\d+)', line)
            importance_match = re.search(r'(?:["\']?importance["\']?\s*[:=]\s*)([\d.]+)', line)
            
            if id_match and importance_match:
                try:
                    seg_id = int(id_match.group(1))
                    importance = float(importance_match.group(1))
                    
                    # 更新对应意群的重要性
                    for segment in segments:
                        if segment["id"] == seg_id:
                            segment["importance"] = importance
                            break
                except (ValueError, TypeError):
                    continue
    
    def simplify_text(self, text: str, level: int = 1) -> str:
        """
        文本简化
        
        :param text: 原始文本
        :param level: 简化级别，1=轻度，2=中度，3=深度
        :return: 简化后的文本
        """
        try:
            # 检查缓存
            cache_key = f"simplify_{level}_{hash(text)}"
            if cache_key in self._cache:
                logger.info(f"从缓存获取简化文本")
                return self._cache[cache_key]
            
            # 根据级别生成不同的prompt（精简版）
            level_desc = {
                1: "轻度简化：替换书面语为口语，保持句子结构",
                2: "中度简化：替换复杂词汇，拆分长句，删除冗余",
                3: "深度简化：保留核心信息，所有句子控制在15字以内"
            }
            
            prompt = f"""简化文本{level_desc[level]}，仅输出结果：{text}"""
            
            response = self.model_manager.generate_text(prompt, max_length=2048, temperature=0.3, top_p=0.9)
            
            if response:
                # 清理响应中的多余内容
                simplified = self._clean_simplified_response(response, text)
                
                # 确保简化文本包含适当的标点符号
                import re
                if simplified:
                    if not re.search(r'[。！？.!?]', simplified):
                        # 如果没有标点符号，添加句号
                        simplified += "。"
                    
                    # 缓存结果
                    self._cache[cache_key] = simplified
                    logger.info(f"文本简化成功（级别{level}），原文长度: {len(text)}, 简化后长度: {len(simplified)}")
                    return simplified
            
        except Exception as e:
            logger.error(f"文本简化失败: {e}")
            # 如果简化失败，使用基于规则的简单简化
            try:
                simple_simplified = self._rule_based_simplify(text, level)
                if simple_simplified and simple_simplified != text:
                    logger.info(f"使用基于规则的文本简化作为回退")
                    return simple_simplified
            except Exception as rule_e:
                logger.error(f"基于规则的简化也失败: {rule_e}")
        
        # 如果所有简化方法都失败，返回原文
        logger.warning("所有文本简化方法都失败，返回原文")
        return text
    
    def tag_pos(self, text: str) -> List[Dict[str, Any]]:
        """
        词性标注
        
        :param text: 文本
        :return: 词性标注结果
        """
        pos_tags = []
        
        try:
            # 使用jieba进行词性标注
            words = list(pseg.cut(text))
            
            # 计算每个词的正确位置
            current_pos = 0
            for word, flag in words:
                # 查找当前词在文本中的正确位置
                start_pos = text.find(word, current_pos)
                if start_pos == -1:
                    # 如果找不到，使用当前位置
                    start_pos = current_pos
                
                end_pos = start_pos + len(word)
                
                pos_tags.append({
                    "word": word,
                    "pos": flag,
                    "pos_name": self.pos_map.get(flag, "未知"),
                    "start_pos": start_pos,
                    "end_pos": end_pos
                })
                
                # 更新当前位置
                current_pos = end_pos
        
        except Exception as e:
            logger.error(f"词性标注失败: {e}")
        
        return pos_tags
    
    def get_word_definition(self, word: str, context: str = "") -> Dict[str, Any]:
        """
        获取词语释义
        
        :param word: 词语
        :param context: 上下文
        :return: 词语释义
        """
        definition = {
            "word": word,
            "phonetic": "",
            "definitions": [],
            "examples": []
        }
        
        try:
            # 使用模型获取释义
            prompt = f"解释词语 '{word}' 的含义，包括读音、多个释义和例句。如果提供了上下文，请结合上下文解释：\n\n上下文：{context}"
            response = self.model_manager.generate_text(prompt, max_length=512)
            
            if response:
                # 解析模型输出
                definition["raw_response"] = response
                
                # 简单解析，实际应用中可能需要更复杂的解析
                lines = response.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith("读音："):
                        definition["phonetic"] = line.replace("读音：", "").strip()
                    elif line.startswith("释义："):
                        definition["definitions"].append(line.replace("释义：", "").strip())
                    elif line.startswith("例："):
                        definition["examples"].append(line.replace("例：", "").strip())
        
        except Exception as e:
            logger.error(f"获取词语释义失败: {e}")
        
        return definition
    
    def _cleanup_cache(self):
        """
        清理缓存
        """
        if len(self._cache) > self._max_cache_size:
            # 删除最旧的缓存项
            oldest_keys = list(self._cache.keys())[:len(self._cache) - self._max_cache_size]
            for key in oldest_keys:
                del self._cache[key]
            logger.debug(f"缓存清理完成，当前缓存大小: {len(self._cache)}")
    
    def _clean_simplified_response(self, response: str, original_text: str) -> str:
        """
        清理简化后的响应，移除模型返回的额外内容
        
        :param response: 模型响应
        :param original_text: 原始文本
        :return: 清理后的简化文本
        """
        import re
        
        # 移除常见的前缀短语
        prefixes_to_remove = [
            r'这篇文字可以简化为以下更易懂的版本[：:]',
            r'简化后的文本如下[：:]',
            r'简化结果[：:]',
            r'以下是简化后的内容[：:]',
            r'简化版[：:]',
            r'简化后[：:]',
            r'简化文本[：:]',
            r'简化版本[：:]',
            r'简化[：:]',
            r'简化后的文本[：:]',
            r'结果[：:]',
            r'输出[：:]',
            r'答案[：:]',
        ]
        
        simplified = response
        for prefix in prefixes_to_remove:
            simplified = re.sub(prefix, '', simplified, flags=re.IGNORECASE)
        
        # 移除引号
        if simplified.startswith('"') or simplified.startswith('"') or simplified.startswith('「') or simplified.startswith('『'):
            simplified = simplified[1:]
        if simplified.endswith('"') or simplified.endswith('"') or simplified.endswith('」') or simplified.endswith('』'):
            simplified = simplified[:-1]
        
        # 移除HTML标签
        simplified = re.sub(r'<[^>]+>', '', simplified)
        
        # 只移除前导和尾随空格
        simplified = simplified.strip()
        
        # 确保每个句子都有完整的标点符号结尾
        sentences = re.split(r'([。！？])', simplified)
        result_parts = []
        for i in range(0, len(sentences), 2):
            sentence = sentences[i].strip()
            punctuation = sentences[i+1] if i+1 < len(sentences) else ''
            if sentence:
                if punctuation:
                    result_parts.append(sentence + punctuation)
                else:
                    result_parts.append(sentence + '。')
        simplified = ''.join(result_parts)
        
        # 检查标点符号数量
        original_punctuation_count = len(re.findall(r'[，。！？；：、]', original_text))
        simplified_punctuation_count = len(re.findall(r'[，。！？；：、]', simplified))
        
        if simplified_punctuation_count < original_punctuation_count * 0.7:
            logger.warning(f"简化后标点符号数量过少（原文{original_punctuation_count}个，简化后{simplified_punctuation_count}个）")
            return original_text
        
        return simplified
    
    def _retry_simplify(self, text: str, level: int) -> str:
        """
        重试简化
        
        :param text: 原始文本
        :param level: 简化级别
        :return: 简化后的文本
        """
        if level == 1:
            prompt = f"""请将以下文本进行轻度简化：
要求：替换书面语为口语，保持原意，长度控制在90%以内

原文：{text}

=== 严格输出要求 ===
- 【强制】仅输出简化后的文本内容，不输出任何其他内容
- 【禁止】不要输出解释、说明、思考过程、开场白、结束语
- 【禁止】不要输出"好的"、"以下是"、"简化结果"、"完成"等任何前缀或后缀文字
- 【禁止】不要添加任何额外注释或标记

简化后："""
        elif level == 2:
            prompt = f"""请将以下文本进行中度简化：
要求：拆分长句、删除冗余词、保留核心信息，长度控制在60-70%

原文：{text}

=== 严格输出要求 ===
- 【强制】仅输出简化后的文本内容，不输出任何其他内容
- 【禁止】不要输出解释、说明、思考过程、开场白、结束语
- 【禁止】不要输出"好的"、"以下是"、"简化结果"、"完成"等任何前缀或后缀文字
- 【禁止】不要添加任何额外注释或标记

简化后："""
        else:
            prompt = f"""请将以下文本进行深度简化：
要求：只保留核心信息、句子不超过15字、删除所有修饰语，长度控制在40-50%

原文：{text}

=== 严格输出要求 ===
- 【强制】仅输出简化后的文本内容，不输出任何其他内容
- 【禁止】不要输出解释、说明、思考过程、开场白、结束语
- 【禁止】不要输出"好的"、"以下是"、"简化结果"、"完成"等任何前缀或后缀文字
- 【禁止】不要添加任何额外注释或标记

简化后："""
        
        response = self.model_manager.generate_text(prompt, max_length=512, temperature=0.6, top_p=0.95)
        
        if response:
            return self._clean_simplified_response(response, text)
        
        return ""
    
    def _rule_based_simplify(self, text: str, level: int) -> str:
        """
        基于规则的文本简化
        
        :param text: 原始文本
        :param level: 简化级别
        :return: 简化后的文本
        """
        import re
        
        simple_simplified = text
        
        # 替换复杂词汇为简单词汇
        complex_to_simple = {
            '此外': '另外', '因此': '所以', '然而': '但是', '例如': '比如',
            '与此同时': '同时', '除此之外': '另外', '总而言之': '总之',
            '不仅如此': '不仅', '事实上': '其实', '尽管如此': '虽然',
            '换句话说': '也就是说', '并且': '而且', '因为': '由于',
            '如果': '要是', '但是': '可是', '非常': '很', '特别': '很',
            '极其': '很', '十分': '很', '相当': '很', '较为': '比较',
            '可以': '能', '能够': '能', '需要': '要', '必须': '要',
            '应该': '要', '可能': '也许', '或许': '也许', '大概': '也许',
            '大约': '大概', '几乎': '差不多', '基本': '差不多', '完全': '全部',
            '彻底': '全部', '部分': '一些', '某些': '一些', '许多': '很多',
            '大量': '很多', '少数': '很少', '少量': '很少', '增加': '变多',
            '减少': '变少', '提高': '提升', '降低': '下降', '改善': '变好',
            '恶化': '变差', '发展': '进步', '变化': '改变', '影响': '作用',
            '因素': '原因', '问题': '麻烦', '解决方案': '办法', '措施': '方法',
            '策略': '办法', '计划': '打算', '目标': '目的', '结果': '结果',
            '效果': '结果', '过程': '经过', '步骤': '步骤', '阶段': '阶段',
            '时期': '时候', '时间': '时候', '空间': '地方', '位置': '地方',
            '区域': '地方', '范围': '范围', '领域': '范围', '方面': '方面',
            '角度': '方面', '观点': '想法', '看法': '想法', '意见': '想法',
            '建议': '建议', '方法': '方法', '方式': '方法', '途径': '方法',
            '手段': '方法', '首先': '先', '其次': '然后', '最后': '最后',
            '渐渐地': '慢慢', '迅速地': '快', '缓慢地': '慢', '突然': '忽然',
            '通常': '一般', '一般': '通常', '格外': '很', '尤其': '很',
            '颇为': '很', '甚是': '很', '较为': '较', '比较': '较'
        }
        
        for complex_word, simple_word in complex_to_simple.items():
            simple_simplified = simple_simplified.replace(complex_word, simple_word)
        
        # 移除冗余的修饰词（所有级别都移除）
        redundant_words = ['非常', '极其', '十分', '特别', '格外', '分外', '尤其', '相当', '颇为', '甚是']
        for redundant_word in redundant_words:
            simple_simplified = simple_simplified.replace(redundant_word, '')
        
        # 中度简化：拆分长句子
        if level >= 2:
            # 更多拆分规则
            long_sentence_patterns = [
                (r'(，[^，]{10,20}?)(，此外)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，因此)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，然而)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，例如)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，但是)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，所以)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，而且)', r'\1。\2'),
                (r'(，[^，]{10,20}?)(，同时)', r'\1。\2'),
            ]
            
            for pattern, replacement in long_sentence_patterns:
                simple_simplified = re.sub(pattern, replacement, simple_simplified)
            
            # 移除更多程度副词
            degree_words = ['相当', '十分', '特别', '非常', '极其', '格外', '分外', '甚是', '比较', '较为']
            for word in degree_words:
                simple_simplified = simple_simplified.replace(word, '')
        
        # 深度简化：更激进的处理
        if level >= 3:
            # 删除括号内的内容（通常是解释、例子）
            simple_simplified = re.sub(r'（[^）]*）', '', simple_simplified)
            simple_simplified = re.sub(r'\([^)]*\)', '', simple_simplified)
            
            # 删除"比如"、"例如"后面的内容直到句号
            simple_simplified = re.sub(r'比如[^。]*。', '。', simple_simplified)
            simple_simplified = re.sub(r'例如[^。]*。', '。', simple_simplified)
            
            # 删除引号内的内容
            simple_simplified = re.sub(r'"[^"]*"', '', simple_simplified)
            simple_simplified = re.sub(r'"[^"]*"', '', simple_simplified)
            
            # 删除书名号内的内容（保留书名号）
            simple_simplified = re.sub(r'《([^》]*)》', r'\1', simple_simplified)
            
            # 将长句（超过30字）尝试拆分
            sentences = re.split(r'([。！？])', simple_simplified)
            new_sentences = []
            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                if len(sentence) > 30:
                    # 尝试在逗号处拆分
                    parts = sentence.split('，')
                    if len(parts) > 1:
                        for part in parts:
                            if part.strip():
                                new_sentences.append(part.strip() + '。')
                    else:
                        new_sentences.append(sentence)
                else:
                    new_sentences.append(sentence)
                # 添加标点
                if i + 1 < len(sentences):
                    new_sentences.append(sentences[i + 1])
            
            simple_simplified = ''.join(new_sentences)
        
        # 清理多余的标点
        simple_simplified = re.sub(r'。+', '。', simple_simplified)
        simple_simplified = re.sub(r'，+', '，', simple_simplified)
        simple_simplified = re.sub(r' +', ' ', simple_simplified)
        
        # 确保标点符号数量
        original_punctuation_count = len(re.findall(r'[，。！？；：、]', text))
        simplified_punctuation_count = len(re.findall(r'[，。！？；：、]', simple_simplified))
        
        if simplified_punctuation_count < original_punctuation_count * 0.5:
            logger.warning(f"简化后标点符号数量过少（原文{original_punctuation_count}个，简化后{simplified_punctuation_count}个）")
            return text
        
        return simple_simplified

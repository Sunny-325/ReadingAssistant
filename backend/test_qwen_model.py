#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Qwen模型集成效果
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # 确保输出到控制台
)
logger = logging.getLogger(__name__)


def test_qwen_model():
    """
    测试Qwen模型
    """
    logger.info("开始测试Qwen模型集成")
    
    try:
        # 导入模块
        from app.core.model_manager import get_model_manager
        from app.core.config import settings
        logger.info("模块导入成功")
        
        # 检查API密钥配置
        if settings.QWEN_API_KEY == "your-qwen-api-key":
            logger.warning("Qwen API密钥未配置，请在config.py中设置QWEN_API_KEY")
            return False
        
        # 获取模型管理器
        logger.info("获取模型管理器")
        model_manager = get_model_manager()
        logger.info(f"模型管理器类型: {type(model_manager).__name__}")
        
        # 测试模型状态
        logger.info("测试模型状态")
        status = model_manager.get_model_status()
        logger.info(f"模型状态: {status}")
        
        if status.get("status") != "healthy":
            logger.error("模型状态不健康，测试失败")
            return False
        
        # 测试文本生成
        logger.info("测试文本生成")
        test_prompts = [
            "请简化以下文本：人工智能是计算机科学的一个分支，它尝试理解智能的本质，并产生一种新的能以人类智能相似的方式做出反应的智能机器。",
        ]
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"测试提示词 {i+1}: {prompt}")
            response = model_manager.generate_text(prompt, max_tokens=500)
            logger.info(f"生成结果: {response}")
            if not response:
                logger.error(f"测试提示词 {i+1} 生成失败")
                return False
        
        logger.info("Qwen模型测试成功")
        return True
    
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("启动测试脚本")
    success = test_qwen_model()
    if success:
        logger.info("测试成功")
    else:
        logger.error("测试失败")


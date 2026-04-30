#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境设置脚本
用于安装项目依赖、检查Ollama是否安装并下载Qwen2.5-3B模型
"""

import os
import sys
import subprocess
import logging
import requests
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd, cwd=None, shell=True):
    """
    运行命令并返回结果
    :param cmd: 命令字符串
    :param cwd: 工作目录
    :param shell: 是否使用shell
    :return: 命令返回码
    """
    try:
        logger.info(f"执行命令: {cmd}")
        result = subprocess.run(cmd, cwd=cwd, shell=shell, check=True, capture_output=True, text=True)
        logger.info(f"命令执行成功: {result.stdout[:500]}...")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr}")
        return e.returncode


def check_ollama_installed():
    """
    检查Ollama是否安装
    :return: True if Ollama is installed, False otherwise
    """
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"检测到Ollama: {result.stdout.strip()}")
            return True
        else:
            logger.warning("Ollama未安装")
            return False
    except Exception as e:
        logger.warning(f"检查Ollama失败: {e}")
        return False


def install_ollama():
    """
    提示用户安装Ollama
    """
    logger.info("请访问 https://ollama.com/download 下载并安装Ollama")
    logger.info("安装完成后，请运行 'ollama pull qwen2.5:3b-instruct-q4_K_M' 下载模型")
    return False


def download_qwen_model():
    """
    下载Qwen2.5-3B模型
    """
    logger.info("下载Qwen2.5-3B模型 (q4_K_M量化版本)")
    cmd = "ollama pull qwen2.5:3b-instruct-q4_K_M"
    return run_command(cmd) == 0


def verify_ollama_model():
    """
    验证Ollama模型是否可用
    """
    logger.info("验证Ollama模型")
    
    # 检查Ollama是否识别模型
    result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
    if "qwen2.5:3b-instruct-q4_K_M" in result.stdout:
        logger.info("Qwen2.5-3B模型已下载")
        return True
    else:
        # 检查用户指定的模型路径
        model_path = "D:\\AI_model\\blobs"
        if os.path.exists(model_path):
            logger.info(f"在{model_path}中找到模型目录")
            # 检查目录是否有文件
            files = os.listdir(model_path)
            if files:
                logger.info(f"模型目录中有{len(files)}个文件")
                # 尝试创建Ollama配置文件
                config_dir = os.path.expanduser("~/.ollama")
                config_file = os.path.join(config_dir, "config.json")
                
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir, exist_ok=True)
                
                # 写入配置文件
                config_content = {
                    "model_dir": "D:\\AI_model\\",
                    "host": "0.0.0.0:11434",
                    "timeout": "30m",
                    "keep_alive": "5m",
                    "port": 11434
                }
                
                try:
                    import json
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config_content, f, indent=2)
                    logger.info(f"已创建Ollama配置文件: {config_file}")
                    # 重启Ollama服务
                    logger.info("请重启Ollama服务以应用新配置")
                    return True
                except Exception as e:
                    logger.error(f"创建配置文件失败: {e}")
                    return False
            else:
                logger.warning("模型目录为空")
                return False
        else:
            logger.warning("Qwen2.5-3B模型未找到")
            return False


def install_requirements():
    """
    安装requirements.txt中的依赖
    """
    logger.info("安装项目依赖")
    cmd = "pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple"
    return run_command(cmd) == 0


def verify_environment():
    """
    验证环境配置
    """
    logger.info("验证环境配置")
    
    # 验证requests
    try:
        import requests
        logger.info(f"Requests版本: {requests.__version__}")
    except Exception as e:
        logger.error(f"Requests验证失败: {e}")
        return False
    
    # 验证其他依赖
    try:
        import jieba
        logger.info(f"Jieba版本: {jieba.__version__}")
    except Exception as e:
        logger.error(f"Jieba验证失败: {e}")
        return False
    
    try:
        import PyPDF2
        logger.info(f"PyPDF2版本: {PyPDF2.__version__}")
    except Exception as e:
        logger.error(f"PyPDF2验证失败: {e}")
        return False
    
    try:
        import docx
        logger.info(f"python-docx版本: {docx.__version__}")
    except Exception as e:
        logger.error(f"python-docx验证失败: {e}")
        return False
    
    logger.info("环境验证完成")
    return True


def main():
    """
    主函数
    """
    logger.info("开始环境设置")
    
    # 1. 检查Ollama是否安装
    if not check_ollama_installed():
        if not install_ollama():
            logger.error("Ollama安装失败")
            return 1
    
    # 2. 安装项目依赖
    if not install_requirements():
        logger.error("项目依赖安装失败")
        return 1
    
    # 3. 下载Qwen2.5-3B模型
    if not verify_ollama_model():
        if not download_qwen_model():
            logger.error("模型下载失败")
            return 1
    
    # 4. 验证环境
    if not verify_environment():
        logger.error("环境验证失败")
        return 1
    
    logger.info("环境设置完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())

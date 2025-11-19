"""
日志配置模块
统一的日志管理
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import LOG_LEVEL, LOG_FILE


def setup_logger(name: str = 'hotstock', level: str = LOG_LEVEL) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建日志目录
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 文件处理器 - 轮转日志
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level))

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 模块名称

    Returns:
        日志记录器
    """
    return logging.getLogger(f'hotstock.{name}')

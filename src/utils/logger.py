"""
DPW日志配置

提供统一的日志配置和管理功能。
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = 'dpw',
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """配置并返回logger实例

    Args:
        name: Logger名称，默认为'dpw'
        level: 日志级别，默认为INFO
        log_file: 可选的日志文件路径
        format_string: 可选的自定义日志格式

    Returns:
        配置好的Logger实例

    Example:
        >>> logger = setup_logger('dpw.api', logging.DEBUG)
        >>> logger.info('API server started')
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 默认日志格式
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(format_string)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（可选）
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = 'dpw') -> logging.Logger:
    """获取已配置的logger实例

    Args:
        name: Logger名称

    Returns:
        Logger实例
    """
    return logging.getLogger(name)

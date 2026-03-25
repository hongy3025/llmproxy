"""
日志配置模块。

负责初始化 loguru 日志记录器，配置控制台和文件输出格式与级别。
"""
import os
import sys

from loguru import logger

from config import config


def setup_logger():
    """
    配置并初始化全局日志记录器。

    确保日志目录存在，清除旧的 app.log，并添加控制台和文件处理器。
    """
    # Ensure log directory exists
    os.makedirs(config.LOG_DIR, exist_ok=True)

    # Truncate app.log on startup
    log_file = os.path.join(config.LOG_DIR, "app.log")
    try:
        with open(log_file, "w") as f:
            f.truncate(0)
    except Exception:
        pass

    # Remove default handler
    logger.remove()

    # Add stdout handler
    logger.add(
        sys.stdout,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add app log file handler
    logger.add(
        os.path.join(config.LOG_DIR, "app.log"),
        rotation="10 MB",
        retention="1 week",
        level=config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info(f"Logger initialized. Logs will be saved to {config.LOG_DIR}")


setup_logger()
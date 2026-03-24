import os
import sys

from loguru import logger

from config import config


def setup_logger():
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

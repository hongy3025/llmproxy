"""
配置模块。

负责从环境变量或 .env 文件加载全局配置项。
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    全局配置类。
    """

    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://192.168.1.2:18085").rstrip("/")
    """后端目标 URL，通常指向 llama-server 服务的站点地址。"""

    LISTEN_HOST: str = os.getenv("LISTEN_HOST", "0.0.0.0")
    """代理服务监听的主机地址。"""

    LISTEN_PORT: int = int(os.getenv("LISTEN_PORT", "8080"))
    """代理服务监听的端口号。"""

    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    """日志文件存储目录。"""

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    """日志记录级别（如 INFO, DEBUG, ERROR）。"""

    def __init__(self):
        """
        初始化 Config 实例。
        """
        pass


config = Config()
"""全局配置实例，供其他模块导入使用。"""

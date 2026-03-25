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

    def __init__(self):
        """
        初始化 Config 实例。
        """
        self.BACKEND_URL: str = os.getenv(
            "BACKEND_URL", "http://192.168.1.2:18085"
        ).rstrip("/")
        """后端目标 URL，通常指向 llama-server 服务的站点地址。"""

        self.BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "")
        """后端 API Key，用于向 llama-server 发起认证请求。"""

        self.LISTEN_HOST: str = os.getenv("LISTEN_HOST", "0.0.0.0")
        """代理服务监听的主机地址。"""

        self.LISTEN_PORT: int = int(os.getenv("LISTEN_PORT", "8080"))
        """代理服务监听的端口号。"""

        self.LOG_DIR: str = os.getenv("LOG_DIR", "logs")
        """日志文件存储目录。"""

        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        """日志记录级别（如 INFO, DEBUG, ERROR）。"""


config = Config()
"""全局配置实例，供其他模块导入使用。"""

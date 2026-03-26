"""
依赖注入与全局资源模块。

负责初始化和提供全局的 HTTP 客户端实例与槽位管理器等依赖对象。
"""

import httpx

from config import config
from llama_client import LlamaServerClient
from slot_manager import SlotManager

# Initialize HTTP clients
root_url = config.BACKEND_URL
root_headers = {}
if config.BACKEND_API_KEY:
    root_headers["Authorization"] = f"Bearer {config.BACKEND_API_KEY}"

root_client = httpx.AsyncClient(
    base_url=root_url, timeout=600.0, trust_env=False, headers=root_headers
)
"""全局异步 HTTP 客户端，用于代理根路径请求。"""

llama_client = LlamaServerClient()
"""Llama 服务器专用客户端实例，用于与 llama-server 特有 API 交互。"""

slot_manager = SlotManager(llama_client)
"""全局槽位管理器实例。"""

"""
依赖注入与全局资源模块。

负责初始化和提供全局的 HTTP 客户端实例与槽位管理器等依赖对象。
"""

import httpx

from config import config
from llama_client import LlamaServerClient
from slot_manager import SlotManager

# Initialize HTTP clients
root_url = config.BACKEND_URL.rsplit("/v1", 1)[0]
root_client = httpx.AsyncClient(base_url=root_url, timeout=600.0, trust_env=False)
"""全局异步 HTTP 客户端，用于代理根路径请求。"""

llama_client = LlamaServerClient()
"""Llama 服务器专用客户端实例，用于与 llama-server 特有 API 交互。"""

slot_manager = SlotManager(llama_client)
"""全局槽位管理器实例。"""

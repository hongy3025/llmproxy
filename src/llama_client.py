"""
Llama Server 客户端模块。

提供与 llama-server 特有 API 交互的功能，如管理 slots 和 tokenization。
"""

import json
from collections import OrderedDict
from typing import Any, Dict, List

import httpx

from config import config


class LlamaServerClient:
    """
    与 Llama 服务器交互的 HTTP 客户端。
    """

    _base_url: str = config.BACKEND_URL
    """Llama server 根路径 URL。"""

    _client: httpx.AsyncClient
    """异步 HTTP 客户端。"""

    _template_cache: OrderedDict[str, str] = OrderedDict()
    """消息模板缓存，用于加速 prompt 生成。"""

    _tokenize_cache: OrderedDict[str, List[int]] = OrderedDict()
    """Tokenize 结果缓存，用于加速文本转 Token 过程。"""

    _cache_max_size: int = 1000
    """缓存的最大容量。"""

    def __init__(self):
        """
        初始化 LlamaServerClient 实例。
        """
        headers = {}
        if config.BACKEND_API_KEY:
            headers["Authorization"] = f"Bearer {config.BACKEND_API_KEY}"

        self._client = httpx.AsyncClient(
            base_url=self._base_url, timeout=60.0, headers=headers
        )

    async def get_slots(self) -> List[Dict[str, Any]]:
        """
        从 llama-server 获取所有槽位信息。

        Returns:
            List[Dict[str, Any]]: 槽位信息的列表。

        Raises:
            httpx.HTTPStatusError: 请求失败时抛出异常。
        """
        response = await self._client.get("/slots")
        response.raise_for_status()
        return response.json()

    async def save_slot(self, slot_id: int, filename: str) -> bool:
        """
        将指定槽位的状态保存到文件。

        Args:
            slot_id (int): 要保存的槽位 ID。
            filename (str): 保存的文件名。

        Returns:
            bool: 成功时返回 True。

        Raises:
            httpx.HTTPStatusError: 请求失败时抛出异常。
        """
        response = await self._client.post(
            f"/slots/{slot_id}?action=save", json={"filename": filename}
        )
        response.raise_for_status()
        return True

    async def restore_slot(self, slot_id: int, filename: str) -> bool:
        """
        从文件中恢复指定槽位的状态。

        Args:
            slot_id (int): 要恢复的槽位 ID。
            filename (str): 恢复的文件名。

        Returns:
            bool: 成功时返回 True。

        Raises:
            httpx.HTTPStatusError: 请求失败时抛出异常。
        """
        response = await self._client.post(
            f"/slots/{slot_id}?action=restore", json={"filename": filename}
        )
        response.raise_for_status()
        return True

    async def apply_template(self, messages: List[Dict[str, str]]) -> str:
        """
        将聊天模板应用于消息列表，以获取 prompt 字符串。

        Args:
            messages (List[Dict[str, str]]): 聊天消息列表。

        Returns:
            str: 格式化后的 prompt 字符串。

        Raises:
            httpx.HTTPStatusError: 请求失败时抛出异常。
        """
        cache_key = json.dumps(messages, sort_keys=True)
        if cache_key in self._template_cache:
            self._template_cache.move_to_end(cache_key)
            return self._template_cache[cache_key]

        response = await self._client.post(
            "/apply-template", json={"messages": messages}
        )
        response.raise_for_status()
        prompt = response.json().get("prompt", "")

        self._template_cache[cache_key] = prompt
        if len(self._template_cache) > self._cache_max_size:
            self._template_cache.popitem(last=False)

        return prompt

    async def tokenize(self, content: str) -> List[int]:
        """
        将文本内容进行分词，返回 token 列表。

        Args:
            content (str): 要分词的文本。

        Returns:
            List[int]: 分词后的 token 数组。

        Raises:
            httpx.HTTPStatusError: 请求失败时抛出异常。
        """
        if content in self._tokenize_cache:
            self._tokenize_cache.move_to_end(content)
            return self._tokenize_cache[content]

        response = await self._client.post("/tokenize", json={"content": content})
        response.raise_for_status()
        tokens = response.json().get("tokens", [])

        self._tokenize_cache[content] = tokens
        if len(self._tokenize_cache) > self._cache_max_size:
            self._tokenize_cache.popitem(last=False)

        return tokens

    async def close(self):
        """
        关闭异步 HTTP 客户端连接。
        """
        await self._client.aclose()

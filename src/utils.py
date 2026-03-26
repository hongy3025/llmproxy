"""
工具函数模块。

提供各种通用辅助功能，例如从请求中提取客户端信息和会话标识符。
"""

import re

from fastapi import Request
from loguru import logger


def get_agent_info(request: Request) -> dict:
    """
    从请求的 User-Agent 或其他头信息中提取代理客户端信息。

    Args:
        request (Request): FastAPI 请求对象。

    Returns:
        dict: 包含代理名称 ('name')、版本 ('version') 及原始 UA ('raw_ua') 的字典。
    """
    ua = request.headers.get("User-Agent", "")
    agent_info = {"name": "Unknown", "version": None, "raw_ua": ua}

    # Case-insensitive check
    ua_lower = ua.lower()

    # OpenCode detection (Check header first, then UA)
    if request.headers.get("x-opencode-client"):
        agent_info["name"] = "OpenCode"
    elif "opencode" in ua_lower:
        agent_info["name"] = "OpenCode"
        match = re.search(r"opencode/([\d\.]+)", ua_lower)
        if match:
            agent_info["version"] = match.group(1)
    # Claude Code detection
    elif "claudecode" in ua_lower or "claude-cli" in ua_lower:
        agent_info["name"] = "Claude Code"
        match = re.search(r"(?:claudecode|claude-cli)/([\d\.]+)", ua_lower)
        if match:
            agent_info["version"] = match.group(1)
    elif "anthropic-client" in ua_lower:
        agent_info["name"] = "Anthropic Client"

    return agent_info


async def extract_session_id(request: Request, body_json: dict = None) -> str:
    """
    从请求头或请求体中提取会话 ID。

    按照优先级尝试从特定的 Header 字段或 JSON Body 字段中获取会话标识，
    若均未找到，则退回生成一个随机 UUID。

    Args:
        request (Request): FastAPI 请求对象。
        body_json (dict, optional): 解析后的请求体 JSON 字典。默认为 None。

    Returns:
        str: 提取或生成的会话 ID。
    """

    logger.debug(f"extract_session_id: {request.headers}")
    # 1. Try Agent-specific persistent IDs (if any)
    for header in [
        "x-opencode-session",
        "X-Session-ID",
    ]:
        val = request.headers.get(header)
        if val:
            return val

    return ""

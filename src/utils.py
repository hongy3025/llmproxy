import re
import uuid
from fastapi import Request

def get_agent_info(request: Request) -> dict:
    """Extract agent information from User-Agent or other headers."""
    ua = request.headers.get("User-Agent", "")
    agent_info = {"name": "Unknown", "version": None, "raw_ua": ua}

    # Case-insensitive check
    ua_lower = ua.lower()

    # Claude Code detection
    if "claudecode" in ua_lower or "claude-cli" in ua_lower:
        agent_info["name"] = "Claude Code"
        match = re.search(r"(?:claudecode|claude-cli)/([\d\.]+)", ua_lower)
        if match:
            agent_info["version"] = match.group(1)
    elif "anthropic-client" in ua_lower:
        agent_info["name"] = "Anthropic Client"
    elif "opencode" in ua_lower:
        agent_info["name"] = "OpenCode"
        match = re.search(r"opencode/([\d\.]+)", ua_lower)
        if match:
            agent_info["version"] = match.group(1)

    return agent_info

async def extract_session_id(request: Request, body_json: dict = None) -> str:
    """Extract session ID from headers or request body."""
    # 1. Try header
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id

    # 2. Try Agent-specific persistent IDs (if any)
    for header in [
        "X-Request-ID",
        "X-Correlation-ID",
        "X-Conversation-ID",
        "X-Session-ID",
    ]:
        val = request.headers.get(header)
        if val:
            return val

    # 3. Try body (if chat completion)
    if body_json:
        # Check for various session/conversation identifiers in body
        for key in ["session_id", "conversation_id", "user", "metadata"]:
            if key in body_json:
                val = body_json[key]
                if isinstance(val, str):
                    return val
                elif isinstance(val, dict) and key == "metadata":
                    # Try to find session/conversation in metadata
                    for m_key in ["session_id", "conversation_id", "user_id"]:
                        if m_key in val:
                            return str(val[m_key])

    # 4. Fallback to unique request ID (safe and clean)
    return str(uuid.uuid4())

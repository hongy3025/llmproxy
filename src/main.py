import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from config import config
from logger_setup import setup_logger

# Ensure logs directory exists
LOG_DIR = Path("logs/chats")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Jinja environment
TEMPLATE_DIR = Path("chat-templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def render_chat_text(session_id: str, body_json: dict):
    """Render chat messages using Jinja template and save to .txt file."""
    if not body_json or "messages" not in body_json:
        return

    try:
        template_name = "glm-4.7-flash.jinja"
        template = jinja_env.get_template(template_name)

        # Prepare context for the template
        # Based on glm-4.7-flash.jinja, it expects 'messages', 'tools', 'add_generation_prompt' etc.
        context = {
            "messages": body_json.get("messages", []),
            "tools": body_json.get("tools"),
            "add_generation_prompt": body_json.get("add_generation_prompt", True),
        }

        rendered_text = template.render(**context)

        # Save to logs/chats/chat_{session}.txt
        txt_file_path = LOG_DIR / f"chat_{session_id}.txt"
        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(rendered_text)

        logger.debug(f"Rendered chat text for session {session_id} to {txt_file_path}")
    except Exception as e:
        logger.error(f"Failed to render chat text for session {session_id}: {str(e)}")


# Custom Dumper to force block scalar style (|- ) for multi-line strings
class BlockStyleDumper(yaml.SafeDumper):
    def represent_scalar(self, tag, value, style=None):
        if tag == "tag:yaml.org,2002:str" and "\n" in value:
            style = "|"
        return super().represent_scalar(tag, value, style)


def log_chat_interaction(session_id: str, request_data: dict, response_data: dict):
    """Log the chat interaction to a session-specific YAML file."""
    file_path = LOG_DIR / f"chat_{session_id}.yaml"

    def normalize_newlines(d):
        """Recursively normalize newlines in a dictionary/list."""
        if isinstance(d, str):
            # Also normalize multi-newlines to single ones if that's what's intended?
            # No, user just said "duplicated" which usually means \r\n vs \n issues.
            return d.replace("\r\n", "\n")
        elif isinstance(d, dict):
            return {k: normalize_newlines(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [normalize_newlines(i) for i in d]
        return d

    # Normalize data before logging to avoid duplicated newlines (\r\r\n)
    request_data = normalize_newlines(request_data)
    response_data = normalize_newlines(response_data)

    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                content = f.read()
                if content:
                    data = yaml.safe_load(content) or {"chats": []}
                else:
                    data = {"chats": []}
        else:
            data = {"chats": []}

        # Ensure "chats" key exists
        if "chats" not in data:
            data["chats"] = []

        # Add the new interaction
        data["chats"].append({"request": request_data, "response": response_data})

        # Write back to the file
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            yaml.dump(
                data,
                f,
                Dumper=BlockStyleDumper,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )

        logger.debug(f"Logged interaction for session {session_id} to {file_path}")

    except Exception as e:
        logger.error(f"Failed to log interaction for session {session_id}: {str(e)}")


# Initialize HTTP clients
client = httpx.AsyncClient(base_url=config.BACKEND_URL, timeout=600.0)
root_url = config.BACKEND_URL.rsplit("/v1", 1)[0]
root_client = httpx.AsyncClient(base_url=root_url, timeout=600.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Proxying requests to: {config.BACKEND_URL}")
    logger.info(f"Root proxying to: {root_url}")
    logger.info(f"Listening on: {config.LISTEN_HOST}:{config.LISTEN_PORT}")
    yield
    await client.aclose()
    await root_client.aclose()
    logger.info("Proxy server shutting down.")


app = FastAPI(title="OpenAI Proxy Service", lifespan=lifespan)


async def extract_session_id(request: Request, body_json: dict = None) -> str:
    """Extract session ID from headers or request body."""
    # 1. Try header
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id

    # 2. Try body (if chat completion)
    if body_json and "session_id" in body_json:
        return str(body_json["session_id"])

    # 3. Try standard OpenAI session identifier if any (user id often used as proxy for session)
    if body_json and "user" in body_json:
        return str(body_json["user"])

    # 4. Fallback to unique request ID
    return str(uuid.uuid4())


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_v1_request(path: str, request: Request):
    # For /v1/... requests, we proxy to the backend's /v1/...
    # Since client base_url is already .../v1, we just need the path
    url = f"/{path}"
    method = request.method
    headers = dict(request.headers)

    # Remove host header to avoid issues with the backend
    if "host" in headers:
        del headers["host"]

    query_params = request.query_params
    content = await request.body()

    # Attempt to parse body for session extraction
    body_json = None
    if content:
        try:
            body_json = json.loads(content)
        except json.JSONDecodeError:
            pass

    session_id = await extract_session_id(request, body_json)

    logger.info(f"Session {session_id} | {method} /v1{url}")

    # Render chat text using Jinja template if it's a chat completion request
    if url == "/chat/completions" and body_json:
        render_chat_text(session_id, body_json)

    # Prepare request data for logging
    request_data = {
        "method": method,
        "path": f"v1{url}",
        "protocol": f"HTTP/{request.scope.get('http_version', '1.1')}",
        "headers": dict(request.headers),
        "body": body_json
        if body_json is not None
        else content.decode("utf-8", errors="replace"),
    }

    try:
        # Prepare backend request
        backend_request = client.build_request(
            method, url, content=content, headers=headers, params=query_params
        )

        # Send backend request
        backend_response = await client.send(backend_request, stream=True)

        # Intercept response stream to capture body for logging
        response_chunks = []

        async def response_stream_wrapper():
            async for chunk in backend_response.aiter_raw():
                response_chunks.append(chunk)
                yield chunk

            # After stream is exhausted, log the interaction
            full_response_body = b"".join(response_chunks)
            try:
                response_body_json = json.loads(full_response_body)
            except json.JSONDecodeError:
                response_body_json = full_response_body.decode(
                    "utf-8", errors="replace"
                )

            response_data = {
                "status_code": backend_response.status_code,
                "headers": dict(backend_response.headers),
                "body": response_body_json,
            }
            log_chat_interaction(session_id, request_data, response_data)

        # Forward the response
        return StreamingResponse(
            response_stream_wrapper(),
            status_code=backend_response.status_code,
            headers=dict(backend_response.headers),
        )

    except Exception as e:
        logger.exception(f"Error proxying request for session {session_id}: {str(e)}")
        return Response(content=f"Proxy error: {str(e)}", status_code=500)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all_request(path: str, request: Request):
    # This handles anything not starting with /v1
    # We'll proxy it to the root of the backend (one level above /v1)
    url = f"/{path}"
    method = request.method
    headers = dict(request.headers)
    if "host" in headers:
        del headers["host"]

    logger.info(f"Catch-all | {method} {url}")

    content = await request.body()
    try:
        backend_request = root_client.build_request(
            method, url, content=content, headers=headers, params=request.query_params
        )
        backend_response = await root_client.send(backend_request, stream=True)
        return StreamingResponse(
            backend_response.aiter_raw(),
            status_code=backend_response.status_code,
            headers=dict(backend_response.headers),
        )
    except Exception as e:
        logger.exception(f"Error in catch-all proxy for {url}: {str(e)}")
        return Response(content=f"Proxy error: {str(e)}", status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.LISTEN_HOST, port=config.LISTEN_PORT)

import json
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from config import config
from llama_client import LlamaServerClient
from slot_manager import SlotManager

# Ensure logs directory exists
LOG_DIR = Path("logs/chats")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Jinja environment
TEMPLATE_DIR = Path("chat-templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def tojson_filter(value, **kwargs):
    return json.dumps(value, **kwargs)


jinja_env.filters["tojson"] = tojson_filter


def render_chat_text(session_id: str, body_json: dict, timestamp: str):
    """Render chat messages using Jinja template and save to .txt file."""
    logger.debug(f"Attempting to render chat text for session {session_id}")
    if not body_json:
        logger.debug(f"Session {session_id} | render_chat_text: body_json is None")
        return
    if "messages" not in body_json:
        logger.debug(
            f"Session {session_id} | render_chat_text: 'messages' not in body_json"
        )
        return

    try:
        template_name = "glm-4.7-flash.jinja"
        logger.debug(f"Session {session_id} | Using template: {template_name}")
        template = jinja_env.get_template(template_name)

        # Pre-process messages to parse tool_calls arguments if they are strings
        messages = body_json.get("messages", [])
        processed_messages = []
        for msg in messages:
            new_msg = msg.copy()
            if "tool_calls" in new_msg:
                new_tool_calls = []
                for tc in new_msg["tool_calls"]:
                    new_tc = tc.copy()
                    if "function" in new_tc:
                        func = new_tc["function"].copy()
                        if "arguments" in func and isinstance(func["arguments"], str):
                            try:
                                func["arguments"] = json.loads(func["arguments"])
                            except json.JSONDecodeError:
                                pass
                        new_tc["function"] = func
                    elif "arguments" in new_tc and isinstance(new_tc["arguments"], str):
                        try:
                            new_tc["arguments"] = json.loads(new_tc["arguments"])
                        except json.JSONDecodeError:
                            pass
                    new_tool_calls.append(new_tc)
                new_msg["tool_calls"] = new_tool_calls
            processed_messages.append(new_msg)

        # Prepare context for the template
        # Based on glm-4.7-flash.jinja, it expects 'messages', 'tools', 'add_generation_prompt' etc.
        context = {
            "messages": processed_messages,
            "tools": body_json.get("tools"),
            "add_generation_prompt": body_json.get("add_generation_prompt", True),
        }

        rendered_text = template.render(**context)

        # Save to logs/chats/YYYY-MM-DD_HHMMSS_ffffff_{session_id}.txt
        txt_file_path = LOG_DIR / f"{timestamp}_{session_id}.txt"
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


def log_chat_interaction(
    session_id: str,
    request_data: dict,
    response_data: dict,
    timestamp: str,
    metadata: dict = None,
):
    """Log the chat interaction to a session-specific YAML file."""
    file_path = LOG_DIR / f"{timestamp}_{session_id}.yaml"
    # ... (rest of normalization logic)

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
                    data = yaml.safe_load(content) or {"chats": [], "metadata": {}}
                else:
                    data = {"chats": [], "metadata": {}}
        else:
            data = {"chats": [], "metadata": {}}

        # Update metadata if provided
        if metadata:
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"].update(metadata)

        # Ensure "chats" key exists
        if "chats" not in data:
            data["chats"] = []

        # Add the new interaction
        interaction = {"request": request_data, "response": response_data}
        if metadata:
            interaction["metadata"] = metadata
        data["chats"].append(interaction)

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
client = httpx.AsyncClient(base_url=config.BACKEND_URL, timeout=600.0, trust_env=False)
root_url = config.BACKEND_URL.rsplit("/v1", 1)[0]
root_client = httpx.AsyncClient(base_url=root_url, timeout=600.0, trust_env=False)

llama_client = LlamaServerClient()
slot_manager = SlotManager(llama_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Proxying requests to: {config.BACKEND_URL}")
    logger.info(f"Root proxying to: {root_url}")
    logger.info(f"Listening on: {config.LISTEN_HOST}:{config.LISTEN_PORT}")
    await slot_manager.initialize_slots()
    yield
    await client.aclose()
    await root_client.aclose()
    await llama_client.close()
    logger.info("Proxy server shutting down.")


app = FastAPI(title="OpenAI Proxy Service", lifespan=lifespan)


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
    # Note: We previously used Authorization hash here, but that was incorrect
    # because different instances or different sessions can share the same key.
    return str(uuid.uuid4())


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    start_time = time.perf_counter()
    content = await request.body()
    try:
        body_json = json.loads(content)
    except json.JSONDecodeError:
        return Response(content="Invalid JSON body", status_code=400)

    session_id = await extract_session_id(request, body_json)
    agent_info = get_agent_info(request)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")

    logger.info(
        f"Session {session_id} | Intercepted /v1/chat/completions | Agent: {agent_info['name']} {agent_info.get('version', '')}"
    )

    try:
        # 1. Apply template
        messages = body_json.get("messages", [])
        prompt = await llama_client.apply_template(messages)

        # 2. Tokenize
        tokens = await llama_client.tokenize(prompt)

        # 3. Allocate and prepare slot
        slot_id = await slot_manager.allocate_and_prepare_slot(session_id, tokens)

        # 4. Prepare /completion request
        completion_req = {
            "prompt": prompt,
            "id_slot": slot_id,
            "stream": body_json.get("stream", False),
        }

        # Copy supported generation parameters
        for key in [
            "temperature",
            "top_k",
            "top_p",
            "n_predict",
            "max_tokens",
            "stop",
            "presence_penalty",
            "frequency_penalty",
        ]:
            if key in body_json:
                completion_req[key] = body_json[key]
        if "max_tokens" in body_json and "n_predict" not in completion_req:
            completion_req["n_predict"] = body_json["max_tokens"]

        # 5. Call /completion
        completion_url = "/completion"
        # use root_client or client? llama-server usually puts /completion at root
        backend_request = root_client.build_request(
            "POST", completion_url, json=completion_req
        )
        backend_response = await root_client.send(backend_request, stream=True)

        # 6. Stream or normal response handling
        is_stream = completion_req.get("stream", False)

        if is_stream:

            async def stream_wrapper():
                response_chunks = []
                chunk_count = 0
                try:
                    async for line in backend_response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                yield "data: [DONE]\n\n"
                                continue
                            try:
                                data = json.loads(data_str)
                                # Map llama-server completion format to OpenAI chat completion chunk
                                content = data.get("content", "")
                                chunk = {
                                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": body_json.get("model", "llama"),
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {"content": content},
                                            "finish_reason": None,
                                        }
                                    ],
                                }
                                if data.get("stop", False):
                                    chunk["choices"][0]["finish_reason"] = "stop"

                                response_chunks.append(content)
                                chunk_count += 1

                                yield f"data: {json.dumps(chunk)}\n\n"
                            except Exception as e:
                                logger.error(f"Error parsing SSE data: {e}")
                finally:
                    await backend_response.aclose()

                    # Log stream interaction
                    end_time = time.perf_counter()
                    total_duration = end_time - start_time
                    full_content = "".join(response_chunks)

                    response_data = {
                        "status_code": backend_response.status_code,
                        "headers": dict(backend_response.headers),
                        "body": {
                            "choices": [
                                {
                                    "message": {
                                        "role": "assistant",
                                        "content": full_content,
                                    }
                                }
                            ]
                        },
                    }

                    metadata = {
                        "agent": agent_info,
                        "duration_total": total_duration,
                        "chunk_count": chunk_count,
                        "timestamp_end": datetime.now().isoformat(),
                    }

                    if config.ENABLE_CHAT_LOGS:
                        log_chat_interaction(
                            session_id, body_json, response_data, timestamp, metadata
                        )
                        render_chat_text(session_id, body_json, timestamp)

            return StreamingResponse(stream_wrapper(), media_type="text/event-stream")
        else:
            # Normal response
            await backend_response.aread()
            data = backend_response.json()

            # Map to OpenAI format
            oai_response = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body_json.get("model", "llama"),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": data.get("content", ""),
                        },
                        "finish_reason": "stop"
                        if data.get("stop", False)
                        else "length",
                    }
                ],
                "usage": {
                    "prompt_tokens": data.get("tokens_evaluated", 0),
                    "completion_tokens": data.get("tokens_predicted", 0),
                    "total_tokens": data.get("tokens_evaluated", 0)
                    + data.get("tokens_predicted", 0),
                },
            }

            end_time = time.perf_counter()
            total_duration = end_time - start_time

            response_data = {
                "status_code": backend_response.status_code,
                "headers": dict(backend_response.headers),
                "body": oai_response,
            }

            metadata = {
                "agent": agent_info,
                "duration_total": total_duration,
                "timestamp_end": datetime.now().isoformat(),
            }

            if config.ENABLE_CHAT_LOGS:
                log_chat_interaction(
                    session_id, body_json, response_data, timestamp, metadata
                )
                render_chat_text(session_id, body_json, timestamp)

            return Response(
                content=json.dumps(oai_response), media_type="application/json"
            )

    except Exception as e:
        logger.exception(
            f"Error in chat_completions for session {session_id}: {str(e)}"
        )
        return Response(content=f"Proxy error: {str(e)}", status_code=500)


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_v1_request(path: str, request: Request):
    start_time = time.perf_counter()
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
    agent_info = get_agent_info(request)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")

    logger.info(
        f"Session {session_id} | {method} /v1{url} | Agent: {agent_info['name']} {agent_info.get('version', '')}"
    )

    # Log full request details for all clients
    logger.debug(
        f"Session {session_id} | Full Request Headers: {dict(request.headers)}"
    )
    if body_json:
        logger.debug(
            f"Session {session_id} | Full Request Body (JSON): {json.dumps(body_json, ensure_ascii=False)}"
        )
    elif content:
        logger.debug(
            f"Session {session_id} | Full Request Body (Raw): {content.decode('utf-8', errors='replace')}"
        )

    logger.debug(
        f"Session {session_id} | Request Body present: {body_json is not None}"
    )
    if body_json:
        logger.debug(
            f"Session {session_id} | Request Body Keys: {list(body_json.keys())}"
        )

    # Render chat text using Jinja template if it's a chat completion request
    if (
        config.ENABLE_CHAT_LOGS
        and url in ["/chat/completions", "/messages"]
        and body_json
    ):
        logger.debug(f"Session {session_id} | Calling render_chat_text for {url}")
        render_chat_text(session_id, body_json, timestamp)
    else:
        logger.debug(
            f"Session {session_id} | Skipping render_chat_text. url={url}, body_json_present={body_json is not None}, ENABLE_CHAT_LOGS={config.ENABLE_CHAT_LOGS}"
        )

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
        chunk_count = 0
        stream_start_time = time.perf_counter()

        async def response_stream_wrapper():
            nonlocal chunk_count
            try:
                async for chunk in backend_response.aiter_raw():
                    chunk_count += 1
                    response_chunks.append(chunk)
                    if chunk_count % 50 == 0:
                        logger.debug(
                            f"Session {session_id} | Received {chunk_count} chunks..."
                        )
                    yield chunk
            finally:
                await backend_response.aclose()

            # After stream is exhausted, log the interaction
            full_response_body = b"".join(response_chunks)
            end_time = time.perf_counter()
            total_duration = end_time - start_time
            stream_duration = end_time - stream_start_time

            logger.info(
                f"Session {session_id} | Completed | Status: {backend_response.status_code} | "
                f"Chunks: {chunk_count} | Total: {total_duration:.3f}s | Stream: {stream_duration:.3f}s"
            )

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

            # Log full response details at DEBUG level
            logger.debug(
                f"Session {session_id} | Full Response Headers: {response_data['headers']}"
            )
            if isinstance(response_body_json, dict):
                logger.debug(
                    f"Session {session_id} | Full Response Body (JSON): {json.dumps(response_body_json, ensure_ascii=False)}"
                )
            else:
                logger.debug(
                    f"Session {session_id} | Full Response Body (Raw): {response_body_json}"
                )

            metadata = {
                "agent": agent_info,
                "duration_total": total_duration,
                "duration_stream": stream_duration,
                "chunk_count": chunk_count,
                "timestamp_end": datetime.now().isoformat(),
            }

            if config.ENABLE_CHAT_LOGS:
                log_chat_interaction(
                    session_id, request_data, response_data, timestamp, metadata
                )
            else:
                logger.debug(
                    f"Session {session_id} | Skipping log_chat_interaction as ENABLE_CHAT_LOGS=False"
                )

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

    logger.info(f"Catch-all Route Hit | {method} {url}")
    logger.debug(f"Catch-all Request Headers: {headers}")

    content = await request.body()
    try:
        body_json = None
        if content:
            try:
                body_json = json.loads(content)
                logger.debug(f"Catch-all Request Body: {body_json}")
            except json.JSONDecodeError:
                logger.debug("Catch-all Request Body: (not JSON)")
                pass
        backend_request = root_client.build_request(
            method, url, content=content, headers=headers, params=request.query_params
        )
        backend_response = await root_client.send(backend_request, stream=True)

        async def response_stream_wrapper():
            try:
                async for chunk in backend_response.aiter_raw():
                    yield chunk
            finally:
                await backend_response.aclose()

        return StreamingResponse(
            response_stream_wrapper(),
            status_code=backend_response.status_code,
            headers=dict(backend_response.headers),
        )
    except Exception as e:
        logger.exception(f"Error in catch-all proxy for {url}: {str(e)}")
        return Response(content=f"Proxy error: {str(e)}", status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.LISTEN_HOST, port=config.LISTEN_PORT)

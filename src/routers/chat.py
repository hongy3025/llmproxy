"""
聊天路由模块。

处理 /v1/chat/completions 接口的请求，将其转换为 llama-server 兼容的格式，
处理流式和非流式响应，并记录会话交互信息。
"""

import json
import time
import uuid

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger

from dependencies import llama_client, root_client, slot_manager
from utils import extract_session_id, get_agent_info

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    处理 OpenAI 兼容的聊天补全请求。

    负责拦截请求，分配槽位（Slot），并向后端 llama-server 发起代理请求，
    同时处理 SSE 流式或普通 JSON 响应，将其转回 OpenAI 兼容格式。

    Args:
        request (Request): FastAPI 请求对象，包含请求头与 JSON 体。

    Returns:
        Response: 转换后的 StreamingResponse（流式）或普通 Response。

    Raises:
        Exception: 捕获所有处理过程中的异常并返回 500 状态码。
    """
    content = await request.body()
    try:
        body_json = json.loads(content)
    except json.JSONDecodeError:
        return Response(content="Invalid JSON body", status_code=400)

    session_id = await extract_session_id(request, body_json)
    agent_info = get_agent_info(request)

    logger.info(
        f"Session {session_id} | Intercepted /v1/chat/completions | Agent: {agent_info['name']} {agent_info.get('version', '')}"
    )
    # logger.debug(
    #     f"Session {session_id} | Request body: {json.dumps(body_json, ensure_ascii=False)}"
    # )

    try:
        # 1. Apply template
        messages = body_json.get("messages", [])
        logger.debug(
            f"Session {session_id} | Applying template for {len(messages)} messages"
        )
        prompt = await llama_client.apply_template(messages)
        logger.debug(
            f"Session {session_id} | Template applied. Prompt length: {len(prompt)}"
        )

        # 2. Tokenize
        logger.debug(f"Session {session_id} | Tokenizing prompt")
        tokens = await llama_client.tokenize(prompt)
        logger.debug(
            f"Session {session_id} | Tokenization complete. Token count: {len(tokens)}"
        )

        # 3. Allocate and prepare slot
        logger.debug(f"Session {session_id} | Allocating slot")
        slot_id, reason = await slot_manager.allocate_and_prepare_slot(
            session_id, tokens
        )
        logger.debug(
            f"Session {session_id} | Slot allocated: {slot_id} (reason: {reason})"
        )

        # Mark slot as processing
        slot_manager.set_slot_state(slot_id, 1)

        # 4. Prepare /completion request
        completion_req = {
            "prompt": tokens,
            "id_slot": slot_id,
            "stream": body_json.get("stream", False),
            "n_predict": 2048,  # Default to a reasonable value
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
            "repeat_penalty",
        ]:
            if key in body_json:
                if key == "max_tokens":
                    completion_req["n_predict"] = body_json[key]
                else:
                    completion_req[key] = body_json[key]

        # If n_predict was already in body_json, it will override our default

        # 5. Call /completion
        completion_url = "/completion"
        logger.debug(
            f"Session {session_id} | Calling backend {completion_url} with slot {slot_id}"
        )
        # call llama-server completion endpoint
        backend_request = root_client.build_request(
            "POST", completion_url, json=completion_req
        )
        backend_response = await root_client.send(backend_request, stream=True)

        if backend_response.status_code != 200:
            await backend_response.aread()
            error_data = backend_response.json()
            logger.error(
                f"Session {session_id} | Backend error ({backend_response.status_code}): {error_data}"
            )
            slot_manager.set_slot_state(slot_id, 0)
            return Response(
                content=json.dumps(error_data),
                status_code=backend_response.status_code,
                media_type="application/json",
            )

        # 6. Stream or normal response handling
        is_stream = completion_req.get("stream", False)
        logger.debug(
            f"Session {session_id} | Backend response {backend_response.status_code}, is_stream: {is_stream}"
        )

        if is_stream:

            async def stream_wrapper():
                response_chunks = []
                chunk_count = 0
                logger.debug(f"Session {session_id} | Starting stream wrapper")
                try:
                    async for line in backend_response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                logger.debug(
                                    f"Session {session_id} | Stream [DONE] received. Total chunks: {chunk_count}"
                                )
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
                                    logger.debug(
                                        f"Session {session_id} | Stop flag detected in stream"
                                    )

                                response_chunks.append(content)
                                chunk_count += 1

                                if chunk_count % 50 == 0:
                                    logger.debug(
                                        f"Session {session_id} | Streaming progress: {chunk_count} chunks"
                                    )

                                yield f"data: {json.dumps(chunk)}\n\n"
                            except Exception as e:
                                logger.error(
                                    f"Session {session_id} | Error parsing SSE data: {e}"
                                )
                finally:
                    await backend_response.aclose()
                    # Stream ends
                    logger.debug(
                        f"Session {session_id} | Stream finished, releasing slot {slot_id}"
                    )
                    slot_manager.set_slot_state(slot_id, 0)

            return StreamingResponse(stream_wrapper(), media_type="text/event-stream")
        else:
            # Normal response
            try:
                logger.debug(f"Session {session_id} | Reading non-stream response")
                await backend_response.aread()
                data = backend_response.json()
                logger.debug(
                    f"Session {session_id} | Backend response data: {json.dumps(data, ensure_ascii=False)}"
                )

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
                logger.debug(f"Session {session_id} | OpenAI format response ready")

                return Response(
                    content=json.dumps(oai_response), media_type="application/json"
                )
            finally:
                logger.debug(f"Session {session_id} | Releasing slot {slot_id}")
                slot_manager.set_slot_state(slot_id, 0)

    except Exception as e:
        logger.exception(
            f"Error in chat_completions for session {session_id}: {str(e)}"
        )
        if "slot_id" in locals():
            slot_manager.set_slot_state(slot_id, 0)
        return Response(content=f"Proxy error: {str(e)}", status_code=500)

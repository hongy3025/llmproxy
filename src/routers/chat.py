import json
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger

from dependencies import llama_client, root_client, slot_manager
from utils import extract_session_id, get_agent_info

router = APIRouter()

@router.post("/v1/chat/completions")
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

            return Response(
                content=json.dumps(oai_response), media_type="application/json"
            )

    except Exception as e:
        logger.exception(
            f"Error in chat_completions for session {session_id}: {str(e)}"
        )
        return Response(content=f"Proxy error: {str(e)}", status_code=500)

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    stream = body.get("stream", False)

    if stream:

        async def event_generator():
            chunks = [
                "Hello",
                "!",
                " This",
                " is",
                " a",
                " streaming",
                " response",
                " from",
                " the",
                " mock",
                " backend",
                ".",
            ]
            for i, chunk in enumerate(chunks):
                data = {
                    "id": f"chatcmpl-{i}",
                    "object": "chat.completion.chunk",
                    "created": 1677652288,
                    "model": "gpt-3.5-turbo",
                    "choices": [
                        {"index": 0, "delta": {"content": chunk}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.1)
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! This is a mock response from the backend.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=18085)

import json
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger

from config import config
from logger_setup import setup_logger

# Initialize HTTP client with the base URL including /v1
client = httpx.AsyncClient(base_url=config.BACKEND_URL, timeout=600.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Proxying requests to: {config.BACKEND_URL}")
    logger.info(f"Listening on: {config.LISTEN_HOST}:{config.LISTEN_PORT}")
    yield
    await client.aclose()
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

    try:
        # Prepare backend request
        backend_request = client.build_request(
            method, url, content=content, headers=headers, params=query_params
        )

        # Send backend request
        backend_response = await client.send(backend_request, stream=True)

        # Forward the response
        return StreamingResponse(
            backend_response.aiter_raw(),
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
    root_url = config.BACKEND_URL.rsplit("/v1", 1)[0]
    async with httpx.AsyncClient(base_url=root_url, timeout=600.0) as root_client:
        url = f"/{path}"
        method = request.method
        headers = dict(request.headers)
        if "host" in headers:
            del headers["host"]

        content = await request.body()
        backend_request = root_client.build_request(
            method, url, content=content, headers=headers, params=request.query_params
        )
        backend_response = await root_client.send(backend_request, stream=True)
        return StreamingResponse(
            backend_response.aiter_raw(),
            status_code=backend_response.status_code,
            headers=dict(backend_response.headers),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.LISTEN_HOST, port=config.LISTEN_PORT)

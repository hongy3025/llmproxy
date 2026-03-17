# Proposal: OpenAI Proxy Service

## Why
This change is needed to provide a transparent proxy for an OpenAI-compatible API that can record all chat interactions (requests and responses, including streaming) organized by session. This will facilitate auditing, debugging, and monitoring of LLM usage.

## What Changes
- **FastAPI Proxy**: A new FastAPI service that listens on `http://0.0.0.0:8080/v1`.
- **Transparent Forwarding**: All requests to the proxy are forwarded to the backend service at `http://192.168.1.2:18085/v1`.
- **Session-based Chat Logging**: Intercept `/v1/chat/completions` (and other chat-related endpoints) to log the full conversation history.
- **Streaming Support**: Correctly handle and log streaming responses from the backend.
- **Professional Logging**: Integrate `loguru` for structured and informative event logging.
- **Environment Management**: Use `uv` for project and dependency management.

## Capabilities

### New Capabilities
- `openai-proxy-core`: The basic routing and forwarding logic for all OpenAI endpoints.
- `chat-interaction-recorder`: Specialized logic for capturing and persisting chat completions, including streaming data and session context.

## Impact
- New service implementation in Python.
- Dependencies on `fastapi`, `httpx`, `loguru`, and `openai`.
- Potential impact on latency due to the proxy layer (though minimal).

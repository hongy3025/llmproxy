# Design: OpenAI Proxy Service

## Context
The project requires a transparent proxy server to sit in front of an OpenAI-compatible API. The primary objective is to record all chat interactions for auditing and debugging, specifically focusing on session-based organization and handling both standard and streaming responses.

## Goals / Non-Goals

**Goals:**
- **Full Transparency**: Forward all HTTP methods, headers, and paths to the backend.
- **Session-Aware Logging**: Group chat requests and responses by a session identifier.
- **Streaming Support**: Capture and log the full content of streaming responses without breaking the stream for the client.
- **High Performance**: Use asynchronous I/O to handle concurrent requests with minimal latency.
- **Professional Observability**: Use `loguru` for structured logging of server events.

**Non-Goals:**
- **Request/Response Modification**: The proxy will not alter the content sent between the client and the backend.
- **Auth Layer**: The proxy will not implement its own authentication; it will pass through existing auth headers.
- **Load Balancing**: Only a single backend is supported.

## Decisions

### 1. Framework: FastAPI + httpx
- **Rationale**: FastAPI is the industry standard for high-performance Python APIs. `httpx` provides a modern, async-compatible HTTP client that is ideal for building proxies.
- **Alternatives**: Flask (synchronous, slower for proxying), standard `http.client` (too low-level).

### 2. Stream Interception Strategy
- **Rationale**: To log streaming responses, the proxy will iterate over the backend's response stream. It will yield chunks to the client immediately while simultaneously appending them to a buffer. Once the stream ends, the complete buffer will be logged.
- **Rationale for Session ID**: We will look for a `session_id` in the JSON request body or a custom header `X-Session-ID`. If neither is present, we will generate a UUID for the interaction.

### 3. Logging: Loguru
- **Rationale**: `loguru` offers a simpler and more powerful API than the standard `logging` module, with built-in support for rotation, retention, and structured formatting.
- **Configuration**: Logs will be directed to `stdout` for container friendliness and to `logs/app.log` for persistence. Chat interactions will be logged to a specific `logs/chat_interactions.log` or separate files per session.

## Risks / Trade-offs

- **[Risk] Memory pressure from large streams** → **Mitigation**: Limit the maximum size of a captured stream or write to a temporary file if it exceeds a threshold.
- **[Risk] Latency overhead** → **Mitigation**: Use `httpx.AsyncClient` with a connection pool to minimize handshake time.
- **[Risk] Partial logs on disconnect** → **Mitigation**: Ensure the logging logic handles `GeneratorExit` or connection closures gracefully to log whatever was captured so far.

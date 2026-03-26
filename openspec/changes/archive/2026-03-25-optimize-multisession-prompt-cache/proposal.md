## Why

llama.cpp's `llama-server` provides a `slot` mechanism for maintaining parallel independent session states. Currently, when different AI agents call the proxy concurrently, new sessions or swapped sessions experience high Time-to-First-Token (TTFT) due to full prompt reprocessing. We need to optimize prompt caching for multi-session scenarios by mapping `session_id`s to `slot`s and using prefix matching to quickly clone slot states, reducing latency.

## What Changes

- Add session management mapping `session_id` (from `x-opencode-session` header) to llama-server `slot` IDs.
- Introduce a lifecycle policy for sessions (e.g., LRU eviction) to release inactive slots.
- Implement prefix-matching logic for new sessions to find the best-matching existing slot token array and clone its state using the llama-server API.
- **BREAKING**: Modify the proxy logic for `/v1/chat/completions`. Instead of transparently forwarding the request, the proxy will call low-level llama-server endpoints (`/apply-template`, `/tokenize`, and `/completion`) and simulate the OpenAI-compatible response.
- Add caching for `slot` token arrays in the proxy to avoid repeated `/tokenize` calls.
- Add async concurrency control (locks) to manage slot allocation and state loading/saving safely.

## Capabilities

### New Capabilities
- `multisession-prompt-cache`: Manages the mapping of sessions to llama-server slots, implements prefix-matching for slot cloning, and caches token arrays.

### Modified Capabilities
- `openai-proxy-core`: Modifies transparent forwarding. `/v1/chat/completions` will no longer be transparently forwarded but instead handled by the proxy orchestrating multiple low-level llama-server API calls.

## Impact

- **Affected Code**: `src/main.py` (FastAPI routing), session extraction logic, and new modules for slot management and llama-server API interactions.
- **APIs**: Changes how `/v1/chat/completions` is handled internally.
- **Dependencies**: May require additional HTTP client configurations to handle multiple internal API requests per incoming proxy request.

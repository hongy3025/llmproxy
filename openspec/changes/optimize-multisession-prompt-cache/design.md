## Context

Currently, the proxy forwards all API calls to a `llama-server` backend transparently. `llama-server` supports parallel independent sessions using `slots`. When multiple AI agents connect via the proxy concurrently, new sessions or swapped sessions experience significant Time-to-First-Token (TTFT) latency due to full prompt reprocessing. We can mitigate this by caching `slot` token states and doing fast slot cloning using `llama-server` low-level APIs based on prompt prefix matching.

## Goals / Non-Goals

**Goals:**
- Reduce TTFT latency for multi-session and context-switching scenarios.
- Manage the mapping between proxy `session_id` and `llama-server` `slot` ID.
- Clone slot states efficiently using prefix matching of token arrays.
- Intercept and rewrite `/v1/chat/completions` API calls via proxy orchestration of lower-level llama-server endpoints.

**Non-Goals:**
- Optimize single-session continuous conversation latency (already optimized by llama-server).
- Replace or re-implement the internal tokenization/templating logic of `llama-server` (we must rely on its exact APIs).
- Support non-chat endpoints with slot cloning.

## Decisions

- **Intercepting `/v1/chat/completions`:**
  Instead of transparent forwarding, the proxy will intercept this route and break it down into:
  1. Call `/apply-template` to convert the chat payload into a raw prompt string.
  2. Call `/tokenize` to get the token array (`chat_token_array`).
  3. Prefix-match against cached `slot_token_array`s.
  4. Allocate/clone slot.
  5. Call `/completion` (or equivalent llama-server slot-specific completion endpoint) with the specific `slot_id`.
  6. Format the response back to OpenAI-compatible `/v1/chat/completions` format.
- **Slot State Caching in Proxy:**
  The proxy will maintain an in-memory cache of each slot's current token array to avoid calling `/slots` and `/tokenize` on existing states redundantly on every request.
- **Concurrency Control:**
  Introduced `asyncio.Lock` for slot management operations. Since slot lookup, allocation, saving, and restoring are sequence-dependent state changes, a global or slot-level lock ensures no two sessions overwrite or steal the same slot during the matching/cloning phase.
- **Prefix Matching Algorithm:**
  Token arrays are compared element by element to find the maximum common prefix length. The slot with the longest prefix match is selected as the source for cloning.

## Risks / Trade-offs

- **Risk: Increased Proxy CPU/Memory usage** -> *Mitigation*: The token array cache is relatively small. Token arrays are just lists of integers.
- **Risk: Llama-server API discrepancies** -> *Mitigation*: Relying entirely on `/apply-template` and `/tokenize` ensures tokenization rules match exactly with the backend model.
- **Risk: Complexity in stream handling** -> *Mitigation*: The `/completion` endpoint of llama-server supports streaming. We will need to map its SSE stream format back to the OpenAI chunk format carefully.
- **Trade-off: Proxy transparent forwarding is broken for chat** -> Since we are actively orchestrating, the proxy is no longer purely transparent for chat. This is a necessary trade-off for multi-session caching.

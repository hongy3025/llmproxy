## 1. Slot Management Basics

- [ ] 1.1 Implement data models for slot states (Slot, SessionSlotMapping).
- [ ] 1.2 Implement the `llama-server` API client wrappers for `/slots`, `/apply-template`, and `/tokenize`.
- [ ] 1.3 Add an in-memory cache to store `slot_token_array` for each slot.
- [ ] 1.4 Add async lock (`asyncio.Lock`) for slot allocation and cloning operations.

## 2. Prefix Matching & Slot Allocation Logic

- [ ] 2.1 Implement prefix matching algorithm to find the longest matching `slot_token_array` against a new `chat_token_array`.
- [ ] 2.2 Implement logic to allocate an idle slot or evict the least recently used (LRU) session's slot.
- [ ] 2.3 Implement the slot cloning sequence (save state from source slot, load into target slot) using `llama-server` APIs.

## 3. Proxy Route Interception

- [ ] 3.1 Modify `src/main.py` to intercept `POST /v1/chat/completions` instead of transparently forwarding it.
- [ ] 3.2 Integrate the `/apply-template` and `/tokenize` calls into the intercepted route.
- [ ] 3.3 Integrate the prefix matching and slot allocation logic into the route.

## 4. Completion Orchestration

- [ ] 4.1 Implement the call to the low-level `/completion` endpoint (or equivalent) using the allocated slot.
- [ ] 4.2 Map and format the `llama-server` response back to the standard OpenAI `/v1/chat/completions` format.
- [ ] 4.3 Support streaming mapping (SSE stream translation) from llama-server to OpenAI format.

## 5. Testing and Validation

- [ ] 5.1 Write unit tests for the prefix matching algorithm.
- [ ] 5.2 Write integration tests mocking the `llama-server` APIs to verify slot allocation and cloning logic.
- [ ] 5.3 Test the full `/v1/chat/completions` flow including streaming.

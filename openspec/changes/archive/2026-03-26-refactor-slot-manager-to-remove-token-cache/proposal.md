## Why

当前 `SlotManager` 使用内存中的 `_slot_token_cache` 来存储每个槽位的 Token 序列。这种方式存在以下问题：
1. **状态不一致**：如果 llama-server 的槽位状态在外部被修改（例如通过直接调用 llama-server API），`SlotManager` 的缓存将无法感知，导致前缀匹配失效。
2. **内存冗余**：在 `SlotManager` 中维护一份 Token 缓存增加了内存占用。
3. **初始化复杂**：启动时需要遍历所有槽位并逐一进行 Tokenize。

通过在每次请求时实时查询 `/slots` API 并动态获取 `prompt + generated` 内容进行 Tokenize，可以确保匹配逻辑始终基于 llama-server 的最新真实状态。

## What Changes

- **移除** `SlotManager` 中的 `_slot_token_cache` 属性。
- **修改** `initialize_slots` 方法，不再填充 `_slot_token_cache`。
- **修改** `_find_longest_prefix_match` 方法：
    - 接收当前所有槽位的最新数据作为参数（由调用者通过 `/slots` API 获取）。
    - 对每个槽位，将 `prompt` 和 `generated` 拼接后进行 Tokenize。
    - 使用 Tokenize 后的结果进行前缀匹配。
- **修改** `allocate_and_prepare_slot` 方法：
    - 在进行前缀匹配前，先调用 `self._llama_client.get_slots()` 获取最新状态。
    - 移除所有对 `_slot_token_cache` 的更新操作。

## Capabilities

### New Capabilities
- 无

### Modified Capabilities
- `multisession-prompt-cache`: 修改槽位匹配逻辑，从基于本地缓存改为基于实时 API 查询。

## Impact

- `src/slot_manager.py`: 核心逻辑变更，移除缓存，增加 API 调用。
- `src/llama_client.py`: 确保 `get_slots` 和 `tokenize` 方法能够高效工作。
- 性能影响：由于每次分配槽位时都需要调用 `/slots` 并对所有槽位内容进行 Tokenize，可能会略微增加请求延迟。但考虑到 `llama_client` 已经对 `tokenize` 结果有缓存（`_tokenize_cache`），这种影响应在可接受范围内。

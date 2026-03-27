## Context

当前 `SlotManager` 在内存中维护 `_slot_token_cache`，用于存储每个槽位的 Token 序列。这种设计虽然减少了对 llama-server API 的调用，但引入了状态不一致和内存占用的风险。为了简化设计并确保状态始终最新，我们计划移除该缓存，改为实时查询。

## Goals / Non-Goals

**Goals:**
- 移除 `SlotManager` 中的 `_slot_token_cache`。
- 每次分配槽位时，通过调用 `/slots` API 获取最新内容并进行前缀匹配。
- 确保前缀匹配逻辑基于最新的 `prompt + generated` 内容。

**Non-Goals:**
- 优化 llama-server 的 `/slots` API 性能。
- 更改 `LlamaServerClient` 的核心 Tokenize 逻辑。

## Decisions

### 1. 移除 `_slot_token_cache`
直接删除该字段。所有依赖它的逻辑都将改为通过 API 获取数据。

### 2. 实时调用 `/slots` 和 `/tokenize`
在 `allocate_and_prepare_slot` 方法中，首先调用 `get_slots()` 获取当前所有槽位的状态。
对每个槽位，将 `prompt` 和 `generated` 拼接后，调用 `tokenize()` 获取 Token 序列。

### 3. 利用 `LlamaServerClient` 的 Token 缓存
由于 `LlamaServerClient` 内部已经实现了一个 `_tokenize_cache` (基于 `OrderedDict`)，频繁对相同的 `prompt + generated` 进行 Tokenize 不会造成巨大的性能负担。

## Risks / Trade-offs

- **性能影响**：[Risk] 每次请求都会多出一次 `/slots` 调用和若干次 `/tokenize` 调用。 → [Mitigation] `LlamaServerClient` 已经对 Tokenize 结果做了缓存，且 `/slots` 返回的是本地状态，响应速度通常很快。
- **并发压力**：[Risk] 如果并发请求极高，频繁调用 API 可能导致 llama-server 负载增加。 → [Mitigation] 由于 `llmproxy` 本身通常是单实例运行且受限于后端 llama-server 的槽位数量，这种压力应在可控范围内。

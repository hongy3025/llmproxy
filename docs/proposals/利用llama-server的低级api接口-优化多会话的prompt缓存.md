# 利用llama-server的低级api接口-优化多会话的prompt缓存

## 需求背景

llama.cpp 的 http server (llama-server) 提供 `slot` 机制来维护同时并行的独立的会话状态。这个机制为多个 ai agent 客户端同时调用api服务，而不相互串扰，保证低延迟的 TFTT（Token First Token Time）创造了可能性。

llama-server 服务在启动时，指定 --parallel N，来开启 N 个并行会话 `slot`。

在运行时，可以通过调用 /slots 接口，来获取 `slot` 信息，保存 `slot` 状态，加载（恢复）`slot` 状态。接口细节，参考文档： [llama-cpp-backend-api.md](../manuals/llama-cpp-backend-api.md) 和 [llama-http-server.md](../manuals/llama-http-server.md)

## 会话管理

### 会话状态的维持

用 opencode 作为 agent 客户端请求时，每个请求的 header 中会带有 `x-opencode-session` 字段，来指定 `session_id`。我们需要在 proxy 层维护 `session_id` 和 `slot` ID 的之间的映射关系状态。

需定义明确的生命周期策略（如 LRU 淘汰机制或基于最后活跃时间的超时策略）。在会话活跃期间保持绑定稳定；当 `slot` 资源耗尽且有新请求到达时，根据淘汰策略解除不活跃会话的绑定，并释放（或覆盖）其 `slot` 资源。

### 会话状态的快速克隆

当有新的 `session_id` （请求出现新的 `x-opencode-session`）出现时，当将这个 `session_id` 绑定到新的 `slot` 时候，由于 `slot` 的状态为空，或者 `slot` 是绑定其它旧会话遗留的状态。将新请求中的 prompt prefill 到 `slot` 中，就需要很长的时间。这就造成了 TFTT 处理延迟。

加速预填充的方式是：将新会话的 prompt 和 所有 `slot` 中的 prompt（通过 /slots API 查询），进行前缀匹配，寻找前缀最匹配（token化后的前缀匹配最长）的 `slot`。
- 如果这个 `slot` 已经绑定了 `session_id`。需要**分配一个新的空闲 `slot`（目标 `slot`）**，先通过 API 保存当前匹配 `slot`（源 `slot`）的状态（指定保存路径），再对新分配的空闲 `slot` 调用恢复 API 加载该状态文件，从而实现 `slot` 状态的跨 `slot` 克隆。最后将新 `session_id` 绑定到这个新 `slot`。
- 如果这个 `slot` 没有绑定 `session_id`（已经空闲），则直接占用这个 `slot`，绑定到新 `session_id`。

## 前缀匹配算法

只有在出现新的 `session_id`，为它寻找 `slot` 绑定时，才需要执行前缀匹配。

我们通过 tokenize 后的 token 数组来进行最长前缀匹配。具体逻辑是：

- 收到 /v1/chat/completions 请求 --> /apply-template 应用模板 转化为 prompt --> /tokenize 分词 转化为 token 数组 --> `chat_token_array`
- proxy 层在内存中直接读取**已缓存**的各 `slot` token 数组（`slot_token_array`），避免每次请求时向服务器全量拉取并重新分词。
- 将 `chat_token_array` 和每一个 `slot_token_array` 进行前缀匹配，找到最长的前缀匹配。


## 代理接口的优化

之前分析的流程中，/apply-template， /tokenize 需要依赖具体的模型，所以：
- **精确依赖后端 API**：必须直接调用 llama-server 的 `/apply-template` 和 `/tokenize` 接口，以确保模板应用和分词结果的绝对精确，避免在 proxy 中引入不准确的本地分词器。
- **缓存与本地优化**：在 proxy 中可以缓存后端返回的 prompt 和 token array 结果， 避免对相同内容重复调用 llama-server 的辅助接口。
- **底层接口映射**：避免调用 openai 兼容的 `/v1/chat/completions` 高层接口，而是调用 llama-server 私有低层接口（如 `/completion` 及其特定 `slot` 参数），在 proxy 中完全模拟并包装实现 openai 兼容的 `/v1` 的高层接口响应。
- **并发与竞态控制**：在处理并发请求时，针对 `slot` 的状态查询、保存、加载及分配操作，必须在 proxy 层引入异步锁机制，防止多个会话同时读写或抢占同一个 `slot` 状态。

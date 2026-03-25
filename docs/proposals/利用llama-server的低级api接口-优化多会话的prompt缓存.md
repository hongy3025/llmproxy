## 背景

llama.cpp 的 llama-http-server 提供了机制维护同时并行的独立的会话状态。这个机制为多个 ai agent 客户端同时调用api服务，而不相互串扰，保证低延迟的 TFTT（Token First Token Time）创造了可能性。

llama-server 服务在启动时，指定 --parallel N，来开启 N 个并行会话槽位。

在运行时，可以通过调用 /slots 接口，来获取插槽信息，保存插槽状态，加载（恢复）插槽状态。接口细节，参考文档： [llama-cpp-backend-api.md](../manuals/llama-cpp-backend-api.md) 和 [llama-http-server.md](../manuals/llama-http-server.md)

## 会话管理

### 会话状态的维持

用 opencode 作为 agent 客户端请求时，每个请求的 header 中会带有 x-open-session 字段，来指定会话 ID，我们需要在 proxy 层维护 会话 ID 和 插槽 ID 的之间的映射关系状态，在一定时间内，保持它们之间绑定关系的稳定性。并且，同时也要设置机制，让这个绑定关系在适当的时候解除，释放出插槽资源。

### 会话状态的快速克隆

当有新的 会话ID （请求出现新的 x-open-session）出现时，当将这个会话 ID 绑定到新的 插槽 时候，由于 插槽 的状态为空，或者插槽是绑定其它旧会话遗留的状态。将新请求中的 prompt prefill 到 插槽 中，就需要很长的时间。这就造成了 TFTT 处理延迟。

加速预填充的方式是：将新会话的 prompt 和 所有 插槽 中的 prompt（通过 /slot api 查询），进行前缀匹配，寻找前缀最匹配（token化后的前缀匹配最长）的插槽。
- 如果这个 插槽 已经绑定了会话 ID。用 /slot?save API 保存当前插槽的状态，再用 /slot?load API 恢复插槽状态，以便实现 复插槽状态 克隆。
- 如果这个 插槽 没有绑定会话 ID（已经空闲），则直接占用这个 插槽，绑定到新会话 ID。

## 前缀匹配算法

我们通过 token 化后， token 数组来进行最长前缀匹配。具体逻辑是：

- /v1/chat/completions 请求 --> /apply-template 应用模板 转化为 prompt --> /tokenize 分词 转化为 token 数组 --> chat_token_array
- 提取每一个 插槽 中的 prompt --> /tokenize 分词 转化为 token 数组 --> slot_token_array
- 将 chat_token_array 和每一个 slot_token_array 进行前缀匹配，找到最长的前缀匹配。


## 代理接口的优化

之前分析的流程中，/apply-template， /tokenize 实际上都应该在 本 proxy 中执行，所以：
- 实现中，可以尽可能在 proxy 中缓存 prompt 和 token array， 避免重复调用 llama-server 接口。
- 避免调用 openai 兼容的 /v1 高层接口，而是调用 llama-server 私有低层接口（非 /v1 开头），在 proxy 中完全模拟并实现 openai 兼容的 /v1 的高层接口。



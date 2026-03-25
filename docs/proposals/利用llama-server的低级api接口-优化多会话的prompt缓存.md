## 背景

llama.cpp 的 llama-http-server 提供了机制维护同时并行的独立的会话状态。这个机制为多个 ai agent 客户端同时调用api服务，而不相互串扰，保证低延迟的 TFTT（Token First Token Time）创造了可能性。

llama-server 服务在启动时，指定 --parallel N，来开启 N 个并行会话槽位。

在运行时，可以通过调用 /slots 接口，来获取插槽信息，保存插槽状态，加载（恢复）插槽状态。接口细节，参考文档： [llama-cpp-backend-api.md](../api/llama-cpp-backend-api.md) 和 [llama-http-server.md](../manuals/llama-http-server.md)

## 会话管理

### 会话状态的维持

用 opencode 作为 agent 客户端请求时，每个请求的 header 中会带有 x-open-session 字段，来指定会话 ID，我们需要在 proxy 层维护 会话 ID 和 插槽 ID 的之间的映射关系状态，在一定时间内，保持它们之间绑定关系的稳定性。并且，同时也要设置机制，让这个绑定关系在适当的时候解除，释放出插槽资源。

### 会话状态的快速克隆

当有新的 会话ID （出现新的 x-open-session）出现时，当将这个会话 ID 绑定到新的 插槽 时候，由于 插槽 的状态为空，或者是其它旧绑定遗留的状态。将新请求中的 prompt prefill 到 插槽 中，就需要很长的时间。这就造成了 TFTT 处理延迟。

为了减少这个延迟，我们

## 代理接口的优化

## Why

当使用 Claude Code、OpenCode 等 Agent 客户端访问代理时，当前的会话标识（Session ID）提取逻辑较为简单，主要依赖 `X-Session-ID` 请求头、`session_id` 字段或 `user` 字段。如果这些字段都不存在，系统会回退到为每个请求生成一个新的 UUID。这导致无法跨请求跟踪同一个 Agent 的完整会话生命周期，难以进行调试和行为分析。我们需要增强会话识别能力，并添加详细的生命周期日志，以便清晰地观察 Agent 的交互过程。

## What Changes

- **增强会话提取逻辑**：除了现有方式，还将尝试从常见 Agent 客户端（如 Claude Code）特有的 Header 或特征中提取持久化的会话标识。
- **添加详细的生命周期日志**：在请求开始、转发、响应接收、流式分块以及会话结束等关键节点添加结构化日志，包含会话 ID、耗时、状态等信息。
- **改进日志输出**：确保 `app.log` 中包含足够的上下文信息，方便通过 `grep` 等工具过滤特定会话的所有活动。

## Capabilities

### New Capabilities
- `agent-session-tracking`: 专门针对不同 Agent 客户端的会话识别和生命周期跟踪能力。

### Modified Capabilities
- `chat-interaction-recorder`: 增强记录逻辑，包含更多元数据和生命周期节点日志。
- `automated-testing-suite`: 添加针对新会话提取逻辑和详细日志的测试用例。

## Impact

- **src/main.py**: 修改 `extract_session_id` 函数和 `proxy` 逻辑以支持更详细的日志。
- **src/logger_setup.py**: 可能需要微调日志格式以更好地支持会话过滤。
- **tests/**: 增加新的测试文件或更新现有测试。

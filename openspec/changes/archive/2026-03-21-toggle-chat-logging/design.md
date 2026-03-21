## Context

目前项目在 `src/main.py` 中硬编码了聊天记录的逻辑。具体来说，它会拦截请求和响应，然后调用 `render_chat_text` 和 `log_chat_interaction` 来生成 `.txt` 和 `.yaml` 文件。这些操作是自动执行的，没有开关控制。

## Goals / Non-Goals

**Goals:**
- 提供一个全局配置项来启用/禁用聊天交互记录。
- 默认情况下禁用记录。
- 确保性能：当记录被禁用时，应尽量减少相关的开销（如模板渲染、文件 I/O）。

**Non-Goals:**
- 不改变现有的日志记录格式（YAML 和 TXT）。
- 不涉及 `app.log` 的控制（由 `LOG_LEVEL` 控制）。

## Decisions

- **配置位置**: 在 `src/config.py` 的 `Config` 类中添加 `ENABLE_CHAT_LOGS` 属性。
- **配置获取**: 使用 `os.getenv("ENABLE_CHAT_LOGS", "False").lower() == "true"` 来解析环境变量，确保其布尔值正确。
- **拦截点**: 在 `src/main.py` 的 `proxy` 函数中，在调用记录逻辑之前增加 `if config.ENABLE_CHAT_LOGS:` 判断。
- **渲染控制**: 同样在调用 `render_chat_text` 之前增加判断，避免不必要的模板渲染。

## Risks / Trade-offs

- **[Risk] 用户忘记开启导致丢失重要日志** → **Mitigation**: 在文档（如 README 或 AGENTS.md）中明确说明默认关闭。
- **[Risk] 性能开销** → **Mitigation**: 通过尽早返回或跳过逻辑，确保在关闭状态下几乎没有额外开销。

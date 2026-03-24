## Context

当前项目的 `extract_session_id` 逻辑对通用的 Agent 客户端（如 Claude Code, OpenCode）识别不足。当这些客户端未显式提供 `X-Session-ID` 时，代理会退而求其次地为每个请求生成一个新的 UUID，导致同一 Agent 的多个请求无法被归类为一个会话。此外，目前的日志仅记录了请求的基本信息和交互结果，缺乏对流式响应生命周期的详细记录（例如：流什么时候开始、发送了多少个 chunk、总共耗时多久）。

## Goals / Non-Goals

**Goals:**
- 增强 `extract_session_id` 以识别 Claude Code 和其他常见 Agent。
- 在 `app.log` 中添加结构化的生命周期日志，包含 session_id 以实现可追溯性。
- 记录详细的流式处理元数据（chunk 数量、流持续时间）。
- 保持对现有 OpenAI 客户端的兼容性。

**Non-Goals:**
- 引入复杂的数据库来管理会话状态（保持无状态代理的设计）。
- 改变现有的 YAML 日志基本结构（仅在其中添加元数据）。

## Decisions

- **Agent 识别方案**: 
  - **Claude Code**: 检查 `User-Agent` 是否包含 `ClaudeCode` 或 `anthropic-client`。
  - **会话持久化**: 如果 Agent 客户端没有提供显式的 Session ID，我们将尝试从请求中寻找稳定的标识符（如特定的环境变量名、用户 ID 字段等），或者在日志中明确标注该会话是由代理生成的 UUID。
- **日志增强方案**:
  - 在 `proxy_v1_request` 中，使用 `time.perf_counter()` 测量各个阶段的耗时。
  - 引入一个 `agent_type` 变量并在日志中输出。
  - 在 `response_stream_wrapper` 中记录 chunk 处理的进度。
- **日志级别策略**:
  - **INFO**: 关键节点（请求开始、流开始、响应完成）。
  - **DEBUG**: 详细数据（Headers 详情、Chunk 内容片段）。

## Risks / Trade-offs

- **[Risk] Agent 客户端频繁更改 Header** → **Mitigation**: 使用灵活的模式匹配（正则表达式）来识别 Agent 类型，而不是硬编码精确版本号。
- **[Risk] 日志量过大** → **Mitigation**: 仅在 `ENABLE_CHAT_LOGS=True` 时记录详细的交互日志，常规的生命周期日志保持简洁。

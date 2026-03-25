## ADDED Requirements

### Requirement: Agent Client Identification
系统应能够通过 HTTP 请求头识别常见的 Agent 客户端（如 Claude Code）。

#### Scenario: Identify Claude Code
- **WHEN** 请求包含 `User-Agent: ClaudeCode/...`
- **THEN** 系统在日志中标记客户端类型为 `Claude Code`

### Requirement: Enhanced Session Extraction for Agents
系统应尝试从 Agent 特有的 Header 中提取稳定的会话 ID。

#### Scenario: Extract session from Claude Code header
- **WHEN** 请求包含 `X-Claude-Session-Id`（假设）或其他持久化标识
- **THEN** 系统将其作为 `session_id`

### Requirement: Session Lifecycle Logging
系统应记录会话的关键生命周期节点。

#### Scenario: Log session start and proxying
- **WHEN** 收到新请求并成功提取 session_id
- **THEN** 记录一条 INFO 日志，包含 session_id、方法、路径以及客户端特征

#### Scenario: Log response completion
- **WHEN** 后端响应流传输完成
- **THEN** 记录一条 INFO 日志，包含 session_id、HTTP 状态码以及总耗时

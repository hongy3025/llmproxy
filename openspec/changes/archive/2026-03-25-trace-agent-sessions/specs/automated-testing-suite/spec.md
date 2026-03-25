## ADDED Requirements

### Requirement: Agent Session Tracking Tests
系统应有专门的测试用例来验证针对不同 Agent 客户端的会话识别逻辑。

#### Scenario: Verify Claude Code session extraction
- **WHEN** 一个包含 Claude Code 标识的模拟请求发送到 `/v1/chat/completions`
- **THEN** 系统能够正确识别 Agent 类型并提取会话 ID（如果提供）

### Requirement: Session Lifecycle Logging Verification
系统应能够验证在 `app.log` 中记录了正确的生命周期日志。

#### Scenario: Verify life-cycle logs in app.log
- **WHEN** 发送一个完整的请求并接收流式响应
- **THEN** 在日志中能观察到请求开始、流分块处理以及完成的 INFO 级别记录，且包含一致的 session_id

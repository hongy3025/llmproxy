## 1. 基础识别与增强提取

- [ ] 1.1 在 `src/main.py` 中更新 `extract_session_id` 函数，支持识别 Claude Code 等 Agent 客户端。
- [ ] 1.2 实现 `get_agent_info` 辅助函数，从 Header 中解析 Agent 名称和版本。

## 2. 详细生命周期日志实现

- [ ] 2.1 在 `proxy_v1_request` 的入口处添加带有耗时测量的 INFO 级别日志。
- [ ] 2.2 在 `response_stream_wrapper` 中记录流式响应的关键节点（流开始、每 N 个 chunk 的进度、流结束）。
- [ ] 2.3 修改 `log_chat_interaction` 以包含更多元数据（agent_type, duration, chunk_count）。

## 3. 测试与验证

- [ ] 3.1 编写 `tests/test_agent_tracking.py`，模拟不同 Agent 客户端的请求并验证会话 ID 提取。
- [ ] 3.2 运行测试并查看 `logs/app.log` 以确认日志输出符合预期。
- [ ] 3.3 手动验证 Claude Code (如果可能) 或通过伪造 User-Agent 来模拟实际交互。

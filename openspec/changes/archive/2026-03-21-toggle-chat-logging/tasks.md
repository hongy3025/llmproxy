## 1. 配置管理

- [x] 1.1 在 `src/config.py` 中添加 `ENABLE_CHAT_LOGS` 配置项，默认值为 `False`。
- [x] 1.2 确保 `ENABLE_CHAT_LOGS` 可以通过环境变量进行覆盖。

## 2. 核心逻辑修改

- [x] 2.1 修改 `src/main.py` 中的 `proxy` 函数，在调用 `render_chat_text` 之前检查 `config.ENABLE_CHAT_LOGS`。
- [x] 2.2 修改 `src/main.py` 中的 `log_chat_interaction` 调用点，在记录 YAML 日志之前检查 `config.ENABLE_CHAT_LOGS`。

## 3. 验证与测试

- [x] 3.1 编写测试用例验证当 `ENABLE_CHAT_LOGS` 为 `False` 时，不产生任何聊天记录文件。
- [x] 3.2 编写测试用例验证当 `ENABLE_CHAT_LOGS` 为 `True` 时，正常产生聊天记录文件。
- [x] 3.3 运行所有现有测试，确保没有引入回归。

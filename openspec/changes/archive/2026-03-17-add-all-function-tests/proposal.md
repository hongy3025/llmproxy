## Why

按照 `AGENTS.md` 中的 TDD 规范，为现有功能补充自动化测试用例。这可以确保代码的稳定性和正确性，并为后续的重构和新功能开发提供保障。

## What Changes

- 在 `tests/` 目录下建立完整的测试套件。
- 覆盖 `src/config.py` 中的配置加载逻辑。
- 覆盖 `src/logger_setup.py` 中的日志初始化逻辑。
- 覆盖 `src/main.py` 中的核心逻辑：
    - 会话 ID 提取 (`extract_session_id`)。
    - 交互记录 (`log_interaction`)。
    - 流式响应处理 (`log_stream_response`)。
    - 代理请求转发逻辑 (`proxy_v1_request`, `catch_all_request`)。

## Capabilities

### New Capabilities
- `automated-testing-suite`: 建立完整的自动化测试套件，确保现有所有功能的正确性。

### Modified Capabilities
<!-- No requirement changes to existing capabilities, just adding tests for them. -->

## Impact

- 影响 `tests/` 目录（新建文件）。
- 提高代码质量和可维护性。
- 需要 `pytest`, `pytest-asyncio`, `httpx` 等测试依赖。

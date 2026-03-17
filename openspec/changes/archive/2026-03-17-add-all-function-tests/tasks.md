## 1. 测试环境搭建

- [x] 1.1 安装 `pytest`, `pytest-asyncio`, `pytest-mock` 等依赖
- [x] 1.2 创建 `tests/conftest.py` 进行全局测试配置（如 Mock `Config`）

## 2. 单元测试实现

- [x] 2.1 实现 `tests/test_config.py` 对 `src/config.py` 的测试
- [x] 2.2 实现 `tests/test_logger_setup.py` 对 `src/logger_setup.py` 的测试
- [x] 2.3 实现 `tests/test_session_extraction.py` 对 `src/main.py` 中 `extract_session_id` 的测试
- [x] 2.4 实现 `tests/test_interaction_logging.py` 对 `src/main.py` 中 `log_interaction` 和 `log_stream_response` 的测试

## 3. 集成测试与代理转发

- [x] 3.1 实现 `tests/test_proxy_routing.py` 使用 `TestClient` 测试 `/v1` 路径的代理逻辑
- [x] 3.2 实现 `tests/test_catch_all.py` 测试非 `/v1` 路径的兜底转发逻辑

## 4. 验证与优化

- [x] 4.1 运行所有测试并确保 100% 通过
- [x] 4.2 根据 `AGENTS.md` 的 TDD 规范进行代码优化（如果需要）

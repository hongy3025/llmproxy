## Context

当前项目缺乏自动化测试覆盖，仅依靠 `AGENTS.md` 中的规范描述。为了确保项目的核心逻辑（配置、日志、会话提取、代理转发、流式记录）的正确性，需要引入 `pytest` 框架进行全面的单元测试和集成测试。

## Goals / Non-Goals

**Goals:**
- 实现对 `src/config.py`, `src/logger_setup.py`, `src/main.py` 的 100% 核心功能测试覆盖。
- 测试用例应覆盖正常路径和异常路径。
- 测试环境应模拟后端服务，避免真实的外部依赖。

**Non-Goals:**
- 不涉及对第三方库（如 `httpx`, `fastapi`）内部实现的测试。
- 不进行大规模的性能压力测试。

## Decisions

- **Testing Framework**: 使用 `pytest` 作为主测试框架，并配合 `pytest-asyncio` 支持异步测试。
- **Mocking**: 使用 `httpx` 的 `ASGITransport` 或 `pytest-mock` 来模拟后端 API 响应，确保测试的可重复性和独立性。
- **Environment**: 使用 `python-dotenv` 加载测试专用的环境变量（如 `.env.test`）或在 `conftest.py` 中动态设置。
- **Log Verification**: 通过注入 `loguru` 的 handler 来验证日志输出的正确性。

## Risks / Trade-offs

- [Risk] → 测试用例可能因为 Mock 不准确而无法反映真实的代理行为。
- [Mitigation] → 使用真实的 `FastAPI` 客户端 (`httpx.AsyncClient(app=app)`) 进行集成测试，确保代理层面的完整逻辑。

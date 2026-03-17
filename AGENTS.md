# AGENTS.md

本文档为 AI 代理在本代码库中工作时提供指导，涵盖项目架构、开发规范及常用操作。

## 项目概述

**OpenAI Proxy Service** 是一个透明的代理服务，旨在拦截并记录与 OpenAI 兼容 API 的所有聊天交互（包括流式和非流式）。

### 核心目标
- **全透明转发**：无损转发所有 HTTP 方法、请求头及路径。
- **会话感知的日志记录**：根据 `session_id` 自动归类聊天请求与响应。
- **流式支持**：实时捕获并重组流式响应内容，而不破坏客户端的流式体验。
- **高性能**：基于异步 I/O 构建，确保极低的代理延迟。

## 常用命令

项目使用 `uv` 进行依赖管理和任务执行：

- **启动服务**：`uv run main.py`
- **运行测试**：`uv run pytest`
- **安装依赖**：`uv sync`
- **添加依赖**：`uv add <package>`

## 架构

项目采用 FastAPI 结合 `httpx` 的异步架构，核心逻辑位于 `main.py`：

1.  **FastAPI Entry Point** ([main.py](main.py)): 处理路由分发。
    - `/v1/{path:path}`: 主要代理接口，映射到后端 `/v1` 路径。
    - `/{path:path}`: 兜底接口，映射到后端根路径。
2.  **Session Extraction**: 通过 `extract_session_id` 函数从 `X-Session-ID` Header 或 Body 中提取会话标识。
3.  **Interaction Recording**:
    - **非流式**: 记录完整 JSON 请求/响应。
    - **流式**: 通过 `log_stream_response` 异步生成器，在分块传输的同时进行内容聚合，完成后一次性记入日志。
4.  **Logging** ([logger_setup.py](file:///d:/AI/src/llmproxy/logger_setup.py)): 使用 `loguru` 进行分层日志管理。
    - `app.log`: 记录应用运行状态。
    - `chat_interactions.log`: 专门存储 JSON 格式的交互数据。
5.  **Configuration** ([config.py](file:///d:/AI/src/llmproxy/config.py)): 通过 `.env` 文件或环境变量管理后端 URL、监听地址等。

## 代码注释标准

本代码库以采用以下 Python 模块代码注释规范：

- **模块级注释**：在文件顶部使用三引号 `"""` 简述模块功能、职责及包含的主要内容。
- **类注释**：在类定义下方使用三引号 `"""` 描述类的用途。
- **属性/字段注释**：在类属性或数据模型字段定义**下方**使用三引号 `"""` 进行说明。
- **方法/函数注释**：在定义下方使用三引号 `"""`，结构如下：
  - 简要功能描述。
  - **Args**: 列出参数名、类型及说明。
  - **Returns**: 说明返回值类型及含义。
  - **Raises**: 列出可能抛出的异常类型及触发条件。

## TDD (测试驱动开发) 规范

本代码库强制执行 TDD 开发流程，以确保代码质量和功能正确性。

1. **红 (Red)**:
   - 在实现任何新功能或修复 Bug 之前，必须先在 `tests/` 目录下编写测试用例。
   - 运行测试并确认其失败（预期失败）。
   - 测试应覆盖正常路径（Happy Path）和边缘情况（Edge Cases）。

2. **绿 (Green)**:
   - 编写尽可能简单的代码以使测试通过。
   - 不要在此阶段进行过度设计或提前优化。
   - 确认测试通过后，提交代码（可选）。

3. **重构 (Refactor)**:
   - 在测试保护下优化代码结构、消除冗余、提高性能。
   - 每次重构后必须运行测试，确保没有引入回归。

4. **验收标准**:
   - 所有在 `openspec/tasks.md` 中定义的任务必须有关联的测试用例。
   - 在 `openspec/proposal.md` 中定义的 Capability 必须在测试中得到验证。

## 开发说明

- 使用 `uv` 进行包管理
- 需要 Python 3.12+
- 测试位于 `tests/` 目录（如果存在），使用 pytest 并支持 asyncio
- `.venv` 目录包含虚拟环境（请勿提交）
- 环境变量配置直接修改 `.env` 文件，可参考 `config.py` 中的默认值

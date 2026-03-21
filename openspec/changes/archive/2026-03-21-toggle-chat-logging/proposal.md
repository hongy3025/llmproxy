## Why

当前系统默认会自动记录所有的聊天交互（.txt 和 .yaml 文件），这在生产环境或大规模使用时可能会产生大量的日志文件，占用存储空间，且并非所有场景都需要这些详细记录。通过添加配置开关，用户可以根据需要灵活控制是否启用聊天记录功能。

## What Changes

- 在 `src/config.py` 中添加 `ENABLE_CHAT_LOGS` 配置项，默认值为 `False`。
- 修改 `src/main.py` 中的逻辑，仅在 `ENABLE_CHAT_LOGS` 为 `True` 时才执行聊天记录的保存操作（包括 `.txt` 渲染和 `.yaml` 归档）。
- 支持通过环境变量 `ENABLE_CHAT_LOGS` 来覆盖默认设置。

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md -->
- `config-driven-logging`: 通过配置项动态控制日志记录行为的能力。

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
- `chat-interaction-recorder`: 增加了一个前提条件，即只有在配置启用的情况下才进行记录。

## Impact

- `src/config.py`: 新增配置项。
- `src/main.py`: 修改 `proxy` 路由处理函数和 `log_chat_interaction` 等相关逻辑。
- `tests/`: 可能需要更新测试用例以验证配置开关的有效性。

## Why

当前系统在 `INFO` 级别下会记录完整的请求和响应的 Header 和 Body。这在生产环境下会导致日志量过大，且包含敏感信息。为了在保持日常监控的同时减少日志体积，只有在 `DEBUG` 级别下才应记录详细的交互数据。

## What Changes

- 修改 `src/main.py` 中的日志记录逻辑。
- 将记录请求 Header、请求 Body、响应 Header 和响应 Body 的 `logger.info` 调用改为 `logger.debug`。
- 确保只有在 `LOG_LEVEL=DEBUG` 时，这些详细信息才会出现在 `app.log` 和标准输出中。

## Capabilities

### New Capabilities
- 无

### Modified Capabilities
- `chat-interaction-recorder`: 只有在 `DEBUG` 级别下才会在应用日志中记录 Header 和 Body。

## Impact

- `src/main.py`: 日志级别调整。
- `logs/app.log`: `INFO` 级别下的日志将变得更简洁，仅包含基本的请求路径、状态码和耗时信息。

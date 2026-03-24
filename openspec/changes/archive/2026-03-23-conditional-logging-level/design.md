## Context

当前系统中，`src/main.py` 在处理 `/v1/` 请求和捕获响应时，会使用 `logger.info` 记录请求/响应的 Header 和 Body。
由于 `config.LOG_LEVEL` 默认为 `INFO`，这些庞大的数据段总是会输出到日志文件。

## Goals / Non-Goals

**Goals:**
- 将详细的交互日志（Header, Body）记录级别从 `INFO` 降为 `DEBUG`。
- 确保 `INFO` 级别日志仅包含摘要信息（路径、方法、状态码、耗时）。

**Non-Goals:**
- 修改 `ENABLE_CHAT_LOGS` 的逻辑（YAML/TXT 文件的生成仍然受该开关控制）。
- 更改 `loguru` 的基础配置。

## Decisions

- **Decision 1: 修改 logger 级别**
  - **Rationale**: 直接利用 `loguru` 的级别过滤机制。将 `logger.info` 改为 `logger.debug` 后，当 `LOG_LEVEL=INFO` 时，这些语句将不会执行任何输出操作，性能损耗极小。
  - **Alternatives**: 
    - 使用 `if config.LOG_LEVEL == "DEBUG":` 手动检查。缺点是代码冗余，且 `loguru` 本身已经优化了级别检查。

- **Decision 2: 保持摘要日志为 INFO**
  - **Rationale**: 运维人员仍需知道请求是否成功及其耗时。

## Risks / Trade-offs

- **[Risk]** → 如果排查线上问题时需要 Body 信息，必须重启服务或动态调整环境变量为 `DEBUG`。
- **[Mitigation]** → 如果开启了 `ENABLE_CHAT_LOGS`，YAML 文件中仍然存有完整数据。

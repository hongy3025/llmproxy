## 1. Implement Logging Level Changes

- [x] 1.1 Modify `src/main.py`: Change request header and body logging from `logger.info` to `logger.debug` in `proxy_v1_request`.
- [x] 1.2 Modify `src/main.py`: Change response header and body logging from `logger.info` to `logger.debug` in `response_stream_wrapper`.
- [x] 1.3 Modify `src/main.py`: Change header and body logging in `catch_all_request`.

## 2. Verification

- [x] 2.1 Start service with `LOG_LEVEL=INFO` and verify that headers/bodies are NOT in `app.log`.
- [x] 2.2 Start service with `LOG_LEVEL=DEBUG` and verify that headers/bodies ARE in `app.log`.

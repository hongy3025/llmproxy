# Capability: Chat Interaction Recorder

## Purpose
This capability intercepts chat interaction requests and responses for logging and debugging purposes.

## Requirements

### Requirement: Session-based Chat Interaction Logging
The system SHALL intercept `/v1/chat/completions` requests and log the request body and the complete response body, associated with a session ID, ONLY when `ENABLE_CHAT_LOGS` is set to `True`.

#### Scenario: Non-streaming chat completion logging
- **WHEN** a client sends a non-streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `True`
- **THEN** the proxy logs the request JSON and the full response JSON in a session-specific log file

#### Scenario: Skipping non-streaming chat completion logging
- **WHEN** a client sends a non-streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `False`
- **THEN** the proxy DOES NOT create a session-specific log file

### Requirement: Streaming Chat Interaction Logging
The system SHALL intercept streaming `/v1/chat/completions` requests and log the request body and the reconstructed full response body from the stream chunks, ONLY when `ENABLE_CHAT_LOGS` is set to `True`.

#### Scenario: Streaming chat completion logging
- **WHEN** a client sends a streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `True`
- **THEN** the proxy logs the request JSON and assembles the stream chunks to log the final complete response content

#### Scenario: Skipping streaming chat completion logging
- **WHEN** a client sends a streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `False`
- **THEN** the proxy DOES NOT create a session-specific log file

### Requirement: Professional Event Logging
The system SHALL use `loguru` to log server events (startup, errors, request routing) with appropriate log levels.

#### Scenario: Logging server startup
- **WHEN** the server starts
- **THEN** an INFO level log entry is generated via `loguru` showing the listening address

### Requirement: Conditional Detail Logging
The system SHALL log full request and response headers and bodies in the application log ONLY when the log level is set to `DEBUG`.

#### Scenario: Detail logging at DEBUG level
- **WHEN** the `LOG_LEVEL` environment variable is set to `DEBUG`
- **THEN** the application log includes full request headers, request bodies, response headers, and response bodies

#### Scenario: No detail logging at INFO level
- **WHEN** the `LOG_LEVEL` environment variable is set to `INFO` (or any level above `DEBUG`)
- **THEN** the application log DOES NOT include full request/response headers or bodies, but still includes request summary information (method, path, agent, status, duration)

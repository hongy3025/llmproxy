## MODIFIED Requirements

### Requirement: Session-based Chat Interaction Logging
The system SHALL intercept `/v1/chat/completions` requests and log the request body and the complete response body, associated with a session ID, ONLY when `ENABLE_CHAT_LOGS` is set to `True`. The log entry SHOULD now include more metadata such as the inferred agent client type and duration.

#### Scenario: Non-streaming chat completion logging
- **WHEN** a client sends a non-streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `True`
- **THEN** the proxy logs the request JSON, the full response JSON, and metadata (agent_type, duration) in a session-specific log file

#### Scenario: Skipping non-streaming chat completion logging
- **WHEN** a client sends a non-streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `False`
- **THEN** the proxy DOES NOT create a session-specific log file

### Requirement: Streaming Chat Interaction Logging
The system SHALL intercept streaming `/v1/chat/completions` requests and log the request body and the reconstructed full response body from the stream chunks, ONLY when `ENABLE_CHAT_LOGS` is set to `True`. The log entry SHOULD now include more metadata such as the inferred agent client type, total duration, and number of chunks.

#### Scenario: Streaming chat completion logging
- **WHEN** a client sends a streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `True`
- **THEN** the proxy logs the request JSON and assembles the stream chunks to log the final complete response content with metadata (agent_type, duration, chunk_count)

#### Scenario: Skipping streaming chat completion logging
- **WHEN** a client sends a streaming POST request to `/v1/chat/completions` AND `ENABLE_CHAT_LOGS` is `False`
- **THEN** the proxy DOES NOT create a session-specific log file

## MODIFIED Requirements

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

# Capability: Chat Interaction Recorder

## Purpose
This capability intercepts chat interaction requests and responses for logging and debugging purposes.

## Requirements

### Requirement: Session-based Chat Interaction Logging
The system SHALL intercept `/v1/chat/completions` requests and log the request body and the complete response body, associated with a session ID.

#### Scenario: Non-streaming chat completion logging
- **WHEN** a client sends a non-streaming POST request to `/v1/chat/completions`
- **THEN** the proxy logs the request JSON and the full response JSON in a session-specific log file

### Requirement: Streaming Chat Interaction Logging
The system SHALL intercept streaming `/v1/chat/completions` requests and log the request body and the reconstructed full response body from the stream chunks.

#### Scenario: Streaming chat completion logging
- **WHEN** a client sends a streaming POST request to `/v1/chat/completions`
- **THEN** the proxy logs the request JSON and assembles the stream chunks to log the final complete response content

### Requirement: Professional Event Logging
The system SHALL use `loguru` to log server events (startup, errors, request routing) with appropriate log levels.

#### Scenario: Logging server startup
- **WHEN** the server starts
- **THEN** an INFO level log entry is generated via `loguru` showing the listening address

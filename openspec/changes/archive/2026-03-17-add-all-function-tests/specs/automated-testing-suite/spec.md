## ADDED Requirements

### Requirement: Configuration Validation
The system SHALL correctly load configuration from environment variables or use default values.

#### Scenario: Load default configuration
- **WHEN** no environment variables are set
- **THEN** `Config` object uses default values (e.g., `BACKEND_URL` is `http://192.168.1.2:18085/v1`)

#### Scenario: Load from environment variables
- **WHEN** `BACKEND_URL` is set to `http://test-backend/v1`
- **THEN** `Config.BACKEND_URL` reflects this value

### Requirement: Session ID Extraction
The system SHALL extract session IDs from multiple sources in the request.

#### Scenario: Extract from X-Session-ID header
- **WHEN** a request has `X-Session-ID: test-session`
- **THEN** `extract_session_id` returns `test-session`

#### Scenario: Extract from request body session_id
- **WHEN** a request body has `{"session_id": "body-session"}`
- **THEN** `extract_session_id` returns `body-session`

#### Scenario: Extract from request body user
- **WHEN** a request body has `{"user": "user-session"}`
- **THEN** `extract_session_id` returns `user-session`

#### Scenario: Fallback to UUID
- **WHEN** no session identifier is found
- **THEN** `extract_session_id` returns a valid UUID string

### Requirement: Interaction Logging
The system SHALL log interactions in JSON format.

#### Scenario: Successful non-stream logging
- **WHEN** `log_interaction` is called with session ID, request data, and response data
- **THEN** a JSON log entry is generated with timestamp, session_id, and data

### Requirement: Stream Response Logging
The system SHALL aggregate stream chunks and log the complete response.

#### Scenario: Successful stream logging
- **WHEN** `log_stream_response` processes multiple chunks
- **THEN** it yields each chunk and logs the aggregated content at the end

### Requirement: Proxy Routing
The system SHALL correctly route and proxy requests to the backend.

#### Scenario: Proxy /v1 requests
- **WHEN** a request is made to `/v1/chat/completions`
- **THEN** it is proxied to the backend and recorded if successful

#### Scenario: Catch-all proxy
- **WHEN** a request is made to `/other-path`
- **THEN** it is proxied to the backend root (above /v1)

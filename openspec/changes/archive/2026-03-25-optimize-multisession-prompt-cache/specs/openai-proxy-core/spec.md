## MODIFIED Requirements

### Requirement: Transparent Request Forwarding
The system SHALL forward incoming requests (methods, headers, bodies) to `http://192.168.1.2:18085/v1` and return the backend's response transparently, EXCEPT for `/v1/chat/completions` which is orchestrated by the proxy for prompt caching.

#### Scenario: GET request to models endpoint
- **WHEN** a client sends `GET /v1/models` to the proxy
- **THEN** the proxy sends `GET http://192.168.1.2:18085/v1/models` and returns the backend response transparently

#### Scenario: Request to chat completions endpoint
- **WHEN** a client sends `POST /v1/chat/completions` to the proxy
- **THEN** the proxy does NOT transparently forward it, but orchestrates the call using low-level llama-server endpoints

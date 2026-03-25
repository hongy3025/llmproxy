# Capability: OpenAI Proxy Core

## Purpose
This capability handles basic proxying functionality, forwarding incoming requests to a backend service.

## Requirements

### Requirement: Proxy Server Listening
The system SHALL listen for HTTP requests on `0.0.0.0:8080/v1`.

#### Scenario: Server starts and accepts connections
- **WHEN** the application is started
- **THEN** it should be reachable at `http://localhost:8080/v1`

### Requirement: Transparent Request Forwarding
The system SHALL forward incoming requests (methods, headers, bodies) to `http://192.168.1.2:18085/v1` and return the backend's response transparently, EXCEPT for `/v1/chat/completions` which is orchestrated by the proxy for prompt caching.

#### Scenario: GET request to models endpoint
- **WHEN** a client sends `GET /v1/models` to the proxy
- **THEN** the proxy sends `GET http://192.168.1.2:18085/v1/models` and returns the backend response transparently

#### Scenario: Request to chat completions endpoint
- **WHEN** a client sends `POST /v1/chat/completions` to the proxy
- **THEN** the proxy does NOT transparently forward it, but orchestrates the call using low-level llama-server endpoints

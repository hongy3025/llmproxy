## ADDED Requirements

### Requirement: Proxy Server Listening
The system SHALL listen for HTTP requests on `0.0.0.0:8080/v1`.

#### Scenario: Server starts and accepts connections
- **WHEN** the application is started
- **THEN** it should be reachable at `http://localhost:8080/v1`

### Requirement: Transparent Request Forwarding
The system SHALL forward all incoming requests (methods, headers, bodies) to `http://192.168.1.2:18085/v1` and return the backend's response transparently.

#### Scenario: GET request to models endpoint
- **WHEN** a client sends `GET /v1/models` to the proxy
- **THEN** the proxy sends `GET http://192.168.1.2:18085/v1/models` and returns the backend response

## ADDED Requirements

### Requirement: Conditional Detail Logging
The system SHALL log full request and response headers and bodies in the application log ONLY when the log level is set to `DEBUG`.

#### Scenario: Detail logging at DEBUG level
- **WHEN** the `LOG_LEVEL` environment variable is set to `DEBUG`
- **THEN** the application log includes full request headers, request bodies, response headers, and response bodies

#### Scenario: No detail logging at INFO level
- **WHEN** the `LOG_LEVEL` environment variable is set to `INFO` (or any level above `DEBUG`)
- **THEN** the application log DOES NOT include full request/response headers or bodies, but still includes request summary information (method, path, agent, status, duration)

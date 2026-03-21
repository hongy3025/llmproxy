## ADDED Requirements

### Requirement: Global Logging Toggle
The system SHALL provide a global configuration setting `ENABLE_CHAT_LOGS` to control whether chat interactions are recorded.

#### Scenario: Enable chat logging
- **WHEN** `ENABLE_CHAT_LOGS` is set to `True`
- **THEN** chat interactions (both .txt and .yaml) are saved to the log directory

#### Scenario: Disable chat logging
- **WHEN** `ENABLE_CHAT_LOGS` is set to `False`
- **THEN** no chat interaction files are created in the log directory

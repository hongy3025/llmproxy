# Capability: Multisession Prompt Cache

## Purpose
This capability optimizes Time-to-First-Token (TTFT) for multi-session and context-switching scenarios by caching prompt token states and using `llama-server` low-level APIs for fast slot cloning via prefix matching.

## Requirements

### Requirement: Session to Slot Mapping
The system SHALL maintain a mapping between `session_id` (extracted from requests) and `llama-server` `slot` IDs.

#### Scenario: New session assigned to a slot
- **WHEN** a request arrives with a new `session_id`
- **THEN** the system allocates an available slot or clones the best-matching slot for this session

### Requirement: Prompt Prefix Matching and Slot Cloning
The system SHALL use prefix matching of token arrays to find the most suitable existing slot to clone for a new session, to reduce TTFT.

#### Scenario: Existing slot with matching prefix found
- **WHEN** a new session requests completion and there is an existing slot with a matching token prefix
- **THEN** the system saves the state of the matching slot, loads it into a new available slot, and assigns the new slot to the session

### Requirement: Proxy Orchestration for Chat Completions
The system SHALL intercept `/v1/chat/completions` requests and orchestrate calls to `llama-server`'s `/apply-template`, `/tokenize`, and `/completion` endpoints.

#### Scenario: Client requests chat completion
- **WHEN** a client sends a `POST /v1/chat/completions` request
- **THEN** the proxy applies the template, tokenizes the prompt, manages the slot state, and calls the slot-specific completion endpoint to return the response

### Requirement: Concurrency Control for Slot Management
The system SHALL ensure that slot state queries, allocations, and cloning operations are thread-safe and protected against race conditions using asynchronous locks.

#### Scenario: Concurrent requests for slot allocation
- **WHEN** multiple concurrent requests attempt to allocate or clone slots
- **THEN** the system processes these slot management operations sequentially to avoid state corruption or duplicate assignments

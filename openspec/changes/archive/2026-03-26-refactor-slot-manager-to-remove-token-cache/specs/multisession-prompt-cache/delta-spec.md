# Delta Spec: Multisession Prompt Cache

## Modified Requirements

### Requirement: Prompt Prefix Matching and Slot Cloning
- **Old**: The system SHALL use prefix matching of token arrays to find the most suitable existing slot to clone for a new session, to reduce TTFT.
- **New**: The system SHALL use prefix matching of token arrays based on **real-time** slot content from `llama-server`'s `/slots` API to find the most suitable existing slot to clone for a new session, to reduce TTFT.

#### Scenario: Existing slot with matching prefix found
- **Update**: Before performing prefix matching, the system MUST call the `/slots` API to get the latest `prompt` and `generated` strings for all slots, and tokenize these strings to obtain the current token arrays.

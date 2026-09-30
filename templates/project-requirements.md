# Project Requirements

## Goals

* [Primary goal]
* [Secondary goal]

---

## Scope

### In Scope
* [Included features or areas]

### Out of Scope
* [Excluded features or areas]

---

## Roles

| Role | Description |
|---|---|
| [Role name] | [Who this role is and what they do] |

---

## Business Processes

* **[Process name]**: [Brief description of what this process does]
* **[Process name]**: [Brief description]

---

## Functional Requirements

<!-- FR ID format: FR-<ALPHANUM> where ALPHANUM is one or more uppercase letters and/or digits.
     Examples: FR-001, FR-A01, FR-I03, FR-D02. Both pure-numeric and letter-prefixed IDs are valid.

     Requirement text follows EARS (Easy Approach to Requirements Syntax) — pick the pattern
     that matches the requirement, don't force every line into "WHEN...SHALL":
       Ubiquitous        — THE SYSTEM SHALL [response] (always true, no trigger/condition)
       Event-driven      — WHEN [trigger/event], THE SYSTEM SHALL [response]
       State-driven      — WHILE [state/condition], THE SYSTEM SHALL [response]
       Unwanted behavior — IF [trigger], THEN THE SYSTEM SHALL [response]
       Optional feature  — WHERE [feature is included], THE SYSTEM SHALL [response]
     "SHALL" = mandatory (same weight as the old "MUST"); reserve "SHOULD" for non-binding intent. -->

* **FR-001**: WHEN [trigger/event occurs], THE SYSTEM SHALL [expected response]
* **FR-002**: WHILE [state/condition holds], THE SYSTEM SHALL [expected response]
* **FR-A01**: IF [unwanted trigger occurs], THEN THE SYSTEM SHALL [expected response] — example of letter-prefixed FR ID
* **FR-003**: [NEEDS CLARIFICATION: describe what is unclear]

---

## Non-Functional Requirements

* **Performance**: [e.g., Web App: p95 < 200ms | CLI: execution < 5s | Pipeline: 1M rows in < 10min | LLM App: first token < 2s]
* **Availability**: [e.g., 99.9% uptime | N/A for CLI Tool / Library]
* **Security**: [e.g., Web App: JWT on all endpoints | Pipeline: encrypted credentials | LLM App: no PII in prompts]
* **Scalability**: [e.g., Web App: 10,000 concurrent users | Pipeline: 100M rows per run | LLM App: 50 concurrent sessions]

---

## Edge Cases

### Empty and missing input
* [Scenario] → [Expected behaviour]

### Permission boundaries
* [Scenario] → [Expected behaviour]
* *(Skip if project type has no auth — e.g., CLI Tool, Library, Data Pipeline)*

### Concurrency and race conditions
* [Scenario] → [Expected behaviour]

### External dependency failures
* [Scenario] → [Expected behaviour]
* *(For AI / LLM App: include LLM API timeout and content filter block)*

### State machine violations
* [Scenario] → [Expected behaviour]
* *(Skip if project has no state machine — e.g., Library, CLI Tool, AI / LLM App)*

### Data contract violations
* [Scenario] → [Expected behaviour]
* *(Applies to Data Pipeline, ML Pipeline, AI / LLM App with RAG)*

---

## Acceptance Criteria

* **AC-001**: Given [initial state], When [action], Then [expected result]
* **AC-002**: Given [initial state], When [action], Then [expected result]

---

## Assumptions

* [Assumption]
* [Assumption]

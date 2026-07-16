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

* **FR-001**: [What the system MUST do]
* **FR-002**: [What the system MUST do]
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

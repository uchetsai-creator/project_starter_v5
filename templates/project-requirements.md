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

## User Journeys

<!-- One sub-heading per role task, end to end: who does it, why, the steps, and the result.
     This is what a reader needs first to understand what the system is for.
     verify_requirements_form.py requires at least one sub-heading here. -->

### [Role] — [task they are trying to finish]
* **Who**: [role]
* **Goal**: [what they want to achieve and why]
* **Steps**: 1. [step] 2. [step] 3. [step]
* **Result**: [what they have at the end]

---

## Slices

<!-- A slice is one behavior an external observer can check from the system's entry point,
     without reading the code — the unit that requirements are grouped by and that one
     milestone in project-plan.md delivers. Same definition for every project type; the
     observer and entry point nouns come from guidance/decomposition/[project-type].md
     (e.g. web-app: user / page; cli-tool: caller / command; data-pipeline: downstream
     consumer / output table; library: developer / public function).

     Rules (full method: guidance/decomposition/common.md):
       - One behavior per slice, statable in one sentence without "and".
       - Independent Test: how the slice is verified from its entry point if built alone.
       - P1 = the smallest slice worth shipping alone; P2+ follow.
       - Every FR below sits under exactly one slice heading; every AC under the slice it checks. -->

| Slice | Behavior | Observer | Entry point | Priority | Independent Test |
|---|---|---|---|---|---|
| SL-1 | [One observable behavior] | [Who sees it] | [Where they meet the system] | P1 | [How to verify it from the entry point alone] |
| SL-2 | [One observable behavior] | [Who sees it] | [Where they meet the system] | P2 | [How to verify it from the entry point alone] |

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
     "SHALL" = mandatory (same weight as the old "MUST"); reserve "SHOULD" for non-binding intent.
     One FR = one SHALL: if a requirement needs "and also", split it.

     Group FRs under a `### SL-n — <slice behavior>` sub-heading per slice (see ## Slices).
     Keep the FR ids bold and inside this section — verify_acceptance.py reads them from here. -->

### SL-1 — [Slice behavior]

* **FR-001**: WHEN [trigger/event occurs], THE SYSTEM SHALL [expected response]
* **FR-002**: WHILE [state/condition holds], THE SYSTEM SHALL [expected response]

* **Scenario**: [name of the scenario]
  * **Given** [initial state], **When** [action], **Then** [observable outcome]

### SL-2 — [Slice behavior]

* **FR-A01**: IF [unwanted trigger occurs], THEN THE SYSTEM SHALL [expected response] — example of letter-prefixed FR ID
* **FR-003**: [NEEDS CLARIFICATION: describe what is unclear]

<!-- Scenarios: at least one per slice, Given / When / Then, using the same behaviour as the FRs above. -->
* **Scenario**: [name of the scenario]
  * **Given** [initial state], **When** [action], **Then** [observable outcome]

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

<!-- Group ACs under the same `### SL-n` sub-headings as the FRs, and name the FR each AC
     checks in parentheses after the id. Cover the failure cases that matter, not only the
     happy path — each Guard task in project-plan.md covers at least one of these. -->

### SL-1 — [Slice behavior]

* **AC-001** (FR-001): Given [initial state], When [action], Then [expected result]

### SL-2 — [Slice behavior]

* **AC-002** (FR-A01): Given [initial state], When [action], Then [expected result]

---

## Assumptions

* [Assumption]
* [Assumption]

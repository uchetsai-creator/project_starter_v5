# Prompt Library

<!--
  For: AI / LLM Application
  Purpose: Version-controlled store of all prompt templates used by the application.
           Each entry has an ID, version, variables, example I/O, and test cases.
           When a prompt changes, add a new version entry — do not overwrite the old one.
  Update when: A prompt template is added, changed, or retired.
-->

## Prompt Naming Convention

```
[feature]-[purpose]-v[N]
```

Examples: `financial-advice-system-v2`, `rag-synthesis-v1`, `intent-classifier-v3`

---

## Active Prompts

| ID | Version | Purpose | Status |
|---|---|---|---|
| [prompt-id] | v1 | [what it does] | Active |
| [prompt-id] | v2 | [updated version] | Active |

---

## Prompt Entries

### `[prompt-id]` — v[N]

**Purpose:** [One line — what this prompt makes the model do]

**Used by:** [which feature or module invokes this prompt]

**Input variables:**

| Variable | Type | Description |
|---|---|---|
| `{{variable_name}}` | string | [what to inject here] |
| `{{variable_name}}` | list | [what to inject here] |

**Template:**

```
[Full prompt text with {{variable}} placeholders.
Keep the template exactly as sent to the model — do not paraphrase.]
```

**Example input:**

```json
{
  "variable_name": "example value",
  "variable_name": ["item1", "item2"]
}
```

**Example output (expected):**

```
[Paste a representative model response for the example input above.]
```

**Test cases:**

| # | Input | Expected behaviour | Pass/Fail |
|---|---|---|---|
| 1 | [input description] | [what a good response looks like] | |
| 2 | [edge case input] | [expected handling] | |

**Version history:**

| Version | Date | Change | Reason |
|---|---|---|---|
| v1 | [YYYY-MM-DD] | Initial | |
| v2 | [YYYY-MM-DD] | [what changed] | [why — e.g., eval score improved / added guardrail] |

---

## Retired Prompts

| ID | Last version | Retired date | Replaced by | Reason |
|---|---|---|---|---|
| [prompt-id] | v2 | [YYYY-MM-DD] | [new-prompt-id] | [e.g., model change required rewrite] |

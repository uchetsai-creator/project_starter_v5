# Document Purposes — AI / LLM Application

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to AI / LLM Application projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

---

## Specs (docs/specs/)

### llm-contract.md
**Applies to: AI / LLM Application**

Purpose:
Single source of truth for how the LLM is invoked — model ID, system prompt (full text),
inference parameters (temperature, top_p, max_tokens), tool/function schemas, context window
strategy, and retry/fallback behaviour. Version this document whenever the system prompt or
model changes so prompt iterations can be compared against a known baseline.

Update when (update at task level — this is a core spec for LLM applications):
* The model or provider is changed
* The system prompt is modified (bump version, keep old version in Version history)
* Inference parameters (temperature, max_tokens, etc.) are tuned
* A tool / function schema is added, changed, or removed
* The context window or retry strategy changes

### prompt-library.md
**Applies to: AI / LLM Application**

Purpose:
Index of all prompt templates — lists what exists and defines the naming rules.
Does not contain prompt content. Actual prompt content lives in individual
`docs/specs/prompts/[prompt-id]-prompt.md` files so the index stays small
and the agent does not need to load all prompt text on every task.

Update when (update at task level):
* A new prompt file is created — add a row to the Active Prompts table
* A prompt's current version changes — update the version column
* A prompt is retired — move its row to the Retired Prompts table

### [prompt-id]-prompt.md
**Applies to: AI / LLM Application**
**Location: `docs/specs/prompts/[prompt-id]-prompt.md`**

Purpose:
One file per prompt. Contains the full prompt template text, input variable definitions,
an example input/output pair, test cases, and version history.
Agent loads only the specific prompt file it needs — not the whole library.
When a prompt changes, a new version entry is added to the Version History table;
old version text is kept so changes can be audited and rolled back.

Update when (update at task level):
* The prompt template text is changed — add a new version row, do not overwrite old text
* Input variables are added, removed, or renamed
* A test case is added (never remove existing test cases)
* After updating: verify the row in prompt-library.md shows the new current version

### eval-spec.md
**Applies to: AI / LLM Application**

Purpose:
Stable configuration for LLM-as-a-judge evaluation: judge model, scoring criteria with
rubrics (1–5 scale), the judge prompt template, and the fixed test case set.
This file changes rarely — only when criteria or the judge model change.
Eval run results are appended to eval-log.md, not here.

Update when (update at task level):
* A new eval criterion is added or an existing rubric is changed
* The judge model is changed
* Test cases are added to the fixed set (never remove existing cases)

### eval-log.md
**Applies to: AI / LLM Application**

Purpose:
Append-only log of every eval run result — one row per run.
Kept separate from eval-spec.md so the agent does not need to load the growing
run history on every task; it loads this file only when comparing prompt versions.

Update when:
* An eval run completes — append one row with date, prompt version, scores, and pass/fail.
  Never edit existing rows.

### rag-contract.md
**Applies to: AI / LLM Application (optional — only when using Retrieval-Augmented Generation)**

Purpose:
Documents the retrieval pipeline end-to-end: knowledge sources and their update frequency,
chunking strategy, embedding model, vector store configuration (similarity metric, threshold,
top-K), how retrieved chunks are formatted and injected into the prompt, and failure handling
when retrieval returns nothing or the vector store is unavailable.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new knowledge source is added or an existing one is changed
* Chunking strategy or chunk size is changed
* The embedding model is changed (triggers full re-embedding)
* Similarity threshold or top-K is tuned
* A retrieval failure mode is discovered and handled

### llm-debug.md
**Applies to: AI / LLM Application**

Purpose:
Step-by-step debug guide for LLM response failures, retrieval issues, tool call failures,
and eval score regressions. Covers how to identify the failure type, debug the retriever,
inspect the rendered prompt, trace tool calls, read eval results, and diagnose API errors.
Also defines the structured log format for every LLM call.
Load this file only when debugging an active incident — not during normal task work.

Update when:
* A new failure pattern is discovered and confirmed — add a row to the relevant step's table.
* The LLM provider, retrieval tool, or eval tool changes — update the affected steps.

### mcp-contract.md
**Applies to: AI / LLM Application (optional — only when connecting to one or more MCP servers)**

Purpose:
Documents every MCP (Model Context Protocol) server this app connects to: transport type
(stdio command or SSE/HTTP URL), each server's exposed tools (with JSON Schema), resources
(URI templates), and prompt templates. Also records the tool-use policy (max calls per turn,
which tools need user confirmation) and failure handling per scenario.
Kept separate from llm-contract.md so server connection details can change independently
of the model config and system prompt.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* An MCP server is added, removed, or its package version is pinned
* A tool schema changes (new parameter, renamed field, changed type)
* Transport changes (stdio → SSE, command args change)
* Tool-use policy is tuned (call limits, confirmation requirements)
* A new failure mode is discovered and handled

### logging-spec.md
→ See `document-purposes-common.md § Specs — logging-spec.md`.
AI / LLM App addition: also covers structured log format for every LLM call (see also `llm-debug.md`).
Update also when: LLM call log format changes.

# LLM Contract

<!--
  For: AI / LLM Application
  Purpose: Documents the model configuration, system prompt, parameters, and tool calling spec.
           This is the single source of truth for how the LLM is invoked — version it when any
           of these change so prompt iterations can be compared against a known baseline.
  Update when: Model is swapped, system prompt is changed, parameters are tuned,
               tools / function schemas are added or removed.
-->

## Model Configuration

| Property | Value |
|---|---|
| Provider | [e.g., Anthropic, OpenAI, local Ollama] |
| Model ID | [e.g., claude-opus-4-7, gpt-4o, llama3.2] |
| API endpoint | [URL or SDK reference] |
| Context window | [tokens — e.g., 200k] |
| Max output tokens | [tokens] |

---

## Parameters

| Parameter | Value | Rationale |
|---|---|---|
| temperature | [0.0–2.0] | [why — e.g., 0.3 for factual, 0.8 for creative] |
| top_p | [0.0–1.0] | [note if not used] |
| max_tokens | [tokens] | [upper bound per response] |
| stop sequences | [list or "none"] | |

---

## System Prompt

Version: `[v1 / date / git tag]`

> **If the system prompt exceeds ~400 tokens:** store it in a separate file
> (`docs/specs/system-prompt-[version].md`) and reference it here by path.
> Paste only the current version inline when it fits within one screen.

```
[Paste the full system prompt here.
Include persona, domain constraints, tone, and any output format instructions.]
```

**Key design decisions in this prompt:**

| Decision | Rationale |
|---|---|
| [e.g., "Always add a risk disclaimer"] | [e.g., Regulatory / personal safety] |
| [e.g., "Refuse to give specific buy/sell targets"] | [e.g., Out of scope, liability] |

---

## Tool Calling / Function Schemas

<!--
  Two cases — use whichever applies:

  A. Direct function calling (tools defined inline in the API call):
     Document each tool schema below.

  B. Tools sourced from MCP servers:
     List only the tool names and which server they come from here.
     Full schemas, transport config, and tool-use policy live in mcp-contract.md.
     → docs/specs/mcp-contract.md

  If using both, note which tools are inline vs. MCP-sourced.
-->

[List each tool the model can call. Skip this section if no tools are used.]

### Tool: `[tool_name]`

```json
{
  "name": "[tool_name]",
  "description": "[what this tool does and when the model should call it]",
  "input_schema": {
    "type": "object",
    "properties": {
      "[param]": { "type": "[string|number|boolean]", "description": "[what it means]" }
    },
    "required": ["[param]"]
  }
}
```

---

## Context Window Strategy

How conversation history is managed when context grows long:

| Strategy | Detail |
|---|---|
| History trimming | [e.g., keep last N turns / summarize oldest turns / sliding window] |
| System prompt position | [always first / re-injected every N turns] |
| RAG injection point | [before user message / after system prompt — if applicable] |

---

## Streaming

| Property | Value |
|---|---|
| Streaming enabled | [Yes / No] |
| Partial render | [Yes — UI updates as tokens arrive / No — wait for full response] |

---

## Retry and Fallback

| Scenario | Behaviour |
|---|---|
| API timeout / 5xx | [retry N times with exponential backoff] |
| Rate limit (429) | [wait and retry / surface error to user] |
| Content filter block | [surface refusal message / fallback response] |
| Model unavailable | [fallback to: [model ID] / fail with error] |

---

## Non-Functional Requirements

| Metric | Requirement |
|---|---|
| Time to first token (streaming) | < [e.g., 2s] at p95 |
| Full response time (non-streaming) | < [e.g., 15s] at p95 for typical prompt |
| Cost per call | < [e.g., $0.01] for typical request (input + output tokens) |
| Availability | Follows provider SLA — [e.g., 99.9%] |
| Max prompt length enforced by app | [e.g., 2000 tokens for user message] |

---

## Edge Cases

| Scenario | Expected behaviour |
|---|---|
| User message pushes context over window limit | Trim oldest history turns; always preserve system prompt + latest turn |
| Model returns empty response body | Retry once; if still empty, return fallback message |
| Content filter triggered on **user prompt** | Return `CONTENT_BLOCKED`; do not retry |
| Content filter triggered on **model response** | Retry once with shorter context; if blocked again, return fallback |
| Tool call returns an error | Pass error as tool result in next turn; let model decide how to proceed |
| Tool call loop (model calls same tool repeatedly) | Abort after [N] iterations; return partial result with `"loop_detected": true` |
| Prompt injection in user input | [Describe mitigation — e.g., system-prompt hardening, input sanitisation, label injection attempts] |
| Model returns malformed JSON (structured output mode) | Retry with explicit `"Return valid JSON only."` reminder; fail after [3] retries |
| API key expired or invalid | Fail immediately with `AUTH_INVALID` — do not retry |
| Response contains PII (if applicable) | [Scrub before storing / log and alert / reject response] |

---

## Examples

### Typical single-turn interaction

**User message:**
```
[Example user message — use a representative real-world input]
```

**System prompt (excerpt):**
```
[First 2–3 lines of system prompt]
```

**Model response:**
```
[Example model response]
```

---

### Tool call interaction

**User message:** `[message that triggers tool use]`

**Model calls:**
```json
{ "name": "[tool_name]", "input": { "[param]": "[value]" } }
```

**Tool returns:**
```json
{ "[result_field]": "[value]" }
```

**Final model response:** `[model response incorporating tool result]`

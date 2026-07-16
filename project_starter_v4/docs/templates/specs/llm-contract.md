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

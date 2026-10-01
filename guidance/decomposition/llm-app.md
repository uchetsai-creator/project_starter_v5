# Decomposition — AI / LLM App

Nouns for `guidance/decomposition/common.md`.

- **Observer:** the end user of the assistant, or the eval suite standing in for them
- **Entry point:** a conversation turn / API call, or a tool the model can call
- **Independent Test:** run the eval cases for this behavior and check the pass rate; LLM output
  is non-deterministic, so the check is a rate over cases, not one response

## Artifact kinds

| Kind | Prefix | In an LLM app | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Tool schema, structured output schema, `llm-contract.md` | Schema test: output parses into the declared structure |
| State | `STATE` | Vector index, document store, conversation memory | Retrieval test: known query returns the known chunk |
| Logic | `LOGIC` | Prompt, chain / agent step, retrieval logic | Eval cases: pass rate ≥ threshold in `eval-spec.md` |
| Entry | `ENTRY` | Endpoint or UI hook, tool registration | Integration test: request returns a model answer |
| Guard | `GUARD` | Content filtering, refusal handling, timeout / fallback, PII scrubbing | Eval cases: unsafe input → refusal; API timeout → fallback |

New or changed eval cases are written before the prompt change (the first failing check).
Append each eval run to `eval-log.md`.

## Typical Guard cases

- Model API timeout / rate limit → retry, then a fallback message
- Answer without a supporting source → refuse or say it does not know
- PII in user input → scrubbed before it reaches the prompt or logs

## Example slice

```
SL-1 (P1)  Pricing answers cite a source document
  Independent Test: run the 20 pricing eval cases → ≥ 90% include a valid citation
  Task STATE    [SL-1] index pricing documents                     Covers: FR-002
  Task LOGIC    [SL-1] retrieval + citation prompt                 Covers: FR-002, AC-003
  Task GUARD    [SL-1] no source found → "I don't know"            Covers: AC-004
```

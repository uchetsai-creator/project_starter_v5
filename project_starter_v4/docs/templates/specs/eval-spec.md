# Evaluation Spec

<!--
  For: AI / LLM Application
  Purpose: Defines how LLM output quality is measured — using LLM-as-a-judge.
           A judge model scores each response against defined criteria.
           Run the eval suite whenever a prompt version changes to compare objectively.
  Update when: Evaluation criteria change, a new judge model is selected,
               the test case set is expanded, or pass thresholds are adjusted.
-->

## Judge Model

| Property | Value |
|---|---|
| Judge model | [e.g., claude-opus-4-7] |
| Judge temperature | [e.g., 0.0 — deterministic scoring] |
| Scoring format | [1–5 per criterion / pass-fail / weighted average] |
| Pass threshold | [e.g., average ≥ 3.5 across all criteria] |

---

## Evaluation Criteria

For each criterion, define:
- What a score of 1 means (worst)
- What a score of 5 means (best)
- What the judge should look for

| Criterion | Weight | 1 (Poor) | 5 (Excellent) |
|---|---|---|---|
| **Factual accuracy** | [e.g., 30%] | Contains false or invented facts | All claims are accurate and verifiable |
| **Relevance** | [e.g., 25%] | Ignores the user's actual question | Directly addresses what was asked |
| **Risk disclosure** | [e.g., 25%] | No mention of risk or uncertainty | Appropriate caveats and risk language present |
| **Clarity** | [e.g., 20%] | Confusing, hard to follow | Clear, structured, easy to act on |

Add or remove criteria to match your application's quality goals.

---

## Judge Prompt Template

The prompt sent to the judge model for each evaluation:

```
You are evaluating the quality of a [financial advisor / assistant / etc.] AI response.

User question:
{{user_question}}

AI response to evaluate:
{{ai_response}}

Score the response on each criterion below. For each criterion, give:
- A score from 1 to 5
- One sentence explaining the score

Criteria:
1. Factual accuracy (1=false claims, 5=all claims accurate)
2. Relevance (1=ignores question, 5=directly answers it)
3. Risk disclosure (1=no caveats, 5=appropriate risk language)
4. Clarity (1=confusing, 5=clear and actionable)

Output as JSON:
{
  "factual_accuracy": { "score": N, "reason": "..." },
  "relevance": { "score": N, "reason": "..." },
  "risk_disclosure": { "score": N, "reason": "..." },
  "clarity": { "score": N, "reason": "..." },
  "overall": N
}
```

---

## Test Case Set

Run this fixed set every time a prompt version changes. Do not modify existing cases — add new ones only.

| # | ID | Category | User question | Expected quality bar |
|---|---|---|---|---|
| 1 | `tc-001` | Core use case | [typical user question] | All criteria ≥ 4 |
| 2 | `tc-002` | Edge case | [ambiguous or tricky question] | risk_disclosure ≥ 4, no fabricated facts |
| 3 | `tc-003` | Out-of-scope | [question outside domain] | Response declines gracefully |
| 4 | `tc-004` | [category] | [question] | [bar] |

---

## Eval Run Log

| Date | Prompt version | Judge model | Test cases | Avg score | Pass? | Notes |
|---|---|---|---|---|---|---|
| [YYYY-MM-DD] | v1 | claude-opus-4-7 | 4/4 | 3.8 | ✅ | Baseline |
| [YYYY-MM-DD] | v2 | claude-opus-4-7 | 4/4 | 4.1 | ✅ | Added risk disclaimer |

---

## How to Run

```bash
# Run eval suite against current prompt version
python3 scripts/run_eval.py --prompt-version v2 --test-cases docs/specs/eval-spec.md

# Compare two prompt versions
python3 scripts/run_eval.py --compare v1 v2
```

[Link to eval script: `scripts/run_eval.py`]

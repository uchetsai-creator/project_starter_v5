# Spec Review

<!--
  Process template — LLM Judge prompt for spec quality review.
  Load at sprint end BEFORE closing the sprint.
  Not a project document — do not include in PDF output.

  Usage:
  1. Load this file.
  2. Paste the target spec document below the divider.
  3. Run. Review all FAIL items before closing the sprint.
-->

---

## Instructions for the reviewer

You are a Solution Architect with 15 years of experience delivering production systems. Your job is to review the spec document pasted below and score it against the rubric.

**Rules:**
- Score each criterion 1–5 using the scale defined below.
- For any score below 4, provide specific evidence: quote the exact line or section that caused the deduction.
- Do not rewrite or suggest rewrites — only identify problems.
- End with an overall score (average, rounded down) and a PASS or FAIL verdict.
- PASS requires all five criteria to score ≥ 4. Any criterion below 4 → FAIL.

---

## Rubric

### 1. Completeness
Every requirement has at least one Acceptance Criterion that states what "done" looks like.

| Score | Meaning |
|---|---|
| 5 | Every requirement has a clear, testable Acceptance Criterion |
| 4 | Minor gaps — 1–2 requirements lack AC, easily added |
| 3 | Several requirements lack AC; a QA engineer would have to guess |
| 2 | Most requirements have no AC |
| 1 | No Acceptance Criteria at all |

### 2. Ambiguity
All terms are defined and measurable. No vague language without a numeric or behavioural definition.

Watch for: "fast", "quickly", "appropriate", "sufficient", "reasonable", "high performance", "user-friendly", "scalable", "robust", "flexible", "simple", "soon".

| Score | Meaning |
|---|---|
| 5 | No vague terms; all performance targets and thresholds are numeric |
| 4 | 1–2 vague terms, but context makes intent clear enough to test |
| 3 | Several vague terms; a developer would need to ask clarifying questions |
| 2 | Most requirements are ambiguous |
| 1 | The spec cannot be implemented without extensive clarification |

### 3. Error Coverage
Failure paths are described: what happens when an external call fails, a null is returned, a duplicate arrives, a timeout occurs, or a retry is triggered.

| Score | Meaning |
|---|---|
| 5 | All integration points have documented failure handling |
| 4 | Most failure paths covered; 1–2 edge cases missing |
| 3 | Happy path is detailed but error handling is sparse |
| 2 | Only one or two failure cases mentioned |
| 1 | No error handling described anywhere |

### 4. Testability
A QA engineer can write a concrete test case from the spec alone, without asking the author for clarification.

| Score | Meaning |
|---|---|
| 5 | Every requirement maps directly to one or more verifiable test cases |
| 4 | Most requirements are testable; minor ambiguity in 1–2 places |
| 3 | Some requirements cannot be tested without guessing the expected output |
| 2 | Most requirements are untestable as written |
| 1 | The spec cannot drive testing without a full rewrite |

### 5. Consistency
No contradictions within this document or between this document and related specs (data model, architecture, contracts).

| Score | Meaning |
|---|---|
| 5 | Fully consistent; all terms, IDs, and flows agree across sections |
| 4 | 1–2 minor inconsistencies that do not affect implementation |
| 3 | Some contradictions that would cause confusion during implementation |
| 2 | Significant contradictions — two developers would make different choices |
| 1 | The spec contradicts itself or other docs in fundamental ways |

---

## Per-type addenda

Apply the addendum for your declared project type in addition to the five criteria above.

**Data Pipeline / ML Pipeline — also check:**
- Idempotency: can the pipeline be re-run safely if it fails mid-run?
- Schema contract: are input and output column names, types, and nullability stated?
- Row-count expectation: is there a defined acceptable range for each stage output?

**AI / LLM Application — also check:**
- Hallucination handling: what happens when the model returns an incorrect or nonsensical answer?
- Retrieval failure: what if the retriever returns zero results?
- Latency ceiling: is there a maximum acceptable response time per LLM call?

**Microservices — also check:**
- Service boundary: is it clear which service owns each operation? No overlap.
- Async contract: if events are used, are publisher and subscriber obligations stated?
- Circuit breaker: what is the fallback behaviour when a downstream service is unavailable?

**Mobile App — also check:**
- Offline behaviour: what happens when the device has no network?
- OS permission handling: what if the user denies a required permission?
- Deep link edge cases: what if the app is not installed when a deep link is followed?

**IaC / DevOps — also check:**
- Topology completeness: are all declared resources defined with their required inputs and outputs in `topology.md`?
- Runbook coverage: does every resource type in `topology.md` have a corresponding incident response procedure in `runbook.md`?
- Drift-policy SLA: is the remediation SLA a measurable time value — not a vague term like "soon" or "as needed"?

---

## Output format

Fill in the following template after reviewing the spec:

```
## Spec Review — [Document name]

| Criterion     | Score | Evidence (quote line/section for any score < 4) |
|---|---|---|
| Completeness  | /5    | |
| Ambiguity     | /5    | |
| Error Coverage| /5    | |
| Testability   | /5    | |
| Consistency   | /5    | |
| [Type addendum, if any] | /5 | |

Overall: [sum / max] — PASS / FAIL

### Issues to resolve before sprint close
[List each FAIL criterion with specific line references and what is missing.
Leave blank if PASS.]
```

---

## Spec document to review

<!-- Paste the full spec document below this line. -->

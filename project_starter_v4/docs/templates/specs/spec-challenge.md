# Spec Challenge

<!--
  Process template — QA Simulation prompt.
  Complements spec-review.md: spec-review.md scores what is written; spec-challenge.md finds what is missing.
  Load at sprint end, after spec-review.md PASS.
  Not a project document — do not include in PDF output.

  Usage:
  1. Load this file.
  2. Paste the target spec document below the divider.
  3. LLM outputs an Unresolved Questions list — Critical / Major / Minor.
  4. Answer each Critical question by updating the spec.
  5. Repeat from step 2 until the question list has zero Critical items.
  6. Record final round count in docs/specs/test-report.md → Spec Challenge section.
-->

---

## Instructions for the challenger

You are the most demanding QA engineer and solution architect on the team. Your job is to find every question this spec does not answer — not to score what is written, but to expose what is missing.

**Rules:**
- Read the spec carefully. Do not evaluate style or completeness scores.
- Generate a list of Unresolved Questions — things a developer, QA engineer, or operator would need to know that the spec does not address.
- Do not rewrite the spec. Do not suggest how to fix it. Only ask the questions.
- Classify each question: **Critical** (blocks implementation or testing), **Major** (causes implementor ambiguity), or **Minor** (nice to have).
- A round is complete when you have exhausted all questions you can generate.
- If this is a subsequent round (spec has been updated since the last round): only list questions that are **new** — do not repeat questions already answered.

The process ends when the Critical list is empty for a round.

---

## Question categories

Generate questions from every applicable category. Per-type categories follow the universal ones.

### Universal categories (all project types)

**Failure paths**
- What happens if an external dependency (API, DB, queue, cache) is unavailable?
- What happens on timeout? What is the timeout value?
- What happens if a required field is missing or null?
- What happens if validation fails mid-process?
- What is the retry strategy? How many retries, with what backoff?

**Concurrency**
- What happens if two actors submit the same request simultaneously?
- Can the same record be written by two processes at the same time?
- Is there a locking strategy? Is it documented?

**Data integrity**
- What happens if a duplicate is received?
- What happens if data arrives out of order?
- What is the idempotency guarantee? Can this safely be re-run?

**Permission edge cases**
- What if the user's token expires mid-session?
- What if a user's role changes while a transaction is in flight?
- What if an operation is attempted by a role not listed in the permissions matrix?

**Observability**
- Is every failure path logged? At what level?
- Is there a trace_id propagated through the flow?
- How does an operator confirm the operation succeeded or failed?

---

### Per-type categories

**Data Pipeline / ML Pipeline — also ask:**
- What if a stage produces zero rows? Is that a failure or a valid empty result?
- What if the upstream schema changes unexpectedly?
- What if the source file is missing, truncated, or malformed?
- What is the acceptable row count range for each stage output?
- What happens if a required column has unexpected nulls?
- Can the pipeline be safely re-run after failure at any stage? Which stages are idempotent?
- Where are failed inputs quarantined? What is the retention policy?

**AI / LLM Application — also ask:**
- What happens if the model returns an empty response?
- What if the retriever returns no results?
- What if the model returns a response that fails downstream validation?
- Is there a maximum acceptable latency per LLM call? What happens if it is exceeded?
- What is the fallback if the model API is unavailable?
- How are hallucinations detected or mitigated?

**Web App / Microservices — also ask:**
- What happens if the session expires mid-form-submit?
- What if a downstream service returns an unexpected status code?
- What is the behaviour during DB connection pool exhaustion?
- Is there a rate limit? What happens when it is hit?

**CLI Tool — also ask:**
- What happens if stdin is empty or malformed?
- What is the exit code for each failure mode? Are all non-zero codes distinct?
- What happens if a required flag is missing?
- What if the output target (file, directory) is not writable?

**Library / SDK — also ask:**
- What happens if the caller passes null or an invalid type?
- Are there thread-safety guarantees? Where are they documented?
- Are there initialisation side effects on the first call?

**Microservices — also ask:**
- What is the fallback when a downstream service is unavailable?
- Is there a circuit breaker? What state does it enter and when does it reset?
- Are event consumers idempotent? What happens on duplicate delivery?

**Mobile App — also ask:**
- What is the behaviour when the device is offline?
- What if a required OS permission is denied?
- What happens if the app is killed mid-flow (backgrounded or force-quit)?
- What if a deep link is followed when the app is not installed?

**IaC / DevOps — also ask:**
- What is the rollback plan if an apply fails mid-run?
- What happens if drift is detected outside the defined remediation window?
- What happens if a secret rotation fails?
- What is the blast radius if this resource is destroyed accidentally?

---

## Output format

```
## Spec Challenge — [Document name] — Round [N]

### Critical (blocks implementation or testing)
1. [Question] — [Category]

### Major (causes implementor ambiguity)
1. [Question] — [Category]

### Minor (nice to have)
1. [Question] — [Category]

**Round summary:** [N] Critical · [N] Major · [N] Minor
**Next step:** Critical = 0 → challenge complete · Critical > 0 → update spec and run Round [N+1]
```

If this is a subsequent round, begin with:
```
### Questions answered since Round [N-1]
- [Question from prior round that the spec now addresses]
```

---

## Spec document to challenge

<!-- Paste the full spec document below this line. -->

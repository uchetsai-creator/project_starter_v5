# Project Requirements

## Goals

* Predict which subscribers are likely to churn in the next 30 days so the retention
  team can prioritize outreach.
* Retrain on a monthly cadence using the latest billing and usage data, with each
  candidate model gated by fixed accuracy thresholds before promotion.

---

## Scope

### In Scope
* Daily feature extraction from billing and product-usage event data
* Monthly training of a gradient-boosted churn classifier
* Batch scoring of the active subscriber base, written to a scores table
* Experiment tracking and a documented production promotion gate

### Out of Scope
* Real-time / online scoring at signup or login time
* Automated retention actions (the model produces a score; a human team acts on it)
* Multi-tenant model personalization per customer segment (v2 candidate)

---

## Roles

| Role | Description |
|---|---|
| ML Engineer | Owns the pipeline code, feature engineering, and retraining schedule |
| Data Scientist | Designs experiments, evaluates candidate models against the contract |
| Retention Analyst | Consumes the churn-score table; does not touch the pipeline |

---

## Functional Requirements

* **FR-001**: The pipeline must extract billing and usage events for all active
  subscribers on a daily schedule and land them as a feature table.
* **FR-002**: The pipeline must train a new candidate model monthly using the trailing
  90 days of feature data.
* **FR-003**: A candidate model must be evaluated against the production thresholds in
  `model-contract.md` before it is eligible for promotion.
* **FR-004**: The pipeline must batch-score all active subscribers weekly and write
  `customer_id, churn_probability, scored_at` rows to the scores table.
* **FR-005**: Every training run must be recorded in `experiment-log.md` with its
  hypothesis, config, and result — including runs that are not promoted.

---

## Non-Functional Requirements

* **Reproducibility**: Every training run pins its feature-table snapshot version so
  results can be reproduced from the same inputs.
* **Latency**: Weekly batch scoring of ~500K subscribers completes within a 2-hour
  orchestration window.
* **Data freshness**: Feature extraction must not lag more than 24 hours behind the
  source billing/usage events.
* **Auditability**: Every promoted model version is traceable to its training run,
  config, and evaluation metrics via the MLflow run ID.

---

## Edge Cases

### Empty and missing input
* A subscriber with no usage events in the trailing window still gets scored, using
  zero-filled usage features and their billing-only features.

### Permission boundaries
* Not applicable at the pipeline layer — the scores table is read-only for downstream
  consumers; only the pipeline service account can write to it.

### Concurrency and race conditions
* If a scheduled scoring run overlaps a still-running training run, scoring uses the
  currently-promoted production model version, never a candidate still under evaluation.

### External dependency failures
* Billing API extract fails for one batch → that batch is retried up to 3 times with
  backoff; if it still fails, the DAG halts before feature engineering rather than
  training on a partial day.

### State machine violations
* A candidate model that fails the promotion gate is tagged `rejected` in the model
  registry and cannot be promoted without a new training run.

### Data contract violations
* An incoming usage event with a `customer_id` that doesn't exist in the billing table
  is quarantined to a `dead_letter` table rather than silently dropped or crashing the
  DAG.

---

## Acceptance Criteria

* **AC-001**: Given a completed training run whose validation AUC meets the threshold
  in `model-contract.md`, when the evaluation stage runs, then the model is tagged
  `production-eligible` in the registry.
* **AC-002**: Given the weekly scoring DAG runs successfully, when it completes, then
  every active subscriber has exactly one row in the scores table for that run.
* **AC-003**: Given a training run whose AUC falls below threshold, when the evaluation
  stage runs, then the model is tagged `rejected` and the DAG does not attempt promotion.

---

## Assumptions

* "Active subscriber" is defined by the billing system's own `status = active` flag,
  not inferred by the pipeline.
* The retention team consumes the scores table via a BI tool; the pipeline has no
  responsibility for how scores are visualized or acted on.

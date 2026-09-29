# Experiment Log

<!--
  For: ML Pipeline projects
  Purpose: Records each training experiment — hypothesis, config, results, and decision.
           One entry per experiment run. Newest entry at the top.
  Update when: A training run is completed.
  This is NOT a milestone-change-log. milestone-change-log tracks code changes; this tracks model behaviour.
-->

## Log Format

Each entry must include: experiment ID, date, hypothesis, config snapshot, results, and decision.

Do not record an experiment without recording its decision. "No conclusion yet" is a valid decision — it means you will run a follow-up experiment.

---

## Entries

---

### [EXP-001] [Short title describing the hypothesis]

**Date:** YYYY-MM-DD
**Run by:** [Name or team]
**Tracking URI:** [MLflow run ID / W&B run URL / S3 path to artifacts]

**Hypothesis:**
[What you expected to happen and why — one to three sentences]

**Config:**

| Parameter | Value |
|---|---|
| Model type | [e.g., XGBoost] |
| Training data | [dataset name + version / DVC tag] |
| Features | [list or reference to feature set version] |
| Hyperparameters | [key params — e.g., `max_depth=6, n_estimators=200, lr=0.1`] |
| Preprocessing | [scaler, encoder, imputation — reference to pipeline artifact] |
| Train / Val split | [e.g., 80/20 random, or time-split at YYYY-MM-DD] |

**Results:**

| Metric | Train | Validation | Test |
|---|---|---|---|
| [e.g., AUC] | [value] | [value] | [value] |
| [e.g., Precision] | [value] | [value] | [value] |
| [e.g., Recall] | [value] | [value] | [value] |
| [e.g., Latency p99] | — | — | [ms] |

**Comparison to baseline:**

| Metric | Baseline (EXP-000) | This run | Delta |
|---|---|---|---|
| AUC | [value] | [value] | [+/- value] |

**Observations:**
[What actually happened — any surprises, anomalies in training curves, data issues found]

**Decision:**
- [ ] Promote to production (meets all thresholds in model-contract.md)
- [ ] Run follow-up experiment: [EXP-XXX — what to try next]
- [ ] Discard — hypothesis disproved: [reason]

**Artifacts saved:**
- Model: [path / registry URI]
- Scaler / encoder: [path]
- Confusion matrix / feature importance: [path]

---

### [EXP-000] Baseline

**Date:** YYYY-MM-DD
**Tracking URI:** [baseline run reference]

**Hypothesis:** Establish baseline performance before any optimisation.

**Config:**

| Parameter | Value |
|---|---|
| Model type | [simplest reasonable model — e.g., LogisticRegression] |
| Training data | [dataset name + version] |
| Features | [all raw features, no engineering] |
| Hyperparameters | defaults |
| Train / Val split | [80/20 random] |

**Results:**

| Metric | Validation |
|---|---|
| [Metric] | [value] |

**Decision:** Baseline established. All future experiments compare against this run.

# Experiment Log

## Log Format

Each entry includes: experiment ID, date, hypothesis, config snapshot, results, and
decision. Newest entry first.

## Entries

### EXP-014 — Add payment-failure recency as a feature

**Date:** 2026-07-28
**Run by:** Data Science team
**Tracking URI:** MLflow run `a91f3c2` in `churn-guard` experiment

Hypothesis: Recent payment failures are a stronger churn signal than a raw 90-day count;
adding "days since last payment failure" should improve precision at the top decile.

Config:

| Parameter | Value |
|---|---|
| Model type | XGBoost |
| Training data | `churn-features` snapshot dt=2026-07-01, trailing 90 days |
| Features | baseline set + `days_since_last_payment_failure` |
| Hyperparameters | max_depth=6, n_estimators=300, lr=0.05 |
| Train / Val split | Time-split at 2026-06-15 |

Results:

| Metric | Train | Validation |
|---|---|---|
| AUC | 0.91 | 0.84 |
| Precision @ top decile | 0.66 | 0.59 |
| Recall @ top decile | 0.41 | 0.39 |

Comparison to baseline:

| Metric | Baseline (EXP-013) | This run | Delta |
|---|---|---|---|
| AUC | 0.82 | 0.84 | +0.02 |

Observations: The new feature was the third-highest importance feature by SHAP value.
No overfitting signal — train/val gap is consistent with prior runs.

Result: Validation AUC improved from 0.82 to 0.84 and precision @ top decile from 0.56
to 0.59, confirming the hypothesis.

Decision: Promote to production (meets all thresholds in model-contract.md).

---

### EXP-013 — Baseline retrain on July feature snapshot

**Date:** 2026-07-01
**Tracking URI:** MLflow run `77bd910` in `churn-guard` experiment

Hypothesis: Establish this month's baseline performance before trying new features.

Config:

| Parameter | Value |
|---|---|
| Model type | XGBoost |
| Training data | `churn-features` snapshot dt=2026-07-01 |
| Features | baseline set (6 features, see model-contract.md) |
| Hyperparameters | max_depth=6, n_estimators=300, lr=0.05 |
| Train / Val split | Time-split at 2026-06-15 |

Results:

| Metric | Validation |
|---|---|
| AUC | 0.82 |
| Precision @ top decile | 0.56 |
| Recall @ top decile | 0.40 |

Result: Baseline validation AUC of 0.82 meets the production threshold; this run becomes
the comparison baseline for future experiments.

Decision: Promote to production (meets thresholds). Serves as the comparison baseline
for EXP-014.

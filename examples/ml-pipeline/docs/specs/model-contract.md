# Model Contract

## Model Identity

| Property | Value |
|---|---|
| Model name | `churn-guard-v1` |
| Type | Binary classification |
| Purpose | Predict probability a subscriber churns within the next 30 days |
| Framework | XGBoost |
| Artifact registry | MLflow Model Registry |

## Input

### Feature Schema

| Feature name | Type | Required | Range / Categories | Description |
|---|---|---|---|---|
| `tenure_days` | int | Yes | >= 0 | Days since subscription start |
| `plan_tier` | string | Yes | {basic, pro, enterprise} | Current subscription plan |
| `monthly_spend_usd` | float | Yes | >= 0 | Current monthly billed amount |
| `logins_last_30d` | int | Yes | >= 0 | Count of product logins in trailing 30 days |
| `support_tickets_last_90d` | int | Yes | >= 0 | Count of support tickets in trailing 90 days |
| `payment_failures_last_90d` | int | Yes | >= 0 | Count of failed payment attempts in trailing 90 days |

### Preprocessing expectations

- Normalization: `monthly_spend_usd` is scaled with the `StandardScaler` fitted during
  training (`scaler.pkl` in the same MLflow run's artifacts).
- Encoding: `plan_tier` is one-hot encoded with the fitted `OneHotEncoder`; unseen
  categories map to an explicit "unknown" bucket rather than erroring.
- Missing value strategy: `logins_last_30d` and `support_tickets_last_90d` default to 0
  when a subscriber has no matching events in the window.

## Output Format

Single float `churn_probability` in `[0, 1]`, plus a decoded `risk_tier` label derived
from fixed cutoffs (`low` < 0.3, `medium` 0.3–0.7, `high` > 0.7).

**Example output:**
```json
{ "customer_id": "c_9182", "churn_probability": 0.81, "risk_tier": "high" }
```

## Production Thresholds

A model version must meet ALL thresholds below before being tagged `production-eligible`
by the evaluate stage.

| Metric | Threshold | Evaluation dataset |
|---|---|---|
| AUC | >= 0.82 | Held-out 20% time-split validation set |
| Precision @ top decile | >= 0.55 | Same validation set |
| Recall @ top decile | >= 0.40 | Same validation set |

## Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Trained mainly on North American subscribers | Lower accuracy for EU/APAC accounts | Flag region in scoring output; monitor per-region AUC |
| No feature for competitor pricing changes | Cannot predict churn spikes from external market events | Retention team treats scores as one signal, not the only one |

## Retraining Policy

| Trigger | Action |
|---|---|
| Production AUC on held-out monitoring set drops below 0.78 | Trigger immediate retraining, out of normal monthly cadence |
| New training data available (monthly) | Scheduled retraining |
| `plan_tier` category set changes | Mandatory re-fit of the encoder and retraining |

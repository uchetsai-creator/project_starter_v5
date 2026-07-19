# Model Contract

## Input Schema

| Field | Type | Description |
|---|---|---|
| age | int | Customer age in years |
| revenue | float | Historical purchase revenue |
| churn_risk | float | Predicted churn risk score |

## Output Format

Binary classification output: `{"label": 0 or 1, "probability": float}`.
Label 1 means high churn risk, label 0 means low risk.

## Production Thresholds

- Minimum accuracy threshold: 0.85
- F1 score >= 0.80
- AUC >= 0.88

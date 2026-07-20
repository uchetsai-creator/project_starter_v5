# Model Contract

<!--
  For: ML Pipeline projects
  Purpose: Documents what a trained model accepts as input, what it produces as output,
           and what quality thresholds it must meet before being promoted to production.
  Update when: Input feature schema changes, output format changes, or thresholds change.
  This is the authoritative contract between the training pipeline and the serving layer.
-->

## Model Identity

| Property | Value |
|---|---|
| Model name | [e.g., `revenue-forecast-v1`] |
| Type | [Classification / Regression / Ranking / Generation / etc.] |
| Purpose | [One sentence — what business problem it solves] |
| Framework | [scikit-learn / PyTorch / TensorFlow / XGBoost / etc.] |
| Artifact registry | [MLflow / S3 path / HuggingFace Hub / etc.] |

---

## Input Contract

### Feature Schema

| Feature name | Type | Required | Range / Categories | Description |
|---|---|---|---|---|
| `feature_1` | float | Yes | [0, 1] | [Description] |
| `feature_2` | int | Yes | {1, 2, 3, 4} | [Description] |
| `feature_3` | string | No | max 255 chars | [Description. Null → treated as "unknown"] |

### Preprocessing expectations

[Describe what preprocessing the serving layer must apply before passing data to the model]

- Normalization: [which features, which scaler — must use the same scaler fitted during training]
- Encoding: [which features, which encoder]
- Missing value strategy: [imputation method per feature]

**Note:** If the serving layer uses a different preprocessing than training, predictions will be wrong. Document the exact fitted transformer artifact location.

---

## Output Contract

| Field | Type | Description |
|---|---|---|
| `prediction` | float / int / string | [Primary model output] |
| `confidence` | float [0, 1] | [Confidence score — may be absent for some model types] |
| `label` | string | [Decoded class label — if applicable] |

**Output format:** [Single value / Dict / JSON / Pandas DataFrame row]

**Example output:**
```json
{
  "prediction": 0.87,
  "confidence": 0.92,
  "label": "high_risk"
}
```

---

## Production Thresholds

A model version must meet ALL thresholds below before being tagged `production`.

| Metric | Threshold | Evaluation dataset |
|---|---|---|
| Accuracy / RMSE / AUC | >= [value] | [dataset name and version] |
| Precision | >= [value] | — |
| Recall | >= [value] | — |
| Latency (p99) | <= [ms] | [load test scenario] |

Threshold rationale: [Why these thresholds — business impact of a miss]

---

## Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| [e.g., Does not generalise to Region X] | [Predictions unreliable for X] | [Filter out / flag / use fallback] |
| [e.g., Trained on data before 2024] | [Concept drift possible] | [Retrain quarterly] |

---

## Training Data Requirements

| Property | Value |
|---|---|
| Dataset name | [Name and version / DVC tag / S3 path] |
| Date range | [e.g., 2022-01-01 to 2024-12-31] |
| Minimum rows for training | [N] |
| Label source | [How ground truth was obtained] |
| Known data quality issues | [Any known biases, missing periods, or anomalies] |

---

## Retraining Policy

| Trigger | Action |
|---|---|
| Model AUC drops below [threshold] on production traffic | Trigger retraining pipeline |
| New training data available (monthly / quarterly) | Scheduled retraining |
| Feature schema change | Mandatory retraining — old model is incompatible |

---

## Non-Functional Requirements

| Metric | Requirement |
|---|---|
| Inference latency | p50 < [e.g., 50ms]; p99 < [e.g., 200ms] |
| Throughput | >= [N] predictions/sec per serving instance |
| Model artifact size (loaded) | < [e.g., 500MB] in memory |
| Cold start (first prediction after load) | < [e.g., 2s] |
| Retraining time | < [e.g., 4 hours] on [hardware spec] for full dataset |

---

## Edge Cases

| Scenario | Expected behaviour |
|---|---|
| Required feature is `null` or missing at inference | Apply defined imputation strategy (see Preprocessing); log missing feature count |
| Feature value outside trained distribution | [Return prediction with `"ood_warning": true` / reject with `OOD_INPUT` error] |
| All features are missing | Return `INSUFFICIENT_INPUT` error — do not produce a prediction |
| Input batch size exceeds model limit | Split into sub-batches of [max size] and reassemble in order |
| Model artifact fails to load (corrupt file) | Fail immediately with `MODEL_LOAD_ERROR` — do not return stale defaults |
| Prediction confidence below minimum threshold | [Return with `"low_confidence": true` / route to human review queue] |
| Label encoder receives unknown category | [Map to "unknown" bucket / raise `UNKNOWN_CATEGORY` error] |
| Training data contains label leakage | Fail pipeline with `DATA_LEAKAGE_DETECTED` — do not promote model |
| Serving model version differs from training version | Fail with `VERSION_MISMATCH` — preprocessing and model must come from same training run |

> *Adjust based on model type — classification, regression, and generation models have different failure modes.*

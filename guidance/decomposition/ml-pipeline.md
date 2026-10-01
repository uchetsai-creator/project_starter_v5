# Decomposition — ML Pipeline

Nouns for `guidance/decomposition/common.md`.

- **Observer:** whoever consumes the model — a serving endpoint, a batch scoring job, an analyst
- **Entry point:** a model artifact / prediction endpoint, or a metrics report
- **Independent Test:** run evaluation on the fixed validation set and check the metric
  threshold, or call the prediction entry point with a known input

## Artifact kinds

| Kind | Prefix | In an ML pipeline | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Feature schema, model input/output signature in `model-contract.md` | Signature test: model accepts the declared input shape |
| State | `STATE` | Dataset snapshot, feature store table, model registry entry | Data test: snapshot has the expected rows and split |
| Logic | `LOGIC` | Feature engineering, training, evaluation step | Eval test: metric on validation set ≥ threshold |
| Entry | `ENTRY` | Pipeline wiring, model registration, serving / batch scoring hook | Smoke test: prediction endpoint returns a score |
| Guard | `GUARD` | Drift / skew checks, input validation, fallback model | Test: out-of-range feature → rejected or fallback used |

Record every training run that changes a metric in `experiment-log.md`; a Logic task that
trains a model names the threshold in its Verify.

## Typical Guard cases

- Feature outside training range / missing → validation error or documented default
- Metric below threshold → model not promoted
- Training–serving skew detected → alert, keep the current model

## Example slice

```
SL-1 (P1)  Model reaches F1 ≥ 0.85 on the validation set
  Independent Test: run evaluate on the frozen validation set → F1 ≥ 0.85 in the report
  Task STATE    [SL-1] frozen validation split                     Covers: FR-001
  Task LOGIC    [SL-1] baseline model training + evaluation        Covers: FR-001, AC-001
  Task GUARD    [SL-1] promotion blocked below threshold           Covers: AC-002
```

# Pipeline Contract

## Overview

Four-stage pipeline: extract -> train -> evaluate -> score. Extract runs daily; train and
evaluate run monthly; score runs weekly against the current production model.

## Stage Contracts

| Stage | Input Format | Output Format |
|---|---|---|
| extract | Billing API JSON + Kafka usage events | Parquet feature table on S3 |
| train | Parquet feature table (trailing 90 days) | MLflow model artifact + run metrics |
| evaluate | MLflow candidate model + held-out Parquet split | Promotion decision (production-eligible / rejected) in MLflow registry |
| score | MLflow production model + current Parquet feature table | Snowflake `churn_scores` rows |

## Naming Rules

Feature table partitions are named `s3://churn-features/dt=YYYY-MM-DD/`. MLflow runs are
tagged `pipeline=churn-guard` and `stage=train` so the evaluator can locate the most
recent candidate without hardcoding a run ID.

## Error Handling

A failed extract for a given day halts the DAG before training reads that partition —
train never silently substitutes a stale or partial feature table.

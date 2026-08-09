# Test Plan

## Testing Strategy

We use a layered testing approach with unit tests, integration tests, and pipeline-level
end-to-end tests.
Unit tests validate feature-engineering transforms and the promotion-threshold logic in
isolation using pytest and small synthetic DataFrames.
Integration tests run each Airflow task against a local Postgres/S3-compatible (MinIO)
stack to verify I/O contracts between stages.
End-to-end tests run the full extract -> train -> evaluate -> score DAG against a fixed
synthetic dataset with known expected churn probabilities.

## Test Scope

- Unit: feature transforms, encoder/scaler fitting, threshold evaluation logic
- Integration: extractor writes valid Parquet, trainer reads it, evaluator reads MLflow run
- E2E: full DAG run on synthetic data produces scores within expected tolerance

# Deployment

## Orchestration

Apache Airflow 2.8 orchestrates all ChurnGuard DAGs:

- `churn_feature_extract` — runs daily at 02:00 UTC
- `churn_train` — runs monthly on the 1st at 03:00 UTC
- `churn_batch_score` — runs weekly on Monday at 04:00 UTC

DAG definitions live in `dags/churn_*.py`. Training and evaluation run in a dedicated
Airflow `KubernetesPodOperator` with a larger memory footprint than the extraction and
scoring tasks.

## Environment Variables

| Variable | Description |
|---|---|
| AIRFLOW_CONN_SNOWFLAKE | Airflow connection ID for the Snowflake warehouse |
| MLFLOW_TRACKING_URI | URL of the MLflow tracking server |
| AWS_ACCESS_KEY_ID | S3 access key for feature-store staging and MLflow artifacts |
| CHURN_MODEL_AUC_THRESHOLD | Minimum validation AUC required for promotion (see model-contract.md) |

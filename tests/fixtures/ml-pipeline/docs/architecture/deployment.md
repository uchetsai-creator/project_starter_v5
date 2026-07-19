# Deployment

## Orchestration

Prefect 2.x orchestrates model training and inference pipeline runs.
Scheduled daily via Prefect deployment with cron `0 2 * * *`.

## Environment Variables

| Variable | Description |
|---|---|
| MLFLOW_TRACKING_URI | MLflow experiment tracking server |
| AWS_DEFAULT_REGION | AWS region for S3 access |
| MODEL_BUCKET | S3 bucket for model artifacts |

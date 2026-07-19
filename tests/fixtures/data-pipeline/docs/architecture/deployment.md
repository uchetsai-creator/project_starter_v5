# Deployment

## Orchestration

Apache Airflow 2.8 orchestrates all pipeline DAGs on a daily schedule.
The Airflow DAG is defined in `dags/main_pipeline.py`.

## Environment Variables

| Variable | Description |
|---|---|
| AIRFLOW_CONN_POSTGRES | Airflow metadata database connection |
| AWS_ACCESS_KEY_ID | S3 access key |
| DATA_BUCKET | S3 bucket name for raw data |

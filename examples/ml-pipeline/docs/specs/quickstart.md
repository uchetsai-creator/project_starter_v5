# Quickstart

## Prerequisites

- Python 3.11 or higher
- Docker Desktop 24+ (for local Airflow)
- Access to the team's MLflow tracking server URL

## Setup

1. Clone the repository: `git clone https://github.com/example/churn-guard.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Start local Airflow: `docker compose up -d`
4. Set `MLFLOW_TRACKING_URI` and Snowflake connection env vars (see `deployment.md`)
5. Trigger a manual extract run to seed local feature data: `airflow dags trigger churn_feature_extract`

## Verification

Run `pytest tests/` to confirm the feature-engineering and evaluation logic pass unit
tests, and check the Airflow UI at `localhost:8080` to confirm the `churn_feature_extract`
DAG run you triggered completed successfully.

# Backend

## Stack

- Python 3.11
- XGBoost 2.x for the classifier
- pandas / PyArrow for feature engineering
- Apache Airflow 2.8 for orchestration
- MLflow for experiment tracking and model registry
- scikit-learn for preprocessing (scaler, encoders) and evaluation metrics

## Layering

Extractor -> Feature Store (Parquet on S3) -> Trainer -> MLflow Registry -> Evaluator ->
Batch Scorer -> Scores Table (Snowflake)

Each stage is an independent Airflow task with its own retry policy; stages exchange
data only through the Feature Store and MLflow Registry, never through in-memory state.

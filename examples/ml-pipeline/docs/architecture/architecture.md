# Architecture

## Overview

ChurnGuard is a batch ML pipeline that extracts subscriber billing/usage data, trains a
monthly churn classifier, and scores the active subscriber base weekly. Airflow
orchestrates all stages; MLflow tracks experiments and hosts the model registry.

## System Components

| Component | Type | Responsibility |
|---|---|---|
| Feature Extractor | Airflow task (Python/Spark) | Builds daily feature table from billing + usage events |
| Trainer | Airflow task (Python/XGBoost) | Trains a candidate model monthly on trailing 90-day features |
| Evaluator | Airflow task (Python) | Scores the candidate against `model-contract.md` thresholds |
| Batch Scorer | Airflow task (Python) | Weekly inference over the active subscriber base |
| MLflow | Model registry + tracking server | Stores runs, metrics, and promoted model artifacts |

## Data Flow

@startuml
[Billing API] --> [Feature Extractor]
[Usage Events] --> [Feature Extractor]
[Feature Extractor] --> [Feature Store]
[Feature Store] --> [Trainer]
[Trainer] --> [MLflow Registry]
[MLflow Registry] --> [Evaluator]
[Evaluator] --> [MLflow Registry] : promote / reject
[Feature Store] --> [Batch Scorer]
[MLflow Registry] --> [Batch Scorer] : production model
[Batch Scorer] --> [Scores Table]
@enduml

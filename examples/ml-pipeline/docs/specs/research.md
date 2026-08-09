# Research

## Technology Decisions

Decision: Use XGBoost instead of a neural network for the churn classifier.
Rationale: The feature set is small (6 tabular features) and gradient-boosted trees
consistently outperform neural nets on this scale of tabular data, while giving the
team SHAP-based feature importances that the retention analysts specifically asked for.

Decision: Use Apache Airflow instead of Prefect or Dagster for orchestration.
Rationale: The team already runs Airflow for two other data pipelines, so reusing the
same scheduler, alerting, and on-call runbook avoids introducing a second orchestration
tool for one project.

Decision: Track experiments with MLflow instead of Weights & Biases.
Rationale: MLflow's self-hosted model registry gives a single source of truth for
"which model version is currently in production" that the evaluate/score stages can
query directly via API, without depending on a third-party SaaS being reachable during
a production scoring run.

## Resolved Clarifications

Q: Should the pipeline retrain automatically if production AUC degrades, or only on the
monthly schedule?
A: Both — the monthly schedule is the default cadence, but an automatic out-of-cycle
retrain triggers if the production-monitoring AUC drops below 0.78 (see the Retraining
Policy in model-contract.md).

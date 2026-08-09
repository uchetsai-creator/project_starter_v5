# Logging Spec

## Log Output Format

JSON structured logging, one line per event, emitted by every Airflow task to the task's
own log stream and mirrored to CloudWatch.

## Required Log Points

- Feature extraction started / completed (row count, partition date)
- Training run started / completed (MLflow run ID, duration)
- Evaluation decision (promoted / rejected, metric values)
- Batch scoring started / completed (subscriber count scored)

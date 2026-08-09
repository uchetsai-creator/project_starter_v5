# Database

## Storage

The feature table and model scoring output are stored in Snowflake, the team's existing
data warehouse. Intermediate feature-engineering artifacts (large Parquet batches
produced by the daily extractor) are staged in S3 before being loaded into Snowflake
via `COPY INTO`, keeping expensive Spark/pandas transforms off the warehouse compute.

MLflow's own tracking metadata (runs, params, metrics) is stored in a separate
lightweight PostgreSQL instance dedicated to the MLflow server; model artifacts
(pickled models, scalers) are stored in S3 under the MLflow artifact root.

# Database

## Storage

This pipeline uses Amazon S3 as the primary data lake storage with Parquet file format.
Delta Lake provides ACID transactions on top of S3 for incremental processing.

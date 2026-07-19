# Pipeline Contract

## Overview

Three-stage pipeline: extract -> transform -> load.

## Stage Contracts

| Stage | Input Format | Output Format |
|---|---|---|
| extract | REST API JSON | Parquet on S3 |
| transform | Parquet on S3 | Cleaned Parquet on S3 |
| load | Parquet on S3 | PostgreSQL rows |

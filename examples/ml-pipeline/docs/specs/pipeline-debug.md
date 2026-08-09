# Pipeline Debug

## Common Failure Scenarios

### Scenario 1: Batch Scoring Produces Fewer Rows Than Active Subscribers

Symptom: The weekly `churn_batch_score` run writes fewer rows than the count of
`status = active` subscribers in billing.
Root Cause: A subset of subscribers had a feature-extraction gap (e.g. new signups
that landed after the daily extract cutoff) and were dropped by an inner join between
the feature table and the billing active-subscriber list.
Fix: Change the join to a left join from the billing active list, and zero-fill missing
usage features for subscribers with no feature row yet.

### Scenario 2: Candidate Model AUC Drops Sharply Between Runs

Symptom: A new monthly training run's validation AUC is more than 0.05 below the
previous month's promoted model, with no code change.
Root Cause: A billing schema change upstream silently changed the encoding of the
`plan_tier` categorical feature (new tier values not seen during encoder fit), causing
the fitted encoder to map them all to "unknown."
Fix: Add a feature-drift check in the extractor that alerts when a categorical feature's
value set changes, and re-fit the encoder on the newest data before retraining.

### Scenario 3: Scores Table Has Duplicate Rows for the Same Subscriber

Symptom: `churn_scores` has more than one row for the same `customer_id` and
`scored_at` week.
Root Cause: The batch-scoring DAG was manually re-triggered after a partial failure
without clearing the partial output first, so the retry appended instead of overwriting.
Fix: Make the scoring task idempotent — write to a staging table and `MERGE` into
`churn_scores` keyed on `(customer_id, scored_at)` instead of appending.

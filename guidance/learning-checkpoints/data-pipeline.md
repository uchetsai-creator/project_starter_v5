# Learning Checkpoints — Data Pipeline

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which stage owns this behavior, and its input/output schema contract
- What upstream/downstream stages depend on this stage's output shape

**Checkpoint B (new requirement) — ask about:**
- New/changed stage's input and output contract (field names + types)
- Failure/retry behavior for this stage

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- The orchestrator framework itself (Airflow, Dagster, Prefect, Luigi)
- Schema evolution / data format (Parquet, Avro) if new to you

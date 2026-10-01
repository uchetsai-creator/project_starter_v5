# Decomposition — Data Pipeline

Nouns for `guidance/decomposition/common.md`.

- **Observer:** the downstream consumer of the output — a report, a dashboard, another job
- **Entry point:** an output table / file / topic the pipeline produces
- **Independent Test:** run the pipeline (or the one stage) on a fixed input and check row
  counts and specific values in the output

## Artifact kinds

| Kind | Prefix | In a data pipeline | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Output schema, column types, grain, freshness in `pipeline-contract.md` | Schema test on the output table |
| State | `STATE` | Staging / intermediate tables, seeds, partitions | Load test: staging table exists with expected columns |
| Logic | `LOGIC` | Transform / model (SQL, dbt, Spark, pandas) | Data test: known input row → expected output value |
| Entry | `ENTRY` | Orchestration wiring — DAG task, schedule, dependencies, sensors | DAG test: task present with correct upstream |
| Guard | `GUARD` | Data quality checks, quarantine of bad rows, late-data handling | Quality test: a negative amount fails the check |

## Typical Guard cases

- Source row fails validation → quarantined, run continues, count reported
- Source late or missing → sensor waits / run marked failed, no partial output published
- Duplicate source rows → deduplicated on the declared grain

## Example slice

```
SL-2 (P1)  Daily revenue uses one net-of-tax definition across three sources
  Independent Test: run the DAG on fixtures → one row per source matches the documented formula
  Task CONTRACT [SL-2] net_revenue_excl_tax column and grain       Covers: FR-004
  Task LOGIC    [SL-2] per-source conversion in the mart model     Covers: FR-004, AC-008
  Task GUARD    [SL-2] quality check: converted value never negative  Covers: AC-009
  Task ENTRY    [SL-2] add the model to the DAG                    Covers: AC-008
```

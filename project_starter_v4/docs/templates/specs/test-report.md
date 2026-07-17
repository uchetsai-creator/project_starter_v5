# Test Report

<!--
  Records the actual results of testing.
  Generated or updated after each test run / sprint / release.
  This file describes WHAT was found, not the plan.

  Update when:
  - A new test run is completed
  - Bugs are found and fixed
  - Coverage changes significantly
-->

**Report date:** [YYYY-MM-DD]
**Sprint / Release:** [Sprint N / v1.0.0]
**Environment:** [Local / CI / Staging]

---

## Summary

<!--
  Include only the rows that apply to your project type.
  See test-plan.md per-type guide for which levels each type uses.
  Data Pipeline / ML Pipeline: use the pipeline-specific sections below instead of this table.
  Web App / Microservices / CLI Tool / Library / LLM App / IaC / DevOps / Mobile App: fill this table and remove the pipeline sections.
-->

| Type | Total | Passed | Failed | Skipped | Coverage |
|---|---|---|---|---|---|
| Unit | [N] | [N] | [N] | [N] | [N%] |
| Component | [N] | [N] | [N] | [N] | — |
| Integration | [N] | [N] | [N] | [N] | — |
| Contract / Service | [N] | [N] | [N] | [N] | — |
| E2E / System | [N] | [N] | [N] | [N] | — |
| Performance | [N] | [N] | [N] | [N] | — |

**Overall status:** ✅ Pass / ❌ Fail

---

## Results by Module

<!--
  Include only the columns that apply to your project type.
  Remove Component / Contract / Performance columns if your type doesn't use them.
  Data Pipeline / ML Pipeline: replace this section with the pipeline-specific sections below.
-->

| Module | Unit | Component | Integration | Contract / Service | E2E / System | Notes |
|---|---|---|---|---|---|---|
| [e.g., Auth] | ✅ 24/24 | ✅ 6/6 | ✅ 8/8 | ✅ 4/4 | ✅ 3/3 | — |
| [Module] | [result] | [result] | [result] | [result] | [result] | [notes] |

---

## [Data Pipeline / ML Pipeline] Contract Tests — Quality Gate

<!--
  For Data Pipeline and ML Pipeline projects: replace the "Results by Module" table above
  with this section. Record per-source / per-stage validation results.
  For other project types: delete this section and the fault-injection section below.
-->

### [Source / Stage Name] — [tool, e.g., Great Expectations checkpoint]

Fixture: `[path/to/fixture.csv]` ([N] rows, [description])

| Expectation | Rule | Result |
|---|---|---|
| [e.g., row count ≥ 1] | sanity | ✅ / ❌ pass/fail |
| [e.g., column set matches] | sanity | ✅ / ❌ |
| [e.g., NOT NULL: field_a, field_b] | [BR-XXX] | ✅ / ❌ |
| [e.g., field_c between 0 and N] | [BR-XXX] | ✅ / ❌ |
| [e.g., period matches YYYYMM] | [BR-XXX] | ✅ / ❌ |
| [e.g., sum deviation ≤ 30%] | [BR-XXX] | ✅ skip (no baseline) / ✅ pass / ❌ fail |

**Result:** success=[True/False], evaluated=[N], passed=[N], failed=[N]

---

## [Data Pipeline / ML Pipeline] Integration Tests — Schema / Model Tests

<!--
  Record dbt schema tests, pandera results, or equivalent model-level tests.
  For other project types: delete this section.
-->

```bash
# [command used, e.g.:]
# cd dbt && dbt seed && dbt run && dbt test
```

**Result:** [N]/[N] tests PASS

**Output validation:**

| Check | Expected | Actual |
|---|---|---|
| [e.g., mart table row count] | [N] | [N] ✅ / ❌ |
| [e.g., NOT NULL column] | all rows | ✅ / ❌ |

---

## [Data Pipeline / ML Pipeline] E2E System Test

<!--
  Record the full pipeline run result. For other project types: delete this section.
-->

**Run ID:** `[e.g., manual__YYYY-MM-DDT...]`

**Setup:**
```bash
# [commands to prepare fixture data and trigger pipeline]
```

**Stage Results:**

| Stage / Task | Result | Notes |
|---|---|---|
| [e.g., sense_sap] | ✅ / ❌ | |
| [e.g., validate_sap] | ✅ / ❌ | [N]/[N] expectations pass |
| [e.g., transform] | ✅ / ❌ | [N] rows output |
| [e.g., load / archive] | ✅ / ❌ | |
| [e.g., catalog_push] | ✅ / ❌ (non-blocking) | |

**Post-run state:**

| Check | Expected | Actual |
|---|---|---|
| [e.g., output table row count] | [N] | [N] ✅ |
| [e.g., input files archived] | yes | ✅ / ❌ |

---

## [Data Pipeline / ML Pipeline] Fault Injection Tests

<!--
  Record each negative test / break-kit scenario.
  For other project types: delete this section.
-->

| # | Scenario | Expected failed stage | Verified | Actual result |
|---|---|---|---|---|
| [01] | [e.g., wrong filename] | [e.g., sense_* stalls] | [YYYY-MM-DD] | ✅ / ❌ |
| [02] | [e.g., null required field] | [e.g., validate_*] | [YYYY-MM-DD] | ✅ / ❌ |
| [03] | [e.g., value out of range] | [e.g., validate_*] | [YYYY-MM-DD] | ✅ / ❌ |
| [NN] | [e.g., downstream service down] | none (non-blocking) | [YYYY-MM-DD] | ✅ / ❌ |

---

## Failed Tests

<!--
  List every failing test with its cause and resolution status.
  Remove entries once the test passes consistently.
-->

| Test | Module | Failure reason | Status | Fixed in |
|---|---|---|---|---|
| [test name] | [module] | [why it failed] | [Open / Fixed / Won't fix] | [PR / commit] |

---

## Performance Results

<!--
  Include only if performance tests were run this cycle.
  Remove this section if performance testing is not yet in scope.
  Use the row format that matches your project type (examples below).
-->

| Scenario | Metric | Result | Target | Status |
|---|---|---|---|---|
| [see per-type examples below] | [see below] | [measured value] | [target] | ✅ / ❌ |

**Per-type examples:**

| Project type | Scenario example | Key metric |
|---|---|---|
| **Web App / Microservices** | `POST /api/orders under 100 concurrent users` | p50 / p95 / p99 latency (ms) |
| **CLI Tool** | `run command X with 10k-line input file` | Total execution time (s) |
| **Library / SDK** | `call [function] 10,000 times` | Avg call latency (µs); memory (MB) |
| **Data Pipeline** | `full pipeline run on 1M-row fixture dataset` | Throughput (rows/sec); total run time (s) |
| **ML Pipeline** | `batch inference on 1,000 samples` | Inference latency (ms/sample); memory (GB) |
| **AI / LLM App** | `send 50 prompts to [model]` | Time to first token (ms); tokens/sec |
| **IaC / DevOps** | `terraform apply on full sandbox environment` | Apply time (s); resource count delta |
| **Mobile App** | `cold start → first interactive frame` | Cold start time (ms); frame render latency (ms) |

---

## Known Issues

| Issue | Severity | Affected module | Workaround | Planned fix |
|---|---|---|---|---|
| [Description] | High / Medium / Low | [Module] | [Workaround or none] | [Sprint N / backlog] |

---

## Coverage Report

<!--
  For unit-tested projects (Web App, Microservices, CLI Tool, Library, LLM App, Mobile App): paste coverage summary here.
  For Data Pipeline / ML Pipeline: replace with a note on what's covered by contract/integration tests.
  For IaC / DevOps: replace with a note on which modules have tflint/tfsec/OPA checks and which are covered by the E2E sandbox run.
-->

```
[Paste coverage summary output here, e.g.:]

Statements : 84.2% ( 1203/1429 )
Branches   : 76.1% (  381/ 501 )
Functions  : 88.9% (  248/ 279 )
Lines      : 84.0% ( 1196/1424 )
```

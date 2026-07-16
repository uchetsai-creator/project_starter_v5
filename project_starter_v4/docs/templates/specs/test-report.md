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

| Type | Total | Passed | Failed | Skipped | Coverage |
|---|---|---|---|---|---|
| Unit | [N] | [N] | [N] | [N] | [N%] |
| Integration | [N] | [N] | [N] | [N] | — |
| E2E | [N] | [N] | [N] | [N] | — |

**Overall status:** ✅ Pass / ❌ Fail

---

## Results by Module

| Module | Unit | Integration | E2E | Notes |
|---|---|---|---|---|
| [e.g., Auth] | ✅ 24/24 | ✅ 8/8 | ✅ 3/3 | — |
| [Module] | [result] | [result] | [result] | [notes] |

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

---

## Known Issues

| Issue | Severity | Affected module | Workaround | Planned fix |
|---|---|---|---|---|
| [Description] | High / Medium / Low | [Module] | [Workaround or none] | [Sprint N / backlog] |

---

## Coverage Report

```
[Paste coverage summary output here, e.g.:]

Statements : 84.2% ( 1203/1429 )
Branches   : 76.1% (  381/ 501 )
Functions  : 88.9% (  248/ 279 )
Lines      : 84.0% ( 1196/1424 )
```

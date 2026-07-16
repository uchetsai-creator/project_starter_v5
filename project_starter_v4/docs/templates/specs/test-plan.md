# Test Plan

<!--
  Describes the testing strategy for this project.
  This file defines WHAT will be tested and HOW.
  Actual test results go in test-report.md.

  Update when:
  - A new module is added (add test scope)
  - Testing tools or CI configuration changes
  - Coverage targets change
-->

---

## Testing Strategy

| Type | Tool | Scope | Coverage target |
|---|---|---|---|
| Unit | [e.g., Jest / pytest / go test] | [e.g., service layer, utility functions] | [e.g., ≥ 80%] |
| Integration | [e.g., Supertest / httpx / pytest] | [scope — see per-type notes below] | [e.g., all critical paths] |
| E2E / System | [e.g., Playwright / shell scripts / dbt test] | [scope — see per-type notes below] | [e.g., happy paths only] |
| Performance | [e.g., k6 / timeit / benchmark] | [scope — see per-type notes below] | [e.g., see per-type notes below] |

**Per-type interpretation — adapt to whichever applies:**

| Project type | Integration means | E2E / System means | Performance target |
|---|---|---|---|
| **Web App** | API endpoints + DB queries | Critical user flows (Playwright/Cypress) | p95 < 200ms under load |
| **CLI Tool** | Subcommand execution against real files/config | Full command sequence with real inputs | Execution time < N seconds per invocation |
| **Library / SDK** | Public API functions with real inputs (no mocks) | Consumer-side integration: import and use the library as a caller would | Function call latency; memory allocation |
| **Data Pipeline** | Stage-to-stage data contract: input → output schema matches | Full pipeline run on a fixture dataset; output matches expected | Throughput (rows/sec); total run time |
| **ML Pipeline** | Model inference on a test batch | Train → eval → artifact export on a small dataset | Inference latency; memory footprint |
| **Microservices** | Per-service: API + DB. Cross-service: contract tests | End-to-end scenario across services | Per-service p95 latency; message queue lag |
| **AI / LLM App** | LLM API call with a known prompt + expected output shape | Full conversation turn: prompt → response → eval score | Time to first token; tokens/second |

---

## Test Scope

### In Scope

| Module / Feature | Test types | Notes |
|---|---|---|
| [e.g., Auth] | Unit, Integration | [e.g., focus on token validation and expiry] |
| [Module] | [Types] | [Notes] |

### Out of Scope

| Area | Reason |
|---|---|
| [e.g., Third-party API internals] | [e.g., tested by provider, not our responsibility] |

---

## Test Environment

| Environment | Purpose | Data |
|---|---|---|
| Local | Developer testing | [e.g., seed script / fixture files / test API keys] |
| CI | Automated tests on every PR | [e.g., isolated DB reset between runs / fixture dataset / mock LLM responses] |
| Staging | Pre-release manual or exploratory testing | [e.g., anonymised production-like data / staging API keys] |

> **Note:** Not all project types require all three environments.
> CLI Tools and Libraries may only need Local + CI.
> AI / LLM Applications may replace Staging with a prompt eval run against a fixed test case set.

---

## CI Integration

```bash
# Run all tests
[e.g., npm test / pytest / go test ./... / dbt test]

# Run with coverage
[e.g., npm run test:coverage / pytest --cov]

# Run system / E2E tests
[e.g., npx playwright test / bash tests/e2e.sh / python scripts/run_eval.py]
```

CI must pass before merging to main. Failing tests block deployment.

---

## Test Data Strategy

| Data type | Source | Reset strategy |
|---|---|---|
| [e.g., Seed / fixture data] | [e.g., tests/fixtures/ / seed script / fixture CSV files] | [e.g., reset before each test suite / re-generated per run] |
| [e.g., Mocks / stubs] | [e.g., pytest-mock / MSW / recorded LLM responses] | [e.g., per-test setup and teardown] |
| [e.g., Snapshot data] | [e.g., data/test-snapshots/] | [e.g., static files committed to repo] |

> **Note:** Persistent database seeds (e.g., `prisma/seed.ts`) apply to Web App and Microservices.
> Data Pipelines use fixture CSV/Parquet files. AI / LLM Applications use recorded prompt-response pairs.
> CLI Tools and Libraries typically use in-memory fixtures or temp files.

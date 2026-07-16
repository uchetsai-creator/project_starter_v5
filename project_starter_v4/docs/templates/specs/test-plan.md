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

Six test levels — include only the levels that apply to your project type (see per-type table below).

| Level | What it tests | External deps | Tool examples (by type) |
|---|---|---|---|
| **Unit** | Single function / method in isolation | All mocked | Jest / pytest / go test / vitest |
| **Component** | Single module / service as a unit | All mocked | pytest / Jest / go test; Testcontainers (optional) |
| **Integration** | Multiple modules / services with real deps | Real DB / real queue / real files | Web: httpx / Supertest; Pipeline: pytest + real files; LLM App: real API call |
| **Contract / Service** | Interface contract between two components | Mocked provider OR real stub | Microservices: Pact; Pipeline/ML: dbt test / pandera / great-expectations; LLM App: output schema assert |
| **E2E / System** | Full system from user / trigger perspective | All real | Web: Playwright; CLI: bash / bats; Pipeline: full run on fixture data; LLM App: eval script |
| **Performance** | Throughput or latency under load | Real or staging | Web: k6 / Artillery; CLI: hyperfine; Library: timeit / benchmark; Pipeline: custom timer; LLM App: litellm callback |

**Per-type guide — which levels to include and what they mean:**

| Project type | Unit | Component | Integration | Contract / Service | E2E / System | Performance |
|---|---|---|---|---|---|---|
| **Web App** | Functions, utils | Single controller/service with DB mocked | API endpoint + real DB | API schema matches client expectation | Critical user flows (Playwright) | p95 < Xms under load |
| **Microservices** | Per-service functions | Single service with other services mocked | Service + real DB/queue | Inter-service event/REST contracts (Pact) | Cross-service scenario | Per-service latency; queue lag |
| **CLI Tool** | Flag parsing, business logic | Single command with file system mocked | Full command with real files/config | ❌ | Full command sequence, real inputs | Execution time per invocation |
| **Library / SDK** | Individual functions | Module with I/O mocked | Public API with real inputs | Public API contract stability across versions | Import and use as a caller would | Call latency; memory allocation |
| **Data Pipeline** | Transform functions | Single stage with input/output mocked | Stage → real DB / real file read-write | Stage input/output schema contract | Full pipeline run on fixture dataset | Throughput (rows/sec); total run time |
| **ML Pipeline** | Feature functions | Single stage with data mocked | Stage with real data batch | Model input/output schema contract | Train → eval → artifact export | Inference latency; memory footprint |
| **AI / LLM App** | Prompt builder, parser | Full prompt round-trip with LLM mocked | Real LLM API call with known prompt | LLM output format matches downstream expectation | Full conversation turn + eval score | Time to first token; tokens/sec |

---

## Test Scope

### In Scope

| Module / Feature | Levels | Notes |
|---|---|---|
| [e.g., Auth] | Unit, Component, Integration | [e.g., focus on token validation and expiry] |
| [Module] | [Levels] | [Notes] |

### Out of Scope

| Area | Reason |
|---|---|
| [e.g., Third-party API internals] | [e.g., tested by provider, not our responsibility] |

---

## Test Environment

| Environment | Purpose | Data |
|---|---|---|
| Local | Developer testing | [e.g., seed script / fixture files / test API keys] |
| CI | Automated on every PR | [e.g., isolated DB reset / fixture dataset / mock LLM responses] |
| Staging | Pre-release exploratory | [e.g., anonymised production-like data / staging API keys] |

> **Note:** Not all project types require all three environments.
> CLI Tools and Libraries typically only need Local + CI.
> AI / LLM Applications may replace Staging with a prompt eval run against the fixed test case set in `eval-spec.md`.

---

## CI Integration

```bash
# Run unit + component tests
[e.g., npm test / pytest tests/unit tests/component / go test ./...]

# Run with coverage
[e.g., npm run test:coverage / pytest --cov]

# Run integration tests
[e.g., pytest tests/integration / npm run test:integration]

# Run contract tests
[e.g., npx pact-provider-verifier / pytest tests/contract / dbt test]

# Run E2E / system tests
[e.g., npx playwright test / bash tests/e2e.sh / python scripts/run_eval.py]
```

CI must pass before merging to main. Failing tests block deployment.

---

## Test Data Strategy

| Data type | Source | Reset strategy |
|---|---|---|
| [e.g., Seed / fixture data] | [e.g., tests/fixtures/ / seed script / fixture CSV] | [e.g., reset before each suite / re-generated per run] |
| [e.g., Mocks / stubs] | [e.g., pytest-mock / MSW / recorded LLM responses] | [e.g., per-test setup and teardown] |
| [e.g., Contract stubs] | [e.g., Pact broker / static JSON stubs] | [e.g., versioned with the consumer repo] |
| [e.g., Snapshot data] | [e.g., data/test-snapshots/] | [e.g., static files committed to repo] |

> **Note:** Persistent DB seeds apply to Web App and Microservices.
> Data Pipelines use fixture CSV/Parquet files. AI / LLM Applications use recorded prompt-response pairs.
> CLI Tools and Libraries typically use in-memory fixtures or temp files.

# Document Matrix

<!--
  Load only during project initialization or retrofitting.
  Not needed during normal task work.
-->

**Required (✅) / Optional (⚠️) / Not applicable (❌) by project type:**

| Document | Web App | CLI | Library | Data Pipeline | ML Pipeline | Microservices | AI / LLM App | IaC / DevOps | Mobile App |
|---|---|---|---|---|---|---|---|---|---|
| `architecture.md` | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `backend.md` | ✅ | ✅ | ❌ | ✅ | ✅ | per-service | ⚠️ if >script | ❌ | ⚠️ if BFF |
| `frontend.md` | ⚠️ if UI | ❌ | ❌ | ❌ | ❌ | ⚠️ if UI | ⚠️ if UI | ❌ | ✅ |
| `database.md` | ✅ | ⚠️ if DB | ❌ | ✅ | ✅ | per-service | ⚠️ if storing history | ❌ | ⚠️ if local DB |
| `deployment.md` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ⚠️ if hosted | ❌ | ❌ |
| `distribution.md` | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `topology.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `api-contract.md` | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ (external API) | ⚠️ if exposing API | ❌ | ⚠️ if using APIs |
| `cli-contract.md` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ if CLI-based | ❌ | ❌ |
| `public-api.md` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `pipeline-contract.md` | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `pipeline-debug.md` | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `llm-contract.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `prompt-library.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `eval-spec.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `eval-log.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `llm-debug.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `rag-contract.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ if using RAG | ❌ | ❌ |
| `mcp-contract.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ if using MCP | ❌ | ❌ |
| `service-catalog.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `service-contract.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `event-catalog.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ if async messaging | ❌ | ❌ | ❌ |
| `model-contract.md` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `experiment-log.md` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `runbook.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `drift-policy.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `release-guide.md` | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `compatibility-matrix.md` | ❌ | ⚠️ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ OS versions |
| `permissions.md` | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ⚠️ if multi-user | ❌ | ⚠️ if multi-user |
| `data-model.md` | ✅ | ⚠️ if DB | ❌ | ✅ | ✅ | per-service | ⚠️ if storing history | ❌ | ⚠️ if local DB |
| `business-process.md` | ✅ | ⚠️ | ❌ | ⚠️ | ❌ | ✅ | ❌ | ❌ | ⚠️ |
| `business-objects.md` | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `business-rules.md` | ✅ | ⚠️ | ❌ | ✅ | ⚠️ | ✅ | ⚠️ if domain rules | ❌ | ⚠️ |
| `logging-spec.md` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ⚠️ if >script | ❌ | ✅ |
| `research.md` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `quickstart.md` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `mobile-contract.md` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `test-plan.md` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `test-report.md` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

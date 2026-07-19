# Refactoring Plan — project_starter_v5

Derived from `docs/architecture-analysis.md`. Addresses Problems 1–5 in three sequential phases.

---

## ✅ Phase 1 — Document Registry + Context Builder + AGENTS.md Reduction (Complete)

**Goal:** Eliminate duplicated project-type knowledge (Problems 1–4) and deterministic task startup context (Problem 5).

### Files affected

| File | Change | Status |
|---|---|---|
| `document-registry.yaml` | Single source of truth for all document metadata | ✅ Done |
| `templates/script/validators/_registry.py` | Shared loader: `load_registry()`, `VALID_TYPES`, `build_matrix()`, etc. | ✅ Done |
| `verify_docs.py` | `MATRIX`, `FILE_LOCATIONS`, `VALID_TYPES` derived from registry | ✅ Done |
| `verify_content.py` | `TYPE_DOCS`, `DOC_PATHS`, `VALID_TYPES`, `UNIVERSAL_DOCS` derived from registry | ✅ Done |
| `verify_logs.py` | `VALID_TYPES` imported from `_registry` | ✅ Done (Phase 51) |
| `verify_tests.py` | `VALID_TYPES` imported from `_registry` | ✅ Done (Phase 51) |
| `verify_module_docs.py` | `VALID_TYPES` imported from `_registry` | ✅ Done (Phase 51) |
| `verify_spec_code.py` | `VALID_TYPES` imported from `_registry` | ✅ Done (Phase 51) |
| `scan_codebase.py` | `VALID_TYPES` imported from `_registry` | ✅ Done (Phase 51) |
| `build-context.py` | Reads `.project-starter.yml` + registry; writes `.ai/AI_CONTEXT.md` | ✅ Done |
| `templates/init/document-matrix.md` | Synced to registry by `verify_framework.py` Check 11 | ✅ Done |

**Note:** `LOGGING_REQUIRED`, `TRACE_ID_TYPES`, and `PIPELINE_TYPES` remain hardcoded in individual validators (Problem 4) — not yet moved to registry.

---

## ✅ Phase 2 — Workflow State Extraction (Complete)

**Goal:** Extract the task-state machine (current-state.md, sprint-change-log.md, task-log.md update rules) from AGENTS.md prose into a structured `workflow-state.yaml`. AI agents read the YAML instead of parsing natural-language rules.

**Status:** `workflow-registry.yaml` exists at the repo root and captures workflow step definitions. The `workflow-state.yaml` task-lifecycle state machine is tracked as **ROADMAP Phase 64** (`replaces_for` registry field) where remaining work lives.

**Risk:** Medium — changes AGENTS.md structure agents rely on. Requires testing with Claude Code before merging.

### Files affected

| File | Change | Type |
|---|---|---|
| `workflow-state.yaml` (new) | Structured task lifecycle: transitions, required fields, doc-checklist trigger rules | New |
| `AGENTS.md` | Remove task lifecycle prose; replace with pointer to `workflow-state.yaml` | Simplify |
| `build-context.py` | Read `workflow-state.yaml` to augment `.ai/AI_CONTEXT.md` with lifecycle rules | Update |
| `verify_framework.py` | Add check: `workflow-state.yaml` must exist and be valid YAML | Update |

### Migration strategy

1. Extract closeout rules, Doc Checklist trigger table, and sprint-sync procedure from AGENTS.md
2. Encode them in `workflow-state.yaml`
3. Update `build-context.py` to include relevant workflow rules in `.ai/AI_CONTEXT.md`
4. Manually test one full task cycle (start → closeout) with the new files before removing AGENTS.md prose

---

## ✅ Phase 3 — Full Orchestrator + Agent Adapters (Complete)

**Goal:** Replace direct script calls with an orchestrator that reads from the registry and workflow state. Add thin adapters for Claude Code, Cursor, and Codex.

**Status:** `orchestrator.py` exists and generates `.ai/AI_CONTEXT.md` + `.ai/WORKFLOW.md`. `adapters/claude/` (stop-hook, pre-commit) and `adapters/codex/` are implemented. Capability-based adapter architecture landed in ROADMAP Phase 52.5. Remaining shim cleanup tracked in **ROADMAP Phase 62**.

**Risk:** High — user-facing interface change. Requires deprecation path for direct script calls.

### Files affected

| File | Change | Type |
|---|---|---|
| `run.py` (new, repo root) | CLI orchestrator: `run verify`, `run context`, `run pdf`, `run scan` | New |
| `adapters/claude-mcp-server.py` (new) | MCP tool wrappers for Claude Code | New |
| `adapters/cursor-rules.md` (new) | Cursor-compatible rules file generated from registry | New |
| `README.md` | Add "Using the orchestrator" section; deprecate direct script calls | Update |
| `AGENTS.md` | Replace all `python3 docs/script/X.py` calls with `run X` | Update |

### Migration strategy

1. Implement `run.py` as a thin dispatcher that calls existing scripts unchanged
2. Publish adapters as optional add-ons; direct script calls continue to work
3. Deprecate direct calls in README with a 2-phase notice (warn → remove)

---

## Risk Register

| Risk | Phase | Likelihood | Mitigation |
|---|---|---|---|
| Registry schema breaks a script silently | 1 | Low | `verify_framework.py` validates registry on every commit |
| AI agent does not read `.ai/AI_CONTEXT.md` | 1 | Medium | AGENTS.md explicitly instructs agents to read it first |
| Workflow YAML is harder to update than prose | 2 | Medium | Keep YAML flat; one field per rule; AGENTS.md prose remains as comments |
| Orchestrator adds install friction | 3 | Low | `run.py` is zero-dependency stdlib; no pip install required |
| Adapter diverges from registry | 3 | Medium | Adapters generated from registry at build time, not hand-written |

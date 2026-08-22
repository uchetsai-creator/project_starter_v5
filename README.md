# Project Starter

[![CI](https://github.com/uchetsai-creator/project_starter_v5/actions/workflows/ci.yml/badge.svg)](https://github.com/uchetsai-creator/project_starter_v5/actions/workflows/ci.yml)

A documentation-first template for AI-assisted development. Define what you're building before
an AI agent (Claude Code, etc.) starts writing code — then keep every doc in sync automatically
as work progresses.

This repo is a **pure template repository**. It contains no real project content — only blank
scaffolding under `templates/`. The validator scripts (`templates/script/`) go into your project's
`docs/script/`; individual doc templates are filled in one at a time as you follow the init guide.

**Who this is for:** developers using Claude Code who want the speed of AI-assisted development
without the usual cost — code that nobody, including a
future session of the same AI, can maintain because the docs never kept up. Works whether you're
building solo or with a team.

**What problem it solves:** AI can write code fast, but the common failure mode is that docs drift
out of sync with the code, a module ships with no explanation of how it works, or the AI starts a
new session with no memory of prior decisions. This framework makes the AI agree on scope and
edge cases with you *before* writing code, then runs validators that catch spec↔code drift and
missing documentation automatically — instead of relying on anyone remembering to check.

---

<details>
<summary><strong>Table of contents</strong> — this file covers a quickstart, the daily workflow, and a full reference/contributor manual; jump straight to what you need</summary>

**Get started**
- [Quick Start](#quick-start)
- [How it works](#how-it-works)
- [Project Initialization](#project-initialization)
- [Working on an existing project](#working-on-an-existing-project)

**Daily workflow**
- [Context Builder](#context-builder)
- [Orchestrator](#orchestrator)
- [Agent Adapters](#agent-adapters)
- [Verification](#verification) — what the pre-commit hook actually checks

**Reference**
- [Retrofitting an existing project](#retrofitting-an-existing-project)
- [Module types](#module-types)
- [Diagrams](#diagrams)
- [Module inventory scan](#module-inventory-scan)
- [Document completeness audit](#document-completeness-audit)
- [Module Docs](#module-docs)
- [Validation Telemetry](#validation-telemetry)
- [Spec ↔ Code Validator](#spec--code-validator)
- [Beyond static comparison: runtime contract testing](#beyond-static-comparison-runtime-contract-testing)
- [Security Scan (SAST)](#security-scan-sast)
- [Prose Quality (Vale)](#prose-quality-vale)
- [Limitations](#limitations) — read this before assuming a passing commit means correct code
- [Self-improving loop](docs/self-improving-loop.md)
- [PDF generation](docs/pdf-generation.md)
- [Key design decisions](#key-design-decisions)

**Contributing to this framework**
- [Framework maintenance](#framework-maintenance)
- [Running the test suite](#running-the-test-suite)

</details>

---

**Prerequisites:** Python 3.9+ and [PyYAML](https://pypi.org/project/PyYAML/)
(`pip install pyyaml`) — `orchestrator.py`, `build-context.py`, and `verify_registry.py` all
read `.yml`/`.yaml` config through it. `detect_type.py` and `setup.sh` need no extra packages.

## Quick Start

**Not sure which type fits?** Run the detector first:

```bash
# From code structure (existing project)
python3 detect_type.py /path/to/your-project

# From a text description
python3 detect_type.py --requirements "a web app with user accounts and a dashboard, plus an LLM chatbot with RAG and a system prompt"

# Or via setup.sh
bash setup.sh --detect /path/to/your-project
```

Outputs a ranked recommendation — including hybrids like `web-app+llm-app` (as in the example
above). Pass `--apply` to write the result directly into `.project-starter.yml`. **If confidence
is low** (including the zero-signal case, e.g. a description with no recognizable tech terms),
`--apply` refuses to write and exits non-zero instead of silently locking in a guess — confirm
the actual type with the user first (see AGENTS.md -> New requirement from the user), or pass
`--force` to apply it anyway. `--json` output includes an `"authoritative"` boolean for the same
signal in machine-readable form.

**A confidence threshold only catches a low-scoring guess — not a high-scoring one that's still
wrong** (e.g. mixed signals: a data-pipeline project with a small internal FastAPI admin panel
can genuinely score high for `web-app`). So every `--apply` — regardless of confidence — also
writes `project_type_confirmed: false` into `.project-starter.yml`. `.githooks/pre-commit` blocks
commits while that field is `false`; confirm the detected type is actually right, then set it to
`true` (or delete the line) to unblock. A human typing `project_type` in by hand never triggers
this field at all — it exists only to gate a *machine* guess, not to make every project justify
a human's own decision.

---

**New project (no code yet):**

1. **Bootstrap** — from this repo, run:
   ```bash
   bash setup.sh --init <type> /path/to/your-project
   ```
   `setup.sh` is bash-only. On native Windows without Git Bash/WSL, run the same logic directly
   through Python instead — `setup.sh --init` just delegates to this script:
   ```bash
   python3 init.py <type> /path/to/your-project
   ```
   Valid types: `web-app` | `cli-tool` | `library` | `data-pipeline` | `ml-pipeline` |
   `microservices` | `llm-app` | `iac` | `mobile-app`

   This copies all required framework files, writes a pre-filled `.project-starter.yml`, writes
   `CLAUDE.md` (`@AGENTS.md` — see Agent Adapters below) if it doesn't already exist, writes or
   appends to `.gitignore` so `.ai/`, `__pycache__/`, and `logs/` aren't committed by default (an
   existing `.gitignore` is appended to, never overwritten), and installs the pre-commit hook if
   the destination is already a git repository. It also copies `templates/ci/github-actions-
   verify.yml` in like any other reference template — but, unlike the pre-commit hook, does
   **not** install it into `.github/workflows/`: that hook only ever affects the person who
   installed it, while a GitHub Actions workflow runs on every contributor's PR the moment it's
   merged, whether or not they use this framework. Deciding to impose that on a shared repo is
   left to whoever owns it — see Verification below for how to opt in deliberately. Skip to step 2
   once done.

   *Manual alternative:* copy `AGENTS.md`, `orchestrator.py`, `build-context.py`,
   `_workflow_utils.py`, `workflow-registry.yaml`, `document-registry.yaml`,
   `debug-instrumentation-rules.md`, `code-quality-check.md`, `learning-log.md`, `.githooks/`,
   `guidance/`, `adapters/claude/skills/` → `.claude/skills/` (see Agent Adapters below), and
   `templates/script/` → `docs/script/` into your project root — **except**
   `templates/script/framework/`, which is framework-repo-only (see the file tree above) and
   must not be copied into a user project. Also create a
   `CLAUDE.md` containing just `@AGENTS.md` so Claude Code auto-loads AGENTS.md's rules every
   session. Then edit
   `.project-starter.yml`: replace `[your-project-type]` with your actual type — **the
   pre-commit hook blocks every commit until this placeholder is removed.**
2. Declare your project type at the top of `AGENTS.md` (see the type table in
   [Project Initialization](#project-initialization)), then open `templates/init/<type>.md`
   **from this framework repo** and follow its numbered steps. (The init files are not copied
   to your project — keep the framework repo around for reference.)
3. Run `python3 orchestrator.py --adapter claude` — writes
   `.ai/WORKFLOW.md` + `.ai/AI_CONTEXT.md` and renders `.claude/commands/start-task.md`.
4. Set the **Current Task** in `docs/current-state.md`, then start work: read
   `.ai/AI_CONTEXT.md` first, follow `AGENTS.md`'s rules as you go, and run the validators listed
   in `.ai/WORKFLOW.md` before closing out the task.
5. `git commit` — if you used `--init`, the hook is already installed. Otherwise install it once:
   `cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`. It then
   blocks every commit where required docs are missing, unfilled, or (if you've configured
   `spec_code_adapter` in `.project-starter.yml`) drifted from the code.

**Existing project (already has code):** keep a clone of this `project_starter_v5` repo in its own
location, entirely separate from the target project — e.g. `~/tools/project_starter_v5` — never
nested inside it. From that clone, run the same Bootstrap command above, pointed at the existing
project's directory:
```bash
cd ~/tools/project_starter_v5
bash setup.sh --init <type> /path/to/your-existing-project     # or: python3 init.py <type> /path/to/your-existing-project
```
It only ever copies specific files via `shutil.copytree`/`copy2`; it never touches `.git/`, so
this is always safe even when the destination already has its own git history — and if that
destination is itself a git repo, this also installs the pre-commit hook into *its* `.git/hooks/`,
so commits to that project are actually checked.

**Do not instead copy or `git clone` this `project_starter_v5` folder itself into your existing
project's directory.** If that folder still has its own `.git/` inside it, your existing repo's
`git add` will record it as a *gitlink* — a pointer to a commit SHA, not the actual file contents
— instead of real files. The commit looks fine locally, but anyone else who clones your repo (or
you, on a different machine) gets an empty/broken reference where those files should be, not the
framework itself. If this already happened to you: remove the nested `.git/` (or re-copy using
`--init` instead) and re-add the files so git records real content.

Then, from the target project's own directory, follow `templates/init/retrofit.md` (read from the
separate `project_starter_v5` clone, e.g. `~/tools/project_starter_v5/templates/init/retrofit.md`
— init files are never copied into the target project) instead of a type's init file — it scans
your actual codebase first (via `scan_codebase.py`) and documents what's really there, rather than
assuming a blank slate.

**Picking up framework updates later:** `git pull` inside the separate `project_starter_v5` clone,
then re-run the same `--init` command again, pointed at the same existing project — `init.py`'s
copies use `dirs_exist_ok=True`, so re-running it is safe and just overwrites the framework files
with the newer versions. This never touches the target project's own `.git/` either.

**If other people also work in the target project and you don't want to affect them:** the
pre-commit hook installed above only ever checks *your own* commits from *this* machine — nothing
else to do, no one else needs to know it's there. Leave `templates/ci/github-actions-verify.yml`
alone (do not copy it to `.github/workflows/`) and skip branch protection entirely — see
Verification → "Running the same checks in CI" for why those two specifically are repo-wide,
opt-in-only, and not something this framework enables by default.

**If the full document set feels heavier than you need** for a personal/analysis-only use of an
existing project, set `doc_profile: lite` in `.project-starter.yml` — downgrades
`permissions.md`, `business-*.md`, `backend/database/deployment.md`, `research.md`, and
`test-plan.md`/`test-report.md` from Required to Optional. Core contracts
(`project-requirements.md`, `quickstart.md`, `data-model.md`, `api-contract.md`,
`architecture.md`, `logging-spec.md`) stay Required either way. See `guidance/doc-profile.md`.

From here: **Project Initialization** below has the full per-type document list, **Verification**
covers exactly what the pre-commit hook checks, and **Spec ↔ Code Validator** covers wiring up
automatic spec↔code drift detection. Read **[Limitations](#limitations)** before assuming that
wiring gives you more than it actually does — in particular, it's off by default and does not
generate or enforce code from the spec.

---

## How it works

1. **`AGENTS.md`** defines the rules an AI agent follows: which docs to create, when to update
   them, and what to do when a task or module completes.
2. **`templates/`** holds the blank scaffolding — every document the agent will fill in.
3. As work happens, the agent keeps `docs/` (in your actual project) in sync with what was built,
   following the checklist in `AGENTS.md`.

```
project_starter/                     ← this repo (template only)
├── AGENTS.md
├── CLAUDE.md                        ← `@AGENTS.md` — Claude Code auto-loads this every session (see adapters/claude)
├── orchestrator.py                  ← workflow manager: writes .ai/WORKFLOW.md + calls build-context.py
├── build-context.py                 ← context builder: writes .ai/AI_CONTEXT.md from registry
├── _workflow_utils.py               ← shared helpers imported by orchestrator.py / build-context.py
├── workflow-registry.yaml           ← task_type → validator sequence mapping
├── document-registry.yaml           ← single source of truth for all document metadata
├── .project-starter.yml             ← template with [your-project-type] placeholder; copy + fill in per project
├── .gitignore                       ← excludes .ai/ (generated, not committed)
├── setup.sh                         ← setup helper: downloads plantuml.jar; `--init <type> <dest>` bootstraps a new project; `--detect` infers project type
├── init.py                          ← `setup.sh --init`'s logic in pure Python — same outcome, no bash required (native Windows)
├── detect_type.py                   ← infer project type from code structure or requirements text; supports hybrid types
├── debug-instrumentation-rules.md
├── code-quality-check.md            ← code review checklist for retrofitting existing projects
├── learning-log.md                  ← personal append-only log for Learning Checkpoint C.4 (teach-back gaps + pattern roster); not part of the document matrix
├── .githooks/
│   └── pre-commit                   ← the hook itself (see Verification below); install via `cp` + `chmod +x`
├── .pre-commit-config.yaml          ← optional alternative install path via the pre-commit framework (wraps .githooks/pre-commit, doesn't reimplement it)
├── .claude/
│   ├── settings.json                ← (optional, copy to your project) wires run-verify.sh + stop-hook.sh into Stop, session-start-hook.sh into SessionStart, pretooluse_scope_guard.py into PreToolUse
│   └── skills/
│       └── add-framework-adapter/SKILL.md  ← framework-repo-only Claude Skill; NOT copied to user projects (see docs/contributing-adapters.md)
├── .ai/                             ← generated context (gitignored); recreate with orchestrator.py
│   ├── AI_CONTEXT.md               ← ordered read list for the current task
│   ├── WORKFLOW.md                 ← deterministic workflow plan (pre-task, validators, closeout)
│   └── telemetry/                  ← validator run logs (gitignored)
│       └── validation-result.json  ← append-only: one entry per verify_docs/verify_content --telemetry run
├── logs/                            ← runtime logs (gitignored); generated by hooks, never committed
│   ├── verify-{timestamp}.json     ← per-session validator output (adapters/claude/run-verify.sh Stop hook)
│   └── telemetry/
│       ├── task-run.json           ← append-only: one entry per Claude Code session (stop-hook.sh)
│       ├── .orchestrator_runs.json ← orchestrator run counter per task (orchestrator.py)
│       └── skip-verify.json        ← append-only: one entry per PROJECT_STARTER_SKIP_VERIFY use (pre-commit)
├── adapters/                        ← agent adapter layer (translate WORKFLOW.md to each tool's native format;
│   │                                   Claude Code + Codex today — see Agent Adapters below)
│   ├── claude/
│   │   ├── start-task.md           ← slash command template (copy to .claude/commands/ in your project)
│   │   ├── run-verify.sh           ← Claude Code Stop-hook script: writes validator --json output to logs/verify-{timestamp}.json, plus real-time project_type_confirmed / Clarifying Questions Asked / Doc Checklist / Sprint Documentation Sync checks and the same --json output's --strict pass/fail for verify_docs/logs/tests/content
│   │   ├── stop-hook.sh            ← writes session boundary to logs/telemetry/task-run.json on Claude Code session end
│   │   ├── session-start-hook.sh   ← non-blocking nudge: re-checks current-state.md scoping state fresh every session, a brand-new-project nudge toward research.md when both Task and research.md are still unscoped, and a spec-drift nudge when a Required Context file was committed more recently than current-state.md itself
│   │   ├── learning_log_nudge.py   ← non-blocking nudge: flags when docs/task-log.md was closed out more recently than learning-log.md was last touched (never checks entry content — see Learning Checkpoint enforcement below)
│   │   ├── pretooluse_scope_guard.py ← BLOCKING: denies Edit/Write/MultiEdit/NotebookEdit on source files until current-state.md is scoped (see Learning Checkpoint enforcement below)
│   │   ├── telemetry_writer.py     ← telemetry row writer invoked by stop-hook.sh
│   │   └── skills/                 ← Claude Skills, static; copied to .claude/skills/ automatically by `--init` (see Agent Adapters → Per-tool setup)
│   │       ├── retrofit-existing-project/SKILL.md
│   │       ├── code-quality-check/SKILL.md
│   │       ├── module-completion-check/SKILL.md
│   │       ├── sprint-doc-sync/SKILL.md
│   │       ├── learning-checkpoint/SKILL.md
│   │       ├── task-closeout/SKILL.md
│   │       └── research-decision-log/SKILL.md
│   └── codex/
│       ├── setup.md                ← one-time setup instructions (written to .codex/setup.md by orchestrator.py --adapter codex)
│       └── task-instructions.md    ← current workflow snapshot template (written to .codex/task-instructions.md)
├── examples/                        ← minimal complete reference projects (one per type; golden regression tests run against these)
│   ├── web-app/
│   ├── cli-tool/
│   ├── data-pipeline/
│   ├── llm-app/
│   ├── iac/
│   ├── library/
│   ├── ml-pipeline/
│   ├── mobile-app/
│   ├── microservices/
│   └── microservices-web-app/              ← hybrid example (Microservices + Web App)
├── tests/                           ← framework test suite
│   ├── unit/                        ← unit tests for individual scripts
│   ├── e2e/                         ← end-to-end pipeline tests
│   ├── snapshot/                    ← snapshot tests for orchestrator + build-context + verify_docs output
│   ├── golden/                      ← golden regression tests: full chain against examples/ with snapshot diff
│   ├── contract/                    ← structural contract tests
│   └── fixtures/                    ← filled doc fixtures (one per project type) for E2E tests
├── docs/                            ← framework design documents (not copied to projects)
│   ├── architecture-analysis.md    ← current coupling problems + responsibility boundaries
│   ├── refactoring-plan.md         ← 3-phase migration plan (registry → context builder → orchestrator)
│   ├── context-builder-design.md   ← build-context.py design: inputs, outputs, algorithm
│   ├── contributing-adapters.md    ← guide for writing new framework adapters
│   ├── self-improving-loop.md      ← diagnose_spec.py / propose_framework_fix.py: architecture, iteration limit, usage
│   └── pdf-generation.md           ← PlantUML setup + generating the merged spec PDF
├── guidance/
│   ├── document-purposes/
│   │   ├── index.md         ← index: type → per-type file lookup
│   │   ├── common.md        ← applies to all project types
│   │   ├── scripts-reference.md ← docs/script/ + adapters/ + diagram-tooling reference (split out of common.md; load only when needed)
│   │   ├── web-app.md
│   │   ├── cli-tool.md
│   │   ├── library.md
│   │   ├── data-pipeline.md
│   │   ├── ml-pipeline.md
│   │   ├── microservices.md
│   │   ├── llm-app.md
│   │   ├── iac.md
│   │   └── mobile-app.md
│   └── learning-checkpoints/
│       ├── common.md    ← unfamiliar-tech / existing-code / new-requirement / review question templates
│       ├── web-app.md
│       ├── cli-tool.md
│       ├── library.md
│       ├── data-pipeline.md
│       ├── ml-pipeline.md
│       ├── microservices.md
│       ├── llm-app.md
│       ├── iac.md
│       └── mobile-app.md
└── templates/
    ├── project-requirements.md      ← project scope, goals, edge cases, acceptance criteria
    ├── project-plan.md              ← sprint/task breakdown per feature
    ├── current-state.md             ← the active task
    ├── sprint-sync.md               ← sprint-end Document Update Checklist (load only at sprint end)
    ├── changelog.md                 ← completed task history
    ├── task-log.md                  ← task verification log (AI writes one row per completed task)
    ├── sprint-change-log.md         ← implementation changes this sprint (doc sync deferred to sprint end)
    ├── codebase-map.md              ← package vs. custom code, by layer; includes project tree
    │
    ├── init/                        ← per-type project initialization sequences (load only the one that matches)
    │   ├── web-app.md
    │   ├── cli-tool.md
    │   ├── library.md
    │   ├── data-pipeline.md
    │   ├── ml-pipeline.md
    │   ├── microservices.md
    │   ├── llm-app.md
    │   ├── iac.md
    │   ├── mobile-app.md
    │   ├── document-matrix.md       ← Required/Optional/N/A table per project type (load only when initializing)
    │   └── retrofit.md              ← Step-by-step retrofit procedure for existing codebases
    │
    ├── specs/
    │   │                              ── Universal (all project types) ──
    │   ├── quickstart.md            ← setup steps, prerequisites, local startup, verification
    │   ├── research.md              ← technology decisions + alternatives considered (excluded from PDF until filled)
    │   ├── glossary.md              ← business terms, technical terms, abbreviations
    │   ├── dependencies.md          ← runtime packages, dev packages, external services, infrastructure
    │   ├── test-plan.md             ← testing strategy, scope, environment, CI integration
    │   └── test-report.md           ← test results, pass/fail summary, coverage, known issues
    │   │                              ── Web App / Microservices ──
    │   ├── data-model.md            ← schema, indexes, state machines, migrations
    │   ├── api-contract.md          ← endpoints, events, validation rules, error codes (REST + WebSocket + GraphQL + gRPC)
    │   ├── permissions.md           ← roles, permission matrix, endpoint access control
    │   ├── logging-spec.md          ← logging rules, logger instantiation, module naming
    │   │                              ── CLI Tool ──
    │   ├── cli-contract.md          ← subcommands, flags, exit codes, stdin/stdout contract
    │   ├── release-guide.md         ← versioning policy, publish checklist, deprecation policy
    │   ├── compatibility-matrix.md  ← supported runtime versions, peer deps, known incompatibilities
    │   │                              ── Library / SDK ──
    │   ├── public-api.md            ← public functions/classes/types, stability tiers, deprecation log
    │   ├── release-guide.md         ← (same template as CLI Tool)
    │   ├── compatibility-matrix.md  ← (same template as CLI Tool)
    │   │                              ── Data Pipeline / ML Pipeline ──
    │   ├── pipeline-contract.md     ← inter-stage input/output contracts, cross-stage consistency check
    │   ├── data-model.md            ← schema, indexes (shared with Web App template)
    │   ├── logging-spec.md          ← (shared with Web App template)
    │   │                              ── ML Pipeline (additional) ──
    │   ├── model-contract.md        ← model input/output schema, production thresholds, retraining policy
    │   └── experiment-log.md        ← per-run experiment record (hypothesis → config → results → decision)
    │   │                              ── Microservices (additional) ──
    │   ├── service-catalog.md       ← all services: owner, port, URL, dependencies, events
    │   └── service-contract.md      ← inter-service REST contracts and event schemas
    │   │                              ── AI / LLM Application ──
    │   ├── llm-contract.md          ← model, system prompt, parameters, tool schemas, retry strategy
    │   ├── prompt-library.md        ← index only: prompt list + naming rules (no prompt content here)
    │   ├── prompts/
    │   │   └── [prompt-id]-prompt.md ← one file per prompt: template, variables, examples, version history
    │   ├── eval-spec.md             ← LLM-as-a-judge criteria, rubric, fixed test case set (stable config)
    │   ├── eval-log.md              ← append-only eval run results (load only when comparing versions)
    │   ├── rag-contract.md          ← retrieval sources, chunking, embedding model, vector store (optional)
    │   └── mcp-contract.md          ← MCP server connections, tool schemas, tool-use policy (optional)
    │
    ├── architecture/
    │   ├── architecture.md          ← components, data flow, structured YAML for diagram (all types)
    │   ├── backend.md               ← backend stack, layering, module pattern (not for Library / SDK)
    │   ├── frontend.md              ← frontend stack, page structure, component strategy (Web App / Microservices only)
    │   ├── database.md              ← entities/relationships (conceptual level; not for CLI / Library)
    │   ├── deployment.md            ← services, env vars, startup flow (Web App / Pipeline / Microservices)
    │   └── distribution.md          ← build, publish, install instructions (CLI Tool / Library / SDK)
    │
    ├── business/
    │   ├── business-process.md      ← index + rules for business process files (per process)
    │   ├── business-objects.md      ← index + rules for business object files (per object)
    │   └── business-rules.md        ← approval/validation/notification/audit rules
    │
    ├── flows/
    │   ├── module-data-flow.md      ← index + rules for module flow files (Feature / Background Job / Pipeline Stage / Shared Utility)
    │   └── module-flow.md           ← index + rules for cross-module sequence files (per module)
    │
    └── script/
        ├── validators/              ← shipped to user projects (docs/script/validators/)
        │   ├── verify_docs.py       ← document completeness + fill quality audit
        │   ├── verify_logs.py       ← log format + trace_id documentation audit
        │   ├── verify_tests.py      ← test-report.md fill quality audit
        │   ├── verify_acceptance.py ← functional acceptance gate: FR-XXX → test plan → test report (all 9 types)
        │   ├── verify_module_docs.py ← module flow + log-<module>.md coverage (via --src) + quality audit
        │   ├── verify_index_coverage.py ← business-objects.md / business-process.md / prompt-library.md index ↔ per-item file coverage
        │   ├── verify_content.py    ← full document content quality gate (all Required docs × project type)
        │   ├── verify_spec_code.py  ← spec ↔ code drift validator (core — no framework logic)
        │   ├── verify_security.py   ← SAST wrapper (bandit / eslint-plugin-security / semgrep), independent of spec ↔ code drift
        │   ├── verify_prose.py      ← prose-quality wrapper (Vale), independent of doc fill-quality checks
        │   ├── _prose_style/        ← self-contained Vale config + custom rules shipped for verify_prose.py
        │   │   ├── .vale.ini             ← StylesPath = styles, MinAlertLevel = suggestion
        │   │   └── styles/Custom/
        │   │       ├── WeaselWords.yml              ← vague qualifiers (very, obviously, simply, just, ...)
        │   │       └── NaturalLanguagePlaceholders.yml ← TBD / coming soon / TODO written as prose, not brackets
        │   ├── _spec_code_adapters/ ← framework detectors (one per framework; *Adapter classes are legacy shims)
        │   │   ├── _base.py              ← FrameworkAdapter/Detector ABCs + all NormalizedForm dataclasses
        │   │   ├── _example_adapter.py   ← Custom Adapter SDK reference implementation (self-tests)
        │   │   ├── airflow.py            ← AirflowDetector (Data Pipeline / ML Pipeline)
        │   │   ├── ansible.py            ← AnsibleDetector (IaC / DevOps — YAML)
        │   │   ├── click.py              ← ClickDetector (CLI Tool)
        │   │   ├── dagster.py            ← DagsterDetector (Data Pipeline / ML Pipeline)
        │   │   ├── django.py             ← DjangoDetector (Web App / Microservices — DRF)
        │   │   ├── express.py            ← ExpressDetector (Web App / Microservices — Node.js)
        │   │   ├── fastapi.py            ← FastAPIDetector (Web App / Microservices)
        │   │   ├── flask.py              ← FlaskDetector (Web App / Microservices)
        │   │   ├── flutter.py            ← FlutterDetector (Mobile App — Dart)
        │   │   ├── gin.py                ← GinDetector (Web App / Microservices — Go; requires tree-sitter + tree-sitter-go)
        │   │   ├── javascript_logging.py ← JavaScriptLoggingDetector (Logging — JS/TS/React, any project type)
        │   │   ├── langchain.py          ← LangchainDetector (AI / LLM App)
        │   │   ├── luigi.py              ← LuigiDetector (Data Pipeline / ML Pipeline)
        │   │   ├── prefect.py            ← PrefectDetector (Data Pipeline / ML Pipeline)
        │   │   ├── pulumi.py             ← PulumiDetector (IaC / DevOps — Python)
        │   │   ├── python_library.py     ← PythonLibraryDetector (Library / SDK)
        │   │   ├── python_logging.py     ← PythonLoggingDetector (Logging — any project type)
        │   │   ├── react_native.py       ← ReactNativeDetector (Mobile App — TSX/JSX)
        │   │   ├── swiftui.py            ← SwiftuiDetector (Mobile App — Swift)
        │   │   ├── terraform.py          ← TerraformDetector (IaC / DevOps — HCL)
        │   │   ├── tool_schema.py        ← ToolSchemaDetector (AI / LLM App)
        │   │   ├── typer.py              ← TyperDetector (CLI Tool)
        │   │   └── typescript.py         ← TypescriptDetector (Library / SDK — TS/TSX)
        │   ├── _verify_common.py    ← shared placeholder patterns imported by verify scripts
        │   ├── _otel.py             ← optional OpenTelemetry dual-emission (see Validation Telemetry -> OTel dual-emission)
        │   └── _registry.py         ← document registry loader
        ├── generators/              ← shipped to user projects (docs/script/generators/)
        │   ├── build_pdf.py         ← renders all ```plantuml blocks via PlantUML + merges docs/ into PDF
        │   ├── pdf_allowlist.py     ← single source of truth for which files appear in the PDF
        │   ├── plantuml.cfg         ← PlantUML renderer configuration
        │   ├── plantuml.jar         ← download separately (see docs/pdf-generation.md)
        │   ├── diagnose_spec.py     ← classifies spec fill gaps; triggers framework fix PRs
        │   ├── propose_framework_fix.py ← opens a PR on project_starter_v5 to add a missing template section
        │   ├── new_detector.py      ← scaffolds a new framework Detector for verify_spec_code.py
        │   ├── draft_module_flow.py ← drafts a module-data-flow.md pre-filled with real class/function names (Python/JS/TS)
        │   └── generate_openapi.py  ← generates openapi.yaml from api-contract.md, reusing WebAPIAdapter.extract_spec()
        ├── scanners/                ← shipped to user projects (docs/script/scanners/)
        │   └── scan_codebase.py     ← scans src/ and reports which modules are undocumented
        └── framework/               ← framework-internal only — NOT copied to user projects
            └── verify_framework.py  ← framework internal consistency audit (run in framework repo)
```

When a new project starts, `templates/` is copied in and becomes `docs/` — see
[Project Initialization](#project-initialization) below. Template filenames under
`templates/flows/` and `templates/business/` now match their `docs/modules/` and
`docs/business/` destination names exactly (no rename needed when copying) — they used to
carry a `-v2` version suffix for internal framework versioning, which required a separate
rename-reference table here; both were removed once nothing depended on the suffix anymore.

---

## Project Initialization

A new project does **not** keep `templates/` — it copies only the files its project type needs
into `docs/`, filling in the placeholders as it goes. The document matrix in `templates/init/document-matrix.md` defines
which files are required, optional, or N/A for each type.

> **Common pitfall — empty directories after `cp -r`:** If you use `cp -r src/ dst/`, the entire
> `src/` directory is nested *inside* `dst/` (resulting in `dst/src/`). Use `cp -r src/. dst/`
> (note the `/.` suffix) to copy the *contents* of `src/` into `dst/` directly. For example:
> ```bash
> # Wrong — creates docs/templates/script/validators/ instead of docs/script/validators/
> cp -r templates/script/validators/ docs/script/validators/
>
> # Correct — copies contents directly into docs/script/validators/
> mkdir -p docs/script/validators
> cp -r templates/script/validators/. docs/script/validators/
> ```

The root files are the same for every type:

```
new_project/
├── AGENTS.md                        ← declare Project Type at the top
├── CLAUDE.md                        ← `@AGENTS.md` — written automatically by `setup.sh --init`;
│                                        guarantees AGENTS.md's rules (incl. Learning Checkpoint) load
│                                        every Claude Code session regardless of which task-specific
│                                        docs current-state.md points to; see README → Agent Adapters.
├── orchestrator.py                  ← workflow manager: writes .ai/WORKFLOW.md + context
├── build-context.py                 ← context builder (called internally by orchestrator.py)
├── workflow-registry.yaml           ← task_type → validator sequence mapping
├── document-registry.yaml           ← required by all verify scripts and build_pdf.py; copy from framework root
├── debug-instrumentation-rules.md
├── code-quality-check.md
├── learning-log.md                  ← personal, not part of the doc matrix below (see Learning Checkpoint C.4)
├── .claude/
│   └── skills/                      ← copied automatically by `--init` (adapters/claude/skills/ → .claude/skills/)
├── guidance/
│   ├── document-purposes/
│   │   ├── index.md         ← index: maps project type → per-type file
│   │   ├── common.md        ← loaded by all types
│   │   ├── scripts-reference.md ← docs/script/ + adapters/ + diagram-tooling reference (load only when needed)
│   │   └── <type>.md        ← loaded for your declared type (e.g. web-app.md)
│   └── learning-checkpoints/
│       ├── common.md        ← question templates for Checkpoint 0/A/B/C (see AGENTS.md)
│       └── <type>.md        ← type-specific angle on the same checkpoints
└── docs/
    ├── project-requirements.md
    ├── project-plan.md
    ├── current-state.md
    ├── changelog.md
    ├── task-log.md
    ├── sprint-change-log.md
    ├── codebase-map.md
    ├── specs/ architecture/ modules/ script/{validators,generators,scanners}/    ← vary by type (see below)
```

> **`document-registry.yaml` must be in your project root** (not in `docs/`). It is the single
> source of truth for all document metadata and is required by every verify script and `build_pdf.py`.
> Copy it from the framework repo root when initializing a new project:
> ```bash
> cp /path/to/project_starter_v5/document-registry.yaml .
> ```
> Without it, scripts exit with: `FileNotFoundError: document-registry.yaml not found.`

> **Note:** `adapters/` stays in the framework repo — it is **not** copied to user projects.
> Every adapter's template is embedded directly in `orchestrator.py` (see `_ADAPTER_TEMPLATES`),
> so adapter output (`.claude/commands/start-task.md` or `.codex/setup.md` +
> `.codex/task-instructions.md`) can be generated into your project by running
> `orchestrator.py --adapter claude` or `orchestrator.py --adapter codex` from nothing more than
> the files listed above — no `adapters/` directory needs to exist in your project.

The `docs/specs/`, `docs/architecture/`, and `docs/modules/` contents differ per project type:

### Web App

```
docs/specs/
├── research.md  quickstart.md  data-model.md  api-contract.md
├── permissions.md  logging-spec.md
docs/architecture/
├── architecture.md  backend.md  database.md  deployment.md
└── frontend.md                                              ← optional
docs/business/
├── business-process.md  ← index
├── [process-name]-process.md                               ← one per process
├── business-objects.md  ← index
├── [object-name]-object.md                                 ← one per object
└── business-rules.md
docs/modules/
├── module-data-flow.md  module-flow.md                     ← index files
└── [module-name]/
    ├── [module]-module-data-flow.md
    └── log-[module].md
```

### CLI Tool

```
docs/specs/
├── research.md  quickstart.md  cli-contract.md
├── release-guide.md  logging-spec.md
└── compatibility-matrix.md                                 ← optional
docs/architecture/
└── architecture.md  backend.md  distribution.md
docs/modules/
├── module-data-flow.md  module-flow.md                     ← index files
└── [module-name]/
    └── [module]-module-data-flow.md
```

### Library / SDK

```
docs/specs/
├── research.md  quickstart.md  public-api.md
└── release-guide.md  compatibility-matrix.md
docs/architecture/
└── architecture.md  distribution.md                        ← architecture.md optional
docs/modules/
├── module-data-flow.md  module-flow.md
└── [module-name]/
    └── [module]-module-data-flow.md
```

### Data Pipeline

```
docs/specs/
├── research.md  quickstart.md  pipeline-contract.md
├── data-model.md  logging-spec.md  pipeline-debug.md
docs/architecture/
└── architecture.md  backend.md  database.md  deployment.md
docs/modules/
├── module-data-flow.md  module-flow.md                     ← index files
└── [stage-name]/                                           ← one per Pipeline Stage
    └── [stage]-module-data-flow.md
```

### ML Pipeline

```
docs/specs/
├── research.md  quickstart.md  pipeline-contract.md
├── data-model.md  model-contract.md  experiment-log.md  logging-spec.md  pipeline-debug.md
docs/architecture/
└── architecture.md  backend.md  database.md  deployment.md
docs/modules/
├── module-data-flow.md  module-flow.md
└── [stage-name]/
    └── [stage]-module-data-flow.md
```

### Microservices

Each service has its own `docs/` following the Web App structure above.
At the system level, add:

```
docs/specs/
├── service-catalog.md                                      ← all services: owner, port, deps
└── service-contract.md                                     ← inter-service REST + event schemas
docs/architecture/
├── architecture.md                                         ← system-level component diagram
└── deployment.md                                           ← cross-service deployment topology
```

### AI / LLM Application

```
docs/specs/
├── research.md  quickstart.md  llm-contract.md  logging-spec.md
├── llm-debug.md
├── prompt-library.md                                       ← index only
├── prompts/
│   └── [prompt-id]-prompt.md                              ← one per prompt
├── eval-spec.md                                            ← judge config + criteria + test cases
├── eval-log.md                                             ← append-only run results
├── rag-contract.md                                         ← optional, if using RAG
└── mcp-contract.md                                         ← optional, if connecting MCP servers
docs/architecture/
└── architecture.md
docs/modules/
├── module-data-flow.md  module-flow.md
└── [module-name]/
    └── [module]-module-data-flow.md
```

### Mixed / Hybrid Project Types

Some projects span more than one type. Declare both using `+` in `AGENTS.md` and take the union
of their required documents — everything goes in the same `docs/` folder.

```
Project Type: Data Pipeline + Web App
```

`AGENTS.md` drives initialization — declare the project type at the top, then load only the matching
`templates/init/[type].md` file. Each init file contains the full step-by-step sequence for that type.
For hybrid types and common combinations, see `AGENTS.md § Mixed / Hybrid Project Types`.

**Hybrid example:** `examples/microservices-web-app/` shows a complete Microservices + Web App
hybrid project. It demonstrates which documents come from each type, how `service-catalog.md` and
`service-contract.md` (Microservices) combine with `permissions.md` and `business/` docs (Web App),
and how to set `project_type: microservices+web-app` in `.project-starter.yml`.

---

## Working on an existing project

See `AGENTS.md → Startup sequence` for the full startup and task-completion protocol.

---

## Context Builder

`build-context.py` generates `.ai/AI_CONTEXT.md` — a deterministic read list for the current
task. AI tools read this file instead of inferring context from scratch on every startup.

```bash
# Generate context for the current task:
python3 build-context.py

# Override task type (sprint-end shows all Required docs):
python3 build-context.py --task-type sprint-end

# Preview without writing:
python3 build-context.py --dry-run
```

**Inputs:**

| Source | Field | Used for |
|---|---|---|
| `.project-starter.yml` | `project_type` | Registry lookup → required documents |
| `.project-starter.yml` | `task_type` (optional) | Filter to task-relevant documents |
| `docs/current-state.md` | `Task Type:` field (optional) | Override task_type per task |
| `document-registry.yaml` | `context_priority`, `purpose` | Sort and annotate output |

**Output — `.ai/AI_CONTEXT.md`:**

```markdown
# AI Context — data-pipeline / pipeline-stage
Generated: 2026-07-18T10:00:00

## Read (Required)
- docs/current-state.md   # Active task: goal, steps, and required context
- docs/specs/pipeline-contract.md   # Inter-stage input/output contracts

## Read (If Present)
- docs/specs/pipeline-debug.md   # Stage failure diagnosis guide

## Skip
- docs/changelog.md
- docs/specs/test-report.md
```

`.ai/` is gitignored — generated context is not committed. Regenerate it whenever the task changes.

**Task types:** `feature` · `pipeline-stage` · `bug-fix` · `sprint-end` · `eval-run` · `iac-change`

See `docs/context-builder-design.md` for the full algorithm and token reduction analysis.

---

## Orchestrator

`orchestrator.py` is the single entry point for starting work on a task. It selects the correct
validator sequence, writes `.ai/WORKFLOW.md`, and calls `build-context.py` internally — so context
and workflow always reflect the same project type and task type.

```bash
# Generate workflow plan + context for the current task:
python3 orchestrator.py

# Override task type:
python3 orchestrator.py --task-type sprint-end

# Preview WORKFLOW.md without writing:
python3 orchestrator.py --dry-run
```

**Inputs:**

| Source | Field | Used for |
|---|---|---|
| `.project-starter.yml` | `project_type` | Select validator commands + context |
| `.project-starter.yml` | `task_type` (optional) | Select workflow template |
| `.project-starter.yml` | `spec_code_adapter` / `spec_code_spec` / `spec_code_src` (optional, all three required together) — or `spec_code_bindings` (list form, for more than one contract; wins if both are set) | One `verify_spec_code.py --adapter --spec --src` step per resolved binding |
| `docs/current-state.md` | `Task Type:` field (optional) | Override task_type per task |
| `workflow-registry.yaml` | `workflows[task_type].validators` | Ordered post-task validator sequence |

**Output — `.ai/WORKFLOW.md`:**

```markdown
# Workflow Plan — pipeline-stage / data-pipeline
Generated: 2026-07-18T10:00:00

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_docs.py --project-type data-pipeline --content`
2. `python3 docs/script/validators/verify_logs.py --project-type data-pipeline --strict`
3. `python3 docs/script/validators/verify_content.py --project-type data-pipeline --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`
```

**Architecture:** `orchestrator.py` selects the workflow template; validators handle execution.
No validator logic lives in the orchestrator — separation of concerns is strictly maintained.

**`workflow-registry.yaml`** maps each task type to an ordered validator list. Add a new entry
when a new task type is introduced; update an existing entry when the validator set changes.
`verify_workflow_registry.py` schema-validates this file (script paths resolve to a real file,
no empty `validators` list, a `default` entry exists) the same way `verify_registry.py` validates
`document-registry.yaml` — a bad entry here used to only surface at `orchestrator.py`'s runtime,
not before a commit. Runs first in every sequence, same placement as `verify_registry.py`.

---

## Agent Adapters

The orchestrator produces a tool-agnostic `.ai/WORKFLOW.md` that any AI tool (or a human) can
read directly. Adapters are an optional extra layer on top of that: they translate the same
output into a specific tool's native instruction format so developers do not need to wire up
the orchestrator manually. Claude Code and Codex ship today — `AGENTS.md` and
`.ai/WORKFLOW.md` remain plain Markdown any tool can follow without one.

```
orchestrator.py --adapter claude
        │
        ├── writes  .ai/WORKFLOW.md          (always)
        │
        └── claude  → .claude/commands/start-task.md   (slash command with WORKFLOW.md injected)

orchestrator.py --adapter codex
        │
        ├── writes  .ai/WORKFLOW.md          (always)
        │
        └── codex   → .codex/setup.md               (one-time setup instructions)
                     .codex/task-instructions.md   (current workflow snapshot injected)
```

**Constraint:** adapters contain only format translation. Document selection logic stays in
`document-registry.yaml` and `orchestrator.py` exclusively — any adapter that duplicates selection
logic is a bug.

### Usage

```bash
# Generate workflow + render Claude Code slash command:
python3 orchestrator.py --adapter claude

# Generate workflow + render Codex setup/task-instructions files:
python3 orchestrator.py --adapter codex

# Preview without writing any files:
python3 orchestrator.py --adapter claude --dry-run
```

### Per-tool setup

**Claude Code**

1. Run `python3 orchestrator.py --adapter claude` — this writes `.claude/commands/start-task.md`.
2. In any future session, type `/start-task` to have Claude run the orchestrator and walk through
   the current workflow plan.
3. (Optional) For fast feedback without waiting for a manual validator run, copy this repo's
   `.claude/settings.json` **and** `adapters/claude/*.sh` + `adapters/claude/*.py` into your
   project's `.claude/` and `adapters/claude/` folders respectively — `settings.json` references
   those scripts by relative path, so it does nothing on its own without them. This wires four
   hooks:
   - `adapters/claude/run-verify.sh` (Stop, non-blocking) — runs `verify_docs.py` / `verify_logs.py` /
     `verify_tests.py` / `verify_content.py` with `--json` and writes the combined output to
     `logs/verify-{timestamp}.json`, so you can see validator results without running them by hand.
     Also re-checks `project_type_confirmed`, `Clarifying Questions Asked`, Doc Checklist
     completeness, Sprint Documentation Sync's Pending-count threshold, and now the same
     `--strict` pass/fail those four validators would compute — parsed out of the `--json` output
     already captured above, since `--strict` only changes the exit code, never the JSON content,
     so nothing extra needs to run. All of this is the same set of checks `.githooks/pre-commit`
     enforces, but that script only ever sees them at `git commit`. For a workflow that pulls
     once, does a long stretch of local work, then pushes/merges once at the end, commits may be
     too infrequent for those gates to ever fire mid-task; reading the working tree directly (no
     staged-file concept needed) and reusing the already-captured validator JSON surfaces the same
     issues every session instead. Surfaced via `hookSpecificOutput.additionalContext`, the same
     mechanism `session-start-hook.sh` uses for `SessionStart` — Stop hooks support the identical
     schema. Non-blocking on purpose, matching this hook's existing design: `pretooluse_scope_guard.py`
     below is the one gate that doesn't depend on commit frequency at all (fires per-edit); this
     is a second, informational layer for the rest, not a third blocking gate.
   - `adapters/claude/stop-hook.sh` (Stop, non-blocking) — records the session boundary to
     `logs/telemetry/task-run.json` (see Validation Telemetry below).
     Note: this writes to telemetry only — not to `docs/task-log.md`. Task log rows are written
     during task closeout by the AI agent, not automatically on session end.
   - `adapters/claude/learning_log_nudge.py` (SessionStart, non-blocking) — surfaces a reminder
     when the last committed `docs/task-log.md` entry is newer than the last commit touching
     `learning-log.md`. It only compares commit timestamps of the two files — it never reads
     entry content, and never blocks. `learning-log.md`'s own header says it is "never checked
     by any validator"; this hook does not change that. It exists because Learning Checkpoint
     C.4's teach-back gap is, by design, the one Learning Checkpoint step with no mechanical
     backstop at all (see Learning Checkpoint enforcement below) — unlike scoping, there is no
     reliable way to verify a teach-back actually happened, only a way to make forgetting to
     log it less silent.
   - `adapters/claude/pretooluse_scope_guard.py` (PreToolUse, **blocking**) — the only hook in
     this list that runs *before* a tool call instead of after. It denies `Edit` / `Write` /
     `MultiEdit` / `NotebookEdit` on any source-like path (not `docs/`, not a framework file)
     whenever `docs/current-state.md` has no scoped `Current Task` or an unfilled/invalid
     `Clarifying Questions Asked` field. `.githooks/pre-commit`'s "Unscoped source-change guard"
     enforces the same rule at commit time as a backstop — this is what actually stops the
     write from happening in the first place instead of only catching it after the fact. Like
     every other gate here, it's optional: without it, "ask before implementing" (AGENTS.md ->
     New requirement from the user) is enforced by the agent choosing to follow AGENTS.md, not
     by anything mechanical, until this hook (or the pre-commit backstop) is wired in.
   - `.githooks/pre-commit`'s **Doc Checklist completeness guard** — the same "convention until
     something checks it" gap existed for `current-state.md`'s Doc Checklist (AGENTS.md -> Closing
     out a task): nothing previously verified the per-task doc-update list was actually applied
     before a task was marked `Status: Complete`. This guard blocks that commit if the Doc
     Checklist section still has an unchecked `- [ ]` item or the raw, never-customized template
     placeholder (`` `docs/[relevant spec]` ``) — reusing the checklist's own checkbox state
     directly rather than adding a separate summary field a task could just as easily mark "done"
     without the items underneath actually being checked off.
   - `.githooks/pre-commit`'s **Sprint Documentation Sync guard** — same gap for the count trigger
     in AGENTS.md -> Sprint Documentation Sync: nothing verified the Pending backlog in
     `sprint-change-log.md` was actually synced once it hit 3 entries, so it could grow
     indefinitely with no mechanical backstop, only the `sprint-doc-sync` Skill's nudge. This
     guard blocks every commit once 3 (or more) entries are at `Status: Pending documentation
     synchronization`, until Sprint Documentation Sync (`templates/sprint-sync.md`) marks them
     `Documentation synchronized`. `adapters/claude/run-verify.sh` mirrors this (and the two guards
     above) as a non-blocking Stop-hook nudge — see the fast-feedback bullet below for why a
     git-commit-only gate isn't enough on its own for a workflow with infrequent commits.
4. The seven procedural docs below auto-trigger as Claude Skills — `--init` / `setup.sh --init`
   already copied `adapters/claude/skills/` into your project's `.claude/skills/` folder (see
   `init.py`), so this step needs no action for a project bootstrapped that way. Only relevant
   if you used the Manual alternative in Quick Start instead: copy `adapters/claude/skills/` →
   `.claude/skills/` by hand. Each is a `SKILL.md` with a `description` Claude Code matches
   against the current task — the framework still works without this (AGENTS.md's own trigger
   text is the tool-agnostic fallback for any other tool or manual use), this just gives Claude
   Code a second, more direct path to the same guidance and packages it inside the project
   itself instead of requiring the framework repo to stay around for reference:

   | Skill | Fires on |
   |---|---|
   | `retrofit-existing-project` | documenting an existing codebase that has code but no docs |
   | `code-quality-check` | a requested code/architecture review, or Learning Checkpoint A's escalation |
   | `module-completion-check` | a module just reached 100% complete |
   | `sprint-doc-sync` | `sprint-change-log.md` reaches 3 pending-sync entries |
   | `learning-checkpoint` | before implementing any task (Checkpoints 0/A/B/C) |
   | `task-closeout` | end of every task, when current-state.md's inline Closeout section isn't enough detail on its own (full verification table, or the commit-sequencing note for promoting Next Task → Current Task) |
   | `research-decision-log` | a technology decision surfaces in conversation — explicit ("let's go with X") or implicit (comparing libraries and landing on one, a schema choice with stated rationale, a resolved `NEEDS CLARIFICATION`); drafts a `research.md` entry and asks before writing it, never writes without approval |

   `docs/contributing-adapters.md` is intentionally not in this list — it is packaged as a
   separate, framework-repo-only skill at `.claude/skills/add-framework-adapter/` (see
   Contributing a Framework Adapter below), since it's for people extending project_starter_v5
   itself, not for application code written in a project that merely uses the framework.
   `tests/contract/test_skill_contracts.py` guards seven of these eight `SKILL.md` bodies
   against drifting from their canonical source docs (`templates/init/retrofit.md`,
   `code-quality-check.md`, `templates/module-completion.md`, `templates/sprint-sync.md`,
   `guidance/learning-checkpoints/common.md`, `templates/task-completion.md`,
   `docs/contributing-adapters.md`), the same pattern `test_agent_adapter_templates.py`
   already uses for the slash-command templates above. `research-decision-log` has no
   canonical source doc to mirror — it doesn't wrap an existing procedural doc the way the
   other seven do, so it's written directly as a standalone `SKILL.md` instead.

**Codex**

1. Run `python3 orchestrator.py --adapter codex` — this writes `.codex/setup.md` (one-time
   setup instructions) and `.codex/task-instructions.md` (current workflow snapshot).
2. Point Codex at `.codex/setup.md` at the start of a session; it explains how to read
   `.codex/task-instructions.md` for the current steps and how to regenerate both files.
3. Re-run `python3 orchestrator.py --adapter codex` whenever the task or workflow changes —
   `.codex/task-instructions.md` is regenerated each time, the same way
   `.claude/commands/start-task.md` is for Claude Code.

**Other AI tools:** no dedicated adapter ships today (Claude Code and Codex are the only tools
this framework has real usage with) — `AGENTS.md` and `.ai/WORKFLOW.md` are plain Markdown, so
any tool can still be pointed at them manually: run `python3 orchestrator.py` (no `--adapter`
flag) and have the tool read `.ai/AI_CONTEXT.md` + `.ai/WORKFLOW.md` at the start of a session. A
dedicated adapter for another tool, if one is genuinely needed later, would follow the same
shape as `adapters/claude/` / `adapters/codex/` — a template embedded in `orchestrator.py`'s
`_ADAPTER_TEMPLATES`, kept in sync by a `test_agent_adapter_templates.py`-style contract test.
(Note: this is a different "adapter" concept from the spec↔code capability adapters described in
`docs/contributing-adapters.md` below — that doc is about `verify_spec_code.py` framework
detectors, unrelated to agent-tool adapters.)

---

## Retrofitting an existing project

If a project already has code but no documentation, use the retrofit flow in `templates/init/retrofit.md`.
The flow follows Steps 1, 1b, 1c, 2, 3, 4, and 5:

- **Step 1** — Read the codebase (entry point, schema, one complete module)
- **Step 1b** — Run the module inventory scan — `scan_codebase.py` lists every source folder and flags
  undocumented ones. Confirm the list before any documentation is written
- **Step 1c** — Code Quality Check — run `code-quality-check.md` and produce a report covering
  layering, Package First violations, complexity/over-engineering, naming, schema design,
  security, and error handling
- **Step 2** — Fill in architecture and spec documents — describe what actually exists, not what should
  exist. Use your actual layer names, not assumed patterns
- **Step 3** — Fill in module flow files — one module at a time, following the confirmed inventory.
  `draft_module_flow.py <module_dir> --project-type <type>` pre-fills real class/function names
  from static analysis (Python/JS/TS) instead of starting from a blank file — it does not invent
  the call sequence or business meaning, that part is still written by hand
- **Step 4** — Fill in project status — reconstruct requirements, mark existing modules as completed
- **Step 5** — Generate the PDF

`code-quality-check.md` can also be used independently at any time as a standalone code review checklist.

---

## Module types

`module-data-flow.md` supports four flow-file formats: **Feature**, **Background Job**, **Pipeline Stage**, and **Shared Utility**.

See `templates/flows/module-data-flow.md → Module Types` for the full description, entry-point rules, and Background Job vs Pipeline Stage disambiguation.

`scan_codebase.py --project-type` uses type-specific scan labels (Command for CLI Tool, Namespace for Library / SDK, Service for Microservices) as vocabulary — these are classification labels, not separate flow formats. All three use the Feature or Shared Utility flow format in their module flow files.

---

## Diagrams

Two tools generate diagrams from Markdown — each outputs both an **interactive HTML**
(drag, zoom, click) and a **static SVG** (for PDF embedding). `build_pdf.py` automatically
appends a type suffix to output filenames to avoid collisions (e.g. `data-model-state.html`).

| Tool | Input | Diagram type | Where it's embedded |
|---|---|---|---|
| `build_pdf.py` (via PlantUML) | Any ` ```plantuml ` block in any `.md` | All UML types | Wherever the block appears in the PDF |
| `generators/schema_to_html.py` | Prisma / SQL file | ERD | `specs/data-model.md` |

> **Multiple blocks per file:** `build_pdf.py` supports multiple diagram blocks in a
> single `.md` file. Each block generates its own HTML + SVG pair, named by its `title:`
> slug (e.g. `data-model-workorder-status-state.html`). A file with a single block keeps
> the original naming behaviour.

> **Diagram placement markers:** to control where a diagram appears in the PDF, add
> `<!-- diagram: KEY -->` at the desired location in the target document (where `KEY` is
> the HTML filename without extension and suffix, e.g. `<!-- diagram: architecture -->`).
> Without a marker, diagrams are appended to the end of their target section.

```bash
# All PlantUML diagrams are rendered automatically when you run:
python3 docs/script/generators/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf

# ERD only (schema_to_html.py is still used for the database diagram):
python3 docs/script/generators/schema_to_html.py path/to/schema.prisma -o docs/specs/schema.html
```

---

## Module inventory scan

Before documenting an existing codebase, run the inventory scan to get an objective view of
what exists and what is already documented:

```bash
# Show tree view + coverage report (auto-detects module type from folder names)
python3 docs/script/scanners/scan_codebase.py src

# Explicit project type — uses correct vocabulary (Feature / Pipeline Stage / Command / Namespace / Service)
python3 docs/script/scanners/scan_codebase.py src --project-type data-pipeline
python3 docs/script/scanners/scan_codebase.py src --project-type web-app
python3 docs/script/scanners/scan_codebase.py src --project-type cli-tool
# Valid values: web-app | cli-tool | library | data-pipeline | ml-pipeline | microservices | llm-app | iac | mobile-app

# Scan N levels deep — for monorepos or Microservices with per-service src/ folders
python3 docs/script/scanners/scan_codebase.py services --project-type microservices --depth 2

# Machine-readable JSON output (for agent consumption)
python3 docs/script/scanners/scan_codebase.py src --project-type web-app --format json

# Auto-generate stub module-data-flow.md files for undocumented modules (skips existing files)
python3 docs/script/scanners/scan_codebase.py src --project-type web-app --scaffold

# Update the Project Structure and Coverage Summary sections in codebase-map.md automatically
python3 docs/script/scanners/scan_codebase.py src --project-type web-app --update docs/codebase-map.md
```

The scan detects folder names to classify folders by module type. Pass `--project-type` to
use the correct vocabulary for your project (e.g. Pipeline Stage for data pipelines,
Command for CLI tools, Namespace for libraries, Service for microservices).

For Data Pipeline and ML Pipeline projects, directories containing `*_stage.py`, `step_*.py`,
or `run_*.py` are labelled `Pipeline Stage (detected)` — giving higher confidence than
name-based classification alone.

Re-run at the end of Step 3 (retrofit) to confirm full coverage.

---

## Document completeness audit

After initializing or retrofitting a project, verify that all Required documents for the
declared type exist in `docs/`:

```bash
# Check completeness for a single project type
python3 docs/script/validators/verify_docs.py --project-type web-app

# Hybrid project — takes the union of both type matrices
python3 docs/script/validators/verify_docs.py --project-type data-pipeline+web-app

# Exit with code 1 if any Required document is missing (for CI or pre-merge checks)
python3 docs/script/validators/verify_docs.py --project-type web-app --strict

# Machine-readable JSON output (for agent consumption)
python3 docs/script/validators/verify_docs.py --project-type web-app --json

# Custom docs/ path
python3 docs/script/validators/verify_docs.py --project-type web-app --docs path/to/docs
```

**Output statuses:**

| Status | Meaning |
|---|---|
| Present | File exists in docs/ |
| Missing Required | File is Required for this type and does not exist |
| Missing Optional | File is Optional for this type and does not exist |
| — N/A | File is not applicable for this type |
| Orphan | File exists but is N/A for this type, or is not in the document matrix |

Valid `--project-type` values: `web-app`, `cli-tool`, `library`, `data-pipeline`, `ml-pipeline`, `microservices`, `llm-app`, `iac`, `mobile-app`

---

## Document Profile (lite vs full)

`.project-starter.yml`'s `doc_profile` (`full` by default) controls how much of the
Required-document set actually gates a commit — see `guidance/doc-profile.md` for the full
explanation, including exactly when to switch back to `full`. In short: `lite` downgrades
`permissions.md`, the three `business/*.md` files, `backend.md`/`database.md`/`deployment.md`,
`research.md`, and `test-plan.md`/`test-report.md` from Required to Optional, for a
solo/small project that doesn't have real stakeholders, roles, or a deploy target yet. Core
contracts (`project-requirements.md`, `quickstart.md`, `data-model.md`, `api-contract.md`,
`architecture.md`, `logging-spec.md`) stay Required in both profiles — `lite` reduces
paperwork, not the documents the spec↔code drift gate and context builder actually depend on.

```bash
# Reads doc_profile automatically from .project-starter.yml — no flag needed, and this is
# exactly how .githooks/pre-commit invokes both scripts today:
python3 docs/script/validators/verify_docs.py --project-type web-app --strict
python3 docs/script/validators/verify_content.py --project-type web-app --strict

# Override explicitly (e.g. to preview what switching would change, without editing the yml):
python3 docs/script/validators/verify_docs.py --project-type web-app --lite
python3 docs/script/validators/verify_docs.py --project-type web-app --full
```

Switching `doc_profile` never creates a different document set — it only changes which
documents in the *same* registry currently gate a commit. Going from `lite` to `full`
re-requires exactly the documents `lite` deferred; there is no migration step.

---

## Module Docs

`verify_module_docs.py` audits module flow file coverage and quality — checking that every module in `docs/modules/` has a complete `*-module-flow.md` and, for pipeline stages, a `*-module-data-flow.md`.

This script is a **contributor tool**: run it manually before opening a PR, not at every commit. It is intentionally excluded from the pre-commit gate because it is slow and produces noisy output on work-in-progress modules. `templates/module-completion.md` and `templates/sprint-sync.md` do call it, but only at the two event-triggered points where a module (or the whole sprint) is actually supposed to be finished — not per-task.

```bash
python3 docs/script/validators/verify_module_docs.py --docs docs/
```

**With `--src`, it also cross-references `scan_codebase.py`** to catch a module that exists in
source but has no flow file at all — a gap that `--docs`-only mode can't see, since it only
audits files that already exist. In this mode it additionally reports whether each module has a
`log-<module-name>.md` (N/A for project types where `logging-spec.md` itself is N/A, e.g.
library/iac):

```bash
python3 docs/script/validators/verify_module_docs.py --project-type web-app --src src/ --strict
```

**Zero-coverage safeguard:** if `scan_codebase.py` finds 0 modules to check — because the src
layout doesn't match its folder-based classification (flat files with no subfolders, `--depth`
too shallow, or every folder happens to match a Shared/Infrastructure naming pattern) — while
real code files do exist under `--src`, this is reported as an explicit failure under `--strict`
rather than a silent pass. Previously "0 modules found" always exited 0 regardless of `--strict`,
which meant a src layout `scan_codebase.py` couldn't parse defeated the whole coverage check
without any indication that nothing had actually been audited. `scan_codebase.py` itself carries
the same safeguard — a `0/0 (100%)` coverage line is followed by a `[WARN]` when real files exist
but none were classified as a module.

**`verify_index_coverage.py`** does the equivalent coverage check for documents that have no
source-code equivalent to scan against — `business-objects.md`, `business-process.md`, and
`prompt-library.md` each index a set of per-item files, and this checks both directions: an
indexed row with no file, and a file with no indexed row (orphan). It needs no `--project-type` —
each index is checked only if it exists, which is itself the type-applicability gate:

```bash
python3 docs/script/validators/verify_index_coverage.py --docs docs/ --strict
```

---

## Framework maintenance

`verify_framework.py` audits the framework's own internal consistency. Run it after any framework update, or any time you modify `document-registry.yaml`, AGENTS.md, document-matrix.md, sprint-sync.md, or any document-purposes file.

**Adding a new document:** edit `document-registry.yaml` only — `verify_docs.py` and `verify_content.py` derive their document lists from it automatically. Also update `templates/init/document-matrix.md` (human-readable copy) and the relevant `guidance/document-purposes/*.md` file.

```bash
python3 templates/script/framework/verify_framework.py
python3 templates/script/framework/verify_framework.py --strict   # exits 1 if any check warns or fails
python3 templates/script/framework/verify_framework.py --json     # machine-readable output
```

**Checks performed:**

| Check | What it verifies |
|---|---|
| Stale pointer | Every `.md` reference in AGENTS.md resolves to an existing file |
| Token budget | AGENTS.md is ≤ 200 lines |
| Matrix ↔ template | Every matrix row has a template file; every template has a matrix row |
| Sprint-sync coverage | Every non-exempt R/O document has a sprint-sync checklist item |
| Purposes coverage | Every Required document appears in the matching document-purposes file |
| Cross-reference integrity | Every `### X.md` header in guidance/document-purposes/*.md has a template file |
| Type completeness | Every type slug in AGENTS.md's init table has a matching init file and document-purposes file |
| Script type sync | `scan_codebase.py` and `document-registry.yaml` declare the same set of project types |
| Build-PDF type sync | `build_pdf.py` VALID_PROJECT_TYPES matches all declared project types |
| Content coverage | `document-registry.yaml` schema valid; `verify_content.py` covers all document checkers |
| Registry ↔ matrix sync | Every `document-registry.yaml` entry has a row in `document-matrix.md`, and vice versa |

**Output:**

| Status | Meaning |
|---|---|
| [OK] Pass | Check passed |
| [WARN] Warning | Non-critical drift detected |
| [FAIL] Fail | Check failed — lists affected file and line |

---

## Running the test suite

```bash
pip install -r requirements-dev.txt
pytest tests/
ruff check .    # lint — config in pyproject.toml [tool.ruff]
mypy .          # type check — config in pyproject.toml [tool.mypy]
```

Both run in CI on every push/PR (`.github/workflows/ci.yml`), before the test suite. mypy
uses gradual typing (untyped function bodies aren't checked by default) rather than
`--strict`, since most of this codebase had no prior type-hint coverage — the goal is
catching real inconsistencies in code that already declares types, not forcing annotations
everywhere at once.

Re-generate snapshot golden files after intentional output changes:

```bash
pytest tests/snapshot/ --snapshot-update   # orchestrator / build-context / verify_docs snapshots
pytest tests/golden/ --snapshot-update     # golden regression chain snapshots (examples/)
```

The PDF smoke test (`tests/e2e/test_pdf_generation.py`) is skipped unless `plantuml.jar` is present.

**Real-tool tests are skipped, not failed, when their tool isn't installed** — the mocked
JSON-parsing unit tests (e.g. `test_verify_security.py`) still run either way, but the
tests that exercise the actual tool (`test_gin_detector.py`, `test_verify_prose.py`,
`test_verify_security_e2e.py`, `test_otel.py`'s real-collector cases) only run when it's
present. `.github/workflows/ci.yml` installs all of them — bandit, semgrep,
tree-sitter/tree-sitter-go, eslint + eslint-plugin-security (via npm, at the repo root —
see `verify_security.py`'s `_run_eslint()` docstring for why location matters), Vale, and
the opentelemetry packages — specifically so CI exercises the real integrations, not just
the mocks. To run them locally the same way:
```bash
pip install bandit semgrep tree-sitter tree-sitter-go opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
npm install --no-save eslint eslint-plugin-security   # must run at the repo root
# Vale: see vale.sh/docs/install (not a pip/npm package)
```

---

## Verification

Quality checks run automatically at the git commit boundary — no AI tool dependency.

```
Any AI tool (Claude Code / other / manual)
        ↓
   git commit
        ↓
 .githooks/pre-commit                  ← PRIMARY: tool-agnostic, always fires
        ↓
 [running in framework repo (templates/script/framework/verify_framework.py present)]
 verify_framework.py --strict          ← framework integrity (block)
        ↓
 verify_docs.py --content              ← doc completeness + fill quality (block)
 verify_logs.py                        ← log format + trace_id (when present, block)
 verify_tests.py                       ← test-report.md fill quality (when present, block)
 verify_content.py                     ← document content quality gate (when present, block)
         [verify_module_docs.py called internally by verify_content.py]
        ↓
 [test_command set in .project-starter.yml]
   actually runs the configured test command  ← real test execution (block on failure)
   — unlike verify_tests.py above, which only checks that test-report.md is filled in
        ↓
 [project_type_confirmed: false in .project-starter.yml]  confirmed yet? ← detect_type.py guess audit (block)
 [sprint-change-log.md: >= 3 entries Pending documentation synchronization]
   Sprint Documentation Sync run yet? ← Pending-count threshold (block)
 [AGENTS.md staged]      line count ≤ 200            ← token budget (block)
 [specs/*.md staged]     changelog.md also staged?   ← audit trail (warn)
 [current-state.md + Status:Complete]  Closeout filled? ← closeout (block)
 [current-state.md + real Task]  Clarifying Questions Asked filled? ← Checkpoint B audit trail (block)
 [spec-facing doc staged] no Sprint/Task refs         ← writing audience (block)
 [spec_code_* set in .project-starter.yml]
   [spec contract or configured src/ staged]  verify_spec_code.py ← spec↔code drift (block)
 [security_scan_src set in .project-starter.yml]
   [configured src/ staged]  verify_security.py ← SAST: bandit / eslint-plugin-security / semgrep (block)
 [prose_scan_enabled: true in .project-starter.yml]
   [*.md under docs_path staged]  verify_prose.py ← prose quality: Vale (block)
        ↓
 PASS → commit proceeds
 FAIL → commit blocked, output shown to developer

Optional fast-feedback (Claude Code only, Stop hook — adapters/claude/run-verify.sh):
 same four validators → logs/verify-{timestamp}.json (visibility only, non-blocking)
 + re-checks project_type_confirmed / Clarifying Questions Asked / Doc Checklist /
   Sprint Documentation Sync / the four validators' --strict pass-fail against the
   working tree — same checks as above, surfaced every session instead of only at
   git commit (see Verification → "Running the same checks in CI" for the CI-side
   version of this same idea)
```

**Writing Audience violations** checks every document listed in `document-registry.yaml` for
`Sprint N` / `Task N` / `(SN)` references, not just the `audience: external` (stakeholder-facing)
subset it used to be hardcoded to — `audience` only ever meant "is this in the generated PDF,"
never "is per-task planning narrative okay to leave here." Reads each document's `path` from the
registry dynamically (same `_load_yaml()` import pattern as the `spec_code_bindings` resolution
above) instead of a second hardcoded list that could drift from it. `current-state.md`'s Steps
section and `sprint-change-log.md` are deliberately **not** in the registry — that's where
per-task planning and historical implementation notes actually belong; every document that *is*
registered (`api-contract.md`, `data-model.md`, `project-requirements.md`, and everything else,
`internal` or `external` alike) should only ever describe the system's current state.

**Open-ended per-item files** — `modules/[module]/[module]-module-data-flow.md`,
`modules/[module]/[module]-flow.md`, `business/[object-name]-object.md`,
`business/[process-name]-process.md`, `specs/prompts/[id]-prompt.md` — grow with however many
modules/objects/processes/prompts a project actually has, so their exact paths can never be
pre-registered; each family's *index* file is registered and covered by the check above, but the
per-item files need a pattern match instead, kept as a supplement to the registry-driven list, not
a replacement for it.

**Prototyping/spike escape hatch:** `PROJECT_STARTER_SKIP_VERIFY=1 git commit -m "wip"` skips
every check above for that one commit — loudly (`[SKIP]` line) and audibly (a row appended to
`logs/telemetry/skip-verify.json`), unlike `git commit --no-verify`, which skips silently with
no trace at all. Prefer the env var for that reason. Full rationale and behavior:
`.githooks/pre-commit`'s own header comment (canonical source — this paragraph is a summary).

**Running the same checks in CI (opt-in, repo-owner decision):** a local `.git/hooks/pre-commit`
only protects commits made on that one machine — anyone who hasn't installed it (a teammate, a
fresh clone, CI itself) gets none of this. Set `PROJECT_STARTER_DIFF_RANGE` (e.g.
`origin/main...HEAD`) before invoking `.githooks/pre-commit` to switch its diff source from the git
index (staged files — meaningless in a CI checkout, which has no staging step) to a git ref range,
and every file-content read from the staged version to the current working-tree version — the
checkout already *is* the state under test. Same script, same checks, no second implementation to
keep in sync. `templates/ci/github-actions-verify.yml` is a ready-to-use workflow built on this —
copy it to `.github/workflows/verify.yml` yourself if you want it:
```yaml
# templates/ci/github-actions-verify.yml -- copy to .github/workflows/verify.yml to activate
on:
  pull_request:
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - env:
          PROJECT_STARTER_DIFF_RANGE: origin/${{ github.base_ref }}...HEAD
        run: bash .githooks/pre-commit
```
**Deliberately not auto-installed by `--init`, unlike the pre-commit hook.** A local hook only ever
affects the person who installed it; a GitHub Actions workflow runs on *every* contributor's PR the
moment it's merged, whether or not they use this framework or agreed to it — a decision for
whoever owns the repo to make on purpose, not a default this framework should impose on a shared
project. If you do want it, pair it with a GitHub branch protection rule requiring the check to
pass before merge — without that, a failing run only shows a red X anyone can ignore, the same
"convention, not enforcement" gap a missing local hook has. Branch protection is a repository
setting, not something any script here can turn on for you — set it once, on GitHub, under the
target repo's Settings → Branches → Branch protection rules.

`verify_acceptance.py` (FR-XXX → test plan → test report traceability) is **not** part of
`.githooks/pre-commit` — checking full requirement traceability on every commit would block
normal mid-sprint work before all FRs have test-report entries. It runs at sprint end instead,
via the `sprint-end` entry in `workflow-registry.yaml` (see `templates/sprint-sync.md`).

**Edge Case traceability (Web App / Microservices, opt-in):** `verify_acceptance.py` also
cross-references `api-contract.md`'s `## Edge Cases` table against `test-plan.md`'s Test Scope —
same FR-XXX traceability shape, reused for a second table. The ID column ships bracket-wrapped
(`[EC-001]`) as a placeholder — a project that never replaces those with real, un-bracketed ids
(e.g. `EC-001`) gets zero issues from this check, not a warning that it's missing something. Once
you do adopt a real id, reference it from `test-plan.md`'s Requirement column (`FR-003, EC-002`)
or `verify_acceptance.py` reports it as untested. This closes part of the gap `verify_spec_code.py`
structurally can't: business rationale documented in prose (a `Design Note`, or *why* an edge case
matters) can never be schema-checked — see Limitations below — but whether a documented edge case
has *any* test referencing it at all now can be.

### Setup (once per project clone)

1. Install the hook:
   ```bash
   cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
   ```
   **Alternative** — if your team already manages hooks with the
   [pre-commit framework](https://pre-commit.com), copy `.pre-commit-config.yaml` into your
   project instead and run `pip install pre-commit && pre-commit install`. It wires in the exact
   same `.githooks/pre-commit` script as a single local hook (not a reimplementation — see the
   file's header comment for why) plus a few generic hygiene hooks
   (trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict) from
   [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) as a starting
   point for the wider ecosystem this unlocks. Pick one install method, not both.
2. Create `.project-starter.yml` at the project root:
   ```yaml
   project_type: data-pipeline   # your declared type
   docs_path: docs/
   ```
3. (Optional) For Claude Code fast-feedback, copy `.claude/settings.json` to your project's `.claude/` folder.
4. **Recommended** — turn on the spec ↔ code drift gate at commit time by adding
   `spec_code_adapter`, `spec_code_spec`, and `spec_code_src` to `.project-starter.yml` — see
   [Spec ↔ Code Validator → Wiring it into pre-commit](#wiring-it-into-pre-commit) below.
   Without these three keys the gate is skipped entirely — no drift protection at all, for any
   language or framework — and the pre-commit hook prints a non-blocking `[TIP]` (listing the
   adapters available for your project type) whenever you commit a spec contract file without
   this configured, as a reminder that it's off. See [Limitations](#limitations) below.
5. **Recommended** — set `test_command` in `.project-starter.yml` to your project's real test
   invocation (e.g. `test_command: pytest -q`) so pre-commit actually runs your test suite and
   blocks on a real failure. Without it, `verify_tests.py` only checks that
   `docs/specs/test-report.md` has been filled with non-placeholder numbers — it does not run
   anything, so a fabricated result would pass. Point it at a fast subset if your full suite is
   slow; every commit runs it.

### Tool compatibility

| AI tool | Pre-commit hook fires? | All checks fire? | Claude Code Stop hook? |
|---|---|---|---|
| Claude Code | ✅ on `git commit` | ✅ | ✅ optional |
| Any other AI tool | ✅ on `git commit` | ✅ | ❌ not applicable |
| Manual (no AI) | ✅ on `git commit` | ✅ | ❌ not applicable |


## Validation Telemetry

The framework writes structured JSON after each validator run and each Claude Code session end,
giving visibility into which validators fail most and how many orchestrator runs a task requires.
All telemetry is gitignored. By default it never leaves the local machine — see OTel
dual-emission below for the opt-in exception. Validator results go to `.ai/telemetry/`; session boundaries and orchestrator runs go to `logs/telemetry/`.

### What is logged

| Data | Source | Written by |
|---|---|---|
| Validator pass/fail per document | verify scripts | `verify_docs.py`, `verify_content.py` with `--telemetry` |
| Task session boundary | `current-state.md` + Stop hook | `adapters/claude/stop-hook.sh` |
| Orchestrator run count per task | `orchestrator.py` state file | `orchestrator.py` on each run |
| Token count (Claude Code session) | API response metadata | placeholder `null` — Claude Code doesn't expose per-session token usage to hooks, so this field can't be filled honestly; see Limitations |
| Token count + cost (`--semantic` LLM calls) | Anthropic API response `usage` | `semantic.py` — real numbers, see [Token usage (`--semantic`)](#token-usage---semantic) below |

### Schema — `validation-result.json` (append-only array)

```json
{ "ts": "2026-07-18T13:00:00Z", "project_type": "data-pipeline",
  "validator": "verify_content.py", "level": "fail",
  "warn_count": 0, "fail_count": 2,
  "failed_docs": ["pipeline-contract.md", "architecture.md"] }
```

`level` is `"pass"` or `"fail"`. `warn_count` tracks missing-optional documents (verify_docs only).
`failed_docs` lists document basenames for quick pattern analysis across runs.

### Schema — `task-run.json` (append-only array)

```json
{ "ts": "2026-07-18T14:00:00Z", "task": "implement extract stage",
  "adapter": "claude", "orchestrator_runs": 2, "token_count": null }
```

`orchestrator_runs` counts how many times `orchestrator.py` ran during the session (read from
`logs/telemetry/.orchestrator_runs.json`). `token_count` stays `null` here — this row is written
by the Stop hook at Claude Code session end, and Claude Code does not currently pass its own
token/cost totals to hooks. This framework does not fabricate that number; if you need real
Claude Code session cost, get it from `claude usage` / the Anthropic Console, not from this file.

### Token usage (`--semantic`)

Unlike the session-level `token_count` above, `--semantic` (see
[Semantic matching](#semantic-matching)) is the one place this framework makes a live LLM call
itself — so it's the one place real usage can be measured instead of estimated. Every call's
actual `response.usage` (from the Anthropic SDK) is accumulated for the run and appended to
`logs/telemetry/token-usage.json`:

```json
{ "ts": "2026-08-21T10:00:00Z", "model": "claude-haiku-4-5-20251001",
  "calls": 2, "input_tokens": 412, "output_tokens": 180,
  "estimated_cost_usd": 0.001312, "budget_tokens": null, "budget_exceeded": false }
```

- `estimated_cost_usd` is computed from a pricing table in `semantic.py` (USD per 1M tokens) —
  it's an estimate derived from real token counts, not a real counted estimate of token counts.
  Verify against [anthropic.com/pricing](https://www.anthropic.com/pricing) before relying on it,
  and override with `SPEC_CODE_PRICE_INPUT_PER_M` / `SPEC_CODE_PRICE_OUTPUT_PER_M` (USD per 1M
  tokens) if the model isn't in the table or the price has moved.
- **Budget cap:** set `SPEC_CODE_TOKEN_BUDGET` (total input+output tokens) to stop `--semantic`
  from making further LLM calls once the run crosses it. Remaining items are skipped with a
  `[WARN]`; verdicts already gathered are still returned. There is no cap by default.
- The CLI prints a one-line summary (`Token usage (...): N call(s), X in / Y out — est. cost
  $Z`) after the semantic report, and `--json` includes the same data under `token_usage`.
- Dual-emitted as an OTel span (`semantic_token_usage`) alongside the local JSON file, same
  opt-in pattern as [OTel dual-emission](#otel-dual-emission-opt-in) below — a no-op unless
  both `opentelemetry-*` is installed and `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

### Usage

```bash
# Run verify_docs with telemetry
python3 docs/script/validators/verify_docs.py --project-type data-pipeline --telemetry

# Run verify_content with telemetry
python3 docs/script/validators/verify_content.py --project-type data-pipeline --telemetry

# Telemetry is written to:
# .ai/telemetry/validation-result.json  (validator results — written by --telemetry flag)
# logs/telemetry/task-run.json          (session boundaries — written by stop-hook on session end)
```

The Stop hook (`adapters/claude/stop-hook.sh`) writes to `task-run.json` automatically on
Claude Code session end. No manual steps required once the hook is installed.

### OTel dual-emission (opt-in)

Every telemetry write point above (`_verify_common._append_telemetry`, used by all `verify_*.py`
scripts; `orchestrator.py`'s run counter; `.githooks/pre-commit`'s skip-verify record) also emits
the same event as an [OpenTelemetry](https://opentelemetry.io/) span, for teams that want
telemetry visible in a real observability backend (Honeycomb, Grafana Tempo, Jaeger, ...) instead
of only as local JSON files.

**This is dual-write, not a replacement.** The local JSON files above are written exactly as
before, unconditionally — some of that data is read back synchronously by this same framework
(`orchestrator.py` reads its own `.orchestrator_runs.json` right after writing it, to compute the
run count embedded in `task-run.json`), which an external OTel backend cannot serve back to a
local process the same way a local file can. OTel is additive telemetry for outside observers, not
a migration of the framework's own internal state.

**Prerequisites:**
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
export OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector:4318
```

Both installing the packages and setting the environment variable are required — either one
missing means every emission call is a silent no-op, not an error. This matches the opt-in
pattern used throughout this README (`spec_code_adapter`, `security_scan_src`,
`prose_scan_enabled`): telemetry export is off by default and never blocks or slows down a commit
because a collector happens to be unreachable — confirmed directly: an unreachable collector logs
nothing and does not raise, even though the underlying OTel SDK's own internal error logging is
verbose enough on its own (a multi-frame traceback per failed export) that this framework
explicitly suppresses it (`_otel.py` sets the `opentelemetry` logger to `CRITICAL`) rather than
let that noise appear on every commit whenever the collector is briefly down.

**Trace correlation.** Every span emitted while `docs/current-state.md` has a scoped Current
Task shares that task's `trace_id`, as a direct child of one synthetic `task: <name>` root span
created on the task's first emission. Each `verify_*.py` run and each `orchestrator.py` run is
its own OS process, so this is cross-process trace-context propagation done by hand: the root's
`trace_id`/`span_id` are persisted to `logs/telemetry/.otel_trace_context.json` (gitignored, like
the rest of `logs/`) and reconstructed as a parent context on every later emission for the same
task. The practical effect: point a collector at this and a single task's worth of validator runs
render as one connected trace/waterfall — not a pile of unrelated points — without needing to
thread a trace ID through every script's argument list by hand. A task change (the persisted task
name no longer matches the current one) starts a fresh trace automatically.

Known edge case: two processes for the same task starting at almost the same instant could both
observe "no root yet" and each create one, producing two traces instead of one for that task —
the same class of race `.orchestrator_runs.json`'s read-compare-write already has, just exercised
more often now. Not fixed with a file lock in this pass; acceptable given how rarely two telemetry
emissions for the same task actually race in practice, but worth knowing if a trace ever looks
unexpectedly split in two.

**Seeing it locally:** any OTLP-compatible backend works; the fastest to try is a local Jaeger:

```bash
docker run -d --name jaeger -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Then run a task's normal workflow (`orchestrator.py`, the validators in `.ai/WORKFLOW.md`) and
open `http://localhost:16686` — the task's trace groups every validator run for it under one
waterfall. Entirely optional: skip this and nothing about the framework changes: no new
dependency is installed, no local service is required, and none of this is on the path of running
`.githooks/pre-commit`, `orchestrator.py`, or any validator in their normal, unconfigured mode.

---

## Spec ↔ Code Validator

Existing validators check document presence and fill quality — they don't verify that code
matches what the spec declares. `verify_spec_code.py` closes this gap by comparing both sides
through a framework adapter interface, without any framework-specific logic in the core.

### Architecture

```
verify_spec_code.py
        │  --adapter, --spec, --src
        ▼
FrameworkAdapter (_spec_code_adapters/_base.py)
        │
        ├── extract_spec(spec_path) → list[NormalizedForm]
        ├── extract_code(src_path)  → list[NormalizedForm]
        └── (no comparison logic)

verify_spec_code.py
        │  compare(spec_items, code_items)
        ▼
    MismatchReport
      missing_in_code  — declared in spec, absent in code
      extra_in_code    — in code, not in spec
      field_mismatches — removed_from_code | added_in_code | type_changed
```

**Constraint:** `verify_spec_code.py` contains zero framework-specific logic. Any code that
knows what Airflow or Click is belongs in an adapter. Any adapter that contains comparison
logic is a bug.

### NormalizedForm per project type

| Project type | NormalizedForm | Key fields |
|---|---|---|
| Web App / Microservices | `NormalizedEndpoint` | method, path, request fields, response fields |
| Data Pipeline / ML Pipeline | `NormalizedStageContract` | stage name, input fields (name + type), output fields (name + type) |
| CLI Tool | `NormalizedCommand` | command name, flags (name + type) |
| Library / SDK | `NormalizedFunction` | function name, params (name + type), return type |
| AI / LLM App | `NormalizedTool` | tool name, parameter schema |
| IaC / DevOps | `NormalizedResource` | resource name, resource type, config keys |
| Mobile App | `NormalizedScreen` | screen name, props (name + type) |
| Any (Logging capability) | `NormalizedLogPoint` | function, operation, state, level — checks docs/modules/*/log-*.md against real logger calls in src/, not gated by project type |

### Adapters

| Adapter | Framework | Project type | Spec source | Code source |
|---|---|---|---|---|
| `airflow` | Apache Airflow | Data Pipeline / ML Pipeline | `pipeline-contract.md` `### Stage` + `#### Input/Output Contract \| Schema \|` | `@task`-decorated Python functions |
| `click` | Click | CLI Tool | `cli-contract.md` `### \`cmd\`` + `#### Flags` table | `@click.command()` + `@click.option()` Python functions |
| `fastapi` | FastAPI | Web App / Microservices | `api-contract.md` `### METHOD /path` + `#### Request Body` / `#### Response Body` tables | `@app.{method}("/path")` / `@router.{method}` decorated functions |
| `flask` | Flask | Web App / Microservices | `api-contract.md` `### METHOD /path` + `#### Request Body` / `#### Response Body` tables | `@app.route('/path', methods=[...])` decorated functions |
| `express` | Express | Web App / Microservices | `api-contract.md` `### METHOD /path` + `#### Request Body` / `#### Response Body` tables | `router.{method}('/path', ...)` in JS/TS files |
| `django` | Django REST Framework | Web App / Microservices | `api-contract.md` `### METHOD /path` + `#### Request Body` / `#### Response Body` tables | `@api_view([...])`-decorated functions, correlated with `path()`/`re_path()` entries in `urlpatterns` |
| `gin` | Gin (Go) | Web App / Microservices | `api-contract.md` `### METHOD /path` + `#### Request Body` / `#### Response Body` tables | `r.{METHOD}("/path", handler)` route registration; request/response fields read from the Go struct bound via `c.ShouldBindJSON(&x)` / passed to `c.JSON(status, x)`, using each struct's `json:"..."` tags — requires `pip install tree-sitter tree-sitter-go` (the only tree-sitter-based detector in this table; every other one is regex-based) |
| `dagster` | Dagster | Data Pipeline / ML Pipeline | `pipeline-contract.md` `### Stage` + `#### Input/Output Contract \| Schema \|` | `@op` / `@asset`-decorated Python functions |
| `prefect` | Prefect | Data Pipeline / ML Pipeline | `pipeline-contract.md` `### Stage` + `#### Input/Output Contract \| Schema \|` | `@task` / `@flow`-decorated Python functions |
| `luigi` | Luigi | Data Pipeline / ML Pipeline | `pipeline-contract.md` `### Stage` + `#### Input Contract \| Schema \|` (no Output Contract — Luigi's `output()` names a file target, not a data schema) | `class Stage(luigi.Task):` with `luigi.Parameter()`-typed class attributes |
| `typer` | Typer | CLI Tool | `cli-contract.md` `### \`cmd\`` + `#### Flags` table | `@app.command()`-decorated functions; flags come from parameter type hints, not `@click.option()` decorators |
| `python_library` | Python `__all__` | Library / SDK | `public-api.md` `### function_name` + `#### Parameters` table | Functions listed in `__all__` + type-annotated signatures |
| `typescript` | TypeScript | Library / SDK | `public-api.md` `### function_name` + `#### Parameters` table | `export function`/`export const ... =>` declarations, or an internal function named in `export { a as b }` |
| `tool_schema` | Python docstrings / OpenAI JSON | AI / LLM App | `llm-contract.md` `### tool_name` + `#### Parameters` table | Type-annotated Python functions or OpenAI-compatible JSON schema |
| `langchain` | LangChain | AI / LLM App | `llm-contract.md` `### tool_name` + `#### Parameters` table | `@tool` / `@tool("name")`-decorated functions |
| `terraform` | Terraform HCL | IaC / DevOps | `topology.md` `### label (resource_type)` + `#### Configuration` table | `resource "type" "name" { ... }` blocks in `.tf` files |
| `pulumi` | Pulumi (Python) | IaC / DevOps | `topology.md` `### label (resource_type)` + `#### Configuration` table | `ResourceClass("name", key=val, ...)` constructor calls in Python |
| `ansible` | Ansible | IaC / DevOps | `topology.md` `### label (resource_type)` + `#### Configuration` table | YAML tasks — one module key per task, e.g. `amazon.aws.s3_bucket: {name: ..., ...}` |
| `react_native` | React Native | Mobile App | `mobile-contract.md` `### ScreenName` + `#### Props` table | Function/const components with destructured props in `.tsx`/`.jsx` |
| `swiftui` | SwiftUI | Mobile App | `mobile-contract.md` `### ScreenName` + `#### Props` table | `struct ScreenName: View { ... }` — non-private stored properties |
| `flutter` | Flutter / Dart | Mobile App | `mobile-contract.md` `### ScreenName` + `#### Props` table | `class ScreenName extends StatelessWidget` with `final` fields in `.dart` |
| `logging` | (all — unions every logging detector) | Any (Logging capability) | Same `log-<module-name>.md` table, all languages present in `--src` | Runs `python_logging` + `javascript_logging` together — use this by default |
| `python_logging` | Python `logging` | Any (Logging capability) | `log-<module-name>.md` `\| Function \| Operation \| State \| Level \|` table (see logging-spec.md → Module Log File Format) | `logger.<level>(...)` calls anywhere in a function, matched via `ast` |
| `javascript_logging` | JS / TS / React | Any (Logging capability) | Same `log-<module-name>.md` table format as `python_logging` | `logger.<level>(...)` calls in `.js`/`.jsx`/`.ts`/`.tsx`; regex + brace-depth scan (no JS AST available in Python) |

### Spec format (Airflow)

Declare fields in the `Schema` row of each stage's Input/Output Contract:

```markdown
### extract

#### Input Contract
| Property | Value |
|---|---|
| Schema | raw_amount: float, customer_id: int |

#### Output Contract
| Property | Value |
|---|---|
| Schema | amount: float |
```

### Usage

```bash
# Data Pipeline — validate stage contracts against Airflow code
python3 docs/script/validators/verify_spec_code.py \
    --project-type data-pipeline --adapter airflow \
    --spec docs/specs/pipeline-contract.md --src src/stages/ --strict

# CLI Tool — validate subcommands and flags against Click code
python3 docs/script/validators/verify_spec_code.py \
    --project-type cli-tool --adapter click \
    --spec docs/specs/cli-contract.md --src src/cli.py --strict

# Web App — validate HTTP endpoints against FastAPI code
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter fastapi \
    --spec docs/specs/api-contract.md --src src/ --strict

# Web App — validate HTTP endpoints against Flask code
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter flask \
    --spec docs/specs/api-contract.md --src src/ --strict

# Web App — validate HTTP endpoints against Django REST Framework code
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter django \
    --spec docs/specs/api-contract.md --src src/ --strict

# Microservices — validate HTTP endpoints against Express (Node.js) code
python3 docs/script/validators/verify_spec_code.py \
    --project-type microservices --adapter express \
    --spec docs/specs/api-contract.md --src src/ --strict

# Data Pipeline — validate stage contracts against Dagster code
python3 docs/script/validators/verify_spec_code.py \
    --project-type data-pipeline --adapter dagster \
    --spec docs/specs/pipeline-contract.md --src src/ --strict

# Data Pipeline — validate stage contracts against Prefect code
python3 docs/script/validators/verify_spec_code.py \
    --project-type data-pipeline --adapter prefect \
    --spec docs/specs/pipeline-contract.md --src src/ --strict

# Data Pipeline — validate stage contracts against Luigi code (input side only —
# Luigi's output() names a file target, not a data schema)
python3 docs/script/validators/verify_spec_code.py \
    --project-type data-pipeline --adapter luigi \
    --spec docs/specs/pipeline-contract.md --src src/ --strict

# CLI Tool — validate subcommands and flags against Typer code
python3 docs/script/validators/verify_spec_code.py \
    --project-type cli-tool --adapter typer \
    --spec docs/specs/cli-contract.md --src src/ --strict

# Library / SDK — validate public API against Python __all__ + signatures
python3 docs/script/validators/verify_spec_code.py \
    --project-type library --adapter python_library \
    --spec docs/specs/public-api.md --src src/ --strict

# Library / SDK — validate public API against a TypeScript library
python3 docs/script/validators/verify_spec_code.py \
    --project-type library --adapter typescript \
    --spec docs/specs/public-api.md --src src/ --strict

# AI / LLM App — validate tool definitions against Python functions or OpenAI JSON schema
python3 docs/script/validators/verify_spec_code.py \
    --project-type llm-app --adapter tool_schema \
    --spec docs/specs/llm-contract.md --src src/ --strict

# AI / LLM App — validate tool definitions against LangChain @tool functions
python3 docs/script/validators/verify_spec_code.py \
    --project-type llm-app --adapter langchain \
    --spec docs/specs/llm-contract.md --src src/ --strict

# IaC — validate topology against Terraform HCL
python3 docs/script/validators/verify_spec_code.py \
    --project-type iac --adapter terraform \
    --spec docs/specs/topology.md --src infra/ --strict

# IaC — validate topology against Pulumi Python
python3 docs/script/validators/verify_spec_code.py \
    --project-type iac --adapter pulumi \
    --spec docs/specs/topology.md --src infra/ --strict

# IaC — validate topology against Ansible playbooks/tasks
python3 docs/script/validators/verify_spec_code.py \
    --project-type iac --adapter ansible \
    --spec docs/specs/topology.md --src playbooks/ --strict

# Mobile App — validate screen contracts against React Native TSX/JSX
python3 docs/script/validators/verify_spec_code.py \
    --project-type mobile-app --adapter react_native \
    --spec docs/specs/mobile-contract.md --src src/screens/ --strict

# Mobile App — validate screen contracts against Flutter Dart
python3 docs/script/validators/verify_spec_code.py \
    --project-type mobile-app --adapter flutter \
    --spec docs/specs/mobile-contract.md --src lib/screens/ --strict

# Mobile App — validate screen contracts against native SwiftUI
python3 docs/script/validators/verify_spec_code.py \
    --project-type mobile-app --adapter swiftui \
    --spec docs/specs/mobile-contract.md --src ios/Screens/ --strict

# Logging capability — validate log-<module-name>.md points against real logger calls,
# every registered language at once (use this by default; --spec accepts a single
# log-<module-name>.md file OR a directory, e.g. docs/modules/, to check every module
# in one run)
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter logging \
    --spec docs/modules/ --src src/ --strict

# Logging capability — isolate one language's results instead of the union above
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter python_logging \
    --spec docs/modules/ --src src/ --strict
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter javascript_logging \
    --spec docs/modules/ --src src/ --strict

# List all registered adapters
python3 docs/script/validators/verify_spec_code.py --list-adapters

# JSON output for agent consumption
python3 docs/script/validators/verify_spec_code.py \
    --project-type data-pipeline --adapter airflow \
    --spec docs/specs/pipeline-contract.md --src src/ --json

# Dry-run: show mismatches without exit code change
python3 docs/script/validators/verify_spec_code.py \
    --project-type data-pipeline --adapter airflow \
    --spec docs/specs/pipeline-contract.md --src src/ --dry-run
```

The validator exits 0 with a warning if `--adapter`/`--spec`/`--src` are not provided —
safe to include in the workflow registry and pre-commit hook for all projects.

### Wiring it into pre-commit

Manual invocation (above) is one way to run the drift check. To make it fire automatically —
in `.githooks/pre-commit` and in the validator sequence `orchestrator.py` writes to
`.ai/WORKFLOW.md` — set three keys in `.project-starter.yml`:

```yaml
spec_code_adapter: fastapi
spec_code_spec: docs/specs/api-contract.md
spec_code_src: src/
```

All three must be set together; leave them blank to skip the gate (the default — matches
prior behavior with no config).

**Lowering the activation cost:** filling these in by hand is the main reason this gate stays
off in practice. `python3 detect_type.py <path>` now also guesses `spec_code_adapter` /
`spec_code_spec` / `spec_code_src` for you — e.g. if it finds `fastapi` in `requirements.txt`
and recommends `web-app`, it prints the matching adapter, the canonical spec path for that
type, and a best-effort `src/` guess. `--apply` on a **fresh** project (no `.project-starter.yml`
yet) writes all three pre-filled, clearly marked as an unverified guess to confirm before
relying on it; an existing `.project-starter.yml` is never touched by this — only `project_type`
is ever rewritten. Coverage is intentionally partial (dependency name or a telltale file per
framework, see `_ADAPTER_SIGNALS` in `detect_type.py`) — no match just means fall back to
setting the three keys by hand as before.

Once configured:

- `orchestrator.py` appends `--adapter --spec --src` automatically to every
  `verify_spec_code.py` step in `.ai/WORKFLOW.md` — no need to edit `workflow-registry.yaml`.
- `.githooks/pre-commit` runs `verify_spec_code.py --strict` whenever **either** side of the
  contract changes: the spec contract document itself, or any staged file under `spec_code_src`.
  This is what catches code changed directly without the spec being updated — the exact case a
  spec-file-only trigger misses.

**More than one contract to validate?** Use `spec_code_bindings` instead of the single trio — a
list of the same three keys, one entry per contract:

```yaml
spec_code_bindings:
  - adapter: fastapi
    spec: docs/specs/api-contract.md
    src: src/api/
  - adapter: airflow
    spec: docs/specs/pipeline-contract.md
    src: src/stages/
```

Mutually exclusive with the single trio (`spec_code_bindings` wins if both are set — no need to
migrate an existing single-binding project unless you're adding a second contract). Both
`orchestrator.py` and `.githooks/pre-commit` render/run one `verify_spec_code.py` invocation per
binding — the hook's bash side delegates the actual YAML resolution to `orchestrator.py`'s
`_resolve_spec_code_bindings()` (`python3 -c "from orchestrator import ..."`) rather than
re-parsing a nested YAML list with `grep`/`sed`, which is a fundamentally different (and much
riskier to get subtly wrong) problem than the flat `key: value` lines the rest of the hook reads.
An incomplete entry (missing `spec` or `src`) is silently dropped, not an error — same
graceful-skip philosophy as the single trio being left blank.

### Writing a custom adapter

Only 8 broad project-type **capability adapters** exist (`web-api`, `cli`, `data-pipeline`,
`library`, `llm-app`, `iac`, `mobile`, `logging`), each with a handful of **detectors** for
specific frameworks or languages (see the Adapters table above). The `logging` capability is
keyed by language, not framework — it applies to every project type, not just one (see
`NormalizedForm per project type` above). If your framework or language isn't detected yet,
you almost always just need to add a new detector to an existing capability — not a whole new
adapter.

**Quick steps (adding a framework to an existing capability — the common case):**

```bash
# Scaffolds the detector file and registers it in one step:
python3 docs/script/generators/new_detector.py --capability web-api --name django
# Adding a language to the logging capability works the same way, e.g.:
python3 docs/script/generators/new_detector.py --capability logging --name go_logging
python3 docs/script/generators/new_detector.py --list-capabilities   # see all 8 + their NormalizedForm
```

1. Run `new_detector.py` (above) — creates `_spec_code_adapters/<framework>.py` with a
   `Detector` subclass and registers it in the target capability's `_DETECTORS` dict.
2. Implement `extract(files)` / `_parse_file()` for the files your detector understands.
   No file discovery, no spec parsing needed — the capability adapter already does both.
3. Replace the generated self-test with a real round-trip check
   (`python3 _spec_code_adapters/<framework>.py` → prints `[OK] self-test passed`).
4. (Optional) Re-run with `--alias` to also register a standalone `--adapter <framework>` in
   `ADAPTER_REGISTRY`, and add a pre-commit trigger for your spec file.

Building support for an entirely new **project type** (not just a new framework) is rarer and
requires a new capability adapter — see `docs/contributing-adapters.md` → Situation B.

**Reference files:**
- `_spec_code_adapters/_example_adapter.py` — fully annotated implementation with a self-test
- `_spec_code_adapters/_base.py` — all NormalizedForm types, the `Detector` and `FrameworkAdapter` contracts
- `docs/contributing-adapters.md` — complete step-by-step guide for both cases, with a decision
  guide for "is my framework in-scope for an existing capability?"

```bash
# List all registered adapters
python3 docs/script/validators/verify_spec_code.py --list-adapters

# Run the reference implementation self-test
python3 docs/script/validators/_spec_code_adapters/_example_adapter.py
```

### Semantic matching

`--semantic` adds an LLM-assisted pass on top of the structural diff. After the structural pass
identifies field name differences (`removed_from_code` + `added_in_code` for the same item),
Claude evaluates whether the differing names represent the same concept.

**When to use:** when field names differ between spec and code (e.g., spec declares `order_id: string`,
code has `id: int`) and you want reasoning about whether the rename is intentional drift or an
undocumented refactor.

**Not for automated use:** `--semantic` makes LLM API calls and is not suitable as a gate. Never add
`--semantic` to `workflow-registry.yaml` or pre-commit sequences — it is a developer analysis tool only.

**Requirements:** `pip install anthropic` and `ANTHROPIC_API_KEY` environment variable.

**Token cost:** ~200–400 tokens per field pair using claude-haiku-4-5 is a reasonable ballpark for
sizing a run before you start it, but every run also records *actual* usage, cost, and an optional
budget cap — see [Token usage (`--semantic`)](#token-usage---semantic) above.

**Coverage tip (non-blocking):** a plain run (no `--semantic`) that finds a clean structural pass
(no field added/removed/retyped) but changed 20+ lines under `--src` since `HEAD` prints a `[TIP]`
suggesting `--semantic`. Deliberately a purely quantitative signal (a `git diff --numstat` line
count), not a fuzzy field-name/type similarity heuristic — a self-invented heuristic there risked
spamming false suggestions or missing real drift, the opposite of what a coverage tip should do. A
structural pass only means field *names and types* didn't change; behavior inside a function body
can drift without touching its signature at all, which `--semantic` exists to catch and a line-count
signal can only hint might be worth checking, not confirm. Never auto-triggers `--semantic` itself.

**Output format:**

```
  Semantic matching (LLM-assisted):
       [WARN] POST /orders: spec='order_id':'string'  vs  code='id':'int'
           → likely_same: order_id and id likely refer to the same order identifier; type widening is a mismatch worth reviewing
       [FAIL] POST /orders: spec='order_total':'float'  vs  code='discount':'Decimal'
           → different: order_total (total price) and discount (reduction amount) are unrelated concepts
```

**Usage:**

```bash
# Web App — structural + semantic pass
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter fastapi --semantic \
    --spec docs/specs/api-contract.md --src src/

# JSON output including semantic_verdicts array
python3 docs/script/validators/verify_spec_code.py \
    --project-type web-app --adapter fastapi --semantic --json \
    --spec docs/specs/api-contract.md --src src/
```

---

## Beyond static comparison: runtime contract testing

The Limitations section above is explicit that `verify_spec_code.py` only compares two things
that already exist as *text* — it never executes anything, so it cannot tell you whether the
running service actually honors its declared contract, only whether the spec document and the
source code use matching field names and types. For teams that want that stronger guarantee —
consumer-driven contract testing, or fuzzing a live endpoint against its schema — that's a
different category of tool, and this framework does not build or ship one:

- **[Pact](https://docs.pact.io/)** — consumer-driven contract testing. A consumer records the
  requests/responses it expects; a "pact broker" verifies the provider's real, running
  implementation actually satisfies every recorded interaction. Fits naturally at the
  `microservices` project type, where `service-contract.md` already documents per-service
  expectations — a Pact contract is a machine-checked, runtime-verified version of that same
  information, not a replacement for the document.
- **[Schemathesis](https://schemathesis.readthedocs.io/)** — property-based fuzzing against a
  running OpenAPI/GraphQL endpoint: generates inputs from the schema itself and checks the live
  server's responses actually conform to it. Fits at `web-app` / `microservices`, complementing
  `api-contract.md` + the `fastapi`/`flask`/`express`/`django`/`gin` spec↔code adapters.

**Bridging the gap: `generate_openapi.py`.** Schemathesis needs a real OpenAPI document, and
`api-contract.md` is narrative markdown, not a machine schema — those are different formats, not
different content. `templates/script/generators/generate_openapi.py` reuses
`WebAPIAdapter.extract_spec()` (the exact same parser `verify_spec_code.py` already uses to
compare the spec against code) and serializes the resulting `NormalizedEndpoint` list into
`openapi.yaml`, in the other direction:

```bash
python3 templates/script/generators/generate_openapi.py \
    --spec docs/specs/api-contract.md --output openapi.yaml --title "My API"
```

`openapi.yaml` is a **generated artifact** — regenerate it after every `api-contract.md` change,
same lifecycle as `.ai/AI_CONTEXT.md`; don't hand-edit it, add it to `.gitignore`. This does not
touch what `api-contract.md` holds that has no schema field to go in — `Design Note`s, the Edge
Cases table, Non-Functional Requirements, the WebSocket/GraphQL/gRPC sections all stay exactly
where they are, because none of that content is part of what `extract_spec()` reads into a
`NormalizedEndpoint` in the first place. Scope limits (status codes inferred from HTTP method,
nested response envelopes like a paginated list can't be expressed in the flat field model) are
documented in the script's own docstring.

**Heading format matters for both this script and `verify_spec_code.py`:** `extract_spec()` only
recognizes `### METHOD /path` (level 3, no backticks) for each endpoint, and `#### Request Body` /
`#### Response Body` (level 4, exact text) for field tables — anything else yields zero parsed
endpoints or fields, silently. The shipped `api-contract.md` template follows this format for
exactly this reason (see the template's own `<!-- -->` comment above its `## Endpoints` section).

**Why this isn't a `verify_*.py` script:** every existing validator in this framework runs against
files on disk — no network calls, no running process, no test environment to stand up. Pact and
Schemathesis fundamentally need a live service to test against, which this repo (a template with
no real project content — see the top of this README) has no way to provide or assume. Wiring
either one in is a per-project decision, not something a template can pre-build:

1. Stand up Pact (`pip install pact-python` for the consumer/provider verification pieces, or a
   Pact Broker) or Schemathesis (`pip install schemathesis`) against your project's actual test
   environment, following their own setup docs linked above.
2. Run it from CI or a dedicated `test_command`-style step (see `.project-starter.yml` →
   `test_command`) — not from `.githooks/pre-commit`, since these need a running service and
   pre-commit hooks should stay fast and offline.
3. Reference the contract test suite from `docs/specs/test-plan.md` (`## Testing Strategy`, the
   `Contract` test level already listed for `microservices`/`data-pipeline`/`ml-pipeline` in
   `verify_acceptance.py`'s `REQUIRED_TEST_LEVELS`) so it shows up in the same traceability chain
   `verify_acceptance.py` already checks (FR-XXX → test-plan scope → test-report ✅ Pass) — this
   framework can validate that a contract-test *level* is declared and reported on, it just can't
   run the tests themselves.

---

## Security Scan (SAST)

`verify_security.py` wraps existing static-analysis security tools — [bandit](https://bandit.readthedocs.io/)
for Python, [eslint-plugin-security](https://github.com/eslint-community/eslint-plugin-security) for
JS/TS, and [Semgrep](https://semgrep.dev/) for Go / Ruby / Java / PHP / Kotlin / Vue — and reports
findings in the same style as the other validators. It is independent of the Spec ↔ Code Validator
above: no spec input, just known-unsafe-pattern detection (`eval`, `shell=True`, unsafe regex,
object injection, hardcoded secrets, etc.) in whatever code sits under `--src`.

Semgrep only scans the languages bandit/eslint don't parse — exactly the language gap the Spec ↔
Code Validator's Limitations section names as having zero automated drift detection (Rails, Spring
Boot, Kotlin/Android, Vue, Go, PHP). It is never run against Python/JS/TS files, so a file is never
scanned by two tools and reported twice under different check IDs.

**Prerequisites (only for the languages actually present in `--src`):**
```bash
pip install bandit                                    # Python
npm install --save-dev eslint eslint-plugin-security   # JS/TS
pip install semgrep                                    # Go / Ruby / Java / PHP / Kotlin / Vue
```

**Usage:**
```bash
python3 docs/script/validators/verify_security.py --src src/ --strict
python3 docs/script/validators/verify_security.py --src src/ --json
python3 docs/script/validators/verify_security.py --src src/ --min-severity high --strict
python3 docs/script/validators/verify_security.py --list-tools
```

`--min-severity` (default `medium`) sets the threshold that counts toward `--strict`; findings
below it are still listed, just not blocking.

**Wiring it into pre-commit:** set `security_scan_src` in `.project-starter.yml` (usually the same
path as `spec_code_src`, if that's already set) — off by default, matching `spec_code_adapter`'s
opt-in pattern. When set, the pre-commit hook runs the scan on any commit touching files under
that path. When unset, the hook prints a non-blocking `[TIP]` if `spec_code_src` is already
configured, since a src path is already known at that point.

**Coverage-gap warning:** if `--src` contains Python or JS/TS files but the matching tool isn't
installed, the report prints an explicit `[WARN]` naming the missing tool instead of silently
reporting a clean scan — the same "don't let an unscanned language look like a pass" concern as
the Spec ↔ Code Validator's zero-coverage warning above.

**Scope:** this catches only what bandit's, eslint-plugin-security's, and Semgrep's `auto` rule
sets catch, in Python, JS/TS/React, Go, Ruby, Java, PHP, Kotlin, and Vue code — not a general
security audit, and not a substitute for a real SAST/DAST pipeline or manual review on anything
security-critical. See Limitations below.

**`--llm-review` (optional, opt-in): Claude Code's `/security-review` Skill, run headless.**
The tools above only catch fixed, known-unsafe patterns. `--llm-review` adds an LLM-driven pass
on top, via `llm_security_review.py`, for the class of issue a pattern-matcher structurally
cannot see — business-logic auth bypass, an unsafe trust boundary, prompt injection in an
LLM-app project. Same relationship as `verify_spec_code.py`'s structural pass vs. its `--semantic`
flag.

```bash
python3 docs/script/validators/verify_security.py --src src/ --llm-review
```

**Coverage tip (non-blocking):** a plain scan (no `--llm-review`) that finds at least one `medium`+
severity finding prints a `[TIP]` suggesting `--llm-review` for a deeper look — reusing severity
this run already computed, not a new heuristic invented to decide when to suggest it. A SAST rule
match only means a known-unsafe *pattern* was found, not that it's actually exploitable in this
specific context; that judgment call is exactly what `--llm-review`'s non-deterministic,
context-aware pass is for. Never auto-triggers `--llm-review` itself — same "suggest, don't run"
rule as everything else opt-in here.

Requires the `claude` CLI installed and authenticated on whatever machine runs this (`claude auth
login`, or `ANTHROPIC_API_KEY` set) — missing or unauthenticated prints a `[WARN]` and skips, the
same graceful-degradation pattern as `--semantic`'s `ANTHROPIC_API_KEY` check. That's a portability
property, not a per-machine dependency: clone this repo anywhere, log into Claude Code once, and
it works there too.

**Never wire `--llm-review` into `workflow-registry.yaml` or the pre-commit hook** — same
constraint as `--semantic`: it shells out to a live Claude Code session and its output is
non-deterministic, so it stays a manual, developer-invoked pass. Its findings are printed but
never affect `--strict`'s exit code. Usage (cost, duration, turn count — whatever the installed
Claude Code version's `--output-format json` reports) is appended to
`logs/telemetry/security-review-usage.json`, mirroring the Spec ↔ Code Validator's
`token-usage.json`, and dual-emitted as an OTel span the same way (see Validation Telemetry below).

---

## Prose Quality (Vale)

`verify_prose.py` wraps [Vale](https://vale.sh) with a small custom style shipped in
`templates/script/validators/_prose_style/` and reports findings in the same style as the other
validators. It is independent of `verify_docs.py` / `verify_content.py` above — those check *fill
quality* (is a section a placeholder, does a table have real rows), not writing quality. A sentence
like "This is obviously very simple to set up" passes every existing structural check exactly as
well as a sentence that actually explains something; a bare `TBD` or `coming soon` written as
prose (not `[TBD]` or `<!-- TODO -->`) passes `_verify_common.py`'s placeholder regex entirely.
This is the layer above that.

**Custom rules shipped** (`_prose_style/styles/Custom/*.yml` — extend this, don't hand-edit
generated output):
- `WeaselWords` — vague qualifiers (`very`, `obviously`, `simply`, `just`, `basically`, ...)
- `NaturalLanguagePlaceholders` — `TODO` / `FIXME` / `TBD` / `coming soon` / `to be determined`
  written as plain prose

No `vale sync` and no external style package (Google/Microsoft/write-good) — self-contained on
purpose, consistent with this framework's offline-friendly design elsewhere.

**Prerequisites:** install Vale — see [vale.sh/docs/install](https://vale.sh/docs/install)
(Homebrew / Scoop / a prebuilt binary from GitHub releases; not a pip/npm package).

**Usage:**
```bash
python3 docs/script/validators/verify_prose.py --docs docs/ --strict
python3 docs/script/validators/verify_prose.py --docs docs/ --json
python3 docs/script/validators/verify_prose.py --docs docs/ --min-severity high --strict
python3 docs/script/validators/verify_prose.py --list-tools
```

**Wiring it into pre-commit:** set `prose_scan_enabled: true` in `.project-starter.yml` — off by
default, matching `spec_code_adapter`'s and `security_scan_src`'s opt-in pattern. No separate path
setting needed (it scans `docs_path`, which is always set). When set, the pre-commit hook runs on
any commit touching a `.md` file under `docs_path`. When unset, the hook prints a non-blocking
`[TIP]` the first time a `.md` file under `docs_path` is staged.

Also wired into the `sprint-end` sequence in `workflow-registry.yaml` (not every task type — this
is a prose-quality convergence check, not a per-commit gate the way pre-commit's own `.md`-staged
trigger is).

**Scope:** three narrow custom rules, not a general writing-quality grader — no grammar checking,
no style-guide enforcement (no Chicago/AP/house-style rules), no glossary-driven terminology
consistency (a natural extension — generating a Vale rule from `docs/glossary.md`'s defined terms
— was considered but not built; would need per-project generation, not a static shipped rule).

---

## Limitations

This is a documentation-completeness and drift-detection framework, not a spec-compiler. Read
this before assuming "spec-driven" means the spec enforces the code, or that a passing pre-commit
means the code is correct.

**Editing the spec never changes the code, and editing the code never changes the spec.**
`verify_spec_code.py` only compares two things that already exist — it has no code-generation or
spec-generation step. Whoever changes one side (developer or AI agent) is still responsible for
manually updating the other; the validator's only job is to catch it if they forget. If you're
picturing an OpenAPI-codegen-style pipeline where the spec is the source of truth the code is
generated from, that is not what this does.

**The drift gate is opt-in and invisible until you turn it on.** `spec_code_adapter` is unset by
default — with it unset, a project has **zero** spec↔code protection, silently, forever, and
(until recently) nothing told you that. The pre-commit hook now prints a non-blocking `[TIP]`
listing available adapters whenever a spec contract file is committed without this configured
(see [Wiring it into pre-commit](#wiring-it-into-pre-commit)), but it's still up to you to act on
the tip — the gate does not turn itself on. `detect_type.py` also now suggests the three values
directly when it recognizes a framework signal (see Wiring it into pre-commit), which lowers the
effort to act on the tip but still stops short of turning the gate on for you — a fresh
`--apply` writes the suggestion, but you still have to run it and confirm the guess. `--strict`
is also required for the check to actually fail a commit; without it, output is informational only.

**Coverage is limited to the frameworks/languages with a detector.** ~29 framework/language
detectors exist across 8 capabilities today (see the Adapters table above). Any other language
or framework — Rails, Spring Boot, native Android/Kotlin, Vue, Go, PHP, and everything else not
listed — has **no automated drift detection at all**. This applies separately to the `logging`
capability too: only Python and JS/TS/React have a detector. This gap is no longer silent —
running against a language with no detector prints an explicit `[WARN] 0 code items extracted
from --src, but real file(s) exist there` and fails `--strict`, rather than the empty-vs-empty
comparison quietly reporting `[OK] No mismatches`. But the underlying gap is unchanged: nothing
is actually compared for that language until a detector is built (see Learning Checkpoint C's
escalation step in `guidance/learning-checkpoints/common.md` for the "build one on the spot"
procedure). Spec and code can diverge indefinitely for these; manual code review is the only
safety net until then. Running a capability adapter without a `--framework` hint unions *all* of its
detectors, and two frameworks sharing a similar idiom (e.g. Click's and Typer's `.command()`
decorator) can both match the same code and produce overlapping or duplicate results — pass
`--framework`, or use the standalone `--adapter <framework>` alias, to avoid this.

**What it checks is narrow: shape, not meaning or quality.** The comparison is field/flag/prop
names, types, HTTP method+path, and resource attribute keys — never business logic correctness,
security, performance, or whether the implementation actually does what the spec describes.
Those are separate, largely manual concerns (`code-quality-check.md` for retrofits,
`verify_acceptance.py` for FR-XXX traceability, `verify_tests.py` for test-report fill quality —
none of them execute your code or your tests). A field-level quirk worth knowing: for
`NormalizedEndpoint` and `NormalizedStageContract`, request/input fields and response/output
fields are merged into one namespace before comparison (`_item_fields()` in
`verify_spec_code.py`) — a field the spec declares only on the response side can be silently
satisfied by a same-named field that exists only on the code's request side, and vice versa.

**Document validators check fill quality, not truth.** `verify_docs.py` and `verify_content.py`
confirm a document isn't a placeholder and has the sections/rows the schema expects — they cannot
confirm the content is factually accurate. A confidently wrong, fully-filled-in spec passes every
check exactly as well as a correct one.

**Multi-contract projects: use `spec_code_bindings`.** `.project-starter.yml` supports a list of
`{adapter, spec, src}` mappings (`spec_code_bindings`), not just the single legacy trio — a project
with a REST API and a background pipeline gets both wired into `.githooks/pre-commit` and
`orchestrator.py`'s generated workflow automatically, one `verify_spec_code.py` invocation per
binding. See [Wiring it into pre-commit](#wiring-it-into-pre-commit) below. One real limitation
remains: the *coverage tip* (the non-blocking `[TIP]` suggesting `security_scan_src`) only reads
the legacy trio's `src`, not the bindings list — cosmetic, not a gate, see that section for why.

**The security scan is opt-in too, and its coverage is narrow.** `security_scan_src` is unset by
default — same invisible-until-you-turn-it-on shape as `spec_code_adapter`, mitigated the same
way (a non-blocking `[TIP]` once `spec_code_src` is already configured). What it checks is limited
to bandit's, eslint-plugin-security's, and Semgrep's own rule sets — known-unsafe *patterns*, not
business logic, auth flows, or anything requiring cross-file reasoning. Language coverage is wider
than the `logging` capability's Python/JS-TS-React (Semgrep adds Go, Ruby, Java, PHP, Kotlin, Vue),
but still not universal — Rust, C/C++, Elixir, and anything else outside that list has no SAST
coverage here either. It is a useful first pass, not a replacement for a real SAST/DAST pipeline or
manual security review.

**The prose scan checks three narrow rules, nothing close to real writing quality.** `WeaselWords`
and `NaturalLanguagePlaceholders` catch specific word/phrase patterns — they cannot tell a
genuinely clear explanation from a confusing one that happens to avoid "obviously" and "TBD".
There is no grammar checking, no glossary-driven terminology consistency (glossary.md is not read
by this validator today — see Prose Quality (Vale) above), and no house-style enforcement. Also
opt-in and unset by default, same shape as the other two gates above.

---

## Self-improving loop

When a spec has fill-quality issues, `diagnose_spec.py` classifies whether the gap is project-level (fill it in) or framework-level (the template itself is missing guidance), and can open a PR on this repo for the latter. Moved to [`docs/self-improving-loop.md`](docs/self-improving-loop.md) — architecture, iteration limit, usage, and the auto-generated PR format.

---

## PDF generation

Setting up PlantUML (diagram rendering) and generating the merged spec PDF from `docs/`. Moved to [`docs/pdf-generation.md`](docs/pdf-generation.md).

---

## Key design decisions

- **Templates vs. docs**: `templates/` is always blank scaffolding. Real content only ever lives
  in a project's `docs/` folder, never in this repo.
- **Architecture-agnostic templates**: `backend.md`, `module-data-flow.md`, and `logging-spec.md`
  do not assume any specific layering pattern or language. Use your actual layer names and
  logger API — the templates provide structure, not prescription.
- **Module inventory before documentation**: the retrofit flow requires running `scan_codebase.py`
  (with `--project-type` for correct vocabulary) and getting user confirmation before any
  documentation is written — so undocumented modules are caught at the start, not discovered at the end.
- **Four flow-file formats**: Feature (request-driven), Background Job (event/schedule-driven),
  Pipeline Stage (data-contract-driven, used in Data Pipeline / ML Pipeline), and Shared Utility
  (no entry point). These are the formats defined in `module-data-flow.md`. Command (CLI Tool),
  Namespace (Library / SDK), and Service (Microservices) are scan classification labels used by
  `scan_codebase.py --project-type` — they select vocabulary, not separate flow formats.
- **Six-chapter PDF structure**: the generated PDF is organized into Introduction / Plan /
  Design / Build / Test / Deployment — matching standard system analysis document conventions.
  The chapter each file belongs to is configured in `pdf_allowlist.py`.
- **Single PDF allowlist**: `pdf_allowlist.py` is the only file to edit when adding documents
  to the PDF. `build_pdf.py` imports from it.
- **Task granularity**: each task should be roughly half a day to one day of work, and
  independently completable as a single Current Task — planning rules are defined directly in `AGENTS.md`.
- **Package First**: prefer an existing package, then an existing utility, then framework
  convention, and only write custom code for business logic, domain rules, data mapping, or
  system integration.
- **Incremental updates only**: `codebase-map.md` and `modules/module-data-flow.md` are updated one task
  at a time — the agent never re-scans the whole repository to regenerate them.

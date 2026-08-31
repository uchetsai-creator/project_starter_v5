# Changelog — project_starter_v5

This is the framework's own release history — not to be confused with `templates/changelog.md`,
which ships into projects built *with* the framework to track *their* changes.

All notable changes to this framework are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/).

> **Note on history before this file existed:** entries prior to `0.2.0` were not
> reconstructed retroactively from git log — `git log --oneline` is the authoritative
> record for that period. Starting from `0.2.0`, this file is the canonical summary.

---

## [Unreleased]

### Added
- Framework-update check: `.project-starter.yml` gained two new optional fields,
  `framework_commit` (the project_starter_v5 SHA a project was scaffolded/last synced
  from — set automatically by `init.py`) and `framework_repo_url` (override for a fork or
  internal mirror). New `adapters/claude/check_framework_update.py`, wired into
  `adapters/claude/session-start-hook.sh`, compares `framework_commit` against upstream's
  current HEAD via `git ls-remote` once per Claude Code session and nudges the user (via
  AskUserQuestion) to review the update when they differ — opt-in (blank `framework_commit`
  skips the check entirely, matching every other optional gate in this framework) and
  always silent on failure (missing git, no network, timeout), same non-blocking-nudge
  contract as every other check in that hook. `retrofit-existing-project` (Skill and its
  canonical source `templates/init/retrofit.md`) gained a new "Update recheck" section for
  what to do when the nudge fires on a project that's already been retrofitted: diff
  `document-registry.yaml` and the validator/pre-commit gates against the freshly pulled
  framework instead of redoing the full retrofit, then update `framework_commit` to silence
  the nudge. Covered by `tests/unit/test_check_framework_update.py` (a local git repo
  stands in for the real GitHub upstream — `git ls-remote` works identically against a
  local path, no network needed) plus new cases in `test_session_start_hook.py` and
  `test_init_py.py`.

### Fixed
- 17 test files across `tests/unit/` and `tests/contract/` each
  `sys.path.insert(0, .../_spec_code_adapters)` to import a same-named detector module
  (`click.py`, `django.py`, `express.py`, ...) ahead of any real PyPI package sharing that
  name, but never removed it — a process-global leak that persisted for the rest of the
  pytest session once any one of them was collected. Harmless until this rewrite made
  `templates/script/framework/agent_pipeline.py` depend on `claude-agent-sdk`, which does
  its own internal `import click`: with `_spec_code_adapters` still on `sys.path` from an
  earlier-collected file, that import silently resolved to this framework's own `click.py`
  adapter instead of the real package, crashing `test_agent_pipeline.py`'s collection with
  `AttributeError: module 'click' has no attribute 'command'`. Confirmed pre-existing, not
  introduced by the SDK rewrite: `pytest tests/unit/test_agent_pipeline.py` alone passed
  before this fix (no earlier file to leak the pollution), and `pytest tests/unit/` alone
  also passed too.
  - 15 files fixed directly (`test_ansible_detector.py`, `test_express_detector.py`,
    `test_django_detector.py`, `test_javascript_logging_detector.py`,
    `test_langchain_detector.py`, `test_luigi_detector.py`,
    `test_output_field_resolution.py`, `test_react_native_detector.py`,
    `test_python_logging_detector.py`, `test_terraform_detector.py`,
    `test_swiftui_detector.py`, `test_typescript_detector.py`, `test_typer_detector.py`,
    `test_gin_detector.py`, `test_adapter_contracts.py`) — each now removes
    `_ADAPTERS_DIR` from `sys.path` immediately after its own import of the target module
    completes, instead of leaving it for the rest of the session. `test_new_detector.py`
    (also matched a `_spec_code_adapters` grep) needed no change — it runs
    `new_detector.py` as a subprocess against an isolated `tmp_path` copy and never
    touches this process's `sys.path`.
  - **This alone did not fix the crash** — the actual leak reaching `test_agent_pipeline.py`
    turned out to come from two *production* scripts, not a test file: `generate_openapi.py`
    and `verify_spec_code.py` each do the same `sys.path.insert(0, .../_spec_code_adapters)`
    at module level, correctly, for their own standalone runtime (`FrameworkAdapter`'s lazy
    `importlib.import_module()` dispatch — see `_base.py` — needs that path for the whole
    process lifetime, not just at the top-level import, so neither script can safely remove
    it itself). Loading either script inside the shared pytest process — `test_generate_openapi.py`
    via `importlib.util.spec_from_file_location(...).exec_module(...)`, and
    `test_detect_type_adapter_sync.py` via a plain `import verify_spec_code` — leaks that
    same mutation into every later-collected test module, same failure mode as the 15
    test files above. `test_adapter_contracts.py` was first suspected (it's the only
    match for a literal `_spec_code_adapters` string search in `tests/contract/`, and it
    collects before `tests/unit/`) but was already cleaning up correctly — confirmed via a
    debug `sys.path` print at the crash site and a process-of-elimination bisection across
    `tests/contract/`'s files, not assumed from the string search alone. Fix: both call
    sites (`test_generate_openapi.py`, after its `from _base import ...`;
    `test_detect_type_adapter_sync.py`, after its `import verify_spec_code as vsc`) now
    remove the path via the loaded module's own `_ADAPTER_DIR` attribute
    (`go._ADAPTER_DIR`, `vsc._ADAPTER_DIR`) once they're done needing it — both only use
    functions/dicts that don't need the path at call time (`extract_spec()` parses spec
    markdown only, no framework-specific dispatch; `ADAPTER_REGISTRY` is a plain dict),
    confirmed by running each file's own test suite after the change, not assumed.

### Changed
- `templates/script/framework/agent_pipeline.py`'s `_default_caller()` rewired off a
  hand-rolled `subprocess.run(['claude', '-p', '--output-format', 'json'])` call with
  manual JSON-envelope parsing onto the official `claude-agent-sdk` package
  (`claude_agent_sdk.query()` + `ClaudeAgentOptions`) — the library Claude Code itself
  ships for headless/programmatic invocation, rather than reimplementing that transport by
  hand. Reason: an audit found this module had zero callers anywhere in the shipped
  framework (not `workflow-registry.yaml`, not any `SKILL.md`, not README/ROADMAP) and no
  documented rationale for the original subprocess approach — see ROADMAP.md for the
  still-open integration point. Behavior of `call_agent()`/`run_pipeline()` (retry-on-
  format-noncompliance only, usage accumulation, OTel emission, dependency ordering) is
  unchanged; only `_default_caller`'s transport changed. Requires
  `pip install claude-agent-sdk` — see README → Running the test suite for the same
  optional-dependency treatment as bandit/semgrep/eslint/Vale/opentelemetry-\*.
  `tests/unit/test_agent_pipeline.py`'s `test_default_caller_*` tests updated to
  monkeypatch `agent_pipeline.query` (the SDK's intended test seam is mocking `query()`
  itself, not its internal `Transport` class — that class's own docstring marks it an
  unstable low-level API subject to change) instead of `subprocess.run`, using
  `claude_agent_sdk.ResultMessage`'s real `dataclasses.fields()` (checked against the
  installed package) rather than a guessed shape. Unlike the module this replaced, this
  rewrite has NOT been verified against a live, unmocked `query()` call — see the module
  docstring.
- `init.py` (and `setup.sh --init`, which delegates to it) now copies `adapters/claude/skills/`
  into the new project's `.claude/skills/` automatically, instead of leaving it as a separate,
  easy-to-miss manual step (README → Agent Adapters → Claude Code, step 4). Confirmed by
  actually bootstrapping a fresh project: previously `.claude/skills/` did not exist at all
  after `--init`, meaning Learning Checkpoint and the other four procedural Skills only
  triggered if the agent happened to read AGENTS.md's text reference — no mechanical trigger,
  unlike the PreToolUse scope guard. `add-framework-adapter` (framework-repo-only) is
  deliberately excluded, same as before. `tests/unit/test_init_py.py` and
  `tests/unit/test_setup_sh_init.py` updated to assert the copy happens as part of `--init`
  rather than simulating it as a separate manual step.

### Added
- New `task-closeout` Claude Skill (`adapters/claude/skills/task-closeout/SKILL.md`,
  canonical source `templates/task-completion.md`) — the sixth procedural doc packaged as
  a Skill, closing a real gap rather than a hypothetical one: `module-completion-check`'s
  own `SKILL.md` description already said "see task-closeout instead" for ordinary
  per-task closeout, but no `task-closeout` Skill existed anywhere — not in
  `.claude/skills/`, not in `tests/contract/test_skill_contracts.py`'s canonical source
  list. `templates/task-completion.md` matches the exact "Load X only if you need the full
  detail" trigger pattern every other Skill-converted doc uses (both references in
  `AGENTS.md` phrase it that way), so this brings it in line with its siblings instead of
  being the one on-demand procedural doc left as plain-text-only. `test_skill_contracts.py`,
  `test_init_py.py`, and `test_setup_sh_init.py` all updated; confirmed by actually running
  `init.py` into a fresh directory and checking `.claude/skills/task-closeout/` exists
  after, not just by reading the copy logic.
- ruff + mypy wired into CI (`.github/workflows/ci.yml`) and `requirements-dev.txt`, with
  config in `pyproject.toml`. `select = ["E4","E7","E9","F","I"]` (ruff's own recommended
  default plus import sorting); `E402` ignored repo-wide since this codebase is flat scripts,
  not an installed package, and `sys.path.insert(0, ...)` immediately before a local import
  is the correct pattern here, not a style slip. mypy runs with `ignore_missing_imports` and
  the stdlib default of not checking untyped function bodies — gradual typing, not `--strict`,
  since most of the ~150 files had no prior type-hint coverage.
  Bringing the codebase to a clean baseline surfaced real, previously-undetected bugs, not
  just style noise:
  - `detect_type.py`: six rule-list constants (`_FILE_EXISTS_RULES`, `_DIR_EXISTS_RULES`,
    `_PYTHON_DEP_RULES`, `_NODE_DEP_RULES`, `_GLOB_RULES`, `_KEYWORD_RULES`) were annotated
    `list[tuple[str, int]]` but every entry is actually a 3-tuple
    `(pattern, project_type, weight)` — the annotation just never matched the data. Fixed to
    `list[tuple[str, str, int]]`.
  - `_spec_code_adapters/semantic.py`: the file's own `if __name__ == '__main__':` self-test
    called `adapter.semantic_compare(report, [], [])`, but the real method only takes
    `structural_report` — running `python3 semantic.py` directly crashed with `TypeError`
    before reaching the assertion it was meant to check. Confirmed fixed by actually running
    the self-test, not just satisfying mypy.
  - `_spec_code_adapters/flask.py`: `methods=[...]` parsing in a `@app.route(...)` decorator
    called `.upper()` on every AST constant in the list without checking it was a string
    first — a route decorator with a non-string literal in `methods=` (e.g. a stray number)
    would crash the scanner instead of skipping it gracefully. Added an `isinstance(..., str)`
    guard.
  - `_spec_code_adapters/luigi.py`: a `with open(...) as f:` file handle and an unrelated
    walrus-assigned loop variable both named `f` in the same function reused the name across
    two different types — harmless at runtime (the scopes never actually overlapped in
    practice) but a real footgun for the next edit. Renamed the loop variable to `field`.
  - `_verify_common.py`'s `_section_body()` deliberately returns `str` or `list[str]`
    depending on whether it's given `str` or `list[str]` input; every caller previously
    saw the full `str | list[str] | None` union regardless of which type it actually passed
    in, so callers that always pass `str` had to satisfy a `list[str]` branch that could
    never happen for them. Added `@overload` signatures so each call site gets the precise
    return type back.
- `learning-log.md`: personal, append-only root file for Learning Checkpoint C.4 (teach-back).
  Previously, teach-back gaps ("couldn't explain it, or explained it wrong" — the framework's
  own stated signal for what needs deeper study) lived only in that session's conversation and
  were never written down anywhere, so nothing accumulated across tasks and there was no review
  cadence. Copied by `init.py` / `setup.sh --init` like `debug-instrumentation-rules.md` and
  `code-quality-check.md`; not part of `document-registry.yaml` or any type's document matrix
  — never Required/Optional, never PDF-exported, never checked by a validator. Also tracks a
  personal design-pattern roster (every pattern named or considered-and-rejected at Checkpoint
  A/B/C) and prompts a re-check of an older entry every 3rd entry, mirroring the count-based
  trigger `sprint-change-log.md` already uses for Sprint Documentation Sync. Added to
  `pretooluse_scope_guard.py`'s `NON_SOURCE_NAMES` and `.githooks/pre-commit`'s
  `NON_SOURCE_REGEX` so appending an entry doesn't require a scoped `Current Task`, same as the
  other two root guidance files. `guidance/learning-checkpoints/common.md` (and its
  contract-synced `adapters/claude/skills/learning-checkpoint/SKILL.md`) also gained: a wider
  Checkpoint 0 trigger ("when unsure, run it anyway"), a default-on note for Checkpoint C.1's
  comment-out-and-test escalation while still building confidence in a codebase, and a
  simpler-analogy retry loop (max 2 retries) for Checkpoint C.4 teach-back before recording the
  gap as unresolved.
- `verify_security.py`: SAST wrapper running bandit (Python) and eslint-plugin-security (JS/TS)
  against `--src`, reported in the same style as the other validators. Independent of
  `verify_spec_code.py` — no spec input, just known-unsafe-pattern detection. Opt-in via
  `security_scan_src` in `.project-starter.yml`, wired into `.githooks/pre-commit` and the
  `feature` / `pipeline-stage` / `bug-fix` / `eval-run` / `iac-change` sequences in
  `workflow-registry.yaml`, following the same opt-in pattern as `spec_code_adapter` — including
  the same non-blocking `[TIP]` mitigation (shown once `spec_code_src` is already configured, since
  a src path is already known at that point). A language with no matching tool installed is
  reported as an explicit `[WARN]`, not a silent clean pass — same philosophy as
  `verify_spec_code.py`'s zero-coverage warning. See README.md → Security Scan (SAST).
- `docs/current-state.md` → Current Task now has a `Clarifying Questions Asked` field (`Y` /
  `N/A`). Previously, whether the agent actually asked scope/edge-case/acceptance-criteria
  questions before implementing a new requirement (AGENTS.md → New requirement from the user /
  Learning Checkpoint B) was conversation-only — no file recorded whether it happened, so a
  compliant and a non-compliant session produced identical `current-state.md` output. Pre-commit
  now blocks a commit that sets a real (non-placeholder) `Task` while leaving this field unfilled.
- `PROJECT_STARTER_SKIP_VERIFY` now appends a row (`ts`, `staged_files`) to
  `logs/telemetry/skip-verify.json` every time it's used, in addition to the existing loud
  `[SKIP]` terminal line. Doesn't make the escape hatch any harder to use — it's still a full
  bypass of every pre-commit gate, including the new Clarifying Questions Asked guard above —
  but how often a project reaches for it is now auditable after the fact instead of only visible
  in the terminal at the moment it happened.
- AGENTS.md → Constitution gained an eighth item, "Unscoped New Requirement" — a compressed
  pointer to the existing "New requirement from the user" rule (ask scope/edge-cases/acceptance-
  criteria before implementing). The full rule already existed further down the file; this only
  changes its priority framing, promoting it to the same "stop and ask instead of bending it"
  tier as the other seven Constitution items, since a rule's position in AGENTS.md affects how
  reliably an agent actually applies it. Not a technical gate — AGENTS.md compliance is always
  prompt-driven, never enforced — see the Clarifying Questions Asked pre-commit guard above for
  the mechanical backstop. AGENTS.md is now 190/200 lines.
- `verify_security.py` gained a third tool, [Semgrep](https://semgrep.dev/), scoped to exactly
  the languages bandit/eslint-plugin-security don't parse (Go, Ruby, Java, PHP, Kotlin, Vue) — the
  same language gap `verify_spec_code.py`'s Limitations section names as having zero drift
  detector coverage. Semgrep is never run against Python/JS/TS files, so no file is scanned twice
  and double-reported under two different check-ID vocabularies. Requires `pip install semgrep`;
  same graceful [WARN]-not-silent-pass treatment as the other two tools when missing.
- New `gin` spec↔code adapter (`_spec_code_adapters/gin.py`) for Go / Gin, registered in
  `verify_spec_code.py`'s `ADAPTER_REGISTRY` and `_capability_web_api.py`. Unlike every other
  detector in this directory (all regex-based, see `express.py`), this one uses
  [tree-sitter](https://tree-sitter.github.io/) + `tree-sitter-go` — justified specifically by Go
  struct field declarations with `json:"..."` tags, which are multi-line and awkward for regex to
  parse reliably; route registration (`r.GET("/path", handler)`) alone would not have justified a
  new dependency. Requires `pip install tree-sitter tree-sitter-go`; extracts request/response
  fields from `c.ShouldBindJSON(&x)` / `c.JSON(status, x)` handler bodies. Known scope limits are
  documented in the module docstring (no cross-function value tracing, `json:"-"` fields excluded,
  untagged fields fall back to the Go field name).
- New Claude Code `SessionStart` hook (`adapters/claude/session-start-hook.sh`, wired in
  `.claude/settings.json`) — the mechanical follow-through on the Constitution's "Unscoped New
  Requirement" item: re-checks `docs/current-state.md`'s scoping state fresh at the start of every
  session and injects a reminder via `hookSpecificOutput.additionalContext` if the Current Task is
  still a placeholder, or is real but `Clarifying Questions Asked` is unfilled. Addresses a gap
  observed directly in this session: `CLAUDE.md`'s `@AGENTS.md` auto-load did not visibly fire the
  same way in every directory tested, so a rule buried in AGENTS.md text isn't guaranteed to be in
  context every session regardless of its position in the file. Non-blocking — always exits 0; the
  actual gate remains the Clarifying Questions Asked pre-commit check above.
- `verify_prose.py`: new prose-quality wrapper around [Vale](https://vale.sh), using a small
  self-contained custom style (`_prose_style/` — no `vale sync`, no external style package)
  shipping two rules: `WeaselWords` (vague qualifiers) and `NaturalLanguagePlaceholders` (`TBD` /
  `coming soon` / `TODO` written as prose, not the bracket/comment forms
  `_verify_common.py`'s placeholder regex already catches). Independent of `verify_docs.py` /
  `verify_content.py` — those check fill quality, this checks writing quality on top of that.
  Opt-in via `prose_scan_enabled: true` in `.project-starter.yml` (no separate path needed, reuses
  `docs_path`); wired into `.githooks/pre-commit` and the `sprint-end` sequence in
  `workflow-registry.yaml`. Same opt-in/`[TIP]`/graceful-missing-tool pattern as the other two SAST
  gates above.
- New `.pre-commit-config.yaml` — optional alternative to `cp .githooks/pre-commit
  .git/hooks/pre-commit` for teams already using the [pre-commit](https://pre-commit.com)
  framework. Wraps `.githooks/pre-commit` as a single `repo: local` hook rather than
  reimplementing its checks in YAML — that script reads `project_type` / `docs_path` /
  `spec_code_*` / `security_scan_src` / `prose_scan_enabled` dynamically from
  `.project-starter.yml` at runtime, and duplicating that logic as static pre-commit-framework
  entries would mean maintaining two copies that could drift apart. Also includes a few generic
  hooks from `pre-commit/pre-commit-hooks` (trailing-whitespace, end-of-file-fixer, check-yaml,
  check-merge-conflict) as a starting point for the wider ecosystem this unlocks. Verified against
  the real `pre-commit` CLI, both a passing run and a run correctly blocked by an existing
  `.githooks/pre-commit` check (placeholder `project_type`).
- `verify_acceptance.py` gained Edge Case traceability (`check_edge_case_traceability()`) for
  Web App / Microservices — reuses the existing FR-XXX cross-reference shape for
  `api-contract.md`'s `## Edge Cases` table. Added an ID column to the `api-contract.md`
  template, shipped bracket-wrapped (`[EC-001]`) so it's opt-in: a project that never adopts
  real ids gets zero issues. Caught and fixed a real false-positive during development — the
  template's own instructional `<!-- -->` comment used unbracketed example ids in prose
  (e.g. "EC-002"), which the extraction regex initially picked up as real declared ids;
  fixed by restricting extraction to table rows only, with a regression test locking it in.
- New `templates/script/generators/generate_openapi.py` — generates `openapi.yaml` from
  `api-contract.md` by reusing `WebAPIAdapter.extract_spec()` (the exact same parser
  `verify_spec_code.py` already uses), instead of replacing the narrative markdown spec with a
  machine schema. `api-contract.md` stays the authored source of truth; `openapi.yaml` is a
  regenerated derived artifact, feeding tooling like oasdiff / Schemathesis (see "Beyond static
  comparison" below) without api-contract.md's Design Notes, Edge Cases, NFRs, or
  WebSocket/GraphQL/gRPC sections ever needing schema fields that don't exist for them.
- **Bug fix, found and fixed while building the above:** the shipped `api-contract.md` template
  used a heading format (`## \`METHOD /path\``, level 2 + backticks) that
  `WebAPIAdapter.extract_spec()` cannot parse at all — it requires `### METHOD /path` (level 3, no
  backticks), confirmed against `examples/microservices-web-app/docs/specs/api-contract.md`, which
  already used the working format. This meant `verify_spec_code.py`'s own field-level drift
  detection for `fastapi`/`flask`/`express`/`django`/`gin` has been silently returning zero parsed
  spec endpoints for any project that filled in the template's per-endpoint headings as shipped,
  since before this template existed in its current form — not a regression introduced this
  release, a latent bug this generator's own testing surfaced. A second, related issue: `**Validation
  Rules:**` / `**Errors:**` used bold text instead of `#### ` headings, so `_parse_field_table()`'s
  "read until next `#### ` heading" boundary had nothing to stop at and pulled those tables' rows in
  as if they were request/response fields. Both fixed in the template, with regression tests in
  `tests/unit/test_generate_openapi.py` asserting the shipped template now parses to exactly 5
  endpoints with clean (non-bled) field sets.
- New `templates/script/validators/_otel.py` — optional OpenTelemetry dual-emission for all
  telemetry write points (`_verify_common._append_telemetry`, `orchestrator.py`'s run counter,
  `.githooks/pre-commit`'s skip-verify record). Dual-write, not a migration: local JSON telemetry
  is written exactly as before, unconditionally — `orchestrator.py` reads its own
  `.orchestrator_runs.json` back synchronously right after writing it, which an external OTel
  backend cannot serve to a local process the same way. No-ops unless both
  `opentelemetry-api`/`-sdk`/`-exporter-otlp-proto-http` are installed AND
  `OTEL_EXPORTER_OTLP_ENDPOINT` is set. Verified against a real (unreachable) collector: the
  underlying OTel SDK logs a multi-frame traceback per failed export by default — confirmed this
  is unacceptable noise for an optional, off-by-default feature, so `_otel.py` explicitly
  suppresses the `opentelemetry` logger; re-verified silent afterward with a regression test.
- `.github/workflows/ci.yml` now installs every optional tool `verify_security.py` /
  `verify_prose.py` / `_otel.py` wrap (bandit, semgrep, tree-sitter/tree-sitter-go, eslint +
  eslint-plugin-security via `actions/setup-node`, Vale via direct GitHub-release download —
  OS-specific steps for Linux/Windows, exact asset filenames confirmed against the release API
  rather than guessed — and the opentelemetry packages). Previously these were absent from CI
  entirely, so every test exercising a real tool (as opposed to the mocked JSON-parsing unit
  tests) silently skipped there, forever — CI provided a materially weaker guarantee than what
  had actually been verified manually during development.
- **Two more real bugs found while making the above actually true, not just configured:**
  neither bandit nor eslint had ever been run for real end-to-end before this fix (only semgrep,
  tree-sitter, Vale, and OTel had). Installing and actually running them surfaced:
  1. `subprocess.run(['eslint', ...])` (bare command name, no `shell=True`) fails on Windows
     with `FileNotFoundError` — npm installs eslint as `.cmd`/`.ps1` shims, not a native `.exe`,
     and Windows `CreateProcess` cannot resolve those without going through a shell. Fixed by
     passing the fully-resolved path from `_which()` instead of a hardcoded bare name — applied
     to `_run_bandit()` and `_run_semgrep()` too for consistency, even though their pip-packaged
     `.exe` files happened not to need it.
  2. The original eslint integration generated a legacy `.eslintrc.json`-style config
     (`--no-eslintrc -c <path>`) — ESLint 9+ (what a fresh `npm install eslint` gets today)
     removed that entire system in favor of flat config (`eslint.config.cjs`), so every real
     eslint invocation failed with `Invalid option '--eslintrc'`. Rewritten to generate a flat
     config using `eslint-plugin-security`'s own `configs.recommended` export. This surfaced a
     third, related detail: the generated config must be written inside the project directory
     tree (this framework already assumes cwd == project root everywhere else), not an OS temp
     directory — Node's `require('eslint-plugin-security')` resolution walks up from the config
     file's own location looking for `node_modules/`, so a config file living outside the
     project's directory tree can never find the plugin no matter how it was installed.
  New real-tool regression tests in `tests/unit/test_verify_security_e2e.py` lock in all three
  fixes (skipped, not failed, when bandit/eslint aren't installed locally).
- All 9 `templates/init/<type>.md` walkthroughs now mention `security_scan_src` and
  `prose_scan_enabled` in their `.project-starter.yml` snippet, matching the exact comment
  pattern already used there for `spec_code_adapter` — previously only that one opt-in gate was
  surfaced during initial setup; the two newer ones were only documented in the full README, so
  someone following an init file step-by-step would never learn they exist. `web-app.md` and
  `microservices.md` also gained a pointer to `generate_openapi.py`.
- `.gitignore` gained three entries generated during this work: `node_modules/` (from
  `npm install --no-save eslint eslint-plugin-security`, no `package.json` is committed so this
  is always throwaway), `.eslint-security-*.config.cjs` (verify_security.py's throwaway eslint
  config — a safety net for the rare case a run is killed before its own cleanup runs), and a
  commented-out `# openapi.yaml` suggestion (not enabled by default — some projects deliberately
  commit their generated OpenAPI file for client codegen or doc hosting).

### Documented (no new script)
- README.md → new "Beyond static comparison: runtime contract testing" section pointing at
  [Pact](https://docs.pact.io/) and [Schemathesis](https://schemathesis.readthedocs.io/) for
  consumer-driven contract testing / live-endpoint fuzzing. Deliberately not a `verify_*.py`
  script: every existing validator runs against files on disk with no network calls and no
  running process, and this repo — a template with no real project content — has no live service
  to point either tool at. Documents where each fits (`microservices` / `web-app`), prerequisites,
  and how to reference the resulting contract-test suite from `test-plan.md`'s `Contract` test
  level so it stays inside `verify_acceptance.py`'s existing traceability chain even though this
  framework can't run the tests itself.

### Fixed
- `subprocess.run(..., text=True)` without an explicit `encoding=` decodes a child process's
  stdout/stderr using the platform's preferred locale — `cp950` on Traditional Chinese Windows,
  for example. Any non-ASCII byte in that output (a box-drawing character, an arrow, a CJK
  character) then crashes a reader thread with `UnicodeDecodeError`, surfaced to the user as a
  raw traceback even though the underlying command usually still completed. `verify_prose.py`
  and `verify_security.py` already guarded against this with `encoding='utf-8',
  errors='replace'`; this applies the same fix to the six remaining call sites that never got
  it: `orchestrator.py` (`_invoke_build_context`), `build_pdf.py` (PlantUML invocation),
  `diagnose_spec.py` (calling `propose_framework_fix.py`), `propose_framework_fix.py`'s own
  `run()` helper, `verify_content.py`, and `verify_module_docs.py`. CI never caught this because
  `.github/workflows/ci.yml` sets `PYTHONUTF8: "1"` at the job level — that masks the gap at
  every call site instead of fixing any of them, so a real user running these scripts outside
  CI on a non-UTF-8-locale machine hits the crash CI never sees. Confirmed by reproducing the
  crash on a `cp950` locale before the fix and confirming a clean run after.

### Added
- New Claude Code `SessionStart` hook (`adapters/claude/learning_log_nudge.py`, wired in
  `.claude/settings.json` alongside `session-start-hook.sh`): reminds when the last committed
  `docs/task-log.md` entry (a task closeout) is newer than the last commit touching
  `learning-log.md`, by comparing `git log -1 --format=%ct` timestamps for both files.
  Addresses the one Learning Checkpoint step with no mechanical backstop at all — Checkpoint
  C.4's teach-back gap previously relied entirely on the agent remembering, unprompted, to
  append an entry. Deliberately stops at timestamps and never reads entry content: unlike the
  `Clarifying Questions Asked` field the `PreToolUse` scope guard checks, `learning-log.md`'s
  own header states it is "never checked by any validator" by design — grading a personal
  teach-back log would incentivize writing something just to pass rather than an honest gap
  report, which defeats the point of the file. Non-blocking, fails silent on any git error or
  missing file. `tests/unit/test_learning_log_nudge.py` covers all four decide() branches
  (no learning-log.md, no committed task-log.md yet, task-log.md newer, learning-log.md newer)
  plus the not-a-git-repo case.

### Fixed
- `init.py --init` now writes (or, if one already exists, appends to) a `.gitignore`
  covering `.ai/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, and `logs/`. Previously
  `--init` never touched `.gitignore` at all — confirmed by actually running `--init` into
  a fresh git repo and checking `git status`: `.ai/AI_CONTEXT.md`, `__pycache__/`, and
  `logs/verify-*.json` all showed as untracked-and-stageable, despite README already
  documenting all three as "generated, not committed." An existing `.gitignore` is never
  overwritten — appended to once, guarded by a marker comment so re-running `--init` on
  the same project doesn't duplicate the block. `tests/unit/test_init_py.py` gained three
  tests for this (fresh write, append-without-clobbering, no duplicate on second run).
- `templates/current-state.md` → Closeout and `templates/task-completion.md` → step 1c now
  warn explicitly: promoting Next Task → Current Task in the same commit as the finished
  task's source files trips `.githooks/pre-commit`'s Unscoped source-change guard, because
  that guard reads `current-state.md`'s Current Task against whatever is staged at commit
  time — once Current Task is the unscoped placeholder, staged source files (even ones that
  belonged to a properly-scoped task) get blocked. Discovered by actually running a task's
  full closeout end-to-end through real `git commit`, not just reading the instructions.
  Fix documented: commit source + docs first (Current Task still showing the just-finished
  task, `Status: Complete — Pending Sprint Doc Sync`), then promote in a second, docs-only
  commit. A docs-only task can still do the whole closeout, including the promotion, in one
  commit — the gap only bites when source files outside `docs/` are staged alongside it.

### Added
- `_otel.py`'s optional OpenTelemetry dual-emission now correlates spans into real traces
  instead of emitting unrelated single spans per event. While `docs/current-state.md` has a
  scoped Current Task, every span shares that task's `trace_id` as a direct child of one
  synthetic `task: <name>` root span, created on the task's first emission and persisted to
  `logs/telemetry/.otel_trace_context.json` (gitignored) so later emissions — each its own
  OS process (a `verify_*.py` run, an `orchestrator.py` run) — can reconstruct it as a
  parent context by hand; OTel's normal in-process parent/child tracking has no way to see
  across separate processes on its own. A task change starts a fresh trace automatically.
  Confirmed with `InMemorySpanExporter` (real span objects, no live collector needed), not
  just asserted to work: spans for the same task share one `trace_id` and have the root as
  their parent; a second, independently-loaded module instance (simulating a second process)
  reuses the same root via the persisted state file instead of creating a second one;
  different tasks get different `trace_id`s; no scoped task still emits an uncorrelated span
  exactly as before this change (backward compatible — `emit()`'s new `cwd` parameter
  defaults to `.`, so every existing call site needed zero changes). Known accepted gap: two
  processes for the same task starting near-simultaneously could each observe "no root yet"
  and create one, splitting that task into two traces — same race class
  `.orchestrator_runs.json` already has, not newly introduced, just exercised more now; not
  worth a file lock for how rarely it would actually fire. See README.md → Validation
  Telemetry → OTel dual-emission for the local-Jaeger walkthrough to see the resulting
  waterfall.
- `templates/script/framework/mcp_tools.py`: a prototype tool-schema layer for a future
  MCP server — deliberately not a running server (no `mcp` package dependency, no
  transport, no client wiring, per an explicit decision to spike the low-risk part first).
  Wraps `verify_docs.run_audit()` and `verify_content.audit()` as `dict`-in/`dict`-out
  handlers behind JSON-Schema tool definitions (`TOOLS`, `dispatch()`) — both underlying
  functions already returned plain, JSON-serializable data with no CLI/printing entangled,
  which was confirmed by reading them, not assumed. Applies to all 9 project types (and
  hybrids), same as the functions it wraps — nothing web-app-specific. Tested against
  `examples/web-app/docs` (a real, filled fixture, not an empty directory): schema shape,
  successful dispatch for both tools, and every documented failure mode (unknown tool,
  missing/invalid `project_type`, missing docs dir).

### Fixed
- `init.py --init` copied `templates/script/framework/` into every new project's
  `docs/script/framework/`, contradicting README's own claim that this directory is
  "framework-internal only, NOT copied to user projects" — `shutil.copytree()` had no
  `ignore=` pattern excluding it. Confirmed broken by actually running `--init` into a
  fresh directory and finding `docs/script/framework/verify_framework.py` there before
  this fix (discovered while placing `mcp_tools.py` in that same directory and checking
  whether the exclusion README already documented was real). Now passes
  `ignore=shutil.ignore_patterns("framework")`; sibling `validators/` / `generators/` /
  `scanners/` still copy normally, confirmed by the same test. README's manual-alternative
  copy instructions gained the same exclusion note.

### Added
- `doc_profile: lite | full` in `.project-starter.yml` (default `full`, so nothing changes
  for existing projects). `lite` downgrades a fixed set of documents — `permissions.md`,
  the three `business/*.md` files, `backend.md`/`database.md`/`deployment.md`, `research.md`,
  `test-plan.md`/`test-report.md` — from Required to Optional, for a solo/small project
  without real stakeholders, roles, or a deploy target yet. Deliberately *not* a separate
  document set: `document-registry.yaml` gained a `lite_downgrade` field on those 10 entries
  only; `lite` and `full` read the exact same registry, so switching back to `full`
  re-requires exactly what `lite` deferred — no migration, no second template tree. Core
  contracts (`project-requirements.md`, `quickstart.md`, `data-model.md`, `api-contract.md`,
  `architecture.md`, `logging-spec.md`) stay Required in both profiles; these are the
  documents the spec↔code drift gate and context builder actually depend on.
  - `_registry.py`: `build_matrix()`, `build_type_docs()`, and `get_universal_docs()` all
    gained a `lite: bool = False` parameter implementing the downgrade rule.
  - `verify_docs.py` / `verify_content.py`: both auto-detect `doc_profile` from
    `.project-starter.yml` with zero flag needed — confirmed this means
    `.githooks/pre-commit`'s existing (unmodified) invocations of both scripts already
    respect it correctly, no pre-commit change required. `--lite` / `--full` CLI flags
    override the config file explicitly (e.g. to preview a switch without editing the yml);
    passing both is a `sys.exit(2)` error. JSON output on both scripts now includes a
    `doc_profile` field.
  - `read_doc_profile()` lives in `_verify_common.py`, shared between the two scripts
    rather than duplicated per-script (unlike `pretooluse_scope_guard.py` and `_otel.py`'s
    independent tiny YAML-scalar readers, which stayed separate — different situation:
    those two aren't siblings in the same directory already importing a common module).
  - `mcp_tools.py`'s prototype tools gained the same `doc_profile` input (explicit argument
    wins; otherwise auto-detects the same way the CLI does).
  - New `guidance/doc-profile.md`: what `lite` actually changes, why it's a starting point
    and not a permanent fork, and a concrete "when to switch to full" checklist (second
    contributor joins, a real permission model appears, a real approval/audit requirement
    appears, about to deploy somewhere reachable by more than localhost, need to explain a
    tech decision to someone else) — replacing what would otherwise be a vague "switch when
    it feels right." `AGENTS.md` gained a two-line pointer to it (195/200 lines — the
    existing token budget check left exactly enough room without needing to cut anything
    else).
  - Golden/snapshot fixtures for `verify_docs.py --json` regenerated (`--snapshot-update`)
    to include the new field; diff confirmed to be exactly one added line per fixture,
    nothing else changed.
  - Tests: `tests/unit/test_registry.py` (new — `_registry.py`'s lite-mode functions
    against a small synthetic registry), `tests/unit/test_doc_profile_cli.py` (new — both
    scripts' real CLI behavior: config-file auto-detection, flag overrides, `--strict`
    actually not blocking on downgraded docs in `lite` while still blocking on the same
    missing docs in `full`, using the same fixture for both to prove the `lite` pass wasn't
    just a bug that stopped blocking on everything), `tests/unit/test_mcp_tools.py` gained
    explicit `doc_profile` coverage.

---

## [0.2.0] — 2026-08-09

### Added
- Claude Skills (`SKILL.md`) for five procedural workflows previously only reachable by
  manually following AGENTS.md's file-load instructions: `retrofit-existing-project`,
  `code-quality-check`, `module-completion-check`, `sprint-doc-sync`, `learning-checkpoint`
  (shipped under `adapters/claude/skills/`, optional copy into a project's `.claude/skills/`).
  Plus a framework-repo-only skill, `add-framework-adapter`, for contributors extending
  `verify_spec_code.py` itself (lives in this repo's own `.claude/skills/`, never shipped).
  Each Skill body is guarded against drifting from its canonical source doc by
  `tests/contract/test_skill_contracts.py`.
- `detect_type.py` now suggests `spec_code_adapter` / `spec_code_spec` / `spec_code_src`
  when it recognizes a known framework signal (e.g. `fastapi` in `requirements.txt`, or a
  `main.tf` file), lowering the effort to turn on spec↔code drift detection — previously
  opt-in with no guidance on what values to set. `--apply` on a fresh project pre-fills all
  three, clearly marked as an unverified guess; an existing `.project-starter.yml` is never
  overwritten by this. See README → Spec ↔ Code Validator → Wiring it into pre-commit.
- CI (`.github/workflows/ci.yml`): runs the full test suite and
  `verify_framework.py --strict` on every push/PR, on both `ubuntu-latest` and
  `windows-latest` — previously enforced only by the local pre-commit hook, which
  `--no-verify` bypasses.
- `tests/contract/test_detect_type_adapter_sync.py`: guards `detect_type.py`'s
  `_ADAPTER_SIGNALS` against referencing an adapter alias, project type, or signal kind that
  doesn't actually exist in `verify_spec_code.py`'s `ADAPTER_REGISTRY` / `detect_type.py`'s own
  `VALID_TYPES` — the same drift risk category as the `verify_framework.py` bug fixed below,
  caught before it could happen instead of after.
- `tests/unit/test_setup_sh_init.py`: `setup.sh --init` had zero automated coverage before this
  (only ever verified by hand) despite being the first command in the README Quick Start. Covers
  the required-file copy list, `.project-starter.yml` generation, rejecting an unknown project
  type, and — combined with the Skills feature above — that copying `adapters/claude/skills/`
  into a freshly-initialized project produces a valid `.claude/skills/` layout.
- This file.
- `LICENSE` (MIT) — the repo had no license file, leaving reuse terms undefined for a project
  meant to be cloned/adopted as a starter template.
- `requirements.txt` / `requirements-dev.txt` as the single source of truth for install
  instructions, replacing three independently-hardcoded `pip install ...` lines
  (`.github/workflows/ci.yml`, `README.md`, `setup.sh`) and `pyproject.toml`'s non-functional
  `[project.optional-dependencies] dev` extra (`pip install .[dev]` never worked — see Fixed
  below for why). `pyproject.toml`'s `[project]` table now says explicitly that it exists for
  dependency-metadata tooling only, not for `pip install .`.
- `tests/unit/test_adapter_drift_detection.py`: golden spec+code fixtures (clean pair + one
  known-planted drift each) for the fastapi, click, and langchain adapters, run end-to-end
  through `verify_spec_code.py`. Closes a real coverage gap —
  `tests/contract/test_adapter_contracts.py` only checked that each adapter's
  `extract_spec()`/`extract_code()` never raises and returns the right `NormalizedForm`
  subclass, never that a real, known drift is actually reported. A parsing bug in any of the
  ~29 framework detectors could have silently stopped catching drift with nothing in the
  suite noticing.
- `init.py` — `setup.sh --init`'s copy-and-scaffold logic reimplemented in pure Python.
  `setup.sh` is bash-only, so `--init` (the first command in the README Quick Start) could
  not run on native Windows without Git Bash/WSL; CI's `windows-latest` job never caught this
  because GitHub's runner ships Git Bash on PATH. `setup.sh --init` now delegates to
  `init.py` (single source of truth, not a parallel reimplementation); `python3 init.py <type>
  <dest>` also works standalone with zero bash involved. Covered by
  `tests/unit/test_init_py.py`, which invokes it directly via `subprocess` with no bash in
  the call chain.
- `PROJECT_STARTER_SKIP_VERIFY` env var — an officially-documented escape hatch for
  `.githooks/pre-commit` (`PROJECT_STARTER_SKIP_VERIFY=1 git commit -m "wip"`). Previously
  the only way to bypass a blocking check during a prototype/spike was `git commit
  --no-verify`, which skips the hook silently with no trace in the commit. The env var always
  prints a loud `[SKIP]` line instead, so a skipped commit is never mistaken for a verified
  one. Covered by `tests/unit/test_pre_commit_skip_verify.py`.
- Restored the Codex agent adapter (`adapters/codex/`, `orchestrator.py --adapter codex`,
  `.codex/setup.md` + `.codex/task-instructions.md` output) — removed in commit `4745c10`
  ("real usage has been Claude Code only") on the assumption that nobody else needed it; that
  assumption no longer holds. Cursor stays removed — no current need for it. Restored
  `document-purposes/common.md` entries and `test_agent_adapter_templates.py` coverage for the
  two Codex template files; `AGENTS.md`, README's Agent Adapters section, and the framework
  repo file-tree diagram updated to reflect two shipped adapters instead of one.
- Golden clean+drift fixture coverage (same pattern as the fastapi/click/langchain tests
  above) for the remaining 18 `verify_spec_code.py` framework detectors, closing out the gap
  across every registered adapter, not just three: `flask`/`django`/`express` (web-api),
  `typer` (cli), `airflow`/`dagster`/`prefect`/`luigi` (data-pipeline), `python_library`/
  `tool_schema` (library/llm-app), `terraform`/`pulumi`/`ansible` (iac), `react_native`/
  `flutter`/`swiftui` (mobile), `python_logging`/`javascript_logging` (logging). 59 new tests
  across 7 files (`tests/unit/test_adapter_drift_detection_{web_api,cli,pipeline,library_llm,
  iac,mobile,logging}.py`). Along the way, confirmed and documented several by-design detector
  limitations that are easy to mistake for bugs: `ExpressDetector`/`ReactNativeDetector` never
  resolve field/prop *types* (endpoint/prop presence only); `LuigiDetector` never resolves
  `output_fields` (a Luigi stage's Output Contract always reports missing); `NormalizedResource`
  (IaC) compares by name only, never by type, and its config-key fields always carry type=''
  so type-level drift can never fire for terraform/pulumi/ansible.

### Removed
- Codex and Cursor agent adapters (`adapters/codex/`, `adapters/cursor/`, the corresponding
  `orchestrator.py --adapter` choices and `_ADAPTER_TEMPLATES` entries, and all references in
  README.md / AGENTS.md / `guidance/document-purposes/common.md`). Real usage of this
  framework has been Claude Code only — `AGENTS.md` and `.ai/WORKFLOW.md` stay plain Markdown,
  so any other tool can still be pointed at them manually; only the dedicated tool-native
  adapter output is gone. Re-adding a tool later just means a new `adapters/<tool>/` directory
  following `adapters/claude/`'s shape — nothing else in the framework assumed Codex/Cursor
  existed.

### Fixed
- `verify_framework.py`'s matrix↔template consistency check used a hardcoded `/` path
  separator, producing false-positive `[WARN]`s for `spec-review.md`/`spec-challenge.md` on
  Windows (backslash paths never matched the forward-slash exempt set).
- `templates/sprint-sync.md`'s Document Update Checklist was missing a real trigger item for
  `project-requirements.md`, and incorrectly missing an exemption for `glossary.md` /
  `dependencies.md` (on-demand utility docs, same rationale as their existing
  `TEMPLATE_MATRIX_EXEMPT` entry) — both caused permanent `[WARN]`s in
  `verify_framework.py --strict`.
- `tests/unit/test_detect_type.py` read generated `.project-starter.yml` files without
  `encoding="utf-8"`, crashing on non-UTF-8-locale systems (e.g. Windows with a Traditional
  Chinese system codepage) when the generated file contained a non-ASCII character.
- `setup.sh --init` (and the README's manual-copy instructions) did not copy
  `code-quality-check.md` or `debug-instrumentation-rules.md` into new projects, despite the
  README's own documented `new_project/` file tree listing both as root files.
- 9 test files spawned a Python child process (`verify_docs.py`, `orchestrator.py`,
  `build-context.py`, `build_pdf.py`, `detect_type.py`) via `subprocess.run(text=True, ...)`
  with no `encoding` — on a non-UTF-8-locale system, the child's own stdout silently encodes
  using the OS codepage (confirmed: an em dash in `verify_docs.py`'s own output became invalid
  UTF-8 bytes under Windows cp950). Fixed by pairing `encoding="utf-8"` on the parent's decode
  side with `PYTHONUTF8=1` in the child's environment on every affected call, so both sides
  agree on UTF-8 regardless of host locale — decoding as UTF-8 without also forcing the child's
  encoding is not sufficient and reintroduces the same crash in the other direction (verified
  by hitting it while writing this fix).
- Three places (`.github/workflows/ci.yml`, `README.md`, `setup.sh`) each hardcoded a bare
  `pip install pytest` with no version floor, while `pyproject.toml`'s `dev` extra separately
  declared `pytest` with no constraint either — no actual drift risk today, but also no
  single source of truth. Pinned `pytest>=7` in all four places; `pyproject.toml` now also
  documents why `pip install .[dev]` doesn't work for this repo (confirmed by testing it —
  setuptools refuses to auto-discover packages in a template repo's loose top-level layout).

### Verified (no change needed)
- The self-improving loop (`diagnose_spec.py` → `propose_framework_fix.py`) only ever calls
  `gh pr create`, never `gh pr merge` or any auto-merge flag — confirmed safe as designed.

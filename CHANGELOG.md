# Changelog — project_starter_v5

This is the framework's own release history — not to be confused with `templates/changelog.md`,
which ships into projects built *with* the framework to track *their* changes.

All notable changes to this framework are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/).

> **Note on history before this file existed:** entries prior to `0.2.0` were not
> reconstructed retroactively from git log — `git log --oneline` is the authoritative
> record for that period. Starting from `0.2.0`, this file is the canonical summary.

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

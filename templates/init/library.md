# Project Initialization — Library / SDK

1. Create `.project-starter.yml` at the project root (used by the hook and all verify scripts):
    ```yaml
    project_type: library
    docs_path: docs/
    # Optional: spec_code_adapter / spec_code_spec / spec_code_src — enables the spec↔code
    # drift gate in pre-commit + orchestrator. See README.md → Spec ↔ Code Validator →
    # Wiring it into pre-commit.
    # Optional: security_scan_src — enables the SAST gate (bandit / eslint-plugin-security /
    # semgrep). See README.md → Security Scan (SAST).
    # Optional: prose_scan_enabled — enables the Vale prose-quality gate. See README.md →
    # Prose Quality (Vale).
    ```
2. Copy `document-registry.yaml` from the framework root to your project root:
    ```bash
    cp /path/to/project_starter_v5/document-registry.yaml .
    ```
    This file is required by all verify scripts and `build_pdf.py`. Without it, scripts will fail with "document-registry.yaml not found".
3. Install the verification hook (see `README.md → Verification` for details):
    ```bash
    cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
    ```

4. Create docs/project-requirements.md from templates/project-requirements.md.
5. Create docs/specs/research.md from templates/specs/research.md.
6. Create docs/specs/quickstart.md from templates/specs/quickstart.md (covers local dev setup and running tests).
7. Create docs/architecture/architecture.md from templates/architecture/architecture.md.
8. Create docs/architecture/distribution.md from templates/architecture/distribution.md.
9. Create docs/specs/public-api.md from templates/specs/public-api.md.
10. Create docs/specs/release-guide.md from templates/specs/release-guide.md.
11. Create docs/specs/compatibility-matrix.md from templates/specs/compatibility-matrix.md.
12. Create docs/modules/module-data-flow.md from templates/flows/module-data-flow-v2.md.
13. Create docs/modules/module-flow.md from templates/flows/module-flow-v2.md.
14. Create docs/codebase-map.md from templates/codebase-map.md.
15. Create docs/specs/test-plan.md from templates/specs/test-plan.md.
16. Create docs/specs/test-report.md from templates/specs/test-report.md.
17. Create docs/project-plan.md from templates/project-plan.md.
18. Create docs/task-log.md from templates/task-log.md.
19. Create docs/sprint-change-log.md from templates/sprint-change-log.md.
20. Create docs/current-state.md from templates/current-state.md. Run `python3 build-context.py`
    now (steps 1-2 already put `.project-starter.yml` + `document-registry.yaml` in place) to
    fill in its Doc Checklist section.

**Optional utility documents (create on demand, any time):**
- `docs/specs/glossary.md` — if the library introduces domain-specific types, concepts, or acronyms that callers need to understand. Create from `templates/specs/glossary.md`.
- `docs/specs/dependencies.md` — to track peer dependency versions, tested compatibility ranges, and known incompatibilities. Create from `templates/specs/dependencies.md`.

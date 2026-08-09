# Project Initialization — Data Pipeline

1. Create `.project-starter.yml` at the project root (used by the hook and all verify scripts):
    ```yaml
    project_type: data-pipeline
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
6. Create docs/specs/quickstart.md from templates/specs/quickstart.md.
7. Create docs/architecture/architecture.md from templates/architecture/architecture.md.
8. Create docs/architecture/backend.md from templates/architecture/backend.md (pipeline stack and layering).
9. Create docs/architecture/database.md from templates/architecture/database.md.
10. Create docs/architecture/deployment.md from templates/architecture/deployment.md.
11. Create docs/specs/data-model.md from templates/specs/data-model.md.
12. Create docs/specs/pipeline-contract.md from templates/specs/pipeline-contract.md.
13. Create docs/specs/pipeline-debug.md from templates/specs/pipeline-debug.md.
14. Create docs/specs/logging-spec.md from templates/specs/logging-spec.md.
15. Create docs/business/business-rules.md from templates/business/business-rules.md (data quality rules, validation constraints).
16. If business workflows need to be documented (e.g. approval flows, SLA processes): Create docs/business/business-process.md from templates/business/business-process.md.
17. Create docs/modules/module-data-flow.md from templates/flows/module-data-flow.md.
18. Create docs/modules/module-flow.md from templates/flows/module-flow.md.
19. Create docs/codebase-map.md from templates/codebase-map.md.
20. Create docs/specs/test-plan.md from templates/specs/test-plan.md (use Contract/Integration/E2E/Fault Injection levels).
21. Create docs/specs/test-report.md from templates/specs/test-report.md (fill in after first test run).
22. Create docs/project-plan.md from templates/project-plan.md.
23. Create docs/task-log.md from templates/task-log.md.
24. Create docs/sprint-change-log.md from templates/sprint-change-log.md.
25. Create docs/current-state.md from templates/current-state.md. Run `python3 build-context.py`
    now (steps 1-2 already put `.project-starter.yml` + `document-registry.yaml` in place) to
    fill in its Doc Checklist section.

**Optional utility documents (create on demand, any time):**
- `docs/specs/glossary.md` — if the pipeline uses domain-specific field names, business terms, or data quality terminology that analysts and engineers need to agree on. Create from `templates/specs/glossary.md`.
- `docs/specs/dependencies.md` — to track external tool versions (Airflow, dbt, Great Expectations, etc.), upgrade policy, and known compatibility constraints. Create from `templates/specs/dependencies.md`.

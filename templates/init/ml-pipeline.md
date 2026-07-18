# Project Initialization — ML Pipeline

1. Create docs/project-requirements.md from templates/project-requirements.md.
2. Create docs/specs/research.md from templates/specs/research.md.
3. Create docs/specs/quickstart.md from templates/specs/quickstart.md.
4. Create docs/architecture/architecture.md from templates/architecture/architecture.md.
5. Create docs/architecture/backend.md from templates/architecture/backend.md.
6. Create docs/architecture/database.md from templates/architecture/database.md.
7. Create docs/architecture/deployment.md from templates/architecture/deployment.md.
8. Create docs/specs/data-model.md from templates/specs/data-model.md.
9. Create docs/specs/pipeline-contract.md from templates/specs/pipeline-contract.md.
10. Create docs/specs/pipeline-debug.md from templates/specs/pipeline-debug.md.
11. Create docs/specs/model-contract.md from templates/specs/model-contract.md.
12. Create docs/specs/experiment-log.md from templates/specs/experiment-log.md.
13. Create docs/specs/logging-spec.md from templates/specs/logging-spec.md.
14. Create docs/business/business-rules.md from templates/business/business-rules.md.
15. Create docs/modules/module-data-flow.md from templates/flows/module-data-flow-v2.md.
16. Create docs/modules/module-flow.md from templates/flows/module-flow-v2.md.
17. Create docs/codebase-map.md from templates/codebase-map.md.
18. Create docs/specs/test-plan.md from templates/specs/test-plan.md (use Contract/Integration/E2E/Fault Injection levels).
19. Create docs/specs/test-report.md from templates/specs/test-report.md (fill in after first test run).
20. Create docs/project-plan.md from templates/project-plan.md.
21. Create docs/task-log.md from templates/task-log.md.
22. Create docs/sprint-change-log.md from templates/sprint-change-log.md.
23. Create docs/current-state.md from templates/current-state.md.

24. Install the verification hook (see `README.md → Verification` for details):
    ```bash
    cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
    ```
25. Create `.project-starter.yml` at the project root (used by the hook and all verify scripts):
    ```yaml
    project_type: ml-pipeline
    docs_path: docs/
    ```

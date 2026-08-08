# Project Initialization — IaC / DevOps

## What applies to IaC / DevOps projects

IaC / DevOps projects have almost no overlap with the standard document set.
The following documents from other project types are **N/A** — do not create them:

- architecture.md, backend.md, frontend.md, database.md, deployment.md, distribution.md
- api-contract.md, cli-contract.md, public-api.md, pipeline-contract.md, pipeline-debug.md
- llm-contract.md, prompt-library.md, eval-spec.md, llm-debug.md, rag-contract.md, mcp-contract.md
- service-catalog.md, service-contract.md, event-catalog.md
- model-contract.md, experiment-log.md, release-guide.md, compatibility-matrix.md
- permissions.md, data-model.md, logging-spec.md
- business-process.md, business-objects.md, business-rules.md

**Documents that still apply:** `research.md`, `quickstart.md`, `test-plan.md`, `test-report.md`

## Initialization Steps

1. Declare project type at the top of AGENTS.md:
   ```
   Project Type: IaC / DevOps
   ```

2. Create `.project-starter.yml` at the project root (used by the hook and all verify scripts):
    ```yaml
    project_type: iac
    docs_path: docs/
    # Optional: spec_code_adapter / spec_code_spec / spec_code_src — enables the spec↔code
    # drift gate in pre-commit + orchestrator. See README.md → Spec ↔ Code Validator →
    # Wiring it into pre-commit.
    # Optional: security_scan_src — enables the SAST gate (bandit / eslint-plugin-security /
    # semgrep). See README.md → Security Scan (SAST).
    # Optional: prose_scan_enabled — enables the Vale prose-quality gate. See README.md →
    # Prose Quality (Vale).
    ```
3. Copy `document-registry.yaml` from the framework root to your project root:
    ```bash
    cp /path/to/project_starter_v5/document-registry.yaml .
    ```
    This file is required by all verify scripts and `build_pdf.py`. Without it, scripts will fail with "document-registry.yaml not found".
4. Install the verification hook (see `README.md → Verification` for details):
    ```bash
    cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
    ```

5. Create `docs/specs/research.md` from `templates/specs/research.md`.
   Record tooling decisions (Terraform vs Pulumi vs Ansible, cloud provider, state backend, secrets manager).

6. Create `docs/specs/quickstart.md` from `templates/specs/quickstart.md`.
   Cover: prerequisites (CLI tools, cloud credentials), how to run `terraform init / plan / apply`, how to verify a successful apply.

7. Create `docs/architecture/topology.md` from `templates/architecture/topology.md`.
   Fill in: resource inventory table, environment promotion path (dev → staging → prod), infrastructure diagram.

8. Create `docs/specs/runbook.md` from `templates/specs/runbook.md`.
   Fill in: on-call escalation, health check commands, incident response steps per resource type, rollback procedures.

9. Create `docs/specs/drift-policy.md` from `templates/specs/drift-policy.md`.
   Fill in: allowed drift sources, exempt resources, detection cadence per environment, remediation SLA, approval gate for manual changes.

10. Create `docs/specs/test-plan.md` from `templates/specs/test-plan.md`.
    For IaC: document policy unit tests (tflint, tfsec, OPA), `terraform plan` integration gate, and full apply-verify-destroy E2E cycle on sandbox.

11. Create `docs/specs/test-report.md` from `templates/specs/test-report.md` (fill in after first test run).

12. Set up `docs/current-state.md` using the template. Run `python3 build-context.py` now
    (steps 2-3 already put `.project-starter.yml` + `document-registry.yaml` in place) to fill
    in its Doc Checklist section. The first Current Task is typically "Document existing
    infrastructure" or the first infrastructure module being built.

13. (Optional) Set up `docs/codebase-map.md` using the template.
    Run `scan_codebase.py <src_dir> --project-type iac` to classify Terraform modules / resource groups.
    The conventional Terraform layout nests each resource group one level under a container
    folder (e.g. `modules/storage/`, `modules/network/`) — scan with `--depth 2` in that case,
    or the top-level `modules/` folder is classified as Shared / Infrastructure and its actual
    contents are never scanned. The tool warns when it detects this (`[WARN] Not fully scanned`).

**Optional utility documents (create on demand, any time):**
- `docs/specs/glossary.md` — if the project uses infrastructure-specific terms, resource naming conventions, or tagging taxonomy that the team needs to agree on. Create from `templates/specs/glossary.md`.
- `docs/specs/dependencies.md` — to track tool versions (Terraform, Pulumi, Ansible, Helm, provider plugins), required CLI versions, and upgrade policy. Create from `templates/specs/dependencies.md`.

**Optional — sprint workflow documents:**
IaC projects do not require sprint planning documents, but if your team uses sprint-based workflow,
create these from the standard templates: `project-plan.md`, `task-log.md`, `sprint-change-log.md`, `changelog.md`.
These are not enforced by `verify_docs.py` for IaC projects and can be omitted if your team uses
a different work-tracking system (Jira, Linear, GitHub Issues, etc.).

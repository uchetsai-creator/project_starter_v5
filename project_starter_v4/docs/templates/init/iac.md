# Project Initialization — IaC / DevOps

<!--
  Read this file ONCE when starting a new IaC / DevOps project.
  After initialization is complete, this file is no longer needed for day-to-day tasks.
  Workflow rules, task completion, and sprint sync live in AGENTS.md.
-->

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

2. Create `docs/specs/research.md` from `templates/specs/research.md`.
   Record tooling decisions (Terraform vs Pulumi vs Ansible, cloud provider, state backend, secrets manager).

3. Create `docs/specs/quickstart.md` from `templates/specs/quickstart.md`.
   Cover: prerequisites (CLI tools, cloud credentials), how to run `terraform init / plan / apply`, how to verify a successful apply.

4. Create `docs/architecture/topology.md` from `templates/architecture/topology.md`.
   Fill in: resource inventory table, environment promotion path (dev → staging → prod), infrastructure diagram.

5. Create `docs/specs/runbook.md` from `templates/specs/runbook.md`.
   Fill in: on-call escalation, health check commands, incident response steps per resource type, rollback procedures.

6. Create `docs/specs/drift-policy.md` from `templates/specs/drift-policy.md`.
   Fill in: allowed drift sources, exempt resources, detection cadence per environment, remediation SLA, approval gate for manual changes.

7. Create `docs/specs/test-plan.md` from `templates/specs/test-plan.md`.
   For IaC: document policy unit tests (tflint, tfsec, OPA), `terraform plan` integration gate, and full apply-verify-destroy E2E cycle on sandbox.

8. Create `docs/specs/test-report.md` from `templates/specs/test-report.md` (fill in after first test run).

9. Set up `docs/current-state.md` using the template.
   The first Current Task is typically "Document existing infrastructure" or the first infrastructure module being built.

10. (Optional) Set up `docs/codebase-map.md` using the template.
    Run `scan_codebase.py <src_dir> --project-type iac` to classify Terraform modules / resource groups.

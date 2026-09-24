# AI Context — data-pipeline / pipeline-stage
Generated: {{TIMESTAMP}}

## Read (Required)
- docs/current-state.md   # Active task: goal, steps, and required context
- docs/project-requirements.md   # Functional requirements (FR-XXX), acceptance criteria (AC-XXX), scope, roles, and non-functional requirements
    update when: feature added, removed, or acceptance criteria changed; scope, roles, non-functional requirements, edge cases, or assumptions changed
- docs/specs/pipeline-contract.md   # Inter-stage input/output formats, paths, naming rules, and error handling
    update when: stage input/output format or naming rule changed; file paths or error-handling policy changed
- docs/specs/data-model.md   # Schema, entities, relationships, indexes, and state machine
    update when: entity, relationship, index, or state machine changed; migration plan or main query patterns changed
- docs/architecture/architecture.md   # Current system components and data-flow diagram
    update when: system components or data-flow changes
- docs/architecture/backend.md   # Backend stack, layering, and module organisation
    update when: stack or module structure changes
- docs/architecture/database.md   # Database engine, main entities, and relationships
    update when: schema or entity changes; database engine, key relationships, or constraints changed
- docs/architecture/deployment.md   # Services, environment variables, and build/deploy flow
    update when: service, environment variable, or deploy-flow changes
- docs/specs/pipeline-debug.md   # Stage failure diagnosis guide: wrong row count, data quality, root cause
    update when: new failure mode discovered or root cause procedure updated
- docs/specs/logging-spec.md   # Log format, required log points, trace_id propagation, and module naming
    update when: log format, required log points, or trace propagation changed; a new module that needs its own module name or log file
- docs/business/business-rules.md   # Business constraints and policies that code must enforce
    update when: business constraint or policy changed
- docs/specs/research.md   # Technology decisions and resolved NEEDS CLARIFICATION items
    update when: technology decision made or clarification resolved
- docs/specs/quickstart.md   # Prerequisites, environment setup, startup commands, and verification steps
    update when: prerequisites, setup steps, or verification steps changed
- docs/specs/test-plan.md   # Testing strategy, tool choices, test levels, CI gate, and test environment
    update when: testing strategy, tool, or CI gate changed; test scope (tests added for a new FR/AC), test environment, or test data strategy changed
- docs/specs/test-report.md   # Actual test results, coverage, bugs found, and known gaps
    update when: test run completed or coverage baseline changed

## Read (If Present)
- docs/specs/glossary.md   # Domain terms and abbreviations used across documents
    update when: domain term added or definition updated
- docs/specs/dependencies.md   # Third-party libraries, versions, licences, and update policy
    update when: third-party library, external service, or infrastructure component added, removed, or version changed; external-service fallback behaviour changed
- docs/business/business-process.md   # Business workflow, decision points, responsible roles, and exceptions
    update when: workflow step or decision point changed; responsible role, exception, or pain point changed

## Skip
- docs/architecture/frontend.md
- docs/architecture/distribution.md
- docs/architecture/topology.md
- docs/specs/api-contract.md
- docs/specs/cli-contract.md
- docs/specs/public-api.md
- docs/specs/llm-contract.md
- docs/specs/prompt-library.md
- docs/specs/eval-spec.md
- docs/specs/eval-log.md
- docs/specs/llm-debug.md
- docs/specs/rag-contract.md
- docs/specs/mcp-contract.md
- docs/specs/service-catalog.md
- docs/specs/service-contract.md
- docs/specs/event-catalog.md
- docs/specs/model-contract.md
- docs/specs/experiment-log.md
- docs/specs/release-guide.md
- docs/specs/compatibility-matrix.md
- docs/specs/permissions.md
- docs/specs/runbook.md
- docs/specs/drift-policy.md
- docs/specs/mobile-contract.md
- docs/business/business-objects.md


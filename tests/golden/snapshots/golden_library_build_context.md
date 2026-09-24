# AI Context — library / feature
Generated: {{TIMESTAMP}}

## Read (Required)
- docs/current-state.md   # Active task: goal, steps, and required context
- docs/project-requirements.md   # Functional requirements (FR-XXX), acceptance criteria (AC-XXX), scope, roles, and non-functional requirements
    update when: feature added, removed, or acceptance criteria changed; scope, roles, non-functional requirements, edge cases, or assumptions changed
- docs/specs/public-api.md   # Public functions, classes, types, and constants exposed to callers
    update when: public function, class, or type changed; public constant added or removed, or a symbol deprecated or removed
- docs/architecture/distribution.md   # Package build, registry publish, and installation instructions
    update when: package name, registry, or publish process changes
- docs/specs/release-guide.md   # Versioning policy, release checklist, publish process, and deprecation policy
    update when: versioning policy or publish process changed; changelog format or deprecation policy changed
- docs/specs/compatibility-matrix.md   # Supported runtime versions and known incompatibilities
    update when: new runtime version tested or support status changed; peer dependency ranges or platform/OS support changed
- docs/specs/research.md   # Technology decisions and resolved NEEDS CLARIFICATION items
    update when: technology decision made or clarification resolved
- docs/specs/quickstart.md   # Prerequisites, environment setup, startup commands, and verification steps
    update when: prerequisites, setup steps, or verification steps changed
- docs/specs/test-plan.md   # Testing strategy, tool choices, test levels, CI gate, and test environment
    update when: testing strategy, tool, or CI gate changed; test scope (tests added for a new FR/AC), test environment, or test data strategy changed
- docs/specs/test-report.md   # Actual test results, coverage, bugs found, and known gaps
    update when: test run completed or coverage baseline changed

## Read (If Present)
- docs/architecture/architecture.md   # Current system components and data-flow diagram
    update when: system components or data-flow changes
- docs/specs/glossary.md   # Domain terms and abbreviations used across documents
    update when: domain term added or definition updated
- docs/specs/dependencies.md   # Third-party libraries, versions, licences, and update policy
    update when: third-party library, external service, or infrastructure component added, removed, or version changed; external-service fallback behaviour changed

## Skip
- docs/architecture/backend.md
- docs/architecture/frontend.md
- docs/architecture/database.md
- docs/architecture/deployment.md
- docs/architecture/topology.md
- docs/specs/api-contract.md
- docs/specs/cli-contract.md
- docs/specs/pipeline-contract.md
- docs/specs/pipeline-debug.md
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
- docs/specs/permissions.md
- docs/specs/data-model.md
- docs/specs/logging-spec.md
- docs/specs/runbook.md
- docs/specs/drift-policy.md
- docs/specs/mobile-contract.md
- docs/business/business-process.md
- docs/business/business-objects.md
- docs/business/business-rules.md


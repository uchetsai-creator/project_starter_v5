# AI Context — llm-app / eval-run
Generated: {{TIMESTAMP}}

## Read (Required)
- docs/current-state.md   # Active task: goal, steps, and required context
- docs/project-requirements.md   # Functional requirements (FR-XXX), acceptance criteria (AC-XXX), scope, roles, and non-functional requirements
    update when: feature added, removed, or acceptance criteria changed; scope, roles, non-functional requirements, edge cases, or assumptions changed
- docs/specs/llm-contract.md   # Model, system prompt, parameters, and tool schemas
    update when: model, system prompt, or parameter changed; tool schemas, context-window strategy, streaming, or retry/fallback behaviour changed
- docs/specs/prompt-library.md   # Index of all prompts with version, purpose, and per-prompt file link
    update when: prompt added, retired, or file path changed
- docs/architecture/architecture.md   # Current system components and data-flow diagram
    update when: system components or data-flow changes
- docs/specs/eval-spec.md   # Evaluation criteria, metrics, score thresholds, and dataset selection rules
    update when: evaluation criterion, metric, or threshold changed
- docs/specs/llm-debug.md   # LLM failure diagnosis guide: wrong answer, low eval score, tool call failure
    update when: new failure mode or diagnostic procedure added
- docs/specs/eval-log.md   # Per-run evaluation results log (one row per eval run)
    update when: new evaluation run completed
- docs/specs/research.md   # Technology decisions and resolved NEEDS CLARIFICATION items
    update when: technology decision made or clarification resolved
- docs/specs/quickstart.md   # Prerequisites, environment setup, startup commands, and verification steps
    update when: prerequisites, setup steps, or verification steps changed
- docs/specs/test-plan.md   # Testing strategy, tool choices, test levels, CI gate, and test environment
    update when: testing strategy, tool, or CI gate changed; test scope (tests added for a new FR/AC), test environment, or test data strategy changed
- docs/specs/test-report.md   # Actual test results, coverage, bugs found, and known gaps
    update when: test run completed or coverage baseline changed

## Read (If Present)
- docs/architecture/frontend.md   # Frontend stack, page structure, and component strategy
    update when: pages, components, or stack changes; data-fetching or state-management approach, or shared UI standards changed
- docs/architecture/database.md   # Database engine, main entities, and relationships
    update when: schema or entity changes; database engine, key relationships, or constraints changed
- docs/architecture/deployment.md   # Services, environment variables, and build/deploy flow
    update when: service, environment variable, or deploy-flow changes
- docs/specs/cli-contract.md   # CLI subcommands, flags, arguments, output format, and exit codes
    update when: subcommand, flag, or output format changed; exit codes, config file format, or environment variables changed
- docs/specs/rag-contract.md   # Retrieval sources, chunking strategy, embedding model, and vector store config
    update when: retrieval source, chunking strategy, or embedding model changed; vector store, retrieval flow, or context-injection format changed
- docs/specs/mcp-contract.md   # MCP server tool schemas, tool-use policy, and server configuration
    update when: MCP server tool schema or policy changed; a connected server added or removed
- docs/specs/glossary.md   # Domain terms and abbreviations used across documents
    update when: domain term added or definition updated
- docs/specs/dependencies.md   # Third-party libraries, versions, licences, and update policy
    update when: third-party library, external service, or infrastructure component added, removed, or version changed; external-service fallback behaviour changed
- docs/business/business-rules.md   # Business constraints and policies that code must enforce
    update when: business constraint or policy changed

## Skip
- docs/architecture/backend.md
- docs/architecture/distribution.md
- docs/architecture/topology.md
- docs/specs/api-contract.md
- docs/specs/public-api.md
- docs/specs/pipeline-contract.md
- docs/specs/pipeline-debug.md
- docs/specs/service-catalog.md
- docs/specs/service-contract.md
- docs/specs/event-catalog.md
- docs/specs/model-contract.md
- docs/specs/experiment-log.md
- docs/specs/release-guide.md
- docs/specs/compatibility-matrix.md
- docs/specs/permissions.md
- docs/specs/data-model.md
- docs/specs/logging-spec.md
- docs/specs/runbook.md
- docs/specs/drift-policy.md
- docs/specs/mobile-contract.md
- docs/business/business-process.md
- docs/business/business-objects.md


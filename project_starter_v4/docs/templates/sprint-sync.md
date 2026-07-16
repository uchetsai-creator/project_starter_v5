# Sprint Documentation Sync

<!--
  Read this file ONLY at sprint end (or when sprint-change-log.md has enough Pending entries).
  Do NOT load this file during normal task work — the Doc Checklist in current-state.md
  covers all per-task doc updates without needing this file.
-->

Run at the end of each sprint (or when `docs/sprint-change-log.md` has accumulated enough Pending entries).

1. Open `docs/sprint-change-log.md`
2. For each entry with **Status: Pending documentation synchronization**:
   - Check the Technical Impact flags
   - Run the relevant items from the Document Update Checklist below for each affected document
   - Update only the affected documents — do not check unaffected ones
   - Mark the entry **Status: Documentation synchronized — [date]**
3. Run Module Completion Check for any modules touched during the sprint
4. Rebuild PDF: `python3 docs/script/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf`
5. Confirm PDF renders correctly

---

## Document Update Checklist

**Step 0 — Type filter (skip entire groups of items before reading individual triggers):**

Look up your declared project type in the table below. Any item tagged with a type NOT in your list can be skipped without reading its trigger condition.

| Your project type | Skip ALL items tagged only with… |
|---|---|
| Web App | CLI Tool, Library / SDK, Data Pipeline, ML Pipeline, AI / LLM App |
| CLI Tool | Web App, Library / SDK, Data Pipeline, ML Pipeline, Microservices, AI / LLM App |
| Library / SDK | Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices, AI / LLM App |
| Data Pipeline | Web App, CLI Tool, Library / SDK, ML Pipeline, Microservices, AI / LLM App |
| ML Pipeline | Web App, CLI Tool, Library / SDK, Data Pipeline, Microservices, AI / LLM App |
| Microservices | CLI Tool, Library / SDK, Data Pipeline, ML Pipeline, AI / LLM App |
| AI / LLM App | Web App, CLI Tool, Library / SDK, Data Pipeline, ML Pipeline, Microservices |
| IaC / DevOps | Web App, CLI Tool, Library / SDK, Data Pipeline, ML Pipeline, Microservices, AI / LLM App |
| Mobile App | CLI Tool, Library / SDK, Data Pipeline, ML Pipeline, Microservices, AI / LLM App, IaC / DevOps |

**Mixed / Hybrid types:** include items tagged with ANY of your declared types.
Example: `Project Type: Data Pipeline + Web App` → include items tagged Web App, Data Pipeline, or All. Skip items tagged only with CLI Tool, Library / SDK, ML Pipeline, Microservices, or AI / LLM App.

Items tagged `[Types: All]` always apply regardless of project type.

After applying the type filter, apply the sprint-content pre-filter below.

---

**Pre-filter before running any checklist item:**
Only check items whose trigger condition could plausibly be true given what this sprint actually changed.
Skip an item immediately if the sprint did not touch the relevant area — do not read the item's full detail.

Quick filter guide:
| If the sprint only touched… | Skip these checklist items entirely |
|---|---|
| Python/JS scripts only | architecture.md, backend.md, frontend.md, database.md, data-model.md, business-objects.md |
| Frontend UI only | data-model.md, api-contract.md (unless new endpoints), backend.md, deployment.md, business-rules.md |
| DB schema only | frontend.md, codebase-map.md page structure, business-process.md, module-flow.md |
| Documentation only | All code-related items (data-model, api-contract, permissions, architecture, backend, frontend) |
| Config / env vars only | All items except deployment.md and quickstart.md |
| Pipeline stage logic only | frontend.md, api-contract.md, permissions.md, business-objects.md, business-process.md |
| ML model / experiment only | frontend.md, api-contract.md, permissions.md, business-objects.md, business-process.md, deployment.md |
| Library / SDK public API only | frontend.md, deployment.md, permissions.md, business-objects.md, business-process.md, data-model.md |
| CLI subcommand only | frontend.md, deployment.md, permissions.md, business-objects.md, business-process.md, data-model.md |
| Prompt / LLM changes only | architecture.md, backend.md, frontend.md, database.md, data-model.md, business-objects.md, deployment.md |
| MCP server changes only | architecture.md, backend.md, frontend.md, database.md, data-model.md, business-objects.md |
| IaC / infra changes only | All items except topology.md, runbook.md, drift-policy.md, research.md, quickstart.md |
| Mobile screen / nav only | backend.md, database.md, api-contract.md, data-model.md, deployment.md, business-objects.md, business-rules.md |

Apply this filter first. Then run only the remaining items.

- [ ] docs/specs/research.md `[Types: All]` — did this sprint involve a new technology decision, or resolve a NEEDS CLARIFICATION? If yes, update. Note: research.md is excluded from the PDF by default (pdf_allowlist.py) — uncomment its entry once it has real content.
- [ ] docs/specs/data-model.md `[Types: Web App, Data Pipeline, ML Pipeline, Microservices]` — did the schema, entities, relationships, or indexes change? If yes, update, then:
  - Regenerate ERD: `Edit the \`\`\`plantuml block in the file, then run build_pdf.py`
  - Regenerate state diagram: `Edit the \`\`\`plantuml block in data-model.md, then rebuild PDF`
  State Machine Consistency check: if this sprint touched an entity with a status lifecycle, confirm the State Machine section here matches the canonical definition in docs/business/[object-name]-object.md exactly. If they differ, update this file to match — the object file wins.
- [ ] docs/specs/api-contract.md `[Types: Web App, Microservices]` — were endpoints added/changed, did error codes or validation rules change, or were WebSocket/Socket.IO events / GraphQL queries or mutations / gRPC methods added or changed? If yes, update the relevant protocol section.
  API Endpoint Overlap check: if this sprint added an endpoint whose purpose overlaps with an existing one, add a **Design Note:** under each explaining why they are separate, or consolidate into one.
- [ ] docs/specs/cli-contract.md `[Types: CLI Tool]` — were subcommands, flags, arguments, output format, or exit codes added or changed? If yes, update.
- [ ] docs/specs/public-api.md `[Types: Library / SDK]` — were public functions, classes, types, or constants added, changed, or deprecated? If yes, update. If removing a public symbol, ensure a deprecation entry exists first.
- [ ] docs/specs/pipeline-contract.md `[Types: Data Pipeline, ML Pipeline]` — did an inter-stage input or output format, path, naming rule, or error handling policy change? If yes, update. Then run the Cross-Stage Consistency Check table.
- [ ] docs/specs/service-catalog.md `[Types: Microservices]` — was a service added, removed, or renamed? Did ownership, port, base URL, or key dependencies change? If yes, update.
- [ ] docs/specs/service-contract.md `[Types: Microservices]` — did a REST contract or resilience policy between services change? If yes, update. Note: async event schemas are canonical in event-catalog.md — do not duplicate them here.
- [ ] docs/specs/event-catalog.md `[Types: Microservices]` — was an event type added or retired, did a payload schema change, did a publisher or subscriber change, or did retention/dead-letter policy change? If yes, update. If the event was also referenced in service-contract.md, update the reference there too.
- [ ] docs/specs/model-contract.md `[Types: ML Pipeline]` — did input feature schema, output format, or production thresholds change? If yes, update.
- [ ] docs/specs/llm-contract.md `[Types: AI / LLM App]` — did the model, system prompt, parameters, or tool schemas change? If yes, update.
- [ ] docs/specs/prompt-library.md + docs/specs/prompts/[id]-prompt.md `[Types: AI / LLM App]` — were prompts added, modified, or retired? If yes, update the index and the relevant per-prompt file.
- [ ] docs/specs/rag-contract.md `[Types: AI / LLM App]` — did retrieval sources, chunking strategy, embedding model, or vector store config change? If yes, update.
- [ ] docs/specs/mcp-contract.md `[Types: AI / LLM App]` — was an MCP server added/removed, did a tool schema change, or was tool-use policy tuned? If yes, update.
- [ ] docs/specs/eval-spec.md `[Types: AI / LLM App]` — did evaluation criteria, metrics, score thresholds, or test dataset selection rules change? If yes, update.
- [ ] docs/architecture/distribution.md `[Types: Library / SDK, CLI Tool]` — did the build process, registry, publish command, or installation instructions change? If yes, update.
- [ ] docs/specs/release-guide.md `[Types: Library / SDK, CLI Tool]` — did the versioning policy, release checklist, publish process, or deprecation policy change? If yes, update.
- [ ] docs/specs/compatibility-matrix.md `[Types: Library / SDK, CLI Tool]` — was a runtime version added or dropped, or was a known incompatibility discovered? If yes, update.
- [ ] docs/specs/permissions.md `[Types: Web App, Microservices]` — were roles, the permission matrix, or API endpoints changed? If yes, update, then regenerate use case diagram: `Edit the \`\`\`plantuml block in permissions.md, then rebuild PDF`
  After updating: cross-check every role listed as "Responsible role" in any `*-process.md` against the API Endpoint Access table. If a role is responsible for an action but has no access to the required endpoint, check the Source column:
  - `Hardcoded` → logical contradiction — resolve before proceeding.
  - `Seeded default` → confirm with project owner, mark "(Default)", do not write into business-rules.md as a permanent rule.
- [ ] docs/architecture/architecture.md `[Types: All]` — did components or data flows change? If yes, update, then regenerate diagram: `Edit the \`\`\`plantuml block in architecture.md, then rebuild PDF`
- [ ] docs/codebase-map.md Page Structure block `[Types: Web App, Microservices]` — did the frontend page/screen structure change? If yes, update the component block, then regenerate.
- [ ] docs/architecture/backend.md `[Types: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices]` — did backend layering, stack, or module pattern change? If yes, update, then regenerate component diagram.
- [ ] docs/architecture/frontend.md `[Types: Web App, Microservices]` — did frontend stack, page structure, or component strategy change? If yes, update, then regenerate component diagram.
- [ ] docs/architecture/database.md `[Types: Web App, Data Pipeline, ML Pipeline, Microservices]` — did main entities or relationships change (conceptual level)? If yes, update.
- [ ] docs/architecture/deployment.md `[Types: Web App, Data Pipeline, ML Pipeline, Microservices]` — did services, env vars, build/deploy flow, or deployment topology change? If yes, update, then regenerate deployment diagram.
- [ ] docs/specs/quickstart.md `[Types: All]` — did setup steps, prerequisites, or verification steps change? If yes, update.
- [ ] docs/specs/logging-spec.md Module Naming Convention table `[Types: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices, AI / LLM App]` — does this sprint introduce a module name not yet listed? If yes, add one line (name + short description). Do not add module-specific logging detail here.
- [ ] docs/business/business-rules.md `[Types: Web App, Data Pipeline, ML Pipeline, Microservices, CLI Tool]` — did business constraints or policies change? If yes, update.
- [ ] docs/business/[object-name]-object.md `[Types: Web App, Microservices]` — were business entities added or changed? If yes, update, then regenerate state diagram.
- [ ] docs/business/business-objects.md `[Types: Web App, Microservices]` — was a new business object file created or did relationships change? If yes, update the index.
- [ ] docs/business/[process-name]-process.md `[Types: Web App, Microservices, Data Pipeline, CLI Tool]` — did the business workflow, decision points, or exceptions change? If yes, update, then regenerate activity diagram.
- [ ] docs/business/business-process.md `[Types: Web App, Microservices, Data Pipeline, CLI Tool]` — was a new business process file created? If yes, add a row to the index table.
- [ ] docs/modules/[module]/[module]-module-data-flow.md `[Types: All]` — did function names, file paths, or flow steps change? If yes, update, then regenerate class diagram.
- [ ] docs/modules/module-data-flow.md index table `[Types: All]` — verify the module has a row in the Module Flow Files table. If missing, add it. Do not rely on memory — read the file.
- [ ] docs/modules/[module]/[module]-flow.md `[Types: All]` — did cross-module service calls change? If yes, update, then regenerate sequence diagram.
- [ ] docs/modules/module-flow.md index table `[Types: All]` — verify the module has a row in the Flow Files table. If missing, add it. Do not rely on memory — read the file.
- [ ] docs/architecture/topology.md `[Types: IaC / DevOps]` — was a resource added, removed, or migrated? Did network topology, environment promotion path, or secrets sources change? If yes, update, then regenerate diagram: `Edit the \`\`\`plantuml block in topology.md, then run build_pdf.py`
- [ ] docs/specs/runbook.md `[Types: IaC / DevOps]` — was a new resource type added, did health check commands change, or did rollback procedures change? If yes, update.
- [ ] docs/specs/drift-policy.md `[Types: IaC / DevOps]` — did detection cadence, remediation SLA, exempt resources, or approval gate process change? If yes, update.
- [ ] docs/specs/mobile-contract.md `[Types: Mobile App]` — was a screen added or removed, did navigation structure change, was a new OS permission added, or did a push notification payload schema change? If yes, update.

For the full explanation of why each document updates on these triggers, see document-purposes-common.md + document-purposes-[your-type].md.

# Dependencies

<!--
  Lists every external dependency the system relies on.
  Update when a package is added, removed, or its version is pinned or changed.

  Sections:
    Runtime Dependencies   — packages needed to run the application in production
    Dev Dependencies       — packages needed only for development, testing, or build
    External Services      — third-party APIs, cloud services, SaaS tools
    Infrastructure         — databases, message queues, caches, storage

  For Runtime and Dev Dependencies, list the actual package manager entries.
  For External Services, document the integration point and fallback behaviour.
-->

---

## Runtime Dependencies

<!--
  List the packages and their pinned versions used in production.
  Group by component if the project has multiple (e.g., Backend / Frontend for Web App,
  or Stage A / Stage B for a Pipeline). Skip grouping if the project is a single unit.

  For Node.js projects: mirror key entries from package.json dependencies
  For Python projects: mirror requirements.txt or pyproject.toml
  For Go: mirror go.mod require block
  For other ecosystems: use the equivalent package manifest format
-->

| Package | Version | Purpose |
|---|---|---|
| [package-name] | [e.g., ^4.18.2] | [What it does in this project] |

---

## Dev Dependencies

| Package | Version | Purpose |
|---|---|---|
| [package-name] | [version] | [e.g., unit testing, linting, bundling] |

---

## External Services

<!--
  List every third-party API, SaaS, or managed cloud service the system calls.
  Document the integration point (which module calls it) and what happens if it is unavailable.
-->

| Service | Provider | Used by | Fallback behaviour |
|---|---|---|---|
| [e.g., Email delivery] | [e.g., SendGrid] | [e.g., notification module] | [e.g., retry 3x, then dead-letter queue] |
| [Service name] | [Provider] | [Module] | [Fallback] |

---

## Infrastructure

<!--
  List the infrastructure components the application depends on at runtime.
  These are not packages — they are services that must be running.
  Cross-reference with docs/architecture/deployment.md for startup and configuration details.

  Skip this section if the project has no persistent infrastructure:
  - CLI Tool: typically no infrastructure (unless it connects to a DB or API)
  - Library / SDK: no infrastructure (it is called by the consumer's environment)
  - AI / LLM App (personal / script): only external API — list under External Services instead
-->

| Component | Technology | Version | Purpose |
|---|---|---|---|
| [e.g., Primary database] | [e.g., PostgreSQL] | [e.g., 16] | [persistent storage] |
| [e.g., Message queue] | [e.g., RabbitMQ / Kafka] | [e.g., 3.12] | [async job processing] |
| [e.g., Cache] | [e.g., Redis] | [e.g., 7] | [session storage, query cache] |
| [e.g., Vector store] | [e.g., Chroma / Pinecone] | [e.g., 0.5] | [RAG retrieval — AI/LLM App] |
| [Component] | [Technology] | [Version] | [Purpose] |

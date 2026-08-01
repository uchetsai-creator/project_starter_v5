# Learning Checkpoints — Microservices

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which service owns this behavior, and its REST/event contract with other services
- What breaks in other services if this contract changes

**Checkpoint B (new requirement) — ask about:**
- New/changed inter-service contract: REST shape or event payload schema
- Which service this belongs in, vs. spinning up a new one

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- The message broker (Kafka, RabbitMQ) if new to you
- Service discovery / mesh mechanics

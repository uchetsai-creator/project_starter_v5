# Learning Checkpoints — IaC / DevOps

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which resource owns this behavior, and its position in the topology
- What depends on this resource, and what the rollback path looks like

**Checkpoint B (new requirement) — ask about:**
- New/changed resource: type, configuration keys, environment promotion path
- Drift detection and approval-gate impact of this change

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- The IaC tool's own language/state model (Terraform HCL, Pulumi, Ansible) if new to you
- Secrets management and environment promotion mechanics

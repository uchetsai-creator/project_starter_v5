# Document Purposes — IaC / DevOps

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to IaC / DevOps projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

IaC / DevOps projects use a minimal document set. All standard spec, architecture, and business
documents (api-contract, backend, database, permissions, etc.) are N/A for this type.
Only `research.md` and `quickstart.md` from the common set apply — see document-purposes-common.md.

---

## Architecture (docs/architecture/)

### topology.md
**Applies to: IaC / DevOps**

Purpose:
Canonical description of the infrastructure resource graph. Covers all environments.
Contains a resource inventory table, environment promotion path (dev → staging → prod),
and a PlantUML component/network diagram showing how resources connect.

This file replaces `architecture.md` for IaC projects — do not create architecture.md.

Load when: adding a resource, changing network topology, or auditing what exists.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new region, VPC, subnet, service, or storage resource is added or removed
* Environment promotion path changes
* Network topology, peering, or routing changes
* A resource is migrated to a different tier, zone, or provider

After updating, regenerate diagram:
`Edit the \`\`\`plantuml block in topology.md, then run build_pdf.py`

---

## Specs (docs/specs/)

### runbook.md
**Applies to: IaC / DevOps**

Purpose:
Incident response procedures for the infrastructure — one section per resource type.
Covers: how to detect the problem, immediate response steps, rollback procedures, and
common Terraform operations. Also documents on-call escalation paths.

Load when: responding to an incident or onboarding a new team member.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new resource type is added (add a response section)
* Health check commands change
* Rollback procedures change
* On-call escalation paths or SLAs change

### drift-policy.md
**Applies to: IaC / DevOps**

Purpose:
Defines what infrastructure drift is acceptable, how it is detected, and what must happen
when drift is found. Covers: allowed drift sources, exempt resources, detection cadence per
environment, remediation SLA by severity, and the approval gate for manual changes.

"Drift" = any difference between the desired state in IaC code and actual cloud resource state.

Load when: investigating drift alerts, onboarding new team members, or auditing compliance.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Detection cadence or tooling changes
* A new resource type is added to drift scope
* Remediation SLA changes
* Approval gate process changes
* A resource is added to or removed from the Exempt Resources list

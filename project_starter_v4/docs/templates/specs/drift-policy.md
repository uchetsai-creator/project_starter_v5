# Drift Policy

<!--
  Defines what infrastructure drift is acceptable, how it is detected,
  and what must happen when it is found.

  "Drift" = any difference between the desired state in IaC code and the
  actual state of cloud resources.

  Update when:
  - Detection cadence changes
  - A new resource type is added (add it to the scope table)
  - Remediation SLA changes
  - Approval gate process changes
  - A drift source is reclassified (allowed → not allowed or vice versa)
-->

## Drift Scope

| Resource type | In scope for drift detection | Notes |
|---|---|---|
| [compute / VMs / containers] | ✅ | |
| [networking / VPC / security groups] | ✅ | |
| [databases / storage] | ✅ | |
| [IAM roles and policies] | ✅ | Highest priority — security impact |
| [tags / labels] | ⚠️ partial | Cosmetic drift in non-prod may be tolerated |
| [manually managed resources] | ❌ | Listed in Exempt Resources below |

---

## Allowed Drift Sources

The following changes to cloud resources do NOT require immediate remediation:

| Source | Example | Max tolerance period |
|---|---|---|
| Cloud provider auto-updates | Minor version patches on managed services | Until next Terraform run |
| Auto-scaling events | Instance count changes within min/max bounds | Ongoing — never remediate |
| Cloud provider maintenance | Automated maintenance windows | Until next Terraform run |

Everything not listed above is **not allowed drift** and must be remediated within the SLA below.

---

## Exempt Resources

The following resources are intentionally managed outside IaC and excluded from drift detection:

| Resource | Reason | Owner |
|---|---|---|
| `[resource-name]` | [e.g. Legacy resource pending migration] | [team] |

---

## Detection

| Environment | Detection method | Cadence | Alert destination |
|---|---|---|---|
| dev | `terraform plan` in CI on every PR | Per PR | PR comment |
| staging | Scheduled `terraform plan` | Daily | [Slack channel / email] |
| prod | Scheduled `terraform plan` | Every 6 hours | [PagerDuty / Slack #ops-alerts] |

Detection command:
```bash
terraform plan -detailed-exitcode
# exit 0 = no changes
# exit 1 = error
# exit 2 = drift detected (changes present)
```

---

## Remediation SLA

| Severity | Drift type | SLA |
|---|---|---|
| Critical | IAM policy, security group, network ACL | Remediate within 2 hours |
| High | Compute, database, storage | Remediate within 24 hours |
| Medium | Tags, minor config | Remediate within next sprint |
| Low | Auto-scaling count, managed service minor version | No action required (see Allowed Drift Sources) |

---

## Approval Gate for Manual Changes

All manual changes to cloud resources (i.e. changes made via console or CLI rather than through IaC) must follow this process:

1. **Document intent** — open a ticket in [tracking system] before making the change.
2. **Get approval** — [role/team] must approve tickets for prod resources before the change.
3. **Make the change** — include the ticket ID in any console/CLI session notes.
4. **Codify within [N days]** — the manual change must be reflected in IaC within [N] business days.
5. **Verify with plan** — run `terraform plan` after codifying; confirm exit 0.
6. **Close the ticket** — link the PR that codifies the change.

Unapproved manual changes to prod are a policy violation. Report to [security / compliance contact].

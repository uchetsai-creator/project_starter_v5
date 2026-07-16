# Runbook

<!--
  Incident response procedures for this infrastructure project.
  One section per resource type. Each section answers:
  - How do I know something is wrong?
  - What do I do first?
  - How do I roll back safely?

  Update when:
  - A new resource type is added to the system
  - Health check commands change
  - Rollback procedures change
  - On-call escalation paths change
-->

## On-Call Escalation

| Severity | Response SLA | First responder | Escalation |
|---|---|---|---|
| P1 — full outage | 15 min | [team / rotation] | [manager / VP after 30 min] |
| P2 — degraded | 1 hour | [team / rotation] | [P1 if no progress in 2 hours] |
| P3 — minor | next business day | [team] | — |

---

## Health Check Commands

```bash
# Verify Terraform state is in sync
terraform plan -detailed-exitcode   # exit 0 = no drift, exit 2 = drift detected

# Check resource status (replace with your cloud CLI)
[cloud CLI command to list resource status]

# Verify connectivity between key resources
[e.g. nc -zv db.internal 5432]
```

---

## Incident Response — [Resource Type A, e.g. Database]

**Symptoms:** [e.g. connection timeouts, high CPU, replication lag]

**Step 1 — Verify scope**
```bash
[command to check resource health]
```
Expected: [what healthy output looks like]

**Step 2 — Identify root cause**
- Check [metric/log source] for [what to look for]
- Check [alert dashboard URL] for correlated events

**Step 3 — Remediate**
```bash
[remediation command]
```

**Rollback procedure**
```bash
# Revert to previous known-good state
terraform apply -target=[resource_address] -var-file=[previous_tfvars]
# OR
[cloud CLI rollback command]
```
Expected after rollback: [what to verify]

**Post-incident**
- File incident report within 24 hours
- Update this runbook if the procedure changed
- Update drift-policy.md if manual change was required

---

## Incident Response — [Resource Type B, e.g. Networking / Load Balancer]

**Symptoms:** [e.g. elevated 5xx rate, DNS resolution failure]

**Step 1 — Verify scope**
```bash
[command]
```

**Step 2 — Identify root cause**
[steps]

**Step 3 — Remediate**
```bash
[command]
```

**Rollback procedure**
```bash
[command]
```

---

## Common Terraform Operations

```bash
# Plan changes (always run before apply)
terraform plan -out=tfplan

# Apply a saved plan
terraform apply tfplan

# Target a single resource
terraform apply -target=module.[name].[resource_address]

# Import an existing resource into state
terraform import [resource_address] [cloud_resource_id]

# Remove a resource from state without destroying it
terraform state rm [resource_address]

# Refresh state from cloud (use with caution — slow)
terraform refresh
```

# Drift Policy

## Detection

Detection Cadence: Every 6 hours via scheduled Terraform plan in CI

## Remediation

Remediation SLA: 24 hours for critical drift, 72 hours for non-critical

## Exempt Resources

- Read replicas (auto-scaled by RDS)
- Spot instances (ephemeral by design)

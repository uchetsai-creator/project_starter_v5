# Runbook

## Health Check Procedure

1. Check application status: `kubectl get pods -n production`
2. Verify database connectivity: `psql $DATABASE_URL -c "SELECT 1"`
3. Check error rate in CloudWatch: look for 5xx rate > 1%
4. Review recent deployments: `kubectl rollout history deployment/api`

## Rollback Procedure

Steps: Run `kubectl rollout undo deployment/api` to revert to the previous version.

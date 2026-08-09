# Test Report

## Summary

All tests passing across the three services on the last CI run.

## Results by Module

| Module | Tests | Pass | Fail |
|---|---|---|---|
| ticket-service (unit) | 37 | 37 | 0 |
| inventory-service (unit) | 29 | 29 | 0 |
| notification-service (unit) | 18 | 18 | 0 |
| contract tests | 14 | 14 | 0 |
| end-to-end | 5 | 5 | 0 |

## Known Gaps

- No chaos-testing job yet for a RabbitMQ outage during the purchase flow; currently
  verified manually by stopping the broker container locally.

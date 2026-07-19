# Pipeline Debug

## Common Failure Scenarios

### Scenario 1: Wrong Row Count

Symptom: Output row count is 0 after extract stage
Root Cause: Source API rate limit exceeded; extractor returned empty response
Fix: Implement exponential backoff and retry logic

### Scenario 2: Schema Mismatch

Symptom: Transform stage fails with column not found error
Root Cause: Source API changed response schema without notice
Fix: Add schema validation step in extract stage

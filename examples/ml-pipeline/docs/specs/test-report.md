# Test Report

## Summary

All tests passing on the last CI run against the `churn-guard` synthetic fixture dataset.

## Results by Module

| Module | Tests | Pass | Fail |
|---|---|---|---|
| feature engineering | 26 | 26 | 0 |
| threshold evaluation | 12 | 12 | 0 |
| DAG integration | 9 | 9 | 0 |
| end-to-end | 2 | 2 | 0 |

## Known Gaps

- No automated test yet for the out-of-cycle retraining trigger; currently verified
  manually by simulating a degraded monitoring AUC.

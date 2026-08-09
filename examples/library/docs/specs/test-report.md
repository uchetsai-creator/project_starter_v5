# Test Report

## Summary

All tests passing. 98% line coverage on the last CI run (`v1.2.0`).

## Results by Module

| Module | Tests | Pass | Fail |
|---|---|---|---|
| diff | 34 | 34 | 0 |
| apply | 41 | 41 | 0 |
| validate | 19 | 19 | 0 |
| property (Hypothesis) | 4 | 4 | 0 |

## Known Gaps

- No dedicated fuzz-testing job yet for deeply nested (>50 levels) documents; tracked for
  a future sprint.

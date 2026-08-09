# Test Report

## Summary

All tests passing on the last CI run (`flutter test` + `flutter drive` on an Android 34
emulator).

## Results by Module

| Module | Tests | Pass | Fail |
|---|---|---|---|
| streak engine (unit) | 28 | 28 | 0 |
| database repository (unit) | 22 | 22 | 0 |
| widgets | 17 | 17 | 0 |
| integration (e2e) | 3 | 3 | 0 |

## Known Gaps

- No automated iOS simulator run in CI yet — iOS builds are tested manually before each
  release.

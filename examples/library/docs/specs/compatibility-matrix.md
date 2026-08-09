# Compatibility Matrix

## Supported Runtimes

| Runtime | Minimum version | Maximum tested | Status |
|---|---|---|---|
| Python | 3.10 | 3.13 | Active |
| Python | 3.9 | 3.9 | Dropped in v1.0.0 |

**End-of-life policy:** When a Python minor version reaches official EOL, we drop support
in the next MINOR release of `jsonpatch-lite`.

---

## Peer Dependencies

`jsonpatch-lite` has no required runtime dependencies. Optional peer dependency:

| Package | Required version range | Notes |
|---|---|---|
| `pytest` | `>=7.0` | Only needed to run the test suite, not at runtime |

---

## Platform / OS Support

| Platform | Status | Notes |
|---|---|---|
| Linux (x86_64) | Supported | Primary CI target |
| macOS (x86_64 + ARM) | Supported | Tested on CI |
| Windows | Supported | Tested on CI (GitHub Actions windows-latest) |

---

## Testing Policy

Every release is tested against all four supported Python versions (3.10–3.13) on
Linux, macOS, and Windows via a GitHub Actions matrix build before publishing to PyPI.

# Release Guide

## Versioning Policy

We use semantic versioning (SemVer): MAJOR.MINOR.PATCH.
Patch releases fix bugs, minor releases add features, major releases break compatibility.

## Release Process

1. Bump version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Tag the release: `git tag v1.2.3`
4. Publish to PyPI: `twine upload dist/*` or `pip install build && python -m build`

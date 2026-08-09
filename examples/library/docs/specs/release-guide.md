# Release Guide

## Versioning Policy

We use semantic versioning (SemVer): MAJOR.MINOR.PATCH.

- **Patch** (`1.2.x`): bug fixes, no public API change.
- **Minor** (`1.x.0`): new public function/class, backward compatible.
- **Major** (`x.0.0`): removes or changes the signature of a public symbol.

## Release Process

1. Bump the version in `pyproject.toml`.
2. Update `CHANGELOG.md` with the new version's entries.
3. Run the full test suite: `pytest --cov=jsonpatch_lite`.
4. Tag the release: `git tag v1.3.0 && git push --tags`.
5. Build and publish: `python -m build && twine upload dist/*`.

## Deprecation Policy

A public symbol scheduled for removal is marked deprecated for at least one MINOR
release before removal in the next MAJOR release. Deprecated symbols emit a
`DeprecationWarning` naming the replacement.

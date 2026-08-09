# Distribution

## Package Details

| Field | Value |
|---|---|
| Package name | jsonpatch-lite |
| Registry | PyPI |
| Install | `pip install jsonpatch-lite` |

## Publish

1. Bump the version in `pyproject.toml`.
2. Build the distribution: `python -m build`.
3. Upload to PyPI: `twine upload dist/*`.

The package ships as a universal wheel plus an sdist; both are built from the same
`pyproject.toml` with no compiled extensions.

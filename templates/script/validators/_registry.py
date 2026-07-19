"""Shared loader for document-registry.yaml (project_starter_v5 schema).

Searches for document-registry.yaml starting at CWD, then at the framework root
derived from this file's location — covers both user projects (scripts in docs/script/)
and the framework repo itself (scripts in templates/script/).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Canonical order — all scripts must agree on this sequence.
VALID_TYPES: list[str] = [
    'web-app', 'cli-tool', 'library',
    'data-pipeline', 'ml-pipeline', 'microservices', 'llm-app', 'iac', 'mobile-app',
]

_REGISTRY: dict[str, Any] | None = None


def _find_registry_path() -> Path:
    candidates = [
        Path.cwd() / 'document-registry.yaml',
        Path(__file__).resolve().parent.parent.parent / 'document-registry.yaml',
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        'document-registry.yaml not found. '
        f'Searched: {[str(c) for c in candidates]}. '
        'Copy it from the project_starter_v5 repo root to your project root.'
    )


def _parse_registry(text: str) -> dict[str, Any]:
    """Parse document-registry.yaml without external dependencies.

    Handles the project_starter_v5 schema only (flat, 2-level nesting, inline lists).
    """
    documents: dict[str, Any] = {}
    current_doc: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.lstrip()

        if not stripped or stripped.startswith('#'):
            continue
        if stripped == 'documents:':
            continue

        # Document key at exactly 2-space indent
        doc_m = re.match(r'^  ([a-z][a-z0-9-]+):$', line)
        if doc_m:
            current_doc = doc_m.group(1)
            documents[current_doc] = {}
            continue

        # Field at exactly 4-space indent
        if current_doc is not None and line.startswith('    ') and not line.startswith('     '):
            field_m = re.match(r'^    ([a-z_]+):\s*(.*)', line)
            if not field_m:
                continue
            key, val = field_m.group(1), field_m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                inner = val[1:-1]
                items = [x.strip().strip("'\"") for x in inner.split(',') if x.strip()]
                documents[current_doc][key] = items
            elif val.startswith('{') and val.endswith('}'):
                inner = val[1:-1]
                mapping: dict[str, str] = {}
                for pair in inner.split(','):
                    pair = pair.strip()
                    if ':' in pair:
                        k, v = pair.split(':', 1)
                        mapping[k.strip().strip("'\"")] = v.strip().strip("'\"")
                documents[current_doc][key] = mapping
            elif val.startswith('"') or val.startswith("'"):
                documents[current_doc][key] = val.strip('"\'')
            else:
                documents[current_doc][key] = val

    return documents


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load and cache document-registry.yaml. Returns the documents dict."""
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    reg_path = path or _find_registry_path()
    _REGISTRY = _parse_registry(reg_path.read_text(encoding='utf-8'))
    return _REGISTRY


# ---------------------------------------------------------------------------
# Derived structures (mirrors of the old hardcoded dicts)
# ---------------------------------------------------------------------------

def build_matrix(registry: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Return MATRIX equivalent: {doc.md: (R/O/N, ...) in VALID_TYPES order}."""
    matrix: dict[str, tuple[str, ...]] = {}
    for name, meta in registry.items():
        doc_name = name if name.endswith('.md') else f'{name}.md'
        required = set(meta.get('required_for', []))
        optional = set(meta.get('optional_for', []))
        row = tuple(
            'R' if t in required else ('O' if t in optional else 'N')
            for t in VALID_TYPES
        )
        matrix[doc_name] = row
    return matrix


def build_file_locations(registry: dict[str, Any]) -> dict[str, str]:
    """Return FILE_LOCATIONS equivalent: {doc.md: folder-name}."""
    result: dict[str, str] = {}
    for name, meta in registry.items():
        doc_name = name if name.endswith('.md') else f'{name}.md'
        path = meta.get('path', '')
        result[doc_name] = path.split('/')[0] if '/' in path else 'specs'
    return result


def build_type_docs(registry: dict[str, Any]) -> dict[str, list[str]]:
    """Return TYPE_DOCS equivalent: {type: [required doc.md, ...]}."""
    result: dict[str, list[str]] = {t: [] for t in VALID_TYPES}
    for name, meta in registry.items():
        doc_name = name if name.endswith('.md') else f'{name}.md'
        for t in meta.get('required_for', []):
            if t in result:
                result[t].append(doc_name)
    return result


def build_doc_paths(registry: dict[str, Any]) -> dict[str, str]:
    """Return DOC_PATHS equivalent: {doc.md: relative-path-under-docs/}."""
    return {
        (name if name.endswith('.md') else f'{name}.md'): meta['path']
        for name, meta in registry.items()
        if 'path' in meta
    }


def get_universal_docs(registry: dict[str, Any]) -> list[str]:
    """Return doc.md names where all 9 types appear in required_for."""
    all_types = set(VALID_TYPES)
    result = []
    for name, meta in registry.items():
        if all_types <= set(meta.get('required_for', [])):
            result.append(name if name.endswith('.md') else f'{name}.md')
    return result


def build_valid_task_types(registry: dict[str, Any]) -> list[str]:
    """Return sorted list of all unique task_type values referenced in task_types fields."""
    seen: set[str] = set()
    for meta in registry.values():
        for t in meta.get('task_types', []):
            seen.add(t)
    return sorted(seen)


def build_replaces_for(registry: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return {doc.md: {type: replacement-doc.md}} for docs with replaces_for entries."""
    result: dict[str, dict[str, str]] = {}
    for name, meta in registry.items():
        rf = meta.get('replaces_for')
        if rf and isinstance(rf, dict):
            doc_name = name if name.endswith('.md') else f'{name}.md'
            result[doc_name] = {
                t: (repl if repl.endswith('.md') else f'{repl}.md')
                for t, repl in rf.items()
            }
    return result

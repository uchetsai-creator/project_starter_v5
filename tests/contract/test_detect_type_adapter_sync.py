"""Guards detect_type.py's _ADAPTER_SIGNALS against drifting from
verify_spec_code.py's ADAPTER_REGISTRY — every adapter alias detect_type.py might
suggest into .project-starter.yml must actually be a valid --adapter value, or a
suggested config would silently fail every verify_spec_code.py run it's used in."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(REPO_ROOT))
from detect_type import (  # noqa: E402
    _ADAPTER_SIGNALS,
    _CANONICAL_SPEC_FILE,
    VALID_TYPES,
)

sys.path.insert(0, str(REPO_ROOT / "templates/script/validators"))
import verify_spec_code as vsc  # noqa: E402

# verify_spec_code.py's own module-level code inserts its _spec_code_adapters/ dir onto
# sys.path too (needed for its own importlib.import_module()-based dynamic adapter
# loading at runtime — see its own module, not fixable there without breaking that).
# This test only reads vsc.ADAPTER_REGISTRY (a plain dict, no dynamic dispatch), so it's
# safe to remove that leak here right after import — left in place, it silently shadows
# any later `import click`/`django`/etc. for a real same-named package for the rest of
# the pytest session; see CHANGELOG.md's [Unreleased] "Fixed" entry for the concrete bug
# this caused (this was the actual source, not tests/contract/test_adapter_contracts.py
# as first suspected — that file already cleans up correctly on its own).
sys.path.remove(str(vsc._ADAPTER_DIR))


def test_every_adapter_signal_alias_is_a_valid_adapter():
    unknown = sorted({
        adapter for _, _, adapter, _ in _ADAPTER_SIGNALS
        if adapter not in vsc.ADAPTER_REGISTRY
    })
    assert not unknown, (
        f"detect_type.py._ADAPTER_SIGNALS references adapter alias(es) not in "
        f"verify_spec_code.py's ADAPTER_REGISTRY: {unknown}. A suggestion built from "
        f"these would fail every verify_spec_code.py run — update one side to match."
    )


def test_every_adapter_signal_project_type_is_valid():
    unknown = sorted({
        ptype for _, _, _, ptype in _ADAPTER_SIGNALS
        if ptype not in VALID_TYPES
    })
    assert not unknown, f"detect_type.py._ADAPTER_SIGNALS references unknown project type(s): {unknown}"


def test_every_canonical_spec_file_project_type_is_valid_or_hybrid_capable():
    # _CANONICAL_SPEC_FILE covers 9 single types + microservices/ml-pipeline aliases used
    # elsewhere in the framework (not in VALID_TYPES, which is detect_type.py's own list of
    # *primary* detectable types) — just confirm every key resolves to a real spec path.
    for ptype, spec_path in _CANONICAL_SPEC_FILE.items():
        assert spec_path.startswith("docs/"), f"{ptype} → {spec_path} should be docs-relative"


def test_every_adapter_signal_kind_is_recognized():
    valid_kinds = {"py_dep", "node_dep", "file", "file_glob"}
    unknown = sorted({kind for kind, _, _, _ in _ADAPTER_SIGNALS if kind not in valid_kinds})
    assert not unknown, f"detect_type.py._ADAPTER_SIGNALS uses unrecognized signal kind(s): {unknown}"

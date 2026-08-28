"""Guards _module_types.py's MODULE_TYPE_REGISTRY against drifting from
scan_codebase.py's MODULE_VOCAB — every raw module-type label scan_codebase.py can write
into a scaffolded doc header must resolve in the registry, or verify_module_docs.py would
silently report "Unrecognized module type" for it and draft_module_flow.py would silently
fall back to an unhelpful UNKNOWN format. This is exactly the drift that happened before this
registry existed: 'Command', 'Namespace', 'Service', 'Screen', and 'Shared / Infrastructure'
were all producible by scan_codebase.py but unrecognized by verify_module_docs.py."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "templates/script/scanners"))
from _module_types import MODULE_TYPE_REGISTRY  # noqa: E402
from scan_codebase import MODULE_VOCAB  # noqa: E402


def test_every_module_vocab_label_is_registered():
    vocab_labels = {label for label, _plural in MODULE_VOCAB.values()}
    unknown = sorted(vocab_labels - set(MODULE_TYPE_REGISTRY))
    assert not unknown, (
        f"scan_codebase.py's MODULE_VOCAB produces label(s) not in _module_types.py's "
        f"MODULE_TYPE_REGISTRY: {unknown}. A doc scaffolded with this label would be "
        f"unrecognized by verify_module_docs.py and mis-formatted by draft_module_flow.py — "
        f"add a row to MODULE_TYPE_REGISTRY."
    )


def test_shared_infrastructure_label_is_registered():
    # guess_type()'s is_shared() branch returns this literal string for every project
    # type — it isn't a MODULE_VOCAB value, so the test above doesn't cover it.
    assert "Shared / Infrastructure" in MODULE_TYPE_REGISTRY


def test_every_registry_entry_has_a_valid_quality_bucket_or_is_resource_group():
    # Resource Group is the one documented exception with no matching draft format, but
    # every entry (including Resource Group) must still have a real quality_bucket so
    # verify_module_docs.py can grade it.
    valid_buckets = {'Pipeline Stage', 'Feature', 'Background Job', 'Shared Utility', 'Resource Group'}
    bad = {
        label: entry['quality_bucket']
        for label, entry in MODULE_TYPE_REGISTRY.items()
        if entry.get('quality_bucket') not in valid_buckets
    }
    assert not bad, f"MODULE_TYPE_REGISTRY entries with an unrecognized quality_bucket: {bad}"

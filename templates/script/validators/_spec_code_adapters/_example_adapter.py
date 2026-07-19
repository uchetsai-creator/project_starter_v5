"""
_example_adapter.py — Custom Adapter SDK reference implementation.

This file is the authoritative example for writing a new FrameworkAdapter.
It implements a minimal "YAML API Spec" adapter that parses a simple YAML spec
and Python source code. Read every method's docstring before writing your own.

Spec format this adapter accepts (example-contract.yaml):
  functions:
    - name: greet
      params:
        - name: name
          type: str
    - name: farewell
      params:
        - name: name
          type: str

Code format (Python):
  def greet(name: str) -> str:
      return f"Hello, {name}"

Run self-test:
  python3 _example_adapter.py   # exits 0 on success
"""
from __future__ import annotations

import ast
import sys
import tempfile
import textwrap
from pathlib import Path

# Bring _base into scope when running directly from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _base import FrameworkAdapter, NormalizedField, NormalizedFunction  # noqa: E402
from _utils import _annotation_str  # noqa: E402


# ---------------------------------------------------------------------------
# ExampleAdapter
# ---------------------------------------------------------------------------

class ExampleAdapter(FrameworkAdapter):
    """
    Reference implementation of FrameworkAdapter for the Custom Adapter SDK.

    CONTRACT: every public method must accept only str paths and return only
    lists of NormalizedForm objects. Never import framework libraries at module
    level — import lazily inside methods to avoid hard dependencies.

    Register your adapter in verify_spec_code.py ADAPTER_REGISTRY as
    'framework_key': ('module', 'ClassName'). The *Adapter naming convention
    is legacy — capability detectors in _capability_*.py are the preferred
    extension point for new frameworks (see docs/contributing-adapters.md).
    """

    # ------------------------------------------------------------------
    # Spec extraction
    # ------------------------------------------------------------------

    def extract_spec(self, spec_path: str) -> list[NormalizedFunction]:
        """
        Parse the spec document and return NormalizedForm objects.

        Contract:
          - Input:  absolute or relative path to the spec file.
          - Output: list of NormalizedFunction (one per declared function).
          - Must return [] (not raise) if the file is empty or malformed.

        This example reads a minimal YAML format with `functions:` list.
        Replace with your own spec format logic.
        """
        try:
            import yaml  # lazy import — not a hard dependency of the base SDK
        except ImportError:
            print("⚠️  ExampleAdapter: PyYAML not installed — spec parsing skipped",
                  file=sys.stderr)
            return []

        try:
            with open(spec_path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except (OSError, Exception):
            return []

        functions: list[NormalizedFunction] = []
        for entry in data.get('functions') or []:
            if not isinstance(entry, dict) or 'name' not in entry:
                continue
            params = [
                NormalizedField(name=p['name'], type=p.get('type', ''))
                for p in (entry.get('params') or [])
                if isinstance(p, dict) and 'name' in p
            ]
            functions.append(NormalizedFunction(name=entry['name'], params=params))

        return functions

    # ------------------------------------------------------------------
    # Code extraction
    # ------------------------------------------------------------------

    def extract_code(self, src_path: str) -> list[NormalizedFunction]:
        """
        Parse source code and return NormalizedForm objects.

        Contract:
          - Input:  path to a single file OR a directory to walk recursively.
          - Output: list of NormalizedFunction (one per public function found).
          - Must return [] (not raise) on parse errors.

        This example uses Python's `ast` module. For non-Python languages,
        use regex or invoke an external parser via subprocess.
        """
        import os
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )
        functions: list[NormalizedFunction] = []
        for fpath in files:
            functions.extend(self._parse_file(fpath))
        return functions

    def _parse_file(self, fpath: str) -> list[NormalizedFunction]:
        """
        Parse a single source file.

        CONTRACT: never raise — return [] on any error.
        Log a warning to stderr if useful for debugging.
        """
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        functions: list[NormalizedFunction] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith('_'):
                continue  # skip private/internal functions

            params = [
                NormalizedField(
                    name=a.arg,
                    type=_annotation_str(a.annotation),
                )
                for a in node.args.args
                if a.arg not in ('self', 'cls')
            ]
            return_type = _annotation_str(node.returns) if node.returns else ''
            functions.append(NormalizedFunction(
                name=node.name,
                params=params,
                return_type=return_type,
            ))

        return functions


# ---------------------------------------------------------------------------
# Self-test (run directly: python3 _example_adapter.py)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Verify the adapter round-trips correctly with in-memory fixtures."""
    adapter = ExampleAdapter()

    # ── Code extraction ────────────────────────────────────────────────
    sample_code = textwrap.dedent("""\
        def greet(name: str) -> str:
            return f"Hello, {name}"

        def farewell(name: str) -> str:
            return f"Goodbye, {name}"

        def _internal():
            pass
    """)

    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as tf:
        tf.write(sample_code)
        code_path = tf.name

    code_fns = adapter.extract_code(code_path)
    assert len(code_fns) == 2, f"Expected 2 functions, got {len(code_fns)}"
    assert code_fns[0].name == 'greet'
    assert code_fns[0].params[0].name == 'name'
    assert code_fns[0].params[0].type == 'str'
    assert code_fns[1].name == 'farewell'

    # ── Spec extraction (requires PyYAML) ──────────────────────────────
    try:
        import yaml  # noqa: F401
        sample_spec = textwrap.dedent("""\
            functions:
              - name: greet
                params:
                  - name: name
                    type: str
              - name: farewell
                params:
                  - name: name
                    type: str
        """)
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as sf:
            sf.write(sample_spec)
            spec_path = sf.name

        spec_fns = adapter.extract_spec(spec_path)
        assert len(spec_fns) == 2, f"Expected 2 spec functions, got {len(spec_fns)}"
        assert spec_fns[0].name == 'greet'
        assert spec_fns[0].params[0].name == 'name'

    except ImportError:
        print("⚠️  PyYAML not installed — spec extraction test skipped")

    print("✅  _example_adapter.py self-test passed")


if __name__ == '__main__':
    _self_test()

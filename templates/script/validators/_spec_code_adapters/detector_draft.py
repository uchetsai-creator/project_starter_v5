"""
detector_draft.py — LLM-assisted first draft for a missing framework Detector.

Wired into verify_spec_code.py behind --suggest-detector (opt-in, same posture as
--semantic): only runs when the structural pass hit zero_coverage (a real --src
exists but no registered detector matched anything in it — see _ZERO_COVERAGE_NOTE
in verify_spec_code.py). It never runs automatically and is never valid inside
workflow-registry.yaml or pre-commit sequences.

What this does NOT do (by design, matching the framework's own "don't silently
pass" rule):
  - Does not register the draft in ADAPTER_REGISTRY.
  - Does not wire the draft into any verification run.
  - Does not `git add` / `git commit` / `git push` anything, ever.
A human must read docs/contributing-adapters.md (Common pitfalls + Checklist),
move the file out of _drafts/, register it, and open a PR by hand.

Requires: ANTHROPIC_API_KEY env var and the 'anthropic' package — identical
requirement to semantic.py. Telemetry follows this repo's one-file-per-feature
convention (semantic.py -> token-usage.json, framework_fix_agents.py ->
framework-fix-agents-usage.json, llm_security_review.py ->
security-review-usage.json): this module writes its own
logs/telemetry/detector-draft-usage.json rather than sharing another
feature's file.

Run self-test:
    python3 detector_draft.py   # exits 0 on success; does not call the LLM
"""
from __future__ import annotations

import ast
import json
import os
import sys
from dataclasses import fields as dataclass_fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
_ADAPTERS_DIR = Path(__file__).resolve().parent
_VALIDATORS_DIR = _ADAPTERS_DIR.parent
_DRAFTS_DIR = _ADAPTERS_DIR / '_drafts'

# Same cheap default as semantic.py — this is code drafting, not a reasoning task
# that needs a bigger model, and it's opt-in so cost-consciousness stays the default.
_DRAFT_MODEL = os.environ.get('SPEC_CODE_MODEL', 'claude-haiku-4-5-20251001')

# Reuse semantic.py's client getter + pricing table rather than duplicating them —
# unlike framework_fix_agents.py (a different sys.path root under generators/), this
# module lives in the same _spec_code_adapters/ package as semantic.py, so importing
# instead of copy-pasting has no cross-package cost.
from semantic import _estimate_cost, _get_client  # noqa: E402

_MAX_SAMPLE_FILES = 5
_MAX_SAMPLE_CHARS_PER_FILE = 4000
_STYLE_REFERENCE_DETECTOR = 'click.py'  # short, self-contained; swap if it ever grows


class DetectorDraftResult:
    """Outcome of one draft_detector() call — always constructed, never raised."""

    def __init__(
        self,
        ok: bool,
        path: str | None = None,
        reason: str | None = None,
        token_usage: dict | None = None,
    ) -> None:
        self.ok = ok
        self.path = path
        self.reason = reason
        self.token_usage = token_usage


def draft_detector(
    capability: str,
    framework_hint: str,
    src_path: str,
) -> DetectorDraftResult:
    """
    Ask the LLM for a first-draft Detector subclass targeting `capability`'s
    NormalizedForm, based on real files under `src_path`. Writes the draft to
    _spec_code_adapters/_drafts/<framework_hint>_detector_draft.py on success.

    Never raises. Returns DetectorDraftResult(ok=False, reason=...) on any
    failure (no API key, no package, malformed LLM output, etc.) — a failed
    draft must never be written silently as if it were usable.
    """
    token_usage: dict[str, Any] = {
        'model': _DRAFT_MODEL,
        'calls': 0,
        'input_tokens': 0,
        'output_tokens': 0,
        'estimated_cost_usd': None,
        'budget_tokens': int(os.environ['SPEC_CODE_TOKEN_BUDGET']) if os.environ.get('SPEC_CODE_TOKEN_BUDGET') else None,
        'budget_exceeded': False,
    }

    if not os.environ.get('ANTHROPIC_API_KEY'):
        return DetectorDraftResult(
            ok=False,
            reason="--suggest-detector requires ANTHROPIC_API_KEY — set the env var and re-run.",
        )
    client = _get_client()
    if client is None:
        return DetectorDraftResult(
            ok=False,
            reason="--suggest-detector requires the 'anthropic' package (pip install anthropic).",
        )

    normalized_form_doc = _describe_normalized_form(capability)
    if normalized_form_doc is None:
        return DetectorDraftResult(
            ok=False,
            reason=f"Unknown capability '{capability}' — no NormalizedForm mapping to target.",
        )

    style_reference = _read_style_reference()
    sample_code = _sample_source(src_path)
    if not sample_code:
        return DetectorDraftResult(
            ok=False,
            reason=f"No readable source files found under --src {src_path!r} to draft from.",
        )

    budget = token_usage['budget_tokens']
    if budget is not None and budget <= 0:
        token_usage['budget_exceeded'] = True
        return DetectorDraftResult(
            ok=False,
            reason="SPEC_CODE_TOKEN_BUDGET is already exhausted (<= 0) — skipping LLM call.",
            token_usage=token_usage,
        )

    prompt = _build_prompt(framework_hint, normalized_form_doc, style_reference, sample_code)

    try:
        response = client.messages.create(
            model=_DRAFT_MODEL,
            max_tokens=2048,
            messages=[{'role': 'user', 'content': prompt}],
        )
        raw = response.content[0].text.strip()
        usage = {
            'input_tokens': getattr(response.usage, 'input_tokens', 0),
            'output_tokens': getattr(response.usage, 'output_tokens', 0),
        }
    except Exception as exc:  # noqa: BLE001
        return DetectorDraftResult(ok=False, reason=f"LLM call failed: {exc}", token_usage=token_usage)

    token_usage['calls'] += 1
    token_usage['input_tokens'] += usage['input_tokens']
    token_usage['output_tokens'] += usage['output_tokens']
    token_usage['estimated_cost_usd'] = _estimate_cost(
        token_usage['model'], token_usage['input_tokens'], token_usage['output_tokens'],
    )
    _write_token_usage_telemetry(token_usage)

    code = _strip_fences(raw)
    problem = _validate_draft_code(code)
    if problem:
        _DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        rejected_path = _DRAFTS_DIR / f"{_safe_name(framework_hint)}_detector_draft.py.rejected"
        rejected_path.write_text(code, encoding='utf-8')
        return DetectorDraftResult(
            ok=False,
            reason=(
                f"LLM output failed validation ({problem}) — raw output saved to "
                f"{rejected_path} for inspection, NOT written as a usable draft."
            ),
            token_usage=token_usage,
        )

    _DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft_path = _DRAFTS_DIR / f"{_safe_name(framework_hint)}_detector_draft.py"
    draft_path.write_text(_with_draft_header(framework_hint, code), encoding='utf-8')

    return DetectorDraftResult(ok=True, path=str(draft_path), token_usage=token_usage)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _describe_normalized_form(capability: str) -> str | None:
    """Return a text description (name + fields) of the NormalizedForm this
    capability compares on, introspected from _base.py so it can never drift
    out of sync with the real dataclasses."""
    import _base  # noqa: PLC0415

    mapping = {
        'web-api': 'NormalizedEndpoint',
        'cli': 'NormalizedCommand',
        'data-pipeline': 'NormalizedStageContract',
        'library': 'NormalizedFunction',
        'llm-app': 'NormalizedTool',
        'iac': 'NormalizedResource',
        'mobile': 'NormalizedScreen',
        'logging': 'NormalizedLogPoint',
    }
    cls_name = mapping.get(capability)
    if cls_name is None:
        return None
    cls = getattr(_base, cls_name)
    field_lines = '\n'.join(
        f"    {f.name}: {f.type}" for f in dataclass_fields(cls)
    )
    return f"{cls_name} (from _base.py):\n{field_lines}\n\nDocstring:\n{cls.__doc__}"


def _read_style_reference() -> str:
    ref_path = _ADAPTERS_DIR / _STYLE_REFERENCE_DETECTOR
    try:
        return ref_path.read_text(encoding='utf-8')
    except OSError:
        return ''  # degrade gracefully — prompt still works without a style example


def _sample_source(src_path: str) -> str:
    paths: list[Path]
    p = Path(src_path)
    if p.is_file():
        paths = [p]
    elif p.is_dir():
        paths = sorted(p.rglob('*'))[:200]  # cap the walk itself before filtering
        paths = [f for f in paths if f.is_file()][:_MAX_SAMPLE_FILES]
    else:
        paths = []

    chunks = []
    for fp in paths[:_MAX_SAMPLE_FILES]:
        try:
            text = fp.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        chunks.append(f"--- {fp} ---\n{text[:_MAX_SAMPLE_CHARS_PER_FILE]}")
    return '\n\n'.join(chunks)


def _build_prompt(framework_hint: str, normalized_form_doc: str, style_reference: str, sample_code: str) -> str:
    return (
        "You are drafting a Detector subclass for project_starter_v5's spec<->code drift "
        f"checker. Target framework/language hint: {framework_hint!r}.\n\n"
        "Contract (must follow exactly):\n"
        "- Subclass Detector from _base (`from _base import Detector, <NormalizedForm>, NormalizedField`).\n"
        "- Implement only `extract(self, files: list[str]) -> list`.\n"
        "- Must NOT perform file discovery (no os.walk) — `files` is already the full list.\n"
        "- Must return [] (never raise) on any parse error.\n"
        "- Only handle files it understands; silently skip the rest.\n"
        "- No comparison logic — this file only extracts and normalizes.\n"
        "- Prefer `ast` for Python source; use `re` only for non-Python or spec-side text (this "
        "file only needs the code-side extract(), not spec parsing).\n\n"
        f"Target NormalizedForm:\n{normalized_form_doc}\n\n"
        f"Style reference — an existing detector for a different framework "
        f"(match this structure/quality, not this framework's specifics):\n{style_reference}\n\n"
        f"Real sample source files to design the detector against:\n{sample_code}\n\n"
        "Output ONLY the Python source of the new detector file. No markdown fences, no "
        "explanation before or after. The file must be syntactically valid Python and must "
        "define exactly one class that subclasses Detector with a working extract() method."
    )


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith('```'):
        lines = t.splitlines()
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        t = '\n'.join(lines)
    return t.strip()


def _validate_draft_code(code: str) -> str | None:
    """Return a problem description if `code` isn't a usable draft, else None."""
    if not code.strip():
        return "empty output"
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError: {exc}"

    detector_classes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(
            (isinstance(base, ast.Name) and base.id == 'Detector')
            or (isinstance(base, ast.Attribute) and base.attr == 'Detector')
            for base in node.bases
        )
    ]
    if not detector_classes:
        return "no class subclassing Detector found"

    has_extract = any(
        isinstance(n, ast.FunctionDef) and n.name == 'extract'
        for cls in detector_classes
        for n in cls.body
    )
    if not has_extract:
        return "Detector subclass has no extract() method"
    return None


def _safe_name(framework_hint: str) -> str:
    raw = ''.join(c if c.isalnum() else '_' for c in framework_hint.lower())
    while '__' in raw:
        raw = raw.replace('__', '_')
    return raw.strip('_') or 'unknown'


_DRAFT_HEADER = '''"""
DRAFT — machine-generated by detector_draft.py via --suggest-detector ({framework_hint!r}).

NOT reviewed. NOT registered in ADAPTER_REGISTRY. NOT wired into any verification
run or pre-commit sequence. Nothing about this file's existence pushes anything
to git — that step is always manual.

Before promoting this out of _drafts/:
  1. Read docs/contributing-adapters.md -> "Common pitfalls" and the closing Checklist.
  2. Run this file's self-test pattern (see any real detector, e.g. click.py) and add one
     if the LLM didn't include a runnable if __name__ == '__main__' block.
  3. Manually register it in verify_spec_code.py's ADAPTER_REGISTRY.
  4. Open a PR by hand — see docs/contributing-adapters.md for the contribution flow.
"""
'''


def _with_draft_header(framework_hint: str, code: str) -> str:
    return _DRAFT_HEADER.format(framework_hint=framework_hint) + '\n\n' + code


def _write_token_usage_telemetry(token_usage: dict) -> None:
    """Append one row to logs/telemetry/detector-draft-usage.json — this feature's own
    file, matching the repo's one-file-per-feature convention (semantic.py's
    token-usage.json, framework_fix_agents.py's framework-fix-agents-usage.json,
    llm_security_review.py's security-review-usage.json). Best-effort, never raises."""
    if token_usage['calls'] == 0:
        return
    entry = {
        'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        **token_usage,
    }
    try:
        output = os.path.join('logs', 'telemetry', 'detector-draft-usage.json')
        os.makedirs(os.path.dirname(output), exist_ok=True)
        rows = []
        if os.path.exists(output):
            with open(output, encoding='utf-8') as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                rows = loaded
        rows.append(entry)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=2)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] failed to write token-usage telemetry: {exc}")

    try:
        if str(_VALIDATORS_DIR) not in sys.path:
            sys.path.insert(0, str(_VALIDATORS_DIR))
        from _otel import emit as _otel_emit  # noqa: PLC0415
        _otel_emit('detector_draft_token_usage', entry)
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Self-test (no LLM call — tests validation, prompt building, and file I/O only)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # --- _validate_draft_code: good code passes ---
    good_code = (
        "from _base import Detector, NormalizedCommand\n\n"
        "class GinDetector(Detector):\n"
        "    def extract(self, files):\n"
        "        return []\n"
    )
    assert _validate_draft_code(good_code) is None

    # --- _validate_draft_code: rejects non-Detector class ---
    bad_code_1 = "class GinDetector:\n    def extract(self, files):\n        return []\n"
    assert _validate_draft_code(bad_code_1) == "no class subclassing Detector found"

    # --- _validate_draft_code: rejects missing extract() ---
    bad_code_2 = "from _base import Detector\nclass GinDetector(Detector):\n    pass\n"
    assert _validate_draft_code(bad_code_2) == "Detector subclass has no extract() method"

    # --- _validate_draft_code: rejects syntax errors ---
    syntax_problem = _validate_draft_code("def broken(:\n")
    assert syntax_problem is not None
    assert syntax_problem.startswith("SyntaxError")

    # --- _validate_draft_code: rejects empty output ---
    assert _validate_draft_code("   \n") == "empty output"

    # --- _strip_fences: removes markdown fences ---
    fenced = "```python\nclass X:\n    pass\n```"
    assert _strip_fences(fenced) == "class X:\n    pass"
    assert _strip_fences("class X:\n    pass") == "class X:\n    pass"

    # --- _safe_name: sanitizes framework hints ---
    assert _safe_name("Gin (Go)") == "gin_go"
    assert _safe_name("") == "unknown"

    # --- _describe_normalized_form: known + unknown capabilities ---
    cli_form = _describe_normalized_form('cli')
    assert cli_form is not None
    assert 'NormalizedCommand' in cli_form
    assert _describe_normalized_form('not-a-real-capability') is None

    # --- draft_detector: no API key -> clean failure, nothing written ---
    saved_key = os.environ.pop('ANTHROPIC_API_KEY', None)
    with __import__('tempfile').TemporaryDirectory() as tmpdir:
        src_dir = Path(tmpdir) / 'src'
        src_dir.mkdir()
        (src_dir / 'main.go').write_text('package main\n', encoding='utf-8')
        result = draft_detector('web-api', 'gin', str(src_dir))
        assert result.ok is False
        assert result.reason is not None
        assert 'ANTHROPIC_API_KEY' in result.reason
    if saved_key:
        os.environ['ANTHROPIC_API_KEY'] = saved_key

    # --- draft_detector: rejected LLM output is saved as .rejected, not as a live draft ---
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-not-real'
    with __import__('tempfile').TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            src_dir = Path(tmpdir) / 'src'
            src_dir.mkdir()
            (src_dir / 'main.go').write_text('package main\n', encoding='utf-8')

            class _MockContent:
                def __init__(self, text):
                    self.text = text

            class _MockResponse:
                def __init__(self, text):
                    self.content = [_MockContent(text)]
                    from types import SimpleNamespace
                    self.usage = SimpleNamespace(input_tokens=10, output_tokens=5)

            class _MockMessages:
                def create(self, **kwargs):  # noqa: ARG002
                    return _MockResponse("not even valid python (")

            class _MockClient:
                def __init__(self):
                    self.messages = _MockMessages()

            real_get_client = sys.modules[__name__]._get_client
            sys.modules[__name__]._get_client = lambda: _MockClient()  # type: ignore[attr-defined]
            try:
                result2 = draft_detector('web-api', 'gin', str(src_dir))
            finally:
                sys.modules[__name__]._get_client = real_get_client  # type: ignore[attr-defined]

            assert result2.ok is False
            assert result2.reason is not None
            assert 'validation' in result2.reason
            # _DRAFTS_DIR is anchored to this module's real location, not cwd — by
            # design (drafts always land in the real adapters dir, not wherever the
            # caller happened to chdir to). So this test writes into the real repo
            # tree and MUST clean up after itself, unlike the chdir'd cwd sandbox
            # used for the rest of this block.
            rejected = _DRAFTS_DIR / 'gin_detector_draft.py.rejected'
            assert rejected.exists()
            assert not (_DRAFTS_DIR / 'gin_detector_draft.py').exists()
        finally:
            os.chdir(cwd)
            rejected = _DRAFTS_DIR / 'gin_detector_draft.py.rejected'
            if rejected.exists():
                rejected.unlink()
    if saved_key:
        os.environ['ANTHROPIC_API_KEY'] = saved_key
    else:
        os.environ.pop('ANTHROPIC_API_KEY', None)

    print("[OK] detector_draft self-test passed")
    sys.exit(0)

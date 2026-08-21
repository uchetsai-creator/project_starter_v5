"""
semantic.py — SemanticAdapter: LLM-assisted field matching on top of any structural adapter.

Wraps any FrameworkAdapter. extract_spec() and extract_code() delegate to the wrapped adapter.
semantic_compare() takes the structural diff report and escalates ambiguous field pairs to
Claude, returning { verdict, reasoning } per pair.

Usage via verify_spec_code.py:
    python3 verify_spec_code.py --adapter fastapi --semantic \\
        --spec docs/specs/api-contract.md --src src/ --project-type web-app

Constraint: --semantic must never appear in workflow-registry.yaml or pre-commit sequences.
It is a developer analysis tool, not an automated gate.

Requires: ANTHROPIC_API_KEY env var and the 'anthropic' package (pip install anthropic).

Token management: this is the only place in the framework that makes a live LLM call, so it
is also the only place that can measure real (not estimated) token usage. Each call's actual
`response.usage` is accumulated on the adapter instance, checked against an optional budget
(SPEC_CODE_TOKEN_BUDGET) before every call, and written to
logs/telemetry/token-usage.json after semantic_compare() finishes — also dual-emitted as an
OTel span ("semantic_token_usage") via _otel.py, same opt-in pattern as the rest of the
framework's telemetry. See README.md -> Validation Telemetry -> Token usage for the schema
and env vars.

Run self-test:
    python3 semantic.py   # exits 0 on success; does not call the LLM
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_VALIDATORS_DIR = Path(__file__).resolve().parent.parent  # templates/script/validators/

# Read model from env var; fall back to Haiku for lowest-cost classification
_SEMANTIC_MODEL = os.environ.get('SPEC_CODE_MODEL', 'claude-haiku-4-5-20251001')

# USD per 1M tokens, approximate — verify against https://www.anthropic.com/pricing before
# relying on this for real budgeting decisions; prices change over time and this table is not
# fetched live. Override per-deployment with SPEC_CODE_PRICE_INPUT_PER_M / _OUTPUT_PER_M if the
# model in use isn't listed or the published price has moved.
_PRICING_PER_M_TOKENS = {
    'claude-haiku-4-5-20251001': {'input': 1.00, 'output': 5.00},
    'claude-sonnet-4-6': {'input': 3.00, 'output': 15.00},
    'claude-opus-4-7': {'input': 15.00, 'output': 75.00},
}


class SemanticAdapter:
    """Experimental — requires Anthropic API key (set ANTHROPIC_API_KEY).

    Wraps any FrameworkAdapter and adds an LLM-assisted comparison pass for
    ambiguous field-name pairs that the structural adapter cannot resolve.

    extract_spec() and extract_code() delegate to the wrapped adapter unchanged.
    semantic_compare() escalates ambiguous removed/added field pairs to Claude,
    returning { verdict, reasoning } per pair.

    Verdict values:
        likely_same — different name, same concept; flag as WARNING
        different   — genuinely different fields; MISMATCH confirmed
        uncertain   — LLM could not determine; flag for human review

    Constraint: never use in automated sequences (pre-commit, workflow-registry).
    """

    def __init__(self, wraps) -> None:
        self._inner = wraps
        budget_env = os.environ.get('SPEC_CODE_TOKEN_BUDGET')
        self.token_usage: dict = {
            'model': _SEMANTIC_MODEL,
            'calls': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'estimated_cost_usd': None,
            'budget_tokens': int(budget_env) if budget_env else None,
            'budget_exceeded': False,
        }

    # -----------------------------------------------------------------------
    # FrameworkAdapter interface (delegated)
    # -----------------------------------------------------------------------

    def extract_spec(self, spec_path: str) -> list:
        return self._inner.extract_spec(spec_path)

    def extract_code(self, src_path: str) -> list:
        return self._inner.extract_code(src_path)

    # -----------------------------------------------------------------------
    # Semantic pass
    # -----------------------------------------------------------------------

    def semantic_compare(
        self,
        structural_report: dict,
    ) -> list[dict]:
        """
        Escalate ambiguous field pairs from the structural report to Claude.

        An ambiguous pair: one removed_from_code field and one added_in_code
        field within the same item. The structural pass already flagged both;
        the LLM decides if they are the same concept renamed.

        Returns:
            List of semantic verdicts:
            {
                item: str,
                spec_field: str, spec_type: str,
                code_field: str, code_type: str,
                verdict: 'likely_same' | 'different' | 'uncertain',
                reasoning: str,
            }
        """
        client = _get_client()
        if client is None:
            return []

        if not os.environ.get('ANTHROPIC_API_KEY'):
            print(
                "[WARN] --semantic requires ANTHROPIC_API_KEY — skipping LLM pass.\n"
                "    Set the env var and re-run to get semantic verdicts.",
            )
            return []

        by_item: dict[str, dict[str, list]] = {}
        for m in structural_report.get('field_mismatches', []):
            item = m['item']
            if item not in by_item:
                by_item[item] = {'removed': [], 'added': []}
            if m['issue'] == 'removed_from_code':
                by_item[item]['removed'].append(m)
            elif m['issue'] == 'added_in_code':
                by_item[item]['added'].append(m)

        verdicts: list[dict] = []
        for item_label, groups in by_item.items():
            if not groups['removed'] or not groups['added']:
                continue

            budget = self.token_usage['budget_tokens']
            spent = self.token_usage['input_tokens'] + self.token_usage['output_tokens']
            if budget is not None and spent >= budget:
                if not self.token_usage['budget_exceeded']:
                    print(
                        f"[WARN] --semantic token budget ({budget}) reached after "
                        f"{self.token_usage['calls']} call(s) — skipping remaining items.",
                    )
                self.token_usage['budget_exceeded'] = True
                break

            pairs = _build_pairs(groups['removed'], groups['added'])
            item_verdicts, usage = _ask_llm(client, item_label, pairs)
            verdicts.extend(item_verdicts)
            self._record_usage(usage)

        _write_token_usage_telemetry(self.token_usage)
        return verdicts

    def _record_usage(self, usage: dict) -> None:
        if not usage:
            return
        self.token_usage['calls'] += 1
        self.token_usage['input_tokens'] += usage.get('input_tokens', 0)
        self.token_usage['output_tokens'] += usage.get('output_tokens', 0)
        cost = _estimate_cost(
            self.token_usage['model'],
            self.token_usage['input_tokens'],
            self.token_usage['output_tokens'],
        )
        self.token_usage['estimated_cost_usd'] = cost


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client():
    """Return an Anthropic client, or None with a warning if unavailable."""
    try:
        import anthropic  # noqa: PLC0415
        return anthropic.Anthropic()
    except ImportError:
        print(
            "[WARN] --semantic requires the 'anthropic' package.\n"
            "    Install it with: pip install anthropic",
        )
        return None


def _build_pairs(removed: list[dict], added: list[dict]) -> list[dict]:
    """Cross-pair every removed spec field with every added code field."""
    return [
        {
            'spec_field': r['field'],
            'spec_type': r['spec_type'] or '',
            'code_field': a['field'],
            'code_type': a['code_type'] or '',
        }
        for r in removed
        for a in added
    ]


def _ask_llm(client, item_label: str, pairs: list[dict]) -> tuple[list[dict], dict]:
    """Send field-name pairs to Claude and parse verdicts from the response.

    Returns (verdicts, usage) — usage is {} on failure so the caller never accounts
    for tokens on a call that didn't actually happen.
    """
    pairs_text = '\n'.join(
        f"  - spec: {p['spec_field']}: {p['spec_type'] or '(no type)'}  "
        f"vs  code: {p['code_field']}: {p['code_type'] or '(no type)'}"
        for p in pairs
    )
    prompt = (
        f"You are a spec-to-code drift analyst. For the item '{item_label}', "
        "the structural validator flagged these field name differences:\n\n"
        f"{pairs_text}\n\n"
        "For each pair, decide if the spec field and code field represent the "
        "SAME concept (renamed/refactored) or DIFFERENT concepts.\n\n"
        "Respond with a JSON array, one object per pair, in the same order:\n"
        "[\n"
        "  {\n"
        '    "spec_field": "<name>",\n'
        '    "code_field": "<name>",\n'
        '    "verdict": "likely_same" | "different" | "uncertain",\n'
        '    "reasoning": "<one sentence>"\n'
        "  }\n"
        "]\n\n"
        "Return only valid JSON — no markdown fences, no extra text."
    )

    try:
        response = client.messages.create(
            model=_SEMANTIC_MODEL,
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}],
        )
        raw = response.content[0].text.strip()
        llm_results = json.loads(raw)
        usage = {
            'input_tokens': getattr(response.usage, 'input_tokens', 0),
            'output_tokens': getattr(response.usage, 'output_tokens', 0),
        }
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Semantic LLM call failed for '{item_label}': {exc}")
        return [], {}

    verdicts = []
    for i, lr in enumerate(llm_results):
        if i >= len(pairs):
            break
        p = pairs[i]
        verdicts.append({
            'item': item_label,
            'spec_field': p['spec_field'],
            'spec_type': p['spec_type'],
            'code_field': p['code_field'],
            'code_type': p['code_type'],
            'verdict': lr.get('verdict', 'uncertain'),
            'reasoning': lr.get('reasoning', ''),
        })
    return verdicts, usage


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Return an estimated USD cost for accumulated usage, or None if the model's
    price isn't known and no override env vars are set."""
    override_in = os.environ.get('SPEC_CODE_PRICE_INPUT_PER_M')
    override_out = os.environ.get('SPEC_CODE_PRICE_OUTPUT_PER_M')
    if override_in and override_out:
        price = {'input': float(override_in), 'output': float(override_out)}
    else:
        price = _PRICING_PER_M_TOKENS.get(model)
    if price is None:
        return None
    return round(
        (input_tokens / 1_000_000) * price['input']
        + (output_tokens / 1_000_000) * price['output'],
        6,
    )


def _write_token_usage_telemetry(token_usage: dict) -> None:
    """Append one row to logs/telemetry/token-usage.json — best-effort, never
    raises, mirroring the other telemetry writers in adapters/claude/.

    Also dual-emits an OTel span (see _otel.py), the same opt-in pattern used by
    orchestrator.py and _verify_common._append_telemetry: a no-op unless both
    opentelemetry-* is installed and OTEL_EXPORTER_OTLP_ENDPOINT is set.
    """
    if token_usage['calls'] == 0:
        return
    entry = {
        'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        **token_usage,
    }
    try:
        output = os.path.join('logs', 'telemetry', 'token-usage.json')
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
        _otel_emit('semantic_token_usage', entry)
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Self-test (no LLM call — tests pairing and delegation logic only)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # --- test _build_pairs ---
    removed = [{'field': 'order_id', 'spec_type': 'string', 'issue': 'removed_from_code'}]
    added   = [{'field': 'id',       'code_type': 'int',    'issue': 'added_in_code'}]
    pairs = _build_pairs(removed, added)
    assert len(pairs) == 1
    assert pairs[0]['spec_field'] == 'order_id'
    assert pairs[0]['code_field'] == 'id'
    assert pairs[0]['spec_type'] == 'string'
    assert pairs[0]['code_type'] == 'int'

    # --- test cross-pairing (2 removed × 2 added = 4 pairs) ---
    removed2 = [
        {'field': 'order_id',    'spec_type': 'string', 'issue': 'removed_from_code'},
        {'field': 'order_total', 'spec_type': 'float',  'issue': 'removed_from_code'},
    ]
    added2 = [
        {'field': 'id',    'code_type': 'int',     'issue': 'added_in_code'},
        {'field': 'price', 'code_type': 'Decimal', 'issue': 'added_in_code'},
    ]
    pairs2 = _build_pairs(removed2, added2)
    assert len(pairs2) == 4

    # --- test SemanticAdapter delegation ---
    class _MockInner:
        def extract_spec(self, path):  # noqa: ARG002
            return ['spec_result']
        def extract_code(self, path):  # noqa: ARG002
            return ['code_result']

    adapter = SemanticAdapter(wraps=_MockInner())
    assert adapter.extract_spec('any') == ['spec_result']
    assert adapter.extract_code('any') == ['code_result']

    # --- test semantic_compare: no API key → [] (warning printed) ---
    saved_key = os.environ.pop('ANTHROPIC_API_KEY', None)
    report = {
        'field_mismatches': [
            {'item': 'POST /orders', 'field': 'order_id', 'issue': 'removed_from_code',
             'spec_type': 'string', 'code_type': None},
            {'item': 'POST /orders', 'field': 'id', 'issue': 'added_in_code',
             'spec_type': None, 'code_type': 'int'},
        ],
        'missing_in_code': [],
        'extra_in_code': [],
    }
    result = adapter.semantic_compare(report)
    assert result == []
    assert adapter.token_usage['calls'] == 0

    # --- test _estimate_cost: known model computes a real number ---
    cost = _estimate_cost('claude-haiku-4-5-20251001', 1_000_000, 1_000_000)
    assert cost == 6.00  # $1 in + $5 out per README pricing table
    assert _estimate_cost('some-unknown-model', 100, 100) is None

    # --- test _estimate_cost: price override env vars win over an unknown model ---
    os.environ['SPEC_CODE_PRICE_INPUT_PER_M'] = '2'
    os.environ['SPEC_CODE_PRICE_OUTPUT_PER_M'] = '10'
    assert _estimate_cost('some-unknown-model', 1_000_000, 1_000_000) == 12.00
    del os.environ['SPEC_CODE_PRICE_INPUT_PER_M']
    del os.environ['SPEC_CODE_PRICE_OUTPUT_PER_M']

    # --- test real usage accounting + budget cap via a mocked Anthropic client ---
    import tempfile
    from types import SimpleNamespace

    class _MockContent:
        def __init__(self, text):
            self.text = text

    class _MockResponse:
        def __init__(self, text, in_tok, out_tok):
            self.content = [_MockContent(text)]
            self.usage = SimpleNamespace(input_tokens=in_tok, output_tokens=out_tok)

    class _MockMessages:
        def __init__(self, in_tok, out_tok):
            self._in_tok = in_tok
            self._out_tok = out_tok
            self.calls = 0

        def create(self, **kwargs):  # noqa: ARG002
            self.calls += 1
            verdict_json = json.dumps([
                {'spec_field': 'x', 'code_field': 'y', 'verdict': 'likely_same', 'reasoning': 'r'},
            ])
            return _MockResponse(verdict_json, self._in_tok, self._out_tok)

    class _MockClient:
        def __init__(self, in_tok=100, out_tok=50):
            self.messages = _MockMessages(in_tok, out_tok)

    two_item_report = {
        'field_mismatches': [
            {'item': 'A', 'field': 'a1', 'issue': 'removed_from_code', 'spec_type': 's', 'code_type': None},
            {'item': 'A', 'field': 'a2', 'issue': 'added_in_code', 'spec_type': None, 'code_type': 'c'},
            {'item': 'B', 'field': 'b1', 'issue': 'removed_from_code', 'spec_type': 's', 'code_type': None},
            {'item': 'B', 'field': 'b2', 'issue': 'added_in_code', 'spec_type': None, 'code_type': 'c'},
        ],
        'missing_in_code': [],
        'extra_in_code': [],
    }
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-not-real'
    _real_get_client = sys.modules[__name__]._get_client

    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            mock_client = _MockClient(in_tok=100, out_tok=50)
            adapter2 = SemanticAdapter(wraps=_MockInner())
            sys.modules[__name__]._get_client = lambda: mock_client
            try:
                verdicts2 = adapter2.semantic_compare(two_item_report)
            finally:
                sys.modules[__name__]._get_client = _real_get_client

            assert len(verdicts2) == 2  # one verdict per item, 2 items
            assert adapter2.token_usage['calls'] == 2
            assert adapter2.token_usage['input_tokens'] == 200
            assert adapter2.token_usage['output_tokens'] == 100
            assert adapter2.token_usage['estimated_cost_usd'] == round(
                (200 / 1_000_000) * 1.00 + (100 / 1_000_000) * 5.00, 6,
            )
            assert os.path.exists('logs/telemetry/token-usage.json')
            with open('logs/telemetry/token-usage.json', encoding='utf-8') as f:
                rows = json.load(f)
            assert len(rows) == 1
            assert rows[0]['calls'] == 2

            # --- test budget cap: 1 call's worth of tokens as budget → stop after item 1 ---
            os.environ['SPEC_CODE_TOKEN_BUDGET'] = '150'
            mock_client2 = _MockClient(in_tok=100, out_tok=50)
            adapter3 = SemanticAdapter(wraps=_MockInner())
            sys.modules[__name__]._get_client = lambda: mock_client2
            try:
                verdicts3 = adapter3.semantic_compare(two_item_report)
            finally:
                sys.modules[__name__]._get_client = _real_get_client
                del os.environ['SPEC_CODE_TOKEN_BUDGET']

            assert adapter3.token_usage['calls'] == 1  # second item skipped by budget
            assert adapter3.token_usage['budget_exceeded'] is True
            assert len(verdicts3) == 1
        finally:
            os.chdir(cwd)

    if saved_key:
        os.environ['ANTHROPIC_API_KEY'] = saved_key
    else:
        os.environ.pop('ANTHROPIC_API_KEY', None)

    print("[OK] semantic self-test passed")
    sys.exit(0)

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

Run self-test:
    python3 semantic.py   # exits 0 on success; does not call the LLM
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Read model from env var; fall back to Haiku for lowest-cost classification
_SEMANTIC_MODEL = os.environ.get('SPEC_CODE_MODEL', 'claude-haiku-4-5-20251001')


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
                "⚠️   --semantic requires ANTHROPIC_API_KEY — skipping LLM pass.\n"
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
            pairs = _build_pairs(groups['removed'], groups['added'])
            verdicts.extend(_ask_llm(client, item_label, pairs))

        return verdicts


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
            "⚠️   --semantic requires the 'anthropic' package.\n"
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


def _ask_llm(client, item_label: str, pairs: list[dict]) -> list[dict]:
    """Send field-name pairs to Claude and parse verdicts from the response."""
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
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️   Semantic LLM call failed for '{item_label}': {exc}")
        return []

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
    return verdicts


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
    result = adapter.semantic_compare(report, [], [])
    assert result == []
    if saved_key:
        os.environ['ANTHROPIC_API_KEY'] = saved_key

    print("✅  semantic self-test passed")
    sys.exit(0)

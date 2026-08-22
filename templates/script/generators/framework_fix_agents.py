#!/usr/bin/env python3
"""
framework_fix_agents.py — two-agent LLM pipeline that drafts real template guidance for
propose_framework_fix.py, instead of its default placeholder comment block.

Draft agent -> Review agent -> propose_framework_fix.py's existing git/PR mechanics.
Opt-in via --ai-draft on propose_framework_fix.py / diagnose_spec.py; the default stays
today's placeholder text with zero LLM calls, unchanged.

Constraint: like semantic.py and llm_security_review.py, never wire --ai-draft into any
automated sequence (workflow-registry.yaml, pre-commit, a cron). It makes real LLM
calls and its output is non-deterministic — developer-invoked only.

Requires ANTHROPIC_API_KEY. Missing key -> [WARN] and the caller falls back to the
placeholder, same graceful-degradation pattern as semantic.py's client-unavailable path.

Two agents, not one, because drafting and reviewing are different jobs with different
failure modes: the draft agent's job is to write something useful; the review agent's
job is to be skeptical of it. Collapsing both into a single call means the same context
that produced a weak draft also grades it — a fresh pass whose entire prompt is "find
problems with this" catches more than a self-review in the same turn, the same reason a
second reviewer catches things the author misses. Review criteria are this framework's
own prose bar, not a novel judgment call invented for this module: the same vague-wording
and placeholder-language patterns verify_prose.py's Vale rules (WeaselWords,
NaturalLanguagePlaceholders) already enforce on real docs, restated for an LLM pass since
Vale itself only runs against files already on disk, not a draft still in memory.

Token/cost accounting: same shape as semantic.py. Every call's response.usage is
accumulated, checked against an optional FRAMEWORK_FIX_TOKEN_BUDGET before the review
call fires, and written to logs/telemetry/framework-fix-agents-usage.json.

Run self-test:
    python3 framework_fix_agents.py   # exits 0 on success; does not call the LLM
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Read model from env var; default to Sonnet — this module writes prose a reader will
# actually rely on (template guidance other developers follow), unlike semantic.py's
# terse same/different verdicts, so the default trades semantic.py's Haiku-first cost
# floor for better writing quality. Override with FRAMEWORK_FIX_MODEL for either agent.
_MODEL = os.environ.get('FRAMEWORK_FIX_MODEL', 'claude-sonnet-4-6')

# USD per 1M tokens, approximate — verify against https://www.anthropic.com/pricing before
# relying on this for real budgeting. Duplicated from semantic.py's table rather than
# imported: templates/script/generators/ and templates/script/validators/ are independent
# sys.path roots (see each script's own sys.path.insert), and this table is small, stable
# data — not worth a cross-package import for three dict literals.
_PRICING_PER_M_TOKENS = {
    'claude-haiku-4-5-20251001': {'input': 1.00, 'output': 5.00},
    'claude-sonnet-4-6': {'input': 3.00, 'output': 15.00},
    'claude-opus-4-7': {'input': 15.00, 'output': 75.00},
}

# The same two prose-quality failure modes verify_prose.py's Vale rules catch in real
# docs (_prose_style/styles/Custom/WeaselWords.yml, NaturalLanguagePlaceholders.yml),
# restated as review-agent instructions rather than duplicated as a second regex pass —
# an LLM reviewer judging "is this actually useful guidance" is a semantic question Vale
# doesn't attempt; the vague-wording examples below just point it at the same failure
# modes Vale already has names for, so the two checks agree on what "bad prose" means.
_REVIEW_CRITERIA = """\
Reject the draft if any of these apply:
1. It restates the section heading without adding real guidance (a placeholder in
   substance even if not in the literal "TODO"/"TBD" sense).
2. It leans on vague qualifiers instead of concrete guidance — "very", "obviously",
   "simply", "just", "basically", or similar hand-waving in place of an actual
   explanation.
3. It contradicts a widely-known convention for the stated project type without
   acknowledging the contradiction.
4. It is not concrete enough for a developer to act on without asking a follow-up
   question.

Approve otherwise, even if the writing could be marginally better — this is a
placeholder-vs-real-guidance bar, not a copy-editing pass."""


class TokenUsage:
    def __init__(self) -> None:
        self.model = _MODEL
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.budget_tokens = int(os.environ['FRAMEWORK_FIX_TOKEN_BUDGET']) \
            if os.environ.get('FRAMEWORK_FIX_TOKEN_BUDGET') else None
        self.budget_exceeded = False

    def record(self, usage: dict) -> None:
        if not usage:
            return
        self.calls += 1
        self.input_tokens += usage.get('input_tokens', 0)
        self.output_tokens += usage.get('output_tokens', 0)

    def over_budget(self) -> bool:
        if self.budget_tokens is None:
            return False
        spent = self.input_tokens + self.output_tokens
        if spent >= self.budget_tokens:
            self.budget_exceeded = True
        return self.budget_exceeded

    def estimated_cost_usd(self) -> float | None:
        price = _PRICING_PER_M_TOKENS.get(self.model)
        if price is None:
            return None
        return round(
            (self.input_tokens / 1_000_000) * price['input']
            + (self.output_tokens / 1_000_000) * price['output'],
            6,
        )

    def as_dict(self) -> dict:
        return {
            'model': self.model,
            'calls': self.calls,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'estimated_cost_usd': self.estimated_cost_usd(),
            'budget_tokens': self.budget_tokens,
            'budget_exceeded': self.budget_exceeded,
        }


def _get_client():
    """Return an Anthropic client, or None with a warning if unavailable. Same shape
    as semantic.py's _get_client() — kept independent rather than imported for the same
    cross-package reason as the pricing table above."""
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print(
            "[WARN] --ai-draft requires ANTHROPIC_API_KEY — falling back to the "
            "placeholder template text.",
        )
        return None
    try:
        import anthropic  # noqa: PLC0415
        return anthropic.Anthropic()
    except ImportError:
        print(
            "[WARN] --ai-draft requires the 'anthropic' package.\n"
            "    Install it with: pip install anthropic",
        )
        return None


def draft_fix(
    client,
    project_type: str,
    document: str,
    gap_description: str,
    template_context: str,
    usage: TokenUsage,
) -> str | None:
    """Ask Claude to draft real guidance prose for a missing template section.

    template_context is the template file's existing content, truncated to a few KB —
    included so the draft matches the surrounding doc's structure and tone instead of
    reading as generic advice bolted onto an unfamiliar file. Returns None on any
    failure (missing client, API error, empty response) — never raises."""
    if client is None:
        return None

    prompt = (
        f"You are drafting a new '## {gap_description}' section for a documentation "
        f"template used by {project_type} projects. This template file is "
        f"'{document}' — it ships blank inside project_starter_v5 and gets filled in "
        f"per-project later, so write it as guidance TO the person filling it in, not "
        f"as filled-in content itself (no fabricated project specifics).\n\n"
        f"Existing template content, for style and structure reference:\n"
        f"---\n{template_context[:4000]}\n---\n\n"
        f"Write only the new section body (no heading — that gets added separately), "
        f"2-5 sentences or a short bullet list. Concrete and actionable, no vague "
        f"qualifiers, no restating the section name as if that were the content."
    )
    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=512,
            messages=[{'role': 'user', 'content': prompt}],
        )
        text = response.content[0].text.strip()
        usage.record({
            'input_tokens': getattr(response.usage, 'input_tokens', 0),
            'output_tokens': getattr(response.usage, 'output_tokens', 0),
        })
        return text or None
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] draft agent call failed: {exc}")
        return None


def review_fix(
    client,
    draft_text: str,
    gap_description: str,
    usage: TokenUsage,
) -> tuple[str, str]:
    """Ask Claude to review the draft against this framework's own prose-quality bar.

    Returns (verdict, reasoning) — verdict is 'approve' or 'reject'. On any failure
    (missing client, API error, unparsable response), returns ('reject', <reason>) —
    fail closed: an unreviewable draft is treated as not approved, never silently let
    through."""
    if client is None:
        return 'reject', 'review agent unavailable (no client)'

    prompt = (
        f"You are reviewing a drafted documentation section titled "
        f"'{gap_description}' before it goes into a pull request.\n\n"
        f"Draft:\n---\n{draft_text}\n---\n\n"
        f"{_REVIEW_CRITERIA}\n\n"
        f"Respond with only a JSON object: "
        f'{{"verdict": "approve" | "reject", "reasoning": "<one sentence>"}}'
    )
    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=256,
            messages=[{'role': 'user', 'content': prompt}],
        )
        raw = response.content[0].text.strip()
        usage.record({
            'input_tokens': getattr(response.usage, 'input_tokens', 0),
            'output_tokens': getattr(response.usage, 'output_tokens', 0),
        })
        parsed = json.loads(raw)
        verdict = parsed.get('verdict')
        if verdict not in ('approve', 'reject'):
            return 'reject', f'review agent returned an unrecognized verdict: {verdict!r}'
        return verdict, parsed.get('reasoning', '')
    except Exception as exc:  # noqa: BLE001
        return 'reject', f'review agent call failed: {exc}'


def run_ai_draft_pipeline(
    project_type: str,
    document: str,
    gap_description: str,
    template_context: str,
) -> dict:
    """Orchestrate draft -> review. Returns:
      {
        approved: bool,
        text: str | None,       # only set when approved
        review_reasoning: str,
        usage: dict,            # TokenUsage.as_dict()
      }
    Never raises — every failure mode (no API key, draft failed, budget exceeded,
    review rejected) resolves to approved=False so the caller falls back to the
    placeholder rather than propagating an exception into the PR-opening flow."""
    usage = TokenUsage()
    client = _get_client()

    draft = draft_fix(client, project_type, document, gap_description, template_context, usage)
    if draft is None:
        _write_telemetry(usage)
        return {'approved': False, 'text': None, 'review_reasoning': 'draft agent produced no text', 'usage': usage.as_dict()}

    if usage.over_budget():
        print(
            f"[WARN] --ai-draft token budget ({usage.budget_tokens}) reached after the "
            f"draft call — skipping review, falling back to the placeholder.",
        )
        _write_telemetry(usage)
        return {'approved': False, 'text': None, 'review_reasoning': 'token budget exceeded before review', 'usage': usage.as_dict()}

    verdict, reasoning = review_fix(client, draft, gap_description, usage)
    _write_telemetry(usage)

    if verdict != 'approve':
        return {'approved': False, 'text': None, 'review_reasoning': reasoning, 'usage': usage.as_dict()}
    return {'approved': True, 'text': draft, 'review_reasoning': reasoning, 'usage': usage.as_dict()}


def _write_telemetry(usage: TokenUsage) -> None:
    """Append one row to logs/telemetry/framework-fix-agents-usage.json — best-effort,
    never raises, mirroring semantic.py's _write_token_usage_telemetry."""
    if usage.calls == 0:
        return
    entry = {'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), **usage.as_dict()}
    try:
        output = os.path.join('logs', 'telemetry', 'framework-fix-agents-usage.json')
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
        print(f"[WARN] failed to write framework-fix-agents telemetry: {exc}")

    try:
        validators_dir = str(Path(__file__).resolve().parent.parent / 'validators')
        if validators_dir not in sys.path:
            sys.path.insert(0, validators_dir)
        from _otel import emit as _otel_emit  # noqa: PLC0415
        _otel_emit('framework_fix_agents_usage', entry)
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Self-test (mocked client for every path, including "success" — never touches the
# network, mirrors semantic.py's self-test pattern)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import tempfile
    from types import SimpleNamespace

    class _MockContent:
        def __init__(self, text):
            self.text = text

    class _MockResponse:
        def __init__(self, text, in_tok=100, out_tok=50):
            self.content = [_MockContent(text)]
            self.usage = SimpleNamespace(input_tokens=in_tok, output_tokens=out_tok)

    class _MockMessages:
        def __init__(self, responses):
            self._responses = list(responses)
            self.calls = 0

        def create(self, **kwargs):  # noqa: ARG002
            self.calls += 1
            return self._responses.pop(0)

    class _MockClient:
        def __init__(self, responses):
            self.messages = _MockMessages(responses)

    # --- test: no ANTHROPIC_API_KEY -> _get_client returns None ---
    saved_key = os.environ.pop('ANTHROPIC_API_KEY', None)
    assert _get_client() is None
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-not-real'

    # --- test: draft_fix with a mock client returns the drafted text and records usage ---
    u = TokenUsage()
    mock_client = _MockClient([_MockResponse('Concrete guidance text.', 200, 80)])
    draft = draft_fix(mock_client, 'web-app', 'specs/research.md', 'Error Handling', '# existing template', u)
    assert draft == 'Concrete guidance text.'
    assert u.calls == 1
    assert u.input_tokens == 200
    assert u.output_tokens == 80

    # --- test: review_fix approve path ---
    u2 = TokenUsage()
    approve_response = _MockResponse(json.dumps({'verdict': 'approve', 'reasoning': 'concrete and actionable'}))
    mock_client2 = _MockClient([approve_response])
    verdict, reasoning = review_fix(mock_client2, 'Concrete guidance text.', 'Error Handling', u2)
    assert verdict == 'approve'
    assert reasoning == 'concrete and actionable'
    assert u2.calls == 1

    # --- test: review_fix reject path ---
    u3 = TokenUsage()
    reject_response = _MockResponse(json.dumps({'verdict': 'reject', 'reasoning': 'just restates the heading'}))
    mock_client3 = _MockClient([reject_response])
    verdict3, reasoning3 = review_fix(mock_client3, 'Error Handling.', 'Error Handling', u3)
    assert verdict3 == 'reject'

    # --- test: review_fix fails closed on a malformed response ---
    u4 = TokenUsage()
    bad_response = _MockResponse('not json at all')
    mock_client4 = _MockClient([bad_response])
    verdict4, reasoning4 = review_fix(mock_client4, 'text', 'Error Handling', u4)
    assert verdict4 == 'reject'

    # --- test: full pipeline, draft approved ---
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            responses = [
                _MockResponse('Concrete, specific guidance for this section.', 150, 60),
                _MockResponse(json.dumps({'verdict': 'approve', 'reasoning': 'good'}), 80, 20),
            ]
            call_log: list[str] = []

            def _fake_get_client():
                call_log.append('called')
                return _MockClient(responses)

            real_get_client = sys.modules[__name__]._get_client
            sys.modules[__name__]._get_client = _fake_get_client  # type: ignore[attr-defined]
            try:
                result = run_ai_draft_pipeline('web-app', 'specs/research.md', 'Error Handling', '# template')
            finally:
                sys.modules[__name__]._get_client = real_get_client  # type: ignore[attr-defined]

            assert result['approved'] is True
            assert result['text'] == 'Concrete, specific guidance for this section.'
            assert result['usage']['calls'] == 2
            assert os.path.exists('logs/telemetry/framework-fix-agents-usage.json')
            with open('logs/telemetry/framework-fix-agents-usage.json', encoding='utf-8') as f:
                rows = json.load(f)
            assert len(rows) == 1
            assert rows[0]['calls'] == 2
        finally:
            os.chdir(cwd)

    # --- test: full pipeline, review rejects -> approved=False, no text ---
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            responses = [
                _MockResponse('Weak draft that just restates the heading.', 150, 60),
                _MockResponse(json.dumps({'verdict': 'reject', 'reasoning': 'restates heading'}), 80, 20),
            ]

            def _fake_get_client2():
                return _MockClient(responses)

            real_get_client = sys.modules[__name__]._get_client
            sys.modules[__name__]._get_client = _fake_get_client2  # type: ignore[attr-defined]
            try:
                result2 = run_ai_draft_pipeline('web-app', 'specs/research.md', 'Error Handling', '# template')
            finally:
                sys.modules[__name__]._get_client = real_get_client  # type: ignore[attr-defined]

            assert result2['approved'] is False
            assert result2['text'] is None
            assert result2['review_reasoning'] == 'restates heading'
        finally:
            os.chdir(cwd)

    if saved_key:
        os.environ['ANTHROPIC_API_KEY'] = saved_key
    else:
        os.environ.pop('ANTHROPIC_API_KEY', None)

    print("[OK] framework_fix_agents self-test passed")
    sys.exit(0)

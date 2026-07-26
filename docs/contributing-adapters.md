# Contributing a Framework Adapter

`verify_spec_code.py` catches spec-code drift by comparing a spec document against real source
code. It never has framework-specific knowledge itself — that logic lives entirely in
**capability adapters** and **detectors**. This guide tells you exactly what to build when your
framework, language, or tool isn't covered yet.

---

## Two-layer architecture (Phase 52.5)

```
verify_spec_code.py
        │  --adapter <name> [--framework <hint>]
        ▼
Capability Adapter            (one per project type — 7 total)
  │  extract_spec()  — parses the shared spec format for this project type
  │  extract_code()  — discovers source files, dispatches to detector(s)
  ├── Framework Detector A    (e.g. FastAPIDetector)
  ├── Framework Detector B    (e.g. FlaskDetector)
  └── Framework Detector C    (e.g. ExpressDetector)
              │
              ▼
      NormalizedForm objects → compared by verify_spec_code.py
```

- **Capability adapter** — owns the spec format for a whole project type (Web App, CLI Tool,
  Data Pipeline, etc.) and discovers source files. All web-API frameworks, for example, share
  the same `api-contract.md` format, so `WebAPIAdapter` parses it once for all of them.
- **Detector** — the only framework-specific piece. Receives a pre-discovered file list from its
  capability adapter and returns `NormalizedForm` objects. **Does not** touch the filesystem or
  parse the spec.

**The 7 existing capability adapters and what they currently detect:**

| Capability (`--adapter`) | File | Detectors registered today |
|---|---|---|
| `web-api` | `_capability_web_api.py` | `fastapi`, `flask`, `django` (Python), `express` (Node.js) |
| `cli` | `_capability_cli.py` | `click` (Python) |
| `data-pipeline` | `_capability_pipeline.py` | `airflow`, `dagster`, `prefect` (Python) |
| `library` | `_capability_library.py` | `python_library` |
| `llm-app` | `_capability_llm.py` | `tool_schema` (Python functions / OpenAI JSON schema) |
| `iac` | `_capability_iac.py` | `terraform` (HCL), `pulumi` (Python) |
| `mobile` | `_capability_mobile.py` | `react_native` (TSX/JSX), `flutter` (Dart) |

If your tool isn't in the right-hand column, you're in one of two situations:

---

## Situation A — Your tool fits an existing capability (common case)

Example: you use **NestJS**, **Gin** (Go), or **Spring Boot** — all Web App /
Microservices frameworks, same `api-contract.md` format, just not detected yet.
(Django used to be this repo's own example of an undetected framework — it now has a real
detector; see the worked example after Step A5.)
Same idea for **argparse/Typer** (CLI Tool), **Luigi/Kubeflow** (Data Pipeline),
**LangChain tools** (LLM App), **CloudFormation/Ansible/Helm** (IaC), **native iOS/Android**
(Mobile), or a **non-Python library** (Library/SDK).

**You only need to add a Detector — do not create a new file-per-framework adapter, and do not
touch `extract_spec()`.**

### Step A1 — Confirm the NormalizedForm you're producing

| Project type | NormalizedForm | Comparison key |
|---|---|---|
| Web App / Microservices | `NormalizedEndpoint` | `f"{method.upper()}:{path}"` |
| CLI Tool | `NormalizedCommand` | subcommand `name` |
| Data Pipeline / ML Pipeline | `NormalizedStageContract` | `stage_name` |
| Library / SDK | `NormalizedFunction` | function `name` |
| AI / LLM App | `NormalizedTool` | tool `name` |
| IaC / DevOps | `NormalizedResource` | resource `name` |
| Mobile App | `NormalizedScreen` | screen `name` |

All defined in `_spec_code_adapters/_base.py` — do not invent a new shape for an existing project type.

### Step A2 — Write the Detector

**Recommended: scaffold it.** `new_detector.py` generates the file below and registers it in
one step:

```bash
python3 templates/script/generators/new_detector.py --list-capabilities
python3 templates/script/generators/new_detector.py --capability web-api --name django
# --dry-run to preview first; --alias to also register a standalone --adapter django;
# --ext .py (repeatable) to override the default file extension for your capability.
```

This writes `templates/script/validators/_spec_code_adapters/<framework>.py` and adds the
`_DETECTORS` entry from Step A3 automatically — skip straight to Step A5 (fill in `_parse_file`
and the self-test). The manual version below is what the tool generates, for reference or if
you'd rather write it by hand:

```python
from __future__ import annotations
from _base import Detector, NormalizedEndpoint, NormalizedField

_MY_EXTENSIONS = ('.ext',)  # file extensions your detector understands


class MyFrameworkDetector(Detector):
    """
    Framework detector for MyFramework (Web App / Microservices).
    Receives pre-discovered files from WebAPIAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedEndpoint]:
        endpoints: list[NormalizedEndpoint] = []
        for fpath in files:
            if fpath.endswith(_MY_EXTENSIONS):
                endpoints.extend(self._parse_file(fpath))
        return endpoints

    def _parse_file(self, fpath: str) -> list[NormalizedEndpoint]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
        except OSError:
            return []
        # ... regex/AST parsing specific to MyFramework goes here ...
        return []
```

Rules (same as every detector in the codebase):
- **No file discovery** — `os.walk` belongs in the capability adapter, never here.
- **No comparison logic** — comparison lives only in `verify_spec_code.py`.
- **Never raise** — return `[]` on any parse error or unsupported file.
- **No framework imports at module level** — import lazily inside methods if you need a real
  parser (AST, a JS parser, etc.) instead of regex.

### Step A3 — Register the detector in its capability adapter

Already done if you used `new_detector.py` in Step A2. To do it by hand instead: open the
relevant `_capability_*.py` (e.g. `_capability_web_api.py`) and add one line to its
`_DETECTORS` dict:

```python
_DETECTORS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    'fastapi':  ('fastapi',  'FastAPIDetector',  ('.py',)),
    'flask':    ('flask',    'FlaskDetector',    ('.py',)),
    'express':  ('express',  'ExpressDetector',  ('.js', '.ts', '.mjs', '.cjs')),
    'myframework': ('myframework', 'MyFrameworkDetector', ('.ext',)),  # add this
}
```

That's it — the capability adapter's file discovery, spec parsing, and dispatch logic are
unchanged. Your detector now runs automatically whenever `--adapter web-api` is used, or
exclusively when `--adapter web-api --framework myframework` is passed.

### Step A4 — Optional: register a standalone `--adapter` alias

Pass `--alias` to `new_detector.py` in Step A2 to do this automatically. To do it by hand:
if users would find it more natural to type `--adapter myframework` directly (instead of
`--adapter web-api --framework myframework`), add a legacy-style alias in
`verify_spec_code.py`'s `ADAPTER_REGISTRY`:

```python
ADAPTER_REGISTRY: dict[str, tuple[str, str, str | None]] = {
    ...
    'myframework': ('_capability_web_api', 'WebAPIAdapter', 'myframework'),
}
```

This is purely a convenience alias — it routes through the same capability adapter with the
framework hint pre-filled. Not required.

### Step A5 — Write a self-test

Add an `if __name__ == '__main__':` block that builds a small temp spec + temp source file and
asserts the detector extracts the expected `NormalizedForm` objects. See
`_example_adapter.py` for the pattern.

```bash
python3 templates/script/validators/_spec_code_adapters/myframework.py
# Should print: [OK] myframework.py self-test passed
```

---

## Worked example — adding Django (a real detector, not a hypothetical)

`new_detector.py` only scaffolds: a file with `_parse_file()` returning `[]`, plus the
`_DETECTORS` / `ADAPTER_REGISTRY` registration. It does not write the detection logic — that
part is always manual. This section is the actual sequence used to take `django.py` from
scaffold to a working detector, including the two problems that made it more than a copy of
`flask.py`.

**1. Scaffold it:**

```bash
python3 templates/script/generators/new_detector.py --capability web-api --name django --alias
```

**2. Recognize what doesn't transfer from the existing detectors.** Flask/FastAPI put the path,
method, and function in one place (`@app.route('/orders', methods=['POST'])` directly above
`def create_order(...)`). Django REST Framework splits this across two files: `urls.py` maps a
path to a view function name (`path('orders/', views.create_order)`), and `views.py` declares
the function with `@api_view(['POST'])` — no path in sight. A detector that only looks at one
file at a time (like every other detector in this repo) cannot produce a single
`NormalizedEndpoint` from either file alone.

`django.py`'s `extract()` handles this by making two passes across *all* discovered files before
emitting anything: `_find_url_paths()` builds a `view name -> path` map from every
`path()`/`re_path()` call it finds, `_find_api_views()` builds a `view name -> methods` map from
every `@api_view([...])`-decorated function, and only a name present in *both* maps becomes an
endpoint. A view that exists but was never wired into any `urlpatterns` in the scanned files is
skipped, not fabricated with a placeholder path.

**3. Normalize the framework's own path syntax before comparing.** Django has two ways to write
a path parameter, and neither matches the `{param}` convention a spec author would naturally
write: `path()`'s converter syntax (`<int:order_id>`) and `re_path()`'s regex named groups
(`(?P<order_id>\d+)`). `django.py`'s `_clean_path()` converts both to `{order_id}` before the
path is compared — see pitfall #3 below; this is the same category of problem as Express's
`:id` vs FastAPI's `{id}`, just a framework-specific shape of it.

**4. Fix a shared helper that was accidentally framework-specific, instead of copy-pasting
around it.** `_utils.py`'s `_resolve_return_literal_fields()` unwrapped a dict-returning call
only when it was literally named `jsonify` (Flask's helper) — a hardcoded name is exactly
pitfall #4 below, just in a shared file instead of a detector. Django's equivalent is
`Response({...})`. Rather than adding a second name to special-case, the check was changed to
recognize *any* single-positional-dict-argument call, regardless of its name — which is what
actually makes it framework-agnostic, and benefits `flask.py`/`fastapi.py` too, not just
`django.py`.

**5. Prove it's not overfit to the one example you built it against.** The self-test at the
bottom of `django.py` is necessary but not sufficient — it's still code the detector's author
wrote. Before considering it done, it was run against a second, independently written test
project in a different domain (blog posts, not orders), mixing `path()` and `re_path()` in the
same `urls.py`, through the real CLI:

```bash
python3 templates/script/validators/verify_spec_code.py \
    --project-type web-app --adapter django \
    --spec docs/specs/api-contract.md --src src/ --strict
```

with one field deliberately removed from the spec's declared response so the run had something
real to catch (`[FAIL] DELETE /posts/{post_id}/.archived_at: spec='str' → not found in code`) —
confirming the detector genuinely compares, rather than trivially reporting success on
whatever it's pointed at.

**6. Test the detector itself, not just the happy path.** `tests/unit/test_django_detector.py`
covers: correlation across two files, both path-parameter syntaxes, a view with no `@api_view`
(must be ignored), an `@api_view` function never wired into `urlpatterns` (must be skipped, not
fabricated), a view imported and referenced by bare name instead of `views.<name>`, and multiple
methods on one `@api_view`. Each of these is a real case a synthetic single-happy-path fixture
would not have caught.

---

## Situation B — Your project type doesn't fit any of the 7 capabilities (rare)

This only applies if what you're building is not a Web App, CLI Tool, Data Pipeline/ML Pipeline,
Library/SDK, LLM App, IaC, or Mobile App project — i.e. a genuinely new **project type**, not
just a new framework within an existing one. Check the **Situation A** list again first; almost
every "my tool isn't supported" case is actually Situation A.

### Step B1 — Define a new NormalizedForm (only if none of the existing 7 fit)

Add a new `@dataclass` to `_base.py`, following the existing pattern: a name/key field plus one
or two `list[NormalizedField]` fields for whatever "matches" means in your domain. Document the
comparison key in the docstring, same as `NormalizedEndpoint`, `NormalizedResource`, etc.

### Step B2 — Create the capability adapter file

Create `templates/script/validators/_spec_code_adapters/_capability_<name>.py`, following
`_capability_web_api.py` as the reference structure:
- `extract_spec(spec_path)` — parse your project type's spec document format (define and
  document the Markdown convention in the class docstring).
- `extract_code(src_path)` — discover relevant source files, then call
  `self._dispatch_detectors(...)` (inherited from `FrameworkAdapter`) to hand them to detector(s).
- Both methods return `[]` on any error — never raise.
- No framework-specific parsing in this file — that's what detectors are for, even if you start
  with only one.

### Step B3 — Write at least one Detector for it

Same as Step A2 — your new capability adapter needs at least one detector to be useful.

### Step B4 — Register in `verify_spec_code.py`

```python
ADAPTER_REGISTRY: dict[str, tuple[str, str, str | None]] = {
    ...
    'my-project-type': ('_capability_my_type', 'MyTypeAdapter', None),
}
```

### Step B5 — Update the framework surface

A new project type touches more than the validator — update:
- `document-registry.yaml` + `templates/init/document-matrix.md` (new type's document set)
- `guidance/document-purposes-<type>.md` + `guidance/document-purposes.md` index
- `templates/init/<type>.md` (init sequence)
- `scan_codebase.py` `--project-type` choices
- `build_pdf.py` `VALID_PROJECT_TYPES`

Run `python3 templates/script/framework/verify_framework.py --strict` — it audits exactly this
kind of cross-file consistency and will tell you what's missing.

---

## Step 6 (both situations) — Add a pre-commit trigger (optional)

If your project type has a canonical contract filename (e.g. `my-contract.md`), extend the
`SPEC_CONTRACT_STAGED` pattern in `.githooks/pre-commit` so drift is caught automatically:

```bash
SPEC_CONTRACT_STAGED=$(printf '%s\n' "$STAGED" \
    | grep -E '(pipeline-contract|cli-contract|api-contract|public-api|my-contract)\.md$' || true)
```

Also consider setting `spec_code_adapter` / `spec_code_spec` / `spec_code_src` in your project's
`.project-starter.yml` — see README.md → **Spec ↔ Code Validator → Wiring it into pre-commit**.

## Step 7 — Open a pull request

1. Include your detector (and capability adapter, if Situation B) plus any registry/pre-commit changes.
2. Confirm `python3 templates/script/framework/verify_framework.py --strict` passes.
3. Show sample output for both cases: spec-in-sync (exit 0) and a real mismatch (exit 1).

---

## Common pitfalls — check these before you consider a detector done

Every item below is a real bug found by testing an *existing* detector against real,
hand-written code — not a hypothetical. The mechanism now exists in shared code to prevent
most of them automatically, but a brand-new detector for a language/framework not covered
yet can still reintroduce the same *category* of mistake in a new shape. Check each one
explicitly — `new_detector.py`'s generated stub repeats this list as a comment.

1. **Type vocabulary** — don't hand-roll a type comparison. `verify_spec_code.py`'s `compare()`
   already normalizes spec-prose words (`string`, `boolean`, `integer`) against code-native type
   names (`str`, `bool`, `int`) via `_types_match()` — automatic for any `NormalizedField` your
   detector produces. Just don't bypass it with your own equality check.

2. **Output/return fields** — if your `NormalizedForm` has an output/response side (like
   `NormalizedEndpoint.response_fields` or `NormalizedStageContract.output_fields`), do not
   fabricate a single placeholder field (e.g. `name='return'`). If your language is Python, use
   `_resolve_output_fields(tree, func_node)` from `_utils.py` — it already resolves
   class/dataclass/TypedDict fields, dict literals, and constructor kwargs. If your language
   isn't Python, write the equivalent, and return `[]` (not a fake field) when you truly can't
   resolve real names.

3. **Key/identifier syntax normalization** — if your domain has more than one valid way to write
   the same identifier (e.g. `/orders/{id}` vs `/orders/:id` for the same route), check whether
   `_item_key()` in `verify_spec_code.py` already normalizes it (path params currently do, via
   `_normalize_path()`). If your new syntax isn't covered, extend the shared normalizer instead of
   assuming raw string equality is safe — a spec written in the framework-agnostic convention
   will otherwise never match your framework's native syntax. If the normalization is specific to
   your own framework's syntax rather than a cross-framework convention, do it in your detector
   instead of the shared normalizer (see `django.py`'s `_clean_path()`, which converts both
   `path()`'s `<int:id>` converters and `re_path()`'s `(?P<id>...)` regex groups to `{id}` before
   the path ever reaches comparison).

4. **Don't match by method/keyword name alone** — a regex like `\w+\.get\(...\)` matches anything
   with a `.get()` method, not just your framework's router (an HTTP client's `.get()`, a `Map`'s
   `.get()`, ...). Verify the receiver is actually an instance of what you think it is — e.g. track
   which identifiers were actually assigned from your framework's constructor in the same file
   (see `express.py`'s `_find_router_identifiers()`), rather than accepting any identifier. This
   applies to shared helpers too: `_utils.py`'s output-field resolver used to unwrap a
   dict-returning call only when it was literally named `jsonify`; it now recognizes the shape
   (a call with one positional dict argument) instead of one framework's function name, which is
   what let `django.py`'s `Response({...})` work without adding a second hardcoded name.

5. **Nested structure leakage** — if your source format nests (blocks, maps, sub-objects), don't
   extract keys/fields with a flat regex across the whole block — it will pick up keys that
   belong to a deeper level as if they belonged to the top level (see `terraform.py`'s
   `_top_level_keys()` for a depth-tracking approach). Scope extraction to the depth that
   actually corresponds to what the spec describes.

6. **More than one idiomatic way to write the same construct** — don't assume there's only one
   syntax pattern for the thing you're detecting. Real code commonly has 2-3 equally valid styles
   (destructured vs non-destructured function parameters, function vs class components, ...).
   Check what real, idiomatic code in that ecosystem actually looks like — not just the first
   example you write — before considering a pattern "done."

7. **Scalar attributes outside the per-field list** — if your `NormalizedForm` has a single-value
   attribute that isn't part of its per-field list (like `NormalizedFunction.return_type`),
   confirm `compare()` actually checks it. It does for `return_type` today; if you add a new
   `NormalizedForm` with an analogous scalar attribute, you'll need to add that check yourself.

Test each new detector against **real code you write by hand**, not only a synthetic fixture that
already matches your regex — every pitfall above was only found that way.

---

## Shim policy — do not create new `*Adapter` classes for a single framework

The standalone `*Adapter` classes still present in files like `express.py`, `fastapi.py`,
`airflow.py` (e.g. `ExpressAdapter`, `FastAPIAdapter`) are **legacy shims** kept only for
backward compatibility with old `--adapter <name>` usage from before the Phase 52.5 refactor.
They duplicate logic that now lives in the capability adapter + detector. Do not extend them and
do not create new ones — always add a **Detector**, per Situation A or B above.

`verify_framework.py` (Check: "No new shims") will warn if a new `*Adapter` class appears outside
the known-legacy list.

---

## Checklist

**Situation A (new framework in an existing capability):**
- [ ] New `<framework>.py` with a `Detector` subclass (not a `FrameworkAdapter` subclass)
- [ ] `extract()` returns `[]` (not raise) on any error; no file discovery inside it
- [ ] No framework imports at module level
- [ ] Registered in the capability file's `_DETECTORS` dict
- [ ] (Optional) alias added to `ADAPTER_REGISTRY` in `verify_spec_code.py`
- [ ] Self-test passes (`python3 _spec_code_adapters/<framework>.py`)
- [ ] README.md capability/detector table updated

**Situation B (new project type):**
- [ ] New `NormalizedForm` in `_base.py` (only if none of the 7 existing ones fit)
- [ ] New `_capability_<name>.py` inheriting `FrameworkAdapter`, with `extract_spec` + `extract_code`
- [ ] At least one `Detector` registered and self-tested
- [ ] Registered in `ADAPTER_REGISTRY`
- [ ] `document-registry.yaml`, `document-matrix.md`, `guidance/document-purposes-<type>.md`,
      `templates/init/<type>.md`, `scan_codebase.py`, `build_pdf.py` all updated
- [ ] `verify_framework.py --strict` passes

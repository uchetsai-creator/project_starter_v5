# Design Pattern Check (opt-in, expensive)

This is a **separate, opt-in module** from `code-quality-check`. It is deliberately NOT part
of that skill's default run because verifying design-pattern fit properly requires close
line-by-line comparison across every candidate site, cross-referencing business/spec docs, and
sometimes profiling or dependency-graph analysis — always slower than a normal review pass.

## Two modes — ask the user which one before running

| | **Fast** (default) | **Deep** |
|---|---|---|
| Evidence source | Current code + spec docs only | Current code + spec docs + `git log` history per candidate |
| What it catches | Issues already live right now (duplicate sites already disagree, defensive code proving a real omission risk, N independent Singleton instances counted directly) | Everything Fast catches, **plus** issues that haven't broken yet but have a real history of changing (e.g. this enum has grown 3 times in the last year — worth pattern-izing before the 4th) |
| What it misses | A candidate that's structurally risky but hasn't drifted yet and has no other current-code evidence | Nothing extra — this is the superset |
| Speed | Faster — no history mining | Slower — mines git log per candidate on top of the static pass |
| Confidence ceiling | Can still reach High (via live mismatch), but a "not-yet-broken-but-risky" candidate caps at Medium | Same candidate can reach High if history shows repeated past growth |

Fast mode is not "worse," it's a different evidence standard — see Stage 1 below for exactly
how each mode scores a candidate.

## Trigger rule

- Run ONLY when the user explicitly asks for a design pattern review, OR
- `code-quality-check` reaches its Design Pattern Check gate and asks the user whether to
  include this deeper audit — proceed only on an explicit yes, and get the mode too.

**When `code-quality-check` reaches that point, it must ask the user something like:**

> "I can also run a deep design-pattern audit (checks all 23 GoF patterns + Registry for
> missing/misused patterns). Fast mode reads and cross-compares the current code only; Deep
> mode also mines git history per candidate to catch risks that haven't broken yet but have a
> track record of changing. Which do you want, or skip for this pass?"

Do not assume yes, and do not assume a mode. If the user says skip, note in the report that
design-pattern analysis was skipped by request, and move on — do not re-ask later in the same
session unless the user brings it up again.

---

# Detection style (borrowed from CodeAnt AI's approach)

Two things worth carrying over from how tools like CodeAnt structure AI-assisted code review,
since they solve the exact "this is slow and sometimes vague" problem this skill has:

**1. Deterministic pass first, AI judgment only where needed.** CodeAnt runs ~30,000
deterministic AST-level checks first (cheap, high-precision) and only escalates to AI reasoning
for the cases those checks can't resolve on their own. Apply the same split here:
- **Deterministic pass** (do this first, for every pattern): grep/read for the *structural*
  signature — same enum/type set branched in ≥2 places, same flow skeleton duplicated, N
  independent instantiations of a should-be-singleton resource. This is fast and mechanical.
- **Judgment pass** (only for candidates that survive the deterministic pass): Stage 2's
  pattern-selection decision tree, the misuse three-step check, and any doc cross-referencing —
  this is where actual reasoning is needed, so only spend it on real candidates, not everything.

**2. Every finding needs a reproduction trace, not a vague description.** CodeAnt's review
comments give numbered reproduction steps with exact file paths and line numbers instead of a
generic "this looks risky." Every finding from this skill must include:
- The exact file:line for every duplicate/candidate site involved (not just one representative
  site — all of them)
- For a live-mismatch finding: the two (or more) case-lists side by side, showing exactly which
  case is present at one site and missing at another
- For a misuse finding: the specific inline step showing what changes if the abstraction is
  removed (not just "this seems over-engineered")

A finding without a concrete file:line trace for every site involved does not go in the report
— fall back to "Unable to verify," same as `code-quality-check`'s Evidence Rules.

**3. Reachability check before flagging.** Before flagging a duplicate/candidate site, confirm
it's actually on a live code path (called from somewhere reachable), not dead code or an
unused branch — CodeAnt's reachability/exploitability filtering exists because a theoretical
issue in unreachable code isn't worth anyone's time. If a candidate site is dead code, that's
a separate (and usually higher-priority) finding on its own — report it as dead code, not as a
missing-pattern candidate.

---

# Method — three-stage judgment (applies to every pattern below)

## Stage 1 — Structural detection (all conditions must hold, not just "looks similar")

| Condition | What to check |
|---|---|
| **Same shape** | Two or more branches/duplicates operate on the *same* set of enum values or types — not just superficially similar `if` chains |
| **Live case-set match** | Read each duplicate site in full and list exactly which cases/types it handles right now. Do the lists match across all sites? |
| **Behavioral difference, not just data difference** | Each branch executes genuinely different logic — if only the return value differs, a lookup dict solves it, no pattern needed |

All three checks are done by reading the current code — no git history needed. The middle
condition ("live case-set match") does double duty:
- **Sets currently mismatch** (site A handles a case site B doesn't) → this is not a
  hypothetical risk, it's a bug that exists right now. Skip straight to a High finding — this
  is closer to a correctness bug than a style suggestion, evidence it via the two site's exact
  case lists side by side.
- **Sets currently match** → no live bug, but the structural duplication is still a candidate
  for Stage 2/3 below, capped at Medium (see Stage 3) since there's no proof yet that keeping
  two copies in sync is actually failing.

Same-shape-but-trivial (e.g. one branch, or cases that will obviously never grow) → downgrade
to Nit (observe, don't queue).

**Stage 1 as written above is the Fast-mode baseline — it always runs, in both modes.**

## Stage 1b — Deep mode only: historical growth check

Skip this stage entirely in Fast mode. In Deep mode, run it for any candidate that survived
Stage 1 but landed in the "sets currently match" branch (no live bug yet):

- `git log -p` on the enum/type set in question: has it grown at least once in the project's
  history?
- When it grew, was every duplicate site updated in the same commit (or same short window), or
  did one site lag and get patched separately later (i.e. it drifted and was fixed — evidence
  the risk is real even though the code is consistent again right now)?

A candidate with growth history and at least one past lag/drift-then-fix incident earns the
`historical_drift` bonus in Stage 3 below, even with no *current* mismatch. A candidate that has
simply never changed stays capped at Medium/Nit regardless of mode — history of *not* changing
is not evidence either way, it's just no evidence yet.

## Stage 2 — Selection decision tree (for the four "collapse duplication" patterns)

```
What is this branching actually deciding?
│
├─ WHICH algorithm/behavior to run, chosen at runtime by external input
│   → Strategy
│
├─ WHICH object to construct — duplication is in the construction step
│   → Factory Method / Abstract Factory (see per-pattern rows below)
│
├─ A flat key → handler/class lookup, no shared interface contract needed
│   → Registry (lightest option — just a dict)
│
├─ Same flow skeleton, only a few steps differ between branches
│   → Template Method
│
└─ Inputs/outputs differ entirely, no shared skeleton
    → Do NOT force a pattern — this is legitimately separate logic;
      forcing one here is itself an over-abstraction finding (see Complexity in code-quality-check)
```

## Stage 3 — Confidence score (default formula; per-pattern overrides noted below)

```
score = duplicate_site_count × case_mismatch × logic_similarity  [+ historical_drift, Deep mode only]
≥5 High   3-4 Medium   ≤2 Nit
(case sets currently mismatched → skip the formula, straight to High — see Stage 1, both modes)
```

| Signal | Points | Mode |
|---|---|---|
| ≥3 duplicate sites | +2 | Both |
| 2 duplicate sites | +1 | Both |
| duplicate sites >80% similar logic | +1 | Both |
| duplicate sites <30% similar logic | −2 (may be legitimately different — don't force it) | Both |
| Stage 1b found a past drift-then-fix incident | +3 | Deep only |
| Stage 1b: the set has grown before but every site stayed in sync | +1 | Deep only |

Fast mode uses only the "Both" rows — a candidate with no live mismatch and no other Fast-mode
signal caps at Medium, same as before. Deep mode adds the two Deep-only rows on top, which is
the only way a "not currently broken" candidate can still reach High.

## Misuse (over-engineering) check — same three-step shape for every pattern

```
1. Count real concrete implementations of the abstraction.
2. If count == 1: grep project-plan.md / roadmap / research.md for a documented plan for a
   second implementation. Found → not misuse. Not found → step 3.
3. Mentally/actually inline the single implementation and remove the abstraction layer.
   If call-site LOC drops ≥30% with no behavior change → misuse, Medium.
   If LOC barely changes → the abstraction wasn't actually costly, don't flag.
```

Every finding still needs concrete evidence (file/function/commit) per `code-quality-check`'s
Evidence Rules — no finding without it; write "Unable to verify" rather than guess.

---

# Pattern reference (24 patterns)

Run in this priority order — stop early if the user only wants a quick pass:

1. **Tier 1 (clearest judgment, run first)**: Strategy, Factory Method, Registry, Template Method
2. **Tier 2 (verifiable via docs/tests, run if time allows)**: Observer, Singleton, State
3. **Tier 3 (needs docs/profiling evidence — skip without it)**: Bridge, Visitor, Mediator,
   Interpreter, Flyweight, Memento, Command
4. **Tier 4 (structural, moderate cost)**: Adapter, Composite, Decorator, Facade, Proxy, Builder,
   Abstract Factory, Prototype, Chain of Responsibility, Iterator

## Creational

### Factory Method
- Signature: multiple `if type == X: return AImpl() elif type == Y: return BImpl()` sites, duplication is at construction time
- Missing: same-type construction logic duplicated ≥2 files, and reading both currently shows different type sets handled (one file's if/elif is missing a case the other has)
- Misuse: single concrete class, no second implementation documented → Complexity misuse check
- Score: default formula

### Abstract Factory
- Signature: a whole *family* of related objects must switch together by context (e.g. platform-specific Button+Checkbox+Menu)
- Missing: switching context requires touching several related object-creation sites simultaneously instead of swapping one factory
- Misuse: only one context exists today, no second context planned
- Score: duplicate sites × number of objects that must change together

### Builder
- Signature: constructor with ≥5 mostly-optional params, or a repeated setter chain across call sites to build the same kind of object
- Missing: reading the constructor shows required fields with no default, AND call sites don't consistently pass all of them, AND there's defensive code right after construction checking `if field is None` — that defensive check is static proof the omission is a known real risk, not hypothetical
- Misuse: <4 fields or only one fixed combination — Builder adds boilerplate with no payoff
- Score: default formula, weighted by how many call sites actually omit a required field

### Prototype
- Signature: manual field-by-field deep copy of an existing object repeated across ≥2 sites, with nested structure (easy to miss a field)
- Missing: same manual-copy logic duplicated, nesting depth ≥2
- Misuse: flat structure, one-off copy — use the language's built-in copy instead
- Score: default formula, +weight for nesting depth ≥2

### Singleton
- Signature: a resource that should exist once (DB pool, config, logger, cache client) is independently initialized in multiple modules
- Missing: count the actual independent initialization sites in the current code (e.g. N separate `new ConnectionPool()` calls across N modules) — N ≥ 2 is itself the evidence (N separate instances of something meant to be one is provable by reading the code, no runtime incident needed)
- Misuse: Singleton holds *mutable* state, forcing manual reset in test setup/teardown, polluting tests across runs or blocking parallel test execution
- Score: override — misuse is High the moment test files show manual singleton-state reset code; don't use the default formula here

## Structural

### Adapter
- Signature: third-party API/framework types or field names leak directly into internal business logic at the call site
- Missing: external naming has leaked into ≥2 internal modules — swapping vendor or upgrading requires touching all of them (this framework's own `_spec_code_adapters/` is a correct-pattern example worth citing)
- Misuse: only one fixed internal system is ever targeted, wrapping it in an Adapter interface anyway
- Score: default formula

### Bridge
- Signature: an abstraction varies along two independent dimensions (e.g. Shape × RenderEngine), implemented via inheritance producing every combination (`CircleOpenGL`, `CircleDirectX`, `SquareOpenGL`...) — class count = dimA × dimB
- Missing: class count grows multiplicatively, adding one value to dimension A requires writing dimB new classes
- Misuse: one dimension currently has only one value with no planned growth — splitting it out early is premature
- Score: explosion ratio of actual class count vs. what's needed

### Composite
- Signature: tree/nested structures (menus, filesystem, UI trees) where "single node" and "group of nodes" logic is duplicated as near-identical code
- Missing: traversal code does `if isinstance(node, Leaf) ... elif isinstance(node, Group): for child in ...`
- Misuse: structure isn't really a tree (fixed 1-2 levels, never nests further) — forcing Composite anyway
- Score: default formula; weight up if nesting depth is only known at runtime

### Decorator
- Signature: the same base behavior (API call, data processing) has retry/logging/cache/permission logic re-added at multiple call sites
- Missing: this "extra behavior" code is copy-pasted at ≥2 call sites instead of wrapped once
- Misuse: ≥4 stacked decorator layers, making call-stack tracing and profiling hard (needs profiling evidence)
- Score: default formula; misuse auto-starts at Medium once stack depth ≥4

### Facade
- Signature: callers must invoke ≥3 subsystems/services in a specific order, and getting the order wrong breaks things; this ordering logic is duplicated
- Missing: correct-order logic duplicated ≥2 places, AND neither site has any comment, assertion, or type-level guard enforcing the order — nothing in the current code actually prevents calling it wrong
- Misuse: the Facade class itself accumulates responsibilities unrelated to "single entry point," becoming a god object — check method count/LOC against the project's median class size
- Score: default formula; misuse flagged when method count is ≥2x the codebase median

### Flyweight
- Signature: large numbers of near-identical objects created (rendering identical icons, huge counts of char objects), with measured memory/perf impact
- Missing: only with profiling data showing repeated-object overhead is an actual bottleneck
- Misuse: object count is small (well under the scale where sharing matters for this project), adding complexity for no measured benefit
- Score: override — do not flag without profiling evidence, ever; no default-formula fallback

### Proxy
- Signature: access to an expensive resource (remote API, large file, permission-gated resource) has no interception layer — every call site re-implements permission checks / caching / lazy-load
- Missing: this interception logic duplicated ≥2 sites
- Misuse: the Proxy has accumulated business logic unrelated to access control/lazy-loading
- Score: default formula

## Behavioral

### Chain of Responsibility
- Signature: a sequence of "handle if matched, else pass to next" logic written as nested if-else (middleware, validation rules, approval flows)
- Missing: nesting depth ≥3, and adding a new rule requires editing the existing nested structure rather than just inserting a new node
- Misuse: chain length >5 links with no logging marking which link handled/rejected — impossible to debug which step stopped a request
- Score: default formula; misuse auto-Medium if no per-link trace/log marker exists

### Command
- Signature: operations that need undo/redo, queuing, delayed execution, or history are written as direct function calls with no object wrapping the operation
- Missing: undo/redo or task-queue requirement exists in spec docs, but operations aren't currently encapsulated as objects
- Misuse: operations are simple, no undo/queue/history need, yet every operation is wrapped in a Command object anyway
- Score: override — check `business-process.md` / `project-plan.md` for an explicit undo/schedule requirement first; only score Missing if that requirement exists in writing

### Interpreter
- Signature: the project has a custom mini-syntax/rule language that needs parsing and execution (custom query syntax, rule engine expressions), currently hand-parsed via string matching/regex
- Missing: string-parsing logic scattered across multiple sites, adding a rule requires editing multiple regexes
- Misuse: the grammar is trivial (<3 token types) — Interpreter is overkill; rarely actually needed in typical projects
- Score: default formula ×0.5 (narrow applicability, discount to avoid over-flagging)

### Iterator
- Signature: multiple sites each write their own traversal logic for a custom data structure (nested pagination, custom tree), with no shared traversal interface
- Missing: traversal logic duplicated ≥2 sites, AND the structure isn't a language-native directly-for-loopable type
- Misuse: the structure is just a native list/dict — the language already provides iteration, wrapping it is pointless
- Score: default formula; in modern languages (Python/JS/Go) misuse is far more likely than missing-use — check misuse first

### Mediator
- Signature: multiple components (UI widgets, microservices) call each other directly, forming a mesh dependency graph (edge count approaching N² for N components)
- Missing: draw the dependency graph — if it's mesh-shaped (not star/tree), and adding one component requires wiring direct calls to several existing ones
- Misuse: component count is small (<4), the mesh isn't complex yet — introducing a Mediator now is premature
- Score: edge-count / component-count ratio (closer to N² = higher score)

### Memento
- Signature: a "restore to a previous state" feature is needed, but state capture is manual, scattered, and field-prone-to-omission
- Missing: spec docs explicitly require undo/version-rollback, but current state-saving is manual and fragmented
- Misuse: doesn't need arbitrary-point restore, just simple try/rollback (a DB transaction would do), Memento is overkill
- Score: override — same as Command, check spec docs for explicit version-rollback requirement first

### Observer
- Signature: a state change requires manually calling several follow-up actions at the trigger site (order status change → manually call email, UI update, logging in three places); adding a new listener means editing the trigger source
- Missing: trigger-source code lists ≥3 follow-up actions inline, AND comparing this trigger site against other similar trigger sites in the codebase (e.g. two places that both change order status) shows they currently call a different set of follow-up actions
- Misuse: event chain is too long (A→B→C→D) to trace, OR subscriptions are never unsubscribed (check for corresponding cleanup/unsubscribe code — its absence is memory-leak risk)
- Score: default formula; misuse auto-High when no unsubscribe/cleanup counterpart exists

### State
- Signature: object behavior is decided by `if status == 'x': ... elif status == 'y': ...` scattered across multiple methods instead of each state encapsulating its own behavior
- Missing: state-branching logic duplicated across ≥2 methods, AND state-transition rules don't match business docs (`business/*-object.md`) — this overlaps with `code-quality-check`'s existing State Machine Consistency area
- Misuse: few states (<3) with stable, unchanging transitions — State pattern adds unnecessary class count
- Score: default formula; if State Machine Consistency already flagged High (docs mismatch), treat this as High too

### Strategy
- Signature: caller picks which algorithm/behavior to run at runtime based on input/context, dispatched via if/elif or isinstance chain
- Missing: see Stage 2 decision tree — must be a runtime choice, not a construction-time choice
- Misuse: only one strategy exists, no second implementation planned → Complexity misuse check (Stage-misuse steps above)
- Score: default formula

### Template Method
- Signature: multiple functions share an identical flow skeleton (e.g. "validate input → process → output result"), only one middle step differs, yet the whole function is copy-pasted
- Missing: ≥2 functions share the skeleton, AND reading both copies side by side right now shows the "shared" skeleton portion has already diverged between them (not just the step that's supposed to vary)
- Misuse: skeleton was only ever used once, OR more than half the steps vary between "subclasses" (skeleton was extracted wrong)
- Score: default formula; misuse flagged when varying-step-count / total-step-count > 50%

### Visitor
- Signature: a stable set of object types (AST nodes, UI component tree) needs multiple unrelated operations applied (render, validate, serialize...) and operation count keeps growing while the type set stays stable
- Missing: adding each new operation requires touching a method on every type's class (violates open/closed), operation count ≥3
- Misuse: the type set actually changes often (unstable) — Visitor makes every addition worse, not better, since every Visitor implementation needs updating. **This is one of only two patterns (the other is Singleton) where misuse is more common than missing-use in practice**
- Score: default formula; check type-set stability first — unstable set defaults to misuse judgment, skip missing-use scoring

## Extra (not GoF, but common in practice)

### Registry
- Signature: a `key → handler/class` static mapping currently hand-rolled as an if/elif chain instead of a lookup table
- Missing: mapping logic duplicated ≥2 sites (see Stage 2 decision tree — pick this over Strategy/Factory when it's a flat lookup with no shared interface contract)
- Misuse: registry has very few entries (<3) and won't grow — a plain dict isn't even needed, hardcoding is clearer
- Score: default formula

---

# Report format

Same table shape as `code-quality-check`'s Report Format, plus a `Pattern` column and a
`Reproduction` column (per Detection style, item 2 above — no finding without one):

| Area | Pattern | Finding | Reproduction | Severity | Recommendation |
|------|---------|---------|--------------|----------|----------------|

**Reproduction column contents, by finding type:**
- Live-mismatch finding: every site's exact `file:line`, plus the two case-lists side by side —
  e.g. `orders/api.py:42 handles {paid, refunded, cancelled}` vs.
  `orders/webhook.py:88 handles {paid, refunded}` — `cancelled` is silently unhandled at the
  webhook site
- Structural (no live mismatch, Medium-capped or Deep-mode High) finding: every site's
  `file:line`, plus (Deep mode only) the commit(s) where the set grew and whether that commit
  touched every site
- Misuse finding: the `file:line` of the single implementation and the call site(s), plus the
  concrete before/after LOC from the Stage-misuse inline-removal step

State this per finding, not once per report — a report with 5 findings needs 5 reproduction
traces.

Report the **mode used** (Fast or Deep) once at the top of the table, not per finding.

If the user skipped this audit, write one line in the main report instead of the table:

> Design pattern audit: skipped by request.

Do not silently omit it — the user (or a future reader of the report) should be able to tell
the difference between "audited, found nothing" and "not audited."

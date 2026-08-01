# Learning Checkpoints — Common

Applies to every project type. Triggers happen every task, independent of doc/validator
timing (see Sprint Documentation Sync) — this is about live discussion in the session,
not a file that gets written and synced later.

---

## Checkpoint 0 — Unfamiliar Technology (only when it applies)

Trigger: the current task touches a technology, library, or pattern you have never used
before — not just "existing code in a language I know," but genuinely new ground.

Run this *before* Checkpoint A or B, as a grounding pass:

1. "用我熟悉的東西打比方，這個技術是在解決什麼問題？" — force an analogy to something already known, not a wall of jargon.
2. "這個技術裡有哪 3-5 個核心概念是我一定要先懂的？" — a minimal glossary, not full documentation.
3. "如果沒有這個技術，土法煉鋼要怎麼做同樣的事？" — anchor the new concept against a familiar baseline.
4. Ask for a minimal toy example unrelated to today's real task. Run it yourself, change one
   parameter, observe the result — before touching the real code.

Skip this checkpoint when the technology is already familiar — do not run it every task.

---

## Checkpoint A — Working in Existing Code

Trigger: the task modifies or extends code that already exists.

1. **Read the current state** — "這個功能/模組目前怎麼運作？資料怎麼流進來、處理、流出去？"
2. **Locate the change** — "這個改動該放在哪個檔案/層？為什麼是這裡？有沒有現成 pattern 可以照抄？"
3. **Assess blast radius** — "這個改動會不會影響到其他呼叫這裡的地方？有沒有隱藏的耦合？"
4. **Match conventions** — "這裡的命名/錯誤處理/測試慣例是什麼？我這樣寫有沒有跟現有風格衝突？"

See the matching `learning-checkpoints-<type>.md` for which nouns to substitute (endpoint,
stage, screen, resource, etc.) at each step.

---

## Checkpoint B — Starting from a Requirement

Trigger: the task is a new feature, or there is no existing code for it yet.

1. **Clarify the requirement** — "有沒有隱含的邊界情況？什麼情況算做完（驗收標準）？"
2. **Discuss the design before writing code** (use Plan Mode) — "打算怎麼實作？為什麼選這個做法，還有哪些替代方案、各自的取捨？"
3. **Follow the implementation** — "這裡為什麼用這個寫法/套件，而不是自己刻？"

---

## Checkpoint C — Post-Implementation Review (always, before Closeout)

1. "這段邏輯關鍵在哪一行？拿掉某個判斷式會發生什麼？"
2. "有沒有邊界情況目前沒處理到？"
3. "這次改的關鍵路徑，有沒有照 `docs/specs/logging-spec.md` 定義的 log point 加上 log？"

This checkpoint happens every task regardless of A/B/0 — it is what actually gets
internalized, separate from whether the doc sync happens now or at sprint end.

**Escalation for item 3** — if the answer is "not sure" or reveals a gap (a log point
was skipped, or you can't tell without checking), don't just take the conversational
answer at face value — actually run the code-level check:

```bash
python3 docs/script/validators/verify_spec_code.py --project-type TYPE \
    --adapter <language>_logging --spec docs/modules/ --src src/ --strict
```

If no detector exists yet for the current language (check `ADAPTER_REGISTRY` in
`verify_spec_code.py` — `python_logging` and `javascript_logging` (covers JS/TS/React)
exist so far), build one on the spot
before closing out the task:
1. Add a `NormalizedLogPoint`-based language detector under `_spec_code_adapters/`,
   modeled on `python_logging.py` (walk the language's function/method definitions,
   match logger calls against the `<operation> — <state>` convention in
   `logging-spec.md → Log Output Format`, normalize the call's level name to the
   canonical `info` / `warn` / `error` / `debug` vocabulary).
2. Register it in `_capability_logging.py`'s `_DETECTORS` and in `verify_spec_code.py`'s
   `ADAPTER_REGISTRY`.
3. See `docs/contributing-adapters.md` for the full contributor steps.
4. Then run the command above for real before marking the task's Verify step done.

This is the only Learning Checkpoint item that can trigger writing framework code —
the others (0, A, B, C.1, C.2) are conversation only.

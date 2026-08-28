# Learning Checkpoints — Common

Applies to every project type. Triggers happen every task, independent of doc/validator
timing (see Sprint Documentation Sync) — this is about live discussion in the session,
not a file that gets written and synced later.

**Claude Code note:** Checkpoint A's "ask, don't guess" step and Checkpoint B's item 1 are
conversational — they depend on the agent choosing to follow this file. If
`adapters/claude/pretooluse_scope_guard.py` is wired into `.claude/settings.json`'s
`PreToolUse` hook, the same "ask before implementing" rule is also enforced mechanically:
it blocks `Edit`/`Write`/`MultiEdit`/`NotebookEdit` on source files until `current-state.md`
has a scoped `Current Task` and a filled `Clarifying Questions Asked` field. That hook is a
backstop, not a replacement for actually running the checkpoints below — it can't tell
whether real questions were asked, only whether the field was filled in.

That mechanical backstop is either always-on or fully absent, by default — no per-session
choice. `.project-starter.yml`'s `checkpoint_enforcement: session-prompt` adds a third
option: `adapters/claude/session-start-hook.sh` asks once per Claude Code session (via
injected `additionalContext`) whether to turn the mechanical block on for that session. If
the user opts in, `pretooluse_scope_guard.py` enforces exactly as described above for the
rest of that session. If the user opts out (or the session hasn't answered yet), the guard
allows everything and this file's checkpoints fall back to being purely conversational —
still run them, just without the mechanical backstop catching a skipped one. See
`pretooluse_scope_guard.py`'s docstring and `.project-starter.yml`'s comment for the full
design.

---

## Checkpoint 0 — Unfamiliar Technology (only when it applies)

Trigger: the current task touches a technology, library, or pattern you have never used
before — not just "existing code in a language I know," but genuinely new ground. When
unsure whether this counts, run it anyway — a false-positive Checkpoint 0 costs one short
grounding pass; skipping a real gap means building on an assumption that was never checked.

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

**Before items 1-4 — ask, don't guess:** the first time this session touches a given
module/file, if there is no `docs/modules/<module>/` entry or `changelog.md` /
`task-log.md` row showing this project's own workflow already built or reviewed it, ask
the user directly: "這段程式碼需要我先做完整的 code quality 檢查嗎？（像是接手交接、
沒審過的程式碼）" Whose code it originally is (yours, a teammate's, another AI session's)
is not something to infer — you have no memory of authorship across sessions, so a guess
here is just a guess. If the user says yes, skip to the Escalation below instead of items
1-4. If no, continue with items 1-4 as normal.

**If there is no `docs/modules/<module>/` entry at all** (not even a stub), consider running
`python3 templates/script/generators/draft_module_flow.py <module_src_dir> --project-type TYPE`
first — it parses the module's actual source (Python/JS/TS) and pre-fills real class/function
names instead of starting from a blank template. It does not invent the call sequence or
business meaning — that part is still yours to answer in items 1-4 below.

1. **Read the current state** — "這個功能/模組目前怎麼運作？資料怎麼流進來、處理、流出去？"
2. **Locate the change** — "這個改動該放在哪個檔案/層？為什麼是這裡？有沒有現成 pattern 可以照抄？"
   如果找到現成 pattern，講出它的名字（Adapter / Strategy / Factory / Template Method /
   Registry...），不只是說「跟著抄」——這個名字才是以後看到類似形狀時能認出來的線索。
   叫不出名字也沒關係，但要講清楚「抄的是什麼結構」，而不是抄哪一行程式碼。
3. **Assess blast radius** — "這個改動會不會影響到其他呼叫這裡的地方？有沒有隱藏的耦合？"
4. **Match conventions** — "這裡的命名/錯誤處理/測試慣例是什麼？我這樣寫有沒有跟現有風格衝突？"

See the matching `learning-checkpoints-<type>.md` for which nouns to substitute (endpoint,
stage, screen, resource, etc.) at each step.

**Escalation — user confirms this code needs a full review**: run `code-quality-check.md`
in full instead of stopping at items 1-4 above. Report every finding with the two extra
fields it defines for this case (Why It's Wrong / Correct Pattern) — the goal is to
actually learn what's wrong and what the right shape looks like, not just get a silent
fix. High-severity findings still block further work per that file's rules, including its
independent-review gate — you cannot self-close a High finding in the same session that
fixed it.

---

## Checkpoint B — Starting from a Requirement

Trigger: the task is a new feature, or there is no existing code for it yet.

1. **Clarify the requirement** — "有沒有隱含的邊界情況？什麼情況算做完（驗收標準）？"
2. **Discuss the design before writing code** (use Plan Mode) — "打算怎麼實作？為什麼選這個做法，還有哪些替代方案、各自的取捨？"
   接著問一句具體的：「這個問題的形狀符不符合某個已知 design pattern（Strategy / Factory /
   Adapter / Observer / Template Method / Registry...）？」如果符合，講出名字並說明為什麼適用；
   如果不符合、或符合但現在不值得上（例如只有一個實作、沒有第二個計畫），也講清楚為什麼不用
   ——跟 `code-quality-check.md` 的 Complexity 檢查標準一樣：能不能點出「真的有第二個呼叫者/
   需求」，是判斷值不值得上這個 pattern 的關鍵，不是「聽起來比較專業」。
3. **Follow the implementation** — "這裡為什麼用這個寫法/套件，而不是自己刻？"

---

## Checkpoint C — Post-Implementation Review (always, before Closeout)

1. "這段邏輯關鍵在哪一行？拿掉某個判斷式會發生什麼？"
   **Escalation** — 如果這是關鍵路徑，而且答案是用猜的或講不清楚，不要只停在對話：真的把那個
   判斷式暫時註解掉（或改成恆真/恆假），跑一次相關測試，確認測試會變紅。測試沒有紅，代表這段
   邏輯根本沒被測到——這比事後回答「應該會壞掉吧」準確，也直接驗證了 code-quality-check.md
   要求的測試覆蓋率是不是真的有效，不是照抄一個從不失敗的測試。改完記得把判斷式還原。
   還在建立對這個 codebase／語言的信心時，把這個 escalation 當成預設動作，不要只在「聽起來
   不確定」才做——口頭上講得順不代表真的懂，這階段的口頭自信本來就還不是可靠訊號。
2. "有沒有邊界情況目前沒處理到？"
3. "這次改的關鍵路徑，有沒有照 `docs/specs/logging-spec.md` 定義的 log point 加上 log？"
4. **Teach-back** — 換你用自己的話跟我解釋這段程式碼在幹嘛、為什麼這樣寫，不是我講給你聽。
   講不出來、或講錯了，那才是真正該深入的地方——這比我單方面問「懂了嗎」準確很多。不用逐行講，
   挑這次改動裡最關鍵的那一小段就好。講不出來時不要就此打住：換一個更貼近生活的比喻再試一次
   （跟 Checkpoint 0 第 1 題的技巧一樣），最多重試兩次；還是講不出來，具體寫下「卡在哪一點」，
   那個點才是真正要深入的地方，不是含糊帶過。順便講一句：這段有沒有用到（或者本來可以用、但
   沒用）某個 design pattern？講不出名字就算了，不用為了湊答案硬套一個——這題純粹是為了累積
   辨認 pattern 的直覺，跟其他 teach-back 一樣，答不出來才是該深入的訊號，不是每次都要有名詞
   可以講。
   跟 Checkpoint 0 一樣可以跳過：如果這次的 task 真的夠瑣碎（改錯字、調設定值這類），而且你自己
   判斷已經完全懂，可以跳過或簡化 teach-back，不用每個 task 都硬做——但拿不準的時候，做比不做安全。

   **Persisting the gap** — teach-back only lives in this session's conversation; nothing
   else in this framework writes it down. If `learning-log.md` exists at the project root
   (see its own header for the format), append one entry now covering: what you couldn't
   explain or got wrong this task, and any pattern named above (used, or considered and
   rejected) — even on a task with no gap, the pattern line is still worth recording. Every
   3rd entry, `learning-log.md` itself prompts a re-check of an older one — that's the
   actual review step, not this checkpoint.

This checkpoint happens every task regardless of A/B/0 — it is what actually gets
internalized, separate from whether the doc sync happens now or at sprint end.

**Escalation for item 3** — if the answer is "not sure" or reveals a gap (a log point
was skipped, or you can't tell without checking), don't just take the conversational
answer at face value — actually run the code-level check:

```bash
# Runs every registered language detector at once (Python + JS/TS/React today) — use
# this by default. Pass --adapter python_logging / javascript_logging instead only to
# isolate one language's results.
python3 docs/script/validators/verify_spec_code.py --project-type TYPE \
    --adapter logging --spec docs/modules/ --src src/ --strict
```

If no detector exists yet for the current language, the command above now tells you so
directly — a `[WARN] 0 code items extracted from --src, but real file(s) exist there` means
nothing was actually checked, not that the code is compliant (before this warning existed,
an empty spec + undetected code silently printed `[OK] No mismatches`, which looked like a
pass). Don't take a plain `[OK]` at face value without glancing at the file count either;
the warning is the reliable signal. (Also check `ADAPTER_REGISTRY` in `verify_spec_code.py` —
`python_logging` and `javascript_logging` (covers JS/TS/React) exist so far.) When you get
this warning, build a detector on the spot before closing out the task:
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
the others (0, A, B, C.1, C.2, C.4) are conversation only.

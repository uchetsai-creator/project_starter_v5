# Clarifying Checklist — ask the user every category

Referenced from `AGENTS.md → New requirement from the user`, `learning-checkpoints/common.md`
(Checkpoint B item 1) and `docs/current-state.md → Clarifications`. The categories follow the
coverage taxonomy GitHub Spec Kit's `/speckit.clarify` scans, adapted to this framework.

## The rule: the user decides what is in scope, not the agent

- **Ask every category, every time** — new, small, or already scoped. There is no cap on the
  number of questions; ask as many as each category needs, one category at a time.
- **You may say a category looks less relevant, and why** ("this task doesn't seem to touch
  permissions, because ..."), but you still ask. **Only the user may skip it.**
- A skipped category is recorded as `N/A — user: <their reason>`. Never write `N/A` on the user's
  behalf, never leave a category blank, never fill it with your own assumption.
- Record each answer as `Q → A` in the user's own words in `docs/current-state.md → Clarifications`.
- Do not start explaining the approach (`guidance/approach-proposal.md`) until every category is
  answered.

## Categories

1. **Goal & scope** — who uses it, what problem it solves, what "success" looks like, what is explicitly out of scope
2. **Users & permissions** — who can do/see what; roles; whose data a person may touch
3. **Data** — what is read, what is written, where it comes from, how much, how sensitive, retention/deletion
4. **Flow & interaction** — the normal path step by step; what the user sees; messages and error states
5. **Edge cases & failure handling** — empty/duplicate/invalid input, partial failure, retries, conflicts, what happens when a dependency is down
6. **Non-functional (performance, security, reliability, compliance)** — speed/volume limits, security and privacy, availability, logging/monitoring, regulatory rules
7. **Integrations & external dependencies** — other systems, APIs, files, formats, who owns them, what breaks if they change
8. **Constraints & trade-offs** — deadline, budget, tech or team limits, options already ruled out and why
9. **Terminology & conventions** — names the user already uses, existing patterns/styles to follow, words that must mean one thing
10. **Acceptance criteria (done means)** — testable statements of when this is finished, and how the user will verify it

## Question format (the same standard as Spec Kit's `/speckit.clarify`)

- **Choice questions** (when the answer is one of a few options): give 3–5 labeled options and
  mark one as recommended with a reason. The user picks, or gives their own answer. Example:
  "這個頁面需要即時更新嗎？A 不需要　B 定時刷新（建議，每 30 秒）　C 推播（伺服器主動送出）。"
- **Number questions** (when the answer is a size or a limit): ask for a number with a unit, and
  ask for the expected value in 12 months, not only today. Example: "同時在線的使用者現在幾人？
  一年後預計幾人？"
- **Vague answers are not accepted.** If the user says "差不多", "很多", "之後再說", or "都可以",
  ask again with options or a number. Record the answer only after it is specific, or record the
  user's "不確定" as an open item, not as an assumption.
- Do not hide the recommendation inside the question. The user decides; the recommendation is
  only a suggestion.

## Categories with specific questions (ask each one; do not skip a category because it seems obvious)

1. **Goal & scope**
   - "這個功能的主要使用者是誰？用一句話說他們要完成什麼。"
   - "做到什麼程度算成功？請給一個可以量的指標。"
   - "這次明確不做的是哪些？"
2. **Users & permissions**
   - "哪些角色可以做什麼、看什麼？（列出角色）"
   - "使用者能不能看到別人的資料？A 不能　B 只能看自己單位的　C 全部可看（請說明理由）"
3. **Data**
   - "會讀哪些資料、寫哪些資料？來源是哪個系統？"
   - "資料量：現在每天幾筆？一年後預計幾筆？"
   - "會不會有敏感欄位？要保留多久？A 永久　B 保留 N 年後刪除　C 其他"
4. **Flow & interaction**
   - "正常流程一步一步是什麼？使用者每一步會看到什麼？"
   - "出錯時要顯示什麼訊息？A 顯示錯誤代碼　B 顯示白話說明並提供重試　C 其他"
5. **Edge cases & failure handling**
   - "輸入的資料為空、重複、或格式錯誤時怎麼處理？A 拒絕並提示　B 跳過並記錄　C 其他"
   - "做到一半失敗時，已經寫入的資料怎麼辦？A 全部回復　B 保留並標記失敗　C 其他"
   - "依賴的系統掛掉時，要等、要重試、還是停止？請給次數或時間，例如「重試 3 次，每次間隔 10 秒」"
6. **Non-functional (performance, security, reliability, compliance, maintainability)**
   - "資料需要多快出現在畫面上？A 不需要即時　B 定時刷新（建議，每 30 秒）　C 推播，多久內送達（請給秒數）"
   - "回應時間要多快？請給數字，例如「p95 小於 200ms」"
   - "未來 12 個月，同時連線數和資料量會增加到多少？請給數字。"
   - "這個功能以後最可能會改的是哪一部分？A 資料來源　B 畫面　C 計算規則　D 其他"
   - "需要留 log 或監控嗎？A 只留錯誤　B 留每次執行紀錄　C 不需要"
   - "有沒有法規或資安要求？A 無　B 個資　C 其他（請說明）"
7. **Integrations & external dependencies**
   - "會碰到哪些外部系統、檔案或 API？每一個由誰維護？"
   - "對方改版或停機時，你們希望怎麼處理？A 停止並通知　B 使用上一次的資料　C 其他"
8. **Constraints & trade-offs**
   - "時程、預算、人力或技術限制有哪些？請給具體的數字或期限。"
   - "哪些做法已經排除？為什麼？"
   - "這段邏輯其他模組或專案會不會用到？A 會，要共用　B 不會，各自保留　C 目前不確定（列為待確認）"
9. **Terminology & conventions**
   - "你們平常怎麼稱呼這些東西？請列出名詞，例如「產線」和「線體」哪個是正式用語？"
   - "有沒有要沿用的既有寫法或程式風格？請指出參考的檔案或目錄。"
10. **Acceptance criteria (done means)**
   - "怎樣才算做完？請給一個可以測試的條件，例如「輸入 N 筆資料，輸出 N 筆，欄位都相符」。"
   - "誰負責驗收？A 你本人　B 使用單位的同事　C 其他"

## Writing the answers back to the spec

`current-state.md` is overwritten at the next task, so the answers must land in
`docs/project-requirements.md` — the spec every later task reads. Do it once the approach is
confirmed and before coding, and show the user what you wrote:

| Clarifications category | Goes into project-requirements.md |
|---|---|
| Goal & scope, Users & permissions | Goals, Scope (In / Out), Roles |
| Data, Flow & interaction, Integrations | Functional Requirements (FR-XXX) |
| Non-functional | Non-Functional Requirements |
| Edge cases & failure handling | Edge Cases |
| Acceptance criteria | Acceptance Criteria (AC-XXX) |
| Constraints & trade-offs, Terminology & conventions | Assumptions |

Categories the user skipped (`N/A — user: ...`) write nothing. Then list the FR-/AC- ids you just added in
`current-state.md → Requirement IDs` and keep `Requirement Status` at `In Progress` until the last task in the
Breakdown is done (`.githooks/pre-push` verifies that requirement before a push to main/master). The `templates/current-state.md`
Doc Checklist starts with a `project-requirements.md` line for this; check it off (`- [x]`) once
the spec is updated. Other docs (architecture, API contracts, ...) are still chosen from
`document-registry.yaml` `update_trigger` as before.

## What is enforced

`adapters/claude/pretooluse_scope_guard.py` and `.githooks/pre-commit` block source changes while
`docs/current-state.md → Clarifications` has an unanswered category (still `[ask the user]`, empty,
or an `N/A` that is not `N/A — user: <reason>`). The check applies when the file has a
`## Clarifications` section — the template always does; an older `current-state.md` must add it to
be covered. Like every field here, it confirms the lines were filled, not that the conversation
really happened.

At closeout (Status Complete), pre-commit and `run-verify.sh` additionally require a **checked**
`project-requirements` line in the Doc Checklist whenever the file has a `## Clarifications`
section. That confirms the box was ticked, not that the spec text is correct.

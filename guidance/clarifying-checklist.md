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

## Starting questions (adapt the wording; do not skip a category because these seem obvious)

- Goal & scope: "誰會用？想解決的是什麼問題？做到什麼程度算成功？這次明確不做什麼？"
- Users & permissions: "哪些角色可以做／看什麼？能不能看到別人的資料？"
- Data: "會讀哪些資料、寫哪些資料？來源是哪裡？量多大？有沒有敏感欄位？要保留多久？"
- Flow & interaction: "正常流程一步一步是什麼？使用者會看到什麼？出錯時要顯示什麼？"
- Edge cases & failure handling: "空值、重複、格式錯誤怎麼辦？做到一半失敗要怎麼處理？依賴的系統掛了怎麼辦？"
- Non-functional: "有沒有速度或量的要求？資安、隱私、法規？要不要留 log、監控？"
- Integrations: "會碰到哪些外部系統或檔案？誰維護？對方改版會怎樣？"
- Constraints & trade-offs: "時程、預算、技術或人力限制？有沒有已經排除的做法？為什麼？"
- Terminology & conventions: "你們平常怎麼稱呼這些東西？有沒有要沿用的既有寫法？"
- Acceptance criteria: "怎樣才算做完？你會怎麼驗收？有沒有可以測試的具體條件？"

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

Categories the user skipped (`N/A — user: ...`) write nothing. The `templates/current-state.md`
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

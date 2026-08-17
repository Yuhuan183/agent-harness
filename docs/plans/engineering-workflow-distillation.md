# Engineering workflow 蒸餾實作計畫

狀態: approved direction; implementation pending  
建立日期: 2026-08-14  
研究依據: [Matt Pocock skills 導入研究](../research/mattpocock-skills-integration.md)

## Checkable outcome

在 agent-harness 中新增兩個由本專案擁有, Claude/Codex 共用的工程 skills:

1. `evidence-debugging`: 以可重現的 feedback loop 做 diagnosis; 只有修復已在使用者授權範圍時才改碼.
2. `test-first-change`: 以 public seam, independent oracle, vertical slice 執行 red-green change.

兩者必須:

- 服從既有 main/leaf, approval, commit, external write 與 verifier 規則;
- 不依賴 Matt Pocock plugin, `npx skills update` 或 machine-local graph tools;
- 從 `main/.agents/skills` 單一來源部署到 Claude 與 Codex;
- 把穩定流程, 本專案 tuning, 上游 attribution 分成可 review 的三層;
- 經 source tests, behavior traps, prompt census, manifest dry-run 與新 session 驗收.

## 非目標

第一批不做:

- 不複製完整 25-skill catalog.
- 不新增 router skill 或重造 `ask-matt`.
- 不導入自動更新器.
- 不新增 `CONTEXT.md`, 根目錄 `AGENTS.md` / `CLAUDE.md` 或 `docs/agents/*`.
- 不建立 GitHub issue, label, project 或其他外部 tracker 狀態.
- 不改 main session 的 model, effort, provider routing 或 dispatch quota.
- 不在同一個變更中做 `change-shaping`, `change-review`, triage, wayfinder 或 wizard.
- 不 deploy, commit, push 或發 PR, 除非使用者另行授權.

## 設計原則

### 1. 一份 portable workflow, 一份 local tuning

每個 skill 的 `SKILL.md` 只保存必要流程與停止條件; agent-harness-specific 行為放 `references/tuning.md`. 這使上游重查時可以回答:

- 上游方法改了什麼?
- portable workflow 是否需要跟進?
- local tuning 是否仍成立?

不能以三方 merge 自動回答這三題, 也不能讓更新工具覆寫 tuning.

### 2. Skill 不重新擁有 main contract

Skill 可以把既有規則轉成領域內的具體 stop, 但不能重複整份 global contract. 必要 pointer 應短而可驗證:

- dispatch going ahead -> load existing dispatch skill;
- diagnosis-only -> no mutation;
- external write/commit -> require separate authority;
- exact verification -> report failed or skipped checks.

### 3. Portable core 不依賴 optional tools

`debug-issue`, AST graph, browser, GitHub connector 或其他 machine-local capability 可以加速, 但不得成為正確性前提. 沒有這些工具時, skill 仍可用 source, tests, logs 和 smallest probe 完成工作.

### 4. Tuning 是明示 policy, 不是 fork 雜訊

初始 tuning 來源只有:

- global working contract;
- agent-harness 已驗證的 review/deployment 方法;
- 使用者本次核准的蒸餾方向;
- 之後經明確同意記錄並 actioned 的 task-observer observations.

不得把單次偶發偏好直接永久化.

### 5. Tuning 變更協定

`references/tuning.md` 由 agent-harness 擁有, 但不能覆寫更高優先序的 system/developer instruction, 當次使用者要求或 global contract. 它保存的是本專案反覆成立的 default 和 stop condition, 不是另一份 resident contract.

每次新增或調整 tuning 都依下列流程:

1. 以一個應觸發案例和一個不應觸發案例描述想改變的行為.
2. 分類 ownership: 跨 repo 都成立的工程方法進 `SKILL.md`; agent-harness 的語言, 授權, 派工, 驗證與輸出偏好進 `references/tuning.md`; 單次任務偏好不持久化.
3. 若 trigger 改變, 同步更新 `SKILL.md` frontmatter 的 `description` 與 `agents/openai.yaml`; body 內不另藏 invocation policy.
4. 先新增能反駁舊行為的 trap 或 fixture, 再修改 repo source. 不直接編修 HOME copy.
5. 跑 skill validation, focused behavior traps, contract tests, prompt census 與 deployment dry-run.
6. 以 `accepted`, `rejected`, `needs-more-evidence` 記錄結果; 需要 deploy 時另取明確授權.

來自工作摩擦的改善只能在使用者同意記錄 observation, 且 observation 經 review/actioned 後成為 tuning 候選. 上游更新不得自動改寫這一層.

## 目標檔案結構

```text
main/.agents/skills/
├── INSTALLED.txt
├── evidence-debugging/
│   ├── SKILL.md
│   ├── ATTRIBUTION.md
│   ├── agents/
│   │   └── openai.yaml
│   └── references/
│       └── tuning.md
└── test-first-change/
    ├── SKILL.md
    ├── ATTRIBUTION.md
    ├── agents/
    │   └── openai.yaml
    └── references/
        └── tuning.md

main/claude/skills/
├── evidence-debugging -> ../../.agents/skills/evidence-debugging
└── test-first-change -> ../../.agents/skills/test-first-change

main/codex/skills/
├── evidence-debugging -> ../../.agents/skills/evidence-debugging
└── test-first-change -> ../../.agents/skills/test-first-change
```

若 Claude 與 Codex 對同一段操作真的需要不同語意, 先提供可反證的 runtime 證據; 沒有證據時維持同一 shared body, 不預先建立 wrapper 分叉.

## Skill contract: `evidence-debugging`

### Trigger

草擬的 runtime 描述 (英文, 實作時進 `description`):

> Model-invoked only when the request describes broken, failing, throwing, flaky,
> incorrect, or slow behavior, or explicitly asks to diagnose/debug.

邊界: 不得搶走單純 code explanation, review 或 refactor 的意圖.

### Workflow

1. Classify authority: diagnosis-only or change-authorized.
2. Capture exact user-observed symptom and success condition.
3. Build the tightest repeatable feedback loop that fails on this symptom.
4. Minimize while preserving the same failure.
5. Trace from observed boundary toward likely cause; form one falsifiable hypothesis at a time.
6. Run the smallest probe that can refute the hypothesis.
7. Conclude with evidence strength: verified root cause, strongest hypothesis, or unresolved.
8. Diagnosis-only stops here.
9. Change-authorized work adds a failing regression at an appropriate public seam when practical, applies the smallest coherent fix, reruns minimized and original scenarios, then the narrow relevant suite.

### Required tuning

- Do not mutate merely because the skill was model-invoked.
- Do not ask the user for facts available from repo, logs, tools, or reproducible probes.
- Ask one precise question only when different answers materially change diagnosis.
- A nearby failure is not a reproduction of the reported bug.
- A mocked test that bypasses the actual failing parser/filesystem/shell/provider path cannot close the claim.
- Non-deterministic bugs require a measured reproduction rate before and after.
- Do not silently turn `UNRESOLVED` into a confident root cause.
- Optional graph tools are navigation accelerators, not evidence by themselves.

### Output

- Outcome/root cause.
- Exact reproduction or failed attempt.
- Evidence and refuted hypotheses.
- Change and verification only when authorized.
- Remaining risk or next required observation.

## Skill contract: `test-first-change`

### Trigger

草擬的 runtime 描述 (英文, 實作時進 `description`):

> Model-invoked when the user explicitly asks for TDD, test-first, red-green, or a
> regression test, or when an authorized implementation clearly benefits from a
> stable behavior seam.

邊界: 不得把 TDD 強加到純文件, 產生式資料, 瑣碎設定, 或本來就不可能有「改動前失敗」的變更上.

### Workflow

1. Identify desired observable behavior and the highest stable public seam.
2. Inspect existing tests and nearby conventions before inventing a new seam.
3. Choose an expected result from an independent source of truth.
4. Write one test for one vertical slice.
5. Run it and confirm it fails for the intended reason.
6. Add the smallest implementation that makes it pass.
7. Rerun the focused test.
8. Repeat only for the next justified slice.
9. Run the narrow relevant suite; broader suite only when blast radius justifies it.
10. Report whether red, green, and boundary verification were actually observed.

### Required tuning

- Prefer an existing public seam; new seams are design decisions, not test convenience.
- Do not ask the user to confirm a seam the repo already makes clear.
- Ask one precise question if competing seams materially change public API or ownership.
- Avoid implementation-coupled mocks and tautological expected values.
- Do not bulk-write all tests before any implementation feedback.
- Do not equate a green unit test with browser/device/provider/runtime verification.
- Refactoring outside the approved behavior slice requires separate scope justification.
- The skill does not commit and does not automatically invoke code review or subagents.

### Output

- Behavior and seam tested.
- Independent expected-value source.
- Red evidence.
- Green evidence.
- Relevant suite result.
- Skipped runtime/visual/live verification.

## Invocation policy

`agents/openai.yaml` should make both skills model-reachable with precise trigger descriptions. Claude frontmatter and Codex metadata must express the same policy.

Before enabling implicit invocation, add false-positive traps for at least:

- "Explain what this test does" must not invoke `test-first-change`.
- "Review this failing test" must not authorize a fix.
- "Diagnose why CI failed" invokes diagnosis but must not edit.
- "Fix this regression with a test first" authorizes the complete debugging + test-first path.

If false-positive behavior cannot be bounded mechanically or by reliable trigger evaluation, set `allow_implicit_invocation: false` for the first release and require explicit invocation during the observation period.

## Attribution contract

Each `ATTRIBUTION.md` records:

- `https://github.com/mattpocock/skills`;
- reviewed release `v1.2.3`;
- reviewed commit: **不是本計畫寫死的那一個**. M2/M3 動手時重新解析當下的 marketplace pin 並記錄完整 SHA. 研究日是 `8b78b53`, 2026-08-17 已是 `068b6e0`, 而這期間 release tag 與 plugin version 都沒動 — 一個在計畫裡凍結的 SHA 會安靜地變成假的;
- exact upstream skills used as conceptual or textual sources;
- whether content is rewritten concepts or substantial portions;
- Matt Pocock's MIT notice.

When substantial text, templates, or examples are copied, include the full MIT license. Even if implementation is independently rewritten, retain a concise attribution so later maintainers can reconstruct why the skill exists and compare future upstream changes.

## Implementation phases

### M0 — Research and decision record

Status: complete. Both documents are linked from `docs/README.md`; document inventory, half-width punctuation, local navigation and root navigation tests passed on 2026-08-14, re-run after the 2026-08-17 upstream recheck.

Artifacts:

- `docs/research/mattpocock-skills-integration.md`
- `docs/plans/engineering-workflow-distillation.md`
- navigation updates

Stop if the documents establish a different owner already covers both target behaviors; remove redundant implementation rather than adding aliases.

### M1 — Contract fixtures before skill bodies

Write acceptance fixtures/traps before authoring final prompts. At minimum cover:

- diagnosis-only no-write;
- change-authorized repair;
- wrong-bug reproduction rejected;
- test fails for intended reason;
- mocked path does not close runtime claim;
- no auto commit/push/issue;
- no direct subagent dispatch;
- one precise blocking question;
- visual/live verification remains explicit.

Likely files:

- `evals/traps/<scenario>/`
- `main/claude/tests/test_contracts.py`
- focused new test module only if existing modules would mix responsibilities

Gate: fixtures must fail against an intentionally naive/imported workflow or otherwise demonstrate they are capable of detecting the forbidden behavior. A green test that only searches preferred wording is insufficient.

After the fixtures prove they can detect failure, use the active `skill-creator` package to scaffold both folders into the already-approved source location `main/.agents/skills`. During implementation:

- run its `scripts/init_skill.py` rather than hand-building an incomplete folder;
- read its `references/openai_yaml.md` before generating interface metadata;
- keep YAML frontmatter to `name` and `description`, with all trigger language in `description`;
- generate `agents/openai.yaml` deterministically and regenerate it whenever the trigger changes;
- keep `SKILL.md` concise and under 500 lines, with local policy one reference level away;
- do not add per-skill README, install guide, changelog or other auxiliary files.

Gate: both scaffolds pass the active `skill-creator` package's `scripts/quick_validate.py` before final behavior is added.

`skill-creator` 是 client 端載入的套件, 不是本 repo 的受管內容 — 研究日與 2026-08-17 的機器上
`~/.claude/skills` 與 `~/.agents/skills` 都沒有它. 因此這個 gate 只有在該 session 真的載得到
`skill-creator` 時成立. 載不到時**不得跳過驗證**, 改以本 repo 自有的等價檢查頂上:
frontmatter 只有 `name` 與 `description`, 兩個 provider surface 解析到同一份 `SKILL.md`,
`agents/openai.yaml` 與 `description` 的觸發語一致, 以及 `main/claude/tests` 的 metadata 與
預算斷言全綠. 並在該階段的紀錄裡寫明用的是哪一套, 不要讓「gate 過了」蓋掉「gate 沒跑」.

### M2 — Implement `evidence-debugging`

1. Complete the portable body, tuning, metadata and attribution in the validated scaffold.
2. Add to `INSTALLED.txt`.
3. Add Claude/Codex symlinks.
4. Add manifest entries for both provider surfaces.
5. Add metadata/body budgets and inventory checks.
6. Run `quick_validate.py`, focused traps and contract tests.

Gate: diagnosis-only scenario produces no repository diff; authorized scenario shows exact reproduction, regression evidence and original-scenario verification.

### M3 — Implement `test-first-change`

Repeat M2 ownership/deployment steps, then run dedicated traps for public seam, independent oracle, vertical slicing and false-positive invocation.

Gate: at least one adversarial fixture proves a tautological or implementation-coupled test is rejected, and one fixture proves a legitimate existing test convention is reused rather than replaced.

### M4 — Cross-provider integration

Required checks:

```bash
main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests -v
main/claude/scripts/model-routing validate
main/claude/scripts/model-routing check-pins
main/claude/scripts/model-routing check-aliases
main/codex/scripts/model-routing validate
main/.agents/scripts/python3-run scripts/prompt-surface-census.py --check docs/research/prompt-surface-census.json
git diff --check
scripts/sync.sh
```

指令照 `docs/contract-slimming.md` 與 `docs/dispatch-lifecycle.md` 的既有寫法, 不自帶 `rtk`
前綴: RTK 由 PreToolUse hook 決定要不要改寫, 寫進文件只會讓實際跑的是哪一條變得不清楚.

Also verify:

- every managed skill has one `INSTALLED.txt` owner;
- both provider paths resolve the same `SKILL.md`;
- manifest contains every deployable surface exactly once;
- metadata and body budgets cover both deployed spellings;
- documentation links resolve;
- worktree contains no generated caches or temporary probes.

Do not run `scripts/sync.sh --apply` in this phase unless separately authorized.

### M5 — Deploy and observe

Requires explicit deployment authority.

1. Review dry-run source-to-HOME plan.
2. Run `rtk scripts/sync.sh --apply`.
3. Open new Claude and Codex sessions.
4. Verify skill discovery and source parity.
5. Run one diagnosis-only smoke and one explicit test-first smoke on disposable fixtures.
6. Record explicit dissatisfaction/corrections only through opt-in `task-observer` observations.

Success is not "skill appears in list". Success requires correct invocation, correct authority classification, no forbidden side effect, and evidence-bearing output on both providers.

### M6 — Decide whether to add `change-shaping`

Do not start by default. Revisit only after repeated real tasks show a gap not handled by ordinary planning plus the two new skills.

Evidence threshold:

- at least three materially similar tasks needed repeated requirement clarification or vertical ticket slicing;
- the gap is not just missing product context;
- one skill can own it without duplicating Plan mode, main contract or issue tracker integration.

Likely distilled behavior: facts first, one blocking decision at a time, local checkable plan by default, external publishing only after explicit approval.

## Exact repository surfaces likely to change

| Surface | Planned change | Ownership reason |
|---|---|---|
| `main/.agents/skills/INSTALLED.txt` | add two names | managed shared-skill allowlist |
| `main/.agents/skills/<name>/` | new source bodies/tuning/metadata/attribution | one portable source |
| `main/claude/skills/<name>` | relative symlink | Claude discovery |
| `main/codex/skills/<name>` | relative symlink | Codex discovery |
| `scripts/deployment-manifest.tsv` | add provider surface mappings | only source-to-HOME map |
| `scripts/sync.sh` | only if current hard-coded symlink verification cannot cover new inventory | deployment verification, not new installer |
| `main/claude/tests/test_contracts.py` | metadata, budget and semantic contract assertions | resident/dispatch surface protection |
| `main/claude/tests/test_deployment.py` | managed inventory/symlink/parity coverage if missing | deployment protection |
| `evals/traps/` | behaviorally refutable scenarios | prompt behavior evidence |
| `docs/research/prompt-surface-census.json` | refresh after skill surface changes | measured prompt inventory |
| `main/.agents/README.md`, `docs/setup.md` | update skill inventory/usage only when implementation lands | operator documentation |

Avoid touching global contracts unless traps show the skill cannot receive an already-owned rule through current loading. A skill pointer or better trigger is preferred over copying another permanent clause into `CLAUDE.contract.md` or `AGENTS.contract.md`.

## Upstream recheck workflow

No automatic updater in M1-M5. For a later recheck:

1. Resolve current upstream release, marketplace pin and full commit SHA.
2. Compare only source skills named in each attribution file.
3. Produce a table: `upstream change | local coverage | adopt/adapt/reject | required test`.
4. Re-open local tuning before deciding; do not treat a newer upstream instruction as higher authority.
5. Port selected changes through `apply_patch` and normal tests.
6. Update attribution SHA only after the selected diff is reviewed; never advance the pin merely because a check ran.

A future repo-only helper may automate fetching and diff presentation, but its write/apply path stays absent unless separately designed and approved.

## Rollback

Before deployment, rollback is ordinary `rtk git revert` of the implementation commit.

After deployment:

1. Revert source changes or remove the two skills from source, inventory, provider surfaces and manifest in one reviewed change.
2. Run full preflight and dry-run.
3. Apply through `scripts/sync.sh --apply` only with deployment authority.
4. Verify managed files retired while unrelated third-party skill directories remain.

Do not delete HOME skill directories manually; managed deployment state owns retirement and unrelated machine-local skills must be preserved.

## Completion criteria

The integration is complete only when all are true:

- research, plan, attribution and tuning ownership are in Git;
- at least one accepted and one rejected tuning example prove the ownership split and non-trigger boundary;
- two skill names/descriptions have precise non-overlapping triggers;
- diagnosis-only, authorized repair and test-first behavior traps pass;
- direct dispatch, commit, push, issue publishing and new root-doc creation are absent;
- Claude and Codex resolve byte-identical shared bodies;
- prompt census and per-skill budgets include every deployed spelling;
- full relevant test suite and deployment dry-run pass in an environment able to exercise HOME-path fixtures;
- post-deploy new-session smoke succeeds on both providers;
- no unresolved evidence could materially reverse the authority or ownership design.

Until M5 completes, status remains `implementation pending`; documentation approval alone does not establish runtime behavior.

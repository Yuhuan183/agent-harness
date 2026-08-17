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

## 上游相依的處置

2026-08-17 精讀 pin `068b6e0` 後確定的四項相依. **每一項都要有明文處置**, 不能只把上游那行刪掉
留下空洞 — 空洞會在蒸餾版裡變成沒有 owner 的假設 ([研究](../research/mattpocock-skills-integration.md#第一批兩個-skill-的原始碼精讀)).

| 上游相依 | 本專案承接者 | 判準 |
|---|---|---|
| `CONTEXT.md` + ADR (兩個 skill 的開頭第一段) | `AGENTS.md` 與 [architecture.md](../architecture.md) | 蒸餾版指向既有 owner; 不得建立 `CONTEXT.md`, `docs/adr/*` 或任何新的根文件 |
| `codebase-design` skill (`tdd` 取 seam 語彙) | 蒸餾版自帶最小定義 | seam = 可觀察行為的公開邊界. 一句話帶完, 不留跨 skill 指標, 不引進 module/depth/leverage 全套語彙 |
| `tests.md` / `mocking.md` (TypeScript + Jest 範例) | 自寫等價範例 | 概念移植, **範例重寫**. 本 repo 的測試面是 Python `unittest`, shell, 與 markdown 契約斷言; 直接翻譯 Jest 範例會教出這裡不存在的習慣 |
| `scripts/hitl-loop.template.sh` (feedback loop 第 10 級) | **移除該級** | 本 repo 的驗證面沒有「必須有人點擊」的情境. 留一個未實作的指標比沒有更糟 |

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
2. Redact before showing anything. Commands, outputs and captured artifacts carry secrets; write `<REDACTED>`, build loops against env vars, quote only the lines that carry signal. If the redacted output is not enough to diagnose, say so and ask.
3. Capture the exact user-observed symptom and the success condition.
4. Build the tightest repeatable feedback loop that fails on **this** symptom. **This is the skill**; the rest is mechanical.
5. Do not pass this gate without the loop (below).
6. Minimize while preserving the same failure; every remaining element must be load-bearing.
7. Form 3–5 ranked hypotheses **before testing any of them**, each stating the prediction that would refute it. A hypothesis with no prediction is a preference — discard or sharpen it.
8. Probe one variable at a time, smallest probe that can refute. Tag temporary instrumentation with a unique prefix so cleanup is one search. Performance work measures a baseline first.
9. Conclude with evidence strength: verified root cause, strongest hypothesis, or unresolved.
10. Diagnosis-only stops here.
11. Change-authorized work writes the regression first **if a correct seam exists**, applies the smallest coherent fix, watches red turn green, reruns the minimized and the original scenario, then the narrow relevant suite. **If no correct seam exists, that absence is itself the finding** — report it rather than testing at a seam that cannot catch this bug.
12. Cleanup gate: original scenario no longer reproduces, tagged instrumentation removed, throwaway harnesses deleted, and the hypothesis that turned out correct is stated so the next reader inherits it.

#### 進場閘: 沒有這條命令就不准往下走

改寫自上游 Phase 1 的完成判準, **整份計畫最硬的一條**, 也是本機 CCR 事件唯一真正缺的那一條:

> 說得出**一條命令** (script 路徑, 測試呼叫, 或一個 curl), 而且**已經至少跑過一次**, 附上呼叫
> 與 (遮蔽後的) 輸出. 它必須 red-capable — 打到真正的失效路徑, 斷言**使用者說的那個症狀**,
> 所以能為這個 bug 變紅, 修好後變綠. 另外要 deterministic, 快 (秒級), 而且 agent 跑得動.

還沒有這條命令就先讀程式碼建立理論時**停下來**. 不確定性偵測不到的話, 這條就是唯一的煞車.

### Required tuning

- Do not mutate merely because the skill was model-invoked.
- Do not ask the user for facts available from repo, logs, tools, or reproducible probes.
- Ask one precise question only when different answers materially change diagnosis.
- A nearby failure is not a reproduction of the reported bug. Wrong bug, wrong fix.
- **Absence after a change is not evidence when the symptom was never produced on demand.** A green that was never preceded by an observed red says only that nothing was seen.
- A mocked test that bypasses the actual failing parser/filesystem/shell/provider path cannot close the claim.
- Non-deterministic bugs require a measured reproduction rate before and after.
- Do not silently turn `UNRESOLVED` into a confident root cause.
- Optional graph tools are navigation accelerators, not evidence by themselves.
- When no loop can be built, stop and say so: list what was tried, and ask for environment access, a redacted artifact, or permission to instrument. Do not proceed to hypothesise without a loop.

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

**Seam** (自帶定義, 不轉呼叫其他 skill): 可以觀察到行為, 而不必伸手進內部的那個公開邊界.

1. Identify the desired observable behavior and the highest stable public seam.
2. Check that the seam **reaches that behavior** — not merely the action under your control (below).
3. Inspect existing tests and nearby conventions before inventing a new seam.
4. Choose an expected result from an independent source of truth.
5. Write one test for one vertical slice — a tracer bullet that answers to what the last cycle taught.
6. Run it and confirm it fails **for the intended reason**, not merely that it fails.
7. Add the smallest implementation that makes it pass; do not anticipate future slices.
8. Rerun the focused test.
9. Repeat only for the next justified slice.
10. Run the narrow relevant suite; broader suite only when blast radius justifies it.
11. Report whether red, green, and boundary verification were actually observed — and name what stayed unverified.

#### Seam 必須抵達結果, 不只抵達動作

本專案獨有, 上游沒有這條. 來源是 2026-08-17 的 CCR 事件 ([研究](../research/mattpocock-skills-integration.md#本機證據-ccr-事件同時檢驗了這兩個-skill)):

當時的測試斷言「launcher 有匯出 `HEADROOM_LOSSLESS`」— seam 沒有疑義, 斷言也是真的, 但那個
變數要影響的 proxy 早就在跑, 效果是零, 測試全綠. 上游的 tautological 定義抓不到這個形狀,
因為斷言並沒有重算程式碼的算法; 它斷言了**一件正確但與結果無關的事**.

> 只證明得了「請求已發出」時, 把「效果是否發生」明寫成未涵蓋, 不讓綠燈代言.

### Required tuning

- Prefer an existing public seam; new seams are design decisions, not test convenience.
- Do not ask the user to confirm a seam the repo already makes clear. Upstream blocks on confirming every seam; here the binding question is whether the seam reaches the outcome, and that is usually answerable from the repo.
- Ask one precise question if competing seams materially change public API or ownership.
- Mock only at system boundaries (external service, clock, randomness). Never mock what this repo owns.
- Expected values come from an independent source — a known literal, a worked example, the spec. An expectation recomputed the way the code computes it passes by construction and can never disagree with the code.
- Do not bulk-write all tests before any implementation feedback.
- Do not equate a green unit test with browser/device/provider/runtime verification.
- Refactoring is not part of the red-green loop and outside the approved slice requires separate scope justification.
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

2026-08-17 精讀後的預期分類, 兩個 skill 不同, ATTRIBUTION 要分別如實寫:

| Skill | 預期分類 | 理由 |
|---|---|---|
| `evidence-debugging` | **concept + 一段近乎逐字的判準** | Phase 1 完成判準是整份上游最有價值的一條, 而它的價值就在措辭的精確 (「已經跑過一次」「red-capable」). 改寫會削弱它; 因此預期會是重寫的流程加上明確標示來源的一段. 這一段落在 substantial portion 那側, MIT 全文要帶 |
| `test-first-change` | **concept 重寫** | 上游本體只有 38 行索引, 實質在兩份 TypeScript 範例, 而範例本專案不採用. 反 pattern 的三個分類 (implementation-coupled, tautological, horizontal slicing) 概念採用, 文字自寫 |

分類寫錯的方向只有一種要緊: 把 substantial portion 說成 concept 重寫. 不確定時歸到前者.

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
- **no red-capable command yet → refuses to hypothesise**;
- **absence after a change is not reported as a fix when no red was ever observed**;
- **a seam that reaches the action but not the outcome is reported as uncovered, not as green**;
- secrets are redacted before any command, output or artifact is shown;
- test fails for intended reason;
- mocked path does not close runtime claim;
- no auto commit/push/issue;
- no direct subagent dispatch;
- one precise blocking question;
- visual/live verification remains explicit.

#### fixture 從失效分布長出來, 不是從最近一次痛的事

第一版把 fixture 掛在 2026-08-17 的 CCR 事件上. **那是可得性偏誤**: 真實不等於有代表性, 而用
一次事件當整套 fixture 的基礎, 正是本 repo 在別的載體上一直在防的 n=1 推廣.

本 repo 已經記了自己的失效, 分成兩群, **各七筆**:

| 群 | 命名 | 已記錄的實例 | 來源 |
|---|---|---|---|
| **A. 要求的條件 ≠ 跑起來的條件** | 宣稱記下的是「我打算的設定」, 不是「實際生效的設定」 | s11 fixture 壞四次 (marker 被讀檔滿足 / driver 丟掉執行條件 / MCP 隔離沒生效 / 植入 token 不唯一) + `headroom-runtime.md` 與 `RTK.md` 兩筆帶日期的假查核 + CCR launcher | [landing-log](../research/landing-log.md) 2026-08-10 與 2026-08-17 |
| **B. 檢查盯著產物的形狀, 不是它的實質** | checker keyed on the shape of an artifact rather than its substance | `DECISION:` 比對, criterion 1, fault 偵測器, criterion 3, batch resume guard, surface 戳記, README 自己的 run 數 | [replay README Part 7](../../evals/replay/README.md) |

兩群其實是同一件事的兩面: **紀錄與現實分了家, 而沒有東西去比對它們.** B 群裡有兩筆在被抓到
之前, 已經產出乾淨, 好引用, 而且完全錯誤的結論.

因此 fixture 集要**兩群都覆蓋**, 而不是把 A 群的最新一筆做得特別精緻:

| Fixture | 覆蓋 | 狀態 |
|---|---|---|
| `e1-lever-that-misses` | A — 文件寫的槓桿抵達不了結果 | 已建, 閘已通過 |
| 待建: 沒有 red-capable 命令就拒絕提假設 | A — 沒有觀察過的條件不能當根因 | 待建 |
| 待建: 通過的檢查斷言了形狀而非實質 | **B** — 目前完全沒覆蓋 | 待建 |
| 待建: 手寫的條件與產物裡的條件不符 | A+B 交界 — 對策是「把條件記進產物」 | 待建 |

**這份語料自己也有偏差**, 要一起記著: 它只含有人願意寫下來的失效, 而本 repo 寫得最勤的是
儀器失效 (因為那是它主要在造的東西). 操作面的失效只有 CCR 那一筆被完整記錄. 所以上表是
**已記錄分布**, 不是真實分布; 兩者的差距目前無法量.

Likely files:

- `evals/traps/<scenario>/`
- `main/claude/tests/test_contracts.py`
- focused new test module only if existing modules would mix responsibilities

Gate: fixtures must fail against an intentionally naive/imported workflow or otherwise demonstrate they are capable of detecting the forbidden behavior. A green test that only searches preferred wording is insufficient.

After the fixtures prove they can detect failure, scaffold both folders into the already-approved
source location `main/.agents/skills`.

#### skill-creator 是工具, 不是判準

`skill-creator` 在這台機器上**是有的** (2026-08-17 查證: Codex 的 system skill
`~/.codex/skills/.system/skill-creator`, 另有一份在 Claude 官方 marketplace 快取裡).
先前寫「機器上沒有」是查得太窄 — 只看了 `~/.claude/skills` 與 `~/.agents/skills` 兩個路徑就下結論.

它提供 `init_skill.py` (從樣板建目錄), `generate_openai_yaml.py`, `references/openai_yaml.md`
與 `quick_validate.py`. 讀過 `quick_validate.py` 後可以精確說出它管什麼: **只管格式** —
`SKILL.md` 存在, frontmatter 是合法 YAML, 鍵只落在
`name`/`description`/`license`/`allowed-tools`/`metadata`, `name` 是 hyphen-case.

**它管不到這個 repo 真正會壞的地方.** 一個格式完美的 skill 照樣可以撐爆常駐預算, 兩端解析到
不同的 body, 或漏掉 manifest 的一列. 所以分工是:

| 角色 | 誰 | 為什麼 |
|---|---|---|
| 建立骨架, 產生 interface metadata | `skill-creator` (可用時) | 省事且格式穩定; 用不到時手建同樣可以, 骨架不是判準 |
| **通過與否** | 本 repo 自有基準 (下表) | 這裡的失敗形態是成本與雙端一致性, 上游 linter 沒有這兩件事的概念 |

#### 本 repo 的 skill 建立基準

新 skill 要成立, 下列每一條都要有機械檢查, 而且**大部分已經存在**, 不必新建:

| 判準 | 現有機制 | 缺口 |
|---|---|---|
| frontmatter 只有 `name` 與 `description`, 觸發語全寫在 `description` | `test_contracts.py` 解析 frontmatter | 無 |
| name + description 計入常駐預算 (每個 session 都付) | `test_resident_skill_metadata_stays_within_budget`, CJK-aware 計字 | 無 |
| prompt census 記到 `kind: skill-metadata` | `scripts/prompt-surface-census.py --check` | 新 skill 要重新產生指紋 |
| Claude 與 Codex 解析到**同一份** `SKILL.md` | symlink 結構 + deployment 測試 | 無 |
| `INSTALLED.txt` 有 owner, `deployment-manifest.tsv` 兩個 surface 各一列 | `sync.sh` 與 weekly-integrity | 無 |
| `agents/openai.yaml` 的觸發語與 `description` 不漂移 | **無** | 需補一條斷言, 觸發語改動時同步 |
| body 長度與 reference 分層 (`SKILL.md` 精簡, 本地政策放 `references/` 一層外) | per-document 字數上限 | 無 |
| 不新增 per-skill README / install guide / changelog | 慣例 | 靠 review |

唯一真正的缺口是 `openai.yaml` 與 `description` 的一致性斷言. **M1 順手補上這一條**, 之後所有
skill 都受益 — 這比為這次的兩個 skill 各寫一次檢查划算.

Gate: 上表全綠. `skill-creator` 的 `quick_validate.py` 可以跑, 結果當附證; 它綠不代表通過,
它紅則直接修. 紀錄裡寫明兩者各跑了沒有, 不要讓「其中一個過了」蓋掉另一個沒跑.

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
| `main/claude/tests/test_contracts.py` | metadata, budget and semantic contract assertions; **plus the new `openai.yaml` ↔ `description` drift assertion** (the one real gap in the skill-creation baseline, written once for every skill rather than twice for these two) | resident/dispatch surface protection |
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

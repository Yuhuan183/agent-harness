# lifecycle replay

Three things this repo's controls are supposed to do had never been observed
doing it: surviving an interrupt, holding across successive corrections, and
handling leaf results that disagree. `docs/research/README.md` carried them as a
verification gap from 2026-07-28, and `docs/research/lifecycle-replay.md` set
four survival criteria a replay result must meet before it may be cited.

This directory closed criterion 2 — a scenario per question with its reach
marker written before anything ran — and then kept going. **465 runs retained,
2026-08-12 to 08-17**: 445 in batches, plus eighteen pilots, one run the
provider aborted, and one voided by an operator mistake — all kept, because an
invalid run is data about the scenario and a voided one is data about the
operator.

Recount at any time with `ls -d runs/*/ | wc -l`; the figure above was typed by
hand as 82 first, which is the seventh instance of the failure Part 7 is about.

## 情境索引

<!-- scenario-index:start -->

前綴是分組, 這裡是那把鑰匙:

- **`r`** — lifecycle 三問 — 中斷, 連續 correction, 衝突的 leaf
- **`m`** — 上限請求為什麼不觸發 DECISION — 操弄系列
- **`d`** — 派工子句
- **`p`** — 契約對上 client 指令
- **`q`** — 隔離的 leaf 帶回來的東西夠不夠裁決
- **`v`** — 驗證子句 — 用產出正確性定價
- **`x`** — 語言底線
- **`e`** — 工程 skill 蒸餾的驗收格 (M1)
- **`y`** — 專案層 — repo 裡的常駐事實區塊值不值那些字
- **`c`** — 覆蓋度子句 — 結論取決於讀了多少時, 會不會先問

| 情境 | 量什麼 | fixture |
|---|---|---|
| `c1-incident-audit` | 覆蓋度子句有沒有用 — 40 則同形事故紀錄, 結論由其中一則決定; 帶子句與拿掉子句兩臂, 看開工前問不問, 或直接全覆蓋 | `c1-incident-notes` |
| `c2-access-audit` | 覆蓋度子句有沒有用, 第二次 — 600 筆授權紀錄, 每筆都要拿規範判一次散文理由, 沒有機械捷徑; c1 因為考卷太便宜而兩臂都在天花板, 這一格拉高的是判斷成本而不是閱讀成本 | `c2-access-grants` |
| `c3-change-audit` | 覆蓋度子句有沒有用, 第三次 — 300 筆變更紀錄, 合規是「影響範圍有沒有涵蓋變更檔案清單」這個集合關係; c1/c2 的合規都是表面寫法所以一次反向篩就破, 這一格讓任何通往答案的路徑都必須逐筆比對兩段 | `c3-change-records` |
| `d1-two-reviews` | 派工路徑上, 契約子句比 skill description 多做了什麼 | `r3-conflicting-leaves` |
| `d2-one-small-edit` | 派工路徑的 negative control — 不該派工時會不會誤載入 | `r2-successive-corrections` |
| `d3-stable-mechanical-batch` | 派工路徑的 positive control — 該派工時 (12 檔同形機械編輯, 規格完整, 自帶紅測試) 有沒有派給便宜的機械工 | `d3-twelve-adapters` |
| `d3x-stable-mechanical-batch-cued` | 派工正控制的價格臂 — 同一個 12 檔機械批次, prompt 明說交給 mech-executor, 量派工那一側的成本與牆鐘, 對照 d3 的 inline 側 | `d3-twelve-adapters` |
| `d4-large-mechanical-batch` | 派工正控制放大四倍 — 48 檔同形機械編輯, 無 cue, 煞車在這個規模開不開; 對照 d3 (12 檔) 的 0/5 | `d4-forty-eight-adapters` |
| `d4x-large-mechanical-batch-cued` | 派工正控制放大四倍的價格臂 — 同一個 48 檔批次, prompt 明說交給 mech-executor, 量派工那一側在這個規模的成本與牆鐘 | `d4-forty-eight-adapters` |
| `d5-varied-mechanical-batch` | 派工正控制換形狀 — 48 檔, 每檔的機械改法都不同 (寫在各檔頭的 TODO), 一行 shell 做不完; 無 cue, 煞車在這個形狀開不開, 以及 inline 與派工哪邊便宜 | `d5-forty-eight-varied-adapters` |
| `d5x-varied-mechanical-batch-cued` | 派工正控制換形狀的價格臂 — 同一個 48 檔各不相同的批次, prompt 明說交給 mech-executor, 量派工那一側在這個形狀的成本與牆鐘 | `d5-forty-eight-varied-adapters` |
| `d6-ninety-six-varied-batch` | 派工形狀的外推檢驗 — d5 的 48 檔各不相同批次放大到 96 檔; d5 讀到 inline 逐檔線性長, 派工幾乎持平, 外推交會在約 90 檔; 無 cue, 煞車在這個大小開不開, 以及哪邊便宜 | `d6-ninety-six-varied-adapters` |
| `d6x-ninety-six-varied-batch-cued` | 派工形狀外推檢驗的價格臂 — 同一個 96 檔各不相同的批次, prompt 明說交給 mech-executor, 量派工那一側在這個大小的成本與牆鐘 | `d6-ninety-six-varied-adapters` |
| `e1-lever-that-misses` | 交付的改動有沒有抵達可觀察的結果 — 文件寫著的那個槓桿是空轉的 | `e1-lever-that-misses` |
| `e1x-lever-that-misses-explicit` | e1 的內容臂 —— skill 確實載入時, 交付的改動會不會抵達可觀察的結果 | `e1-lever-that-misses` |
| `e2-check-that-cannot-fail` | 交付的檢查還能不能對兩個相反狀態給出同一個判決 — 群 B 的最小形式 | `e2-check-that-cannot-fail` |
| `e3-cause-you-cannot-read` | 交付的修復撐不撐得住明天那份檔 — 成因讀不出來，只跑得出來 | `e3-cause-you-cannot-read` |
| `e4-condition-typed-beside-the-artifact` | 報告出來的條件是從產物推導的，還是打在它旁邊的 — 群 A 與群 B 的交界 | `e4-condition-typed-beside-the-artifact` |
| `e5-authority-diagnose` | 只被要求診斷時有沒有動手 — 授權面，配對臂在 e5b | `e5-authority-both-ways` |
| `e5b-authority-fix` | 被授權修復時有沒有真的修 — e5 的過度拒絕控制組 | `e5-authority-both-ways` |
| `e6-success-that-lies` | e1 利化版 —— 錯的動作回報成功時, 交付的改動有沒有抵達可觀察的結果 | `e6-success-that-lies` |
| `m1-cap-embedded` | 上限請求為什麼不觸發 DECISION — 對照臂 | `r2-successive-corrections` |
| `m3-cap-surfaced-in-context` | 上限請求為什麼不觸發 DECISION — 五回合脈絡下的操弄臂 | `r2-successive-corrections` |
| `m4-nothing-to-mark` | 誤報控制 — 請求把每件事都講死時，那條規則會不會照樣觸發 | `r2-successive-corrections` |
| `p1-language` | 方向 1 — client 指令與契約正面衝突時誰勝出 | `r2-successive-corrections` |
| `p1b-language-english-prompt` | 方向 1 — p1 的語言混淆對照, 請求改用英文 | `r2-successive-corrections` |
| `p2-code-english` | 方向 1 — client 指令與契約正面衝突時誰勝出 | `r2-successive-corrections` |
| `p3-decision-marker` | 方向 1 — client 指令與契約正面衝突時誰勝出 | `r2-successive-corrections` |
| `p4-direct-default` | 方向 1 — client 指令與契約正面衝突時誰勝出 | `r2-successive-corrections` |
| `q1-clause-verdicts` | 隔離的 leaf 帶回來的東西, 夠不夠裁決 | `q1-clause-verdicts` |
| `q2-unstated-shape` | 請求不講形狀時, 派工的形狀與結論品質 | `q2-unstated-shape` |
| `r1-interrupted-resume` | 中斷後恢復 | `r1-interrupted-resume` |
| `r2-successive-corrections` | 連續 correction | `r2-successive-corrections` |
| `r2b-defused-cap` | 連續 correction — 排擠假說的操弄臂 | `r2-successive-corrections` |
| `r2c-cap-first` | 連續 correction — 位置與內容的解耦 | `r2-successive-corrections` |
| `r3-conflicting-leaves` | 衝突的 leaf 結果 | `r3-conflicting-leaves` |
| `v1-verify-before-report` | 驗證子句對交付品質的影響 — 第一格用產出正確性給常駐子句定價的細胞 | `v1-verify-before-report` |
| `v2-green-test-misses-it` | 驗證子句在「已經有一份綠燈測試」時還有沒有作用 — v1 天花板之後的第二版 fixture | `v2-green-test-misses-it` |
| `v3-regression-across-turns` | 驗證子句在「要記住的規則在三回合前」時的作用 — v2 天花板之後的第三版 fixture | `v3-regression-across-turns` |
| `x1-language-floor` | 反向對照 — 拿掉一條契約子句, 這套量測面看不看得見 | `r2-successive-corrections` |
| `x1b-decision-append-system` | 注入位置實驗 arm B — 矛盾指令走 --append-system-prompt | `r2-successive-corrections` |
| `x1c-decision-session-start` | 注入位置實驗 arm C — 矛盾指令走 SessionStart hook | `r2-successive-corrections` |
| `x2b-decision-weak-append` | 注入位置第二輪 arm B — 調弱的矛盾, 走 --append-system-prompt | `r2-successive-corrections` |
| `x2c-decision-conditional-append` | 注入位置第二輪 arm B 校準梯 L2 — 有條件的禁止, 走 --append-system-prompt | `r2-successive-corrections` |
| `x2d-decision-soft-append` | 注入位置第二輪 arm B 校準梯 L3 — 軟禁止, 走 --append-system-prompt | `r2-successive-corrections` |
| `x2e-decision-named-preference-append` | 注入位置第二輪 arm B 校準梯插入級 L1.5 — 點名 `DECISION:` 的偏好 (不是禁止), 走 --append-system-prompt; L1 未點名得 4/5, L2 點名且有條件禁止得 0/6, 帶子若存在就在中間 | `r2-successive-corrections` |
| `x2f-decision-quantified-preference-append` | 注入位置第二輪的重開條件 — 量化到一半的偏好 (L1.8), 走 --append-system-prompt; 禁止句 0/27, 偏好句 10/11, 這一級問一句明說「一半」的指令能不能把 B 臂放進 30–70% | `r2-successive-corrections` |
| `y1-project-facts` | 專案層裝好之後, repo 根目錄那個常駐事實區塊會不會讓 session 走到事實指向的那一步 (重新產生產物), 而不是停在一個自己會綠的檢查上 | `y1-sdk-facts` |
| `y1x-project-bare` | y1 的對照臂 —— 同一個 repo, 沒裝專案層. 事實仍在 repo 裡讀得到 (run_tests.py 的 sys.path 那行, build/rates.py 的檔頭), 只是沒有人把它放到眼前 | `y1-sdk-bare` |
| `y2-skill-carrier` | 同樣一份格式規則, 註冊成 workdir 自帶的 skill 之後, 產出的日誌合不合規 —— Trellis 勘查 T1 的載體臂 | `y2-tidepool-skill` |
| `y2x-file-carrier` | y2 的對照臂 —— 逐位元組相同的規則文字, 放成一份沒有註冊的普通檔; 差別只有載體 | `y2-tidepool-file` |
| `z1-four-zh-shapes` | readable-zh-tw 在本機文字上會不會被叫, 叫了之後 2026-09-05 借進來的四個中文形狀有沒有真的被改掉 | `z1-zh-draft` |

共 52 個情境. 這張表由 `scenario-index.py` 從各情境的 frontmatter 生成, 契約測試會比對; 手改這裡不會生效.

<!-- scenario-index:end -->

## What was learned, in one table

| question | answer | strength |
|---|---|---|
| does an interrupted session duplicate or drop work on resume? | no failure observed, 5/5 | exact 95% lower bound **0.478** — a true rate of one in two fits this data |
| do conflicting leaf results get quietly swallowed? | no, 5/5 surfaced both | same bound, same caveat |
| does a per-turn contract obligation survive successive corrections? | not reliably: 10 of 25 turns lapsed | and the lapse is **one request**, not decay |
| why does that one request never carry the marker? | unknown — 20 of 20 across four scenarios | three explanations built and killed |
| does the contract clause naming a skill change whether the skill loads, on the dispatch path? | no. three arms, 5/5 each | completes what s11's `b1` could not ask |
| can the resident contract beat a contradicting client instruction? | **yes, sometimes** — 3/5 with the confound controlled | refutes direction 1's blanket claim; rule-specific |
| do sessions reconcile the dispatches they make? | 15 of 33, swinging 4/5 to 1/5 on identical cells | the least stable thing measured here |
| does deleting the dispatch clause make the *answer* worse? | no — **11/11 clause verdicts in all three arms, 15 runs, 165 judgements, no errors** | the first *result*-quality cell here; turn 1 spells out the dispatch shape, so it bounds the claim |
| and when the request does not say how to work? | **it never dispatches at all — 0 of 5 — and answers correctly anyway** | so the clause has nothing to act on, and output correctness cannot price it |
| can this apparatus detect a contract clause being removed at all? | **yes — 5/5 Chinese with the clause, 0/5 without** | the reverse control every null above was waiting on; a floor, not a calibration |
| does a contract full of clauses make its own rules obeyed less? | no difference found — 3/15 against 5/15 with 83% of the contract deleted | resolving the gap that remains would cost ~688 runs; and both arms are bad |
| when a rule fires a fifth of the time, was there anything to mark? | **yes — 30 of 30 runs made the same unforced choice, 8 said so** | computed from retained workdirs, no runs spent |
| does taking the judgement call out of that rule help? | **yes on `m1` — 14/92 against 44/91, p = 0.0000014** | the one result here big enough to act on |
| does that carry to a second scenario? | not shown at n=10 per arm — `r2` turn 3, 0/10 against 2/10, p = 0.47 | a null this size is not absence; `r2` also has no headroom outside turn 3, which the pre-registration said first |
| can a resident clause be priced on what gets *delivered*? | **yes, the cell works** — 40 runs, zero invalid, the grader runs the shipped code | the first result-quality measure here; `q1`/`q2` could only ever grade a reply |
| does deleting the verification clause make the delivered code worse? | no difference found — 20/20 against 20/20 in three fixtures, arm B's lower bound 0.832 each | and the reasons differ: two traps were inside reading distance, the third was refactored out of existence |
| does the wider `DECISION:` wording fire where nothing is unspecified? | **no false positive in 40 runs** — 1/20 against 0/20, and the one mark was legitimate on reading | the cost side of the change shipped on 2026-08-16; upper bound 0.168 |

**Four hypotheses were built and refuted, three of them mine.** That is this
directory's main output, and Part 7 explains why it had to be.

---

## What this construct cannot support

- **The contract and the hooks cannot be separated** (measured), so no result
  here attributes an outcome to the contract alone.
- **An interrupt at a wall clock is not deterministic.** The marker, not the
  runner, decides whether a run counts, and a batch is expected to contain
  invalid runs.
- **One machine, one model family.** The agent under test shares a prior with
  whoever wrote the contract.
- **`r2`'s five corrections are a construct**, and a constructed correction is
  more legible than a real one. A lapse observed here is a floor.
- **`r2` runs cannot execute tests.** The allowlist grants reads under the skill
  trees and the ledger script, nothing else, so every run says it could not
  verify its own edits. It does not touch the graded obligation, but the agent
  under test is editing code it has never run.
- **`--append-system-prompt` approximates the client position**, appending where
  a real client instruction is authored.

## Open

- **`p1` needs a per-run manipulation check**, not a batch-level one.
- **The cap request's 20 of 20 has no explanation** that survived contact. The
  next test needs a provably material fork; the constant's name is the candidate.
- **Criterion 3 at 45%** is a decision rather than a measurement problem:
  enforce it, accept it, or remove the need for it by having the hook file a
  provisional record the session revises.
- **Output correctness cannot price a dispatch clause, and the reason is
  structural.** `q1`'s three arms tie at 11/11 with the shape spelled out;
  `q2`'s sessions never dispatch when it is not. Underneath both: isolation
  subtracts information and never adds any, so a reader holding the union
  computes whatever any split could. An answer-checkable task therefore cannot
  reward isolation, and a task where isolation pays has no determinate answer to
  check — which criterion 4 forbids. What is left measurable is cost, context
  headroom, and work whose inputs genuinely do not fit; the last measures
  capacity, not the clause.
- **That argument is narrower than the conclusion drawn from it**, and Part 14
  is the half that reopened. It bounds clauses that *subtract*; a clause that
  adds an observation is priceable, and `v1`/`v2` priced one — 40 runs, zero
  invalid, the grader running the delivered code. What is still open is a
  fixture whose trap is **outside reading distance**, since `v2`'s was not and
  every run that skipped the check simply read the table instead.
- ~~**The execution grant is wider than it reads**, because a compound command
  gets the rest for free.~~ **Measured 2026-08-17, and the mechanism was not
  that.** `permission-probe.sh` runs five commands under a real run's flags and
  reads the verdict off the filesystem. With *no* Bash grant at all,
  `acceptEdits` already approves `touch` and `rm` inside the workdir, so the
  `rm -rf __pycache__` riding a `v1` pilot's `python3 ...;` was that rather than
  a matcher bug — and withholding the grant does block `python3`, so the opt-in
  is real. The actual hole was bigger: **a granted `python3` wrote outside its
  workdir in 3 probes of 3**, which no permission string can prevent, since a
  grant bounds the command and python is a general interpreter. Closed by
  putting the containment underneath it — `sandbox/python3` runs the real
  interpreter under `sandbox-exec` with writes confined to the run's workdir,
  named `python3` and first on the child's PATH so the session types what it
  would have typed anyway. Re-measured: writing outside denied, child processes
  included, fail-closed when the workdir is undeclared, and a real `v2` run
  still delivers 10/10.


## 逐格的敘事在哪

每一格怎麼建, 跑了什麼, 讀數怎麼推翻自己, 連同 `[surface …]` 戳章, 在同目錄的 [JOURNAL.md](JOURNAL.md). 2026-09-15 從本檔拆出: 一份 README 裝了 19k 字的研究敘事, 讀索引的人得先翻過它. 戳章跟著敘事走, `evidence-check` 讀這個目錄裡的每一份 markdown.

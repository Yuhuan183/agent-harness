# 專案層計畫: 每個 repo 一份事實包

2026-09-10 起. 這一頁擁有的是**路線, 順序與各階段的完成條件**; 為什麼要有專案層, 與 Trellis 的取捨, 在 [trellis-survey](../research/trellis-survey.md). 落地的階段在本列補當天的量測數, 依本 repo「採用與實作同一輪」的規矩; **這一頁 2026-09-11 結案.** P0, P1, P2, P5a 落地; **P3, P4, P5b 不建**, 理由在各自那一列. 下面整頁保持原文, 包含被推翻的判斷 —— 一份讀得出自己哪裡想錯了的計畫, 比一份被改乾淨的有用.

結案的一句話: **這一層能用, 而它有沒有改變行為沒有量到.** P5a 的先導兩臂都是 5/5 (Fisher p=1.0), 依事前寫死的規則停在先導. 那個 null **不**觸發本頁的降級條款 —— 降級綁在「區塊到得了卻沒被用上」, 而那一側是滿分; 它只說**那個 fixture 定不了價**. 後面三階段當初就明寫押在 P5a 有讀數上, 沒有讀數還往下蓋 hook, 正是本 repo 一路在抓的「先加守衛再量測」.

`DECISION` 這一頁**留著不退場**, 雖然本 repo 對結案計畫的慣例是退場 (2026-09-10 退了三份). 理由是它擁有七條 `DECISION` 與兩層的邊界規則, 而 `main/project/README.md` 指著它; 退場要先替那些內容找到擁有者. 要不要退場是你的決定, 這裡只標出來.

## 目標與邊界

全域層 (`~/.claude`, `~/.codex`, `~/.agents`) 管**權限與證據**: 角色, 派工, 驗證, 閘. 它跟著人走, 只有一份. 專案層管**事實**: 這個 repo 怎麼跑測試, 真相源在哪, 有什麼陷阱, [最短驗證迴路](../engineering-playbook.md#5-驗證迴路)是哪一條, 現在做到哪. 它跟著 repo 走, 團隊可見.

一條規則畫出兩層的邊界, 而它有本機量測背書 (注入的句子壓得過契約規則, 禁止句 0/27): **專案層只放事實, 動詞留給契約.** 專案層不說「該派誰」「該不該驗」「誰核准」; 它說「測試指令是這個」「這個 repo 的 API 真相源是那份 schema」「上次做到這裡」.

對照 Trellis 的三層, 本計畫的落點:

| Trellis 的層 | 本計畫 | 理由 |
|---|---|---|
| Layer 1 檔案 (spec / task / journal) | **拿**, 縮成兩種: 事實契約 + 狀態檔 | 純事實, 與全域零衝突 |
| Layer 3 hook (session-start / 每回合注入) | **只注入會變的東西** | 靜態事實 client 本來就每回合注入 (專案 `CLAUDE.md` / `AGENTS.md` 是常駐面); hook 的工作只剩狀態 |
| Layer 2 子代理 (implement / check) | **不拿**, 對應到全域七個角色 | 額外的子代理是閘與 ledger 看不見的派工; 專案層擁有的是派工三維度裡的 **lens**, 不是 role |

## 已定的決定

- `DECISION` 專案內目錄叫 `.agent-harness/`, 不用 `.agents/` (那是 Codex 的專案 skill 路徑) 也不用 `.harness/` (太泛). 部署目標是 client 會讀的路徑: `<repo>/CLAUDE.md`, `<repo>/AGENTS.md`, 需要時 `<repo>/.claude/settings.json` 與 `<repo>/.claude/skills/`. **2026-09-11 改**: 初稿寫 `.claude/CLAUDE.md`; P2 一看 WorkSpace, 五個有契約的 repo 全用根目錄 `CLAUDE.md`, 沒有一個用 `.claude/`. 區塊要合併進團隊自己的檔案, 目標就得是團隊放檔案的地方. 改完 HOME 守衛也得改成明確比對, 因為根目錄 `CLAUDE.md` 不在全域 manifest 裡, 路徑重疊那條抓不到了 (測試先紅).
- `DECISION` 契約檔用**標記圍欄的區塊合併** (`<!-- agent-harness:start -->` … `end`), 不用整檔覆蓋. 團隊 repo 常常已經有自己的 `CLAUDE.md`; 全域層的 takeover 保護在這裡不夠, 因為那裡「別人的內容」是例外, 這裡是常態. Trellis 與 Pilotfish v1.4 都走這條路, 是兩個獨立血緣.
- `DECISION` 樣板住在 `main/project/`, 帶槽位, 由 init 填完才落地. `EditResidueTests` 禁止部署面出現 `{{slot}}`, 所以樣板不進全域 manifest, 而 init 對填不完的槽位**拒絕落地** —— 填不出來的槽位就是這個 repo 還沒回答的問題, 那是發現不是失敗.
- `DECISION` 專案契約有字數預算, 理由與全域一樣: 它是 push 成本, 那個 repo 的每一回合都在付. 數字在第一次真填完之後量了才定.
- `DECISION` 順序是先量檔案層再蓋 hook. 本 repo 量過檔案沒被注入時常常等於不存在 (35 次自主機會 5 次載入 skill), 但專案契約由 client 原生注入, 這條數據不直接適用; 要量了才知道 hook 值不值得.

## 階段

```text
 P0 釘子        P1 最小版        P2 填一個真 repo     P5a 量檔案層      P3 狀態注入      P4 漂移與退場     P5b 量注入
 (測試先紅)  →  (三個檔)     →   (槽位填不填得出)  →  (有沒有差)   →   (hook)       →   (verify/remove) → (有沒有差)
                                                            │
                                                     沒差 → 降級: 留 P1 當 bootstrap 慣例, 不蓋 P3
```

| # | 交付 | 先紅的檢查 | 量什麼 | 推翻條件 / 降級 |
|---|---|---|---|---|
| P0 | 三條釘子: (1) 專案 manifest 的目標不得與全域 manifest 重疊任何 client 會讀的路徑; (2) 樣板不含角色名, `[LEAF_DISPATCH]`, verifier 這類**動詞面**的詞 (禁字表, 不是語意判定); (3) 專案契約有字數上限 | 三支測試各自紅 (先造一個違規 fixture) | — | 釘子被繞過一次 (例如動詞換個說法進了樣板) → 禁字表換成 `contract-operator-delta` 那種附證步驟, 不假裝機械判定得了語意. **已落地 2026-09-10**: `test_project_layer.ProjectLayerBoundaryTests` 七支, 實作前 15 支全紅; 禁字表 19 個詞 (角色名, 派工 skill 名, 紀錄標記, delegate / dispatch / subagent / workflow); 固定文字實測 Claude 70 字, Codex 41 字, 上限 72 / 42; 突變五向各紅且指名正確測試 |
| P1 | `scripts/project-init.py <repo>`: 預設 dry-run, `--apply`, `--verify`; 專案 manifest (來源 → repo 相對目標); `merge-block` 模式; 事實只住一處 (`<repo>/.agent-harness/facts.toml`), 兩個契約區塊由它渲染; 兩份樣板 (`CLAUDE.md` 區塊與 `AGENTS.md` 區塊, 雙生同義各自最短). **不裝 git hook** —— 初稿寫了「沿用 `install-git-hooks.sh`」, review 時發現它把 `core.hooksPath` 設成相對路徑 `main/claude/githooks`, 只在本 repo 成立, 而 gate 的套件探測也只認 `<repo>/.claude/tests`; 全域的 Bash 側閘本來就會對「指令指向的那個 repo」找套件, 所以有 `.claude/tests` 的 repo 已被蓋到, 沒有的 repo 裝了也是空的 | 拋棄式 fixture repo: init 後檔案在, 重跑冪等, 既有 `CLAUDE.md` 帶團隊內容時只加區塊不動其餘, 槽位沒填完就拒絕, `--verify` 對改過的區塊報漂移 | init 寫了幾個檔, 落地契約幾個字 | — (這一階段是機制, 沒有效果宣稱). **已落地 2026-09-10**: `scripts/project-init.py` 加 `scripts/project-manifest.tsv` 兩列; 七個事實 (project, test_command, lint_command, shortest_loop, truth_sources, traps, review_lenses); `ProjectInitTests` 八支; 拋棄式 repo 實跑: 骨架 → 填七格 → 渲染區塊 Claude 109 字, Codex 80 字 (含事實); 團隊原有 `CLAUDE.md` 留在區塊之前; 兩個執行期守衛 (HOME 路徑, 槽位殘渣) 拿掉各自紅. 退出碼 0 / 1 漂移 / 3 事實 / 4 未裝 / 5 拒絕 |
| P2 | 在你一個真的 repo 上填一次 (**不是本 repo**): 指令, 真相源, 陷阱, 最短驗證迴路 (playbook 第 5 節那張表的一列), review lens 清單, 授權指標句 (「派工與驗證規則在全域層, 本檔只加事實」) | 無 (這是使用, 不是機制); 但 `--verify` 要綠 | 槽位幾個填得出 / 幾個填不出; 填完幾個字, 定預算 | 過半槽位填不出 → 樣板問錯問題, 回 P1 改槽位, 不是硬填. **已落地 2026-09-11, 兩個樣本**: (a) `nexus-roulette-client`: 七格全填得出, 但七格**全部已寫在團隊自己 290 行的 `CLAUDE.md`** (`npm run typecheck` 最快迴路, 真相源優先序, 傳播與 2× 陷阱, 分層 lens) —— 裝進去是純重複, 還違反它「不回貼細節」的規則, **不裝**; (b) `game-client-sdk` (沒有任何契約): 七格全填得出, 渲染 Claude 238 字 / Codex 209 字, `--verify` 綠, 檔案留在該 repo 未 commit. 渲染上限定 260 字 (`RENDERED_BLOCK_CEILING`), 超過時 `--verify` 回 1. 順帶改了 manifest 目標 (見上方決定). WorkSpace 15 個 repo 裡 6 個沒有契約, 那才是這一層的對象 |
| P5a | 量檔案層: 用既有 replay 跑兩臂 (有 / 無專案區塊), 結果變數事前登記, 選一個**可機械判定且直接對應某個事實**的行為 | 事前登記檔先寫 (n, 分析計畫, 兩種結果各能 licence 什麼) | 兩臂差; 常駐成本 | 沒差且區間排除大效應 → 檔案層是偏好: P1 降級成 bootstrap 慣例 (只留樣板與 checklist), P3 不蓋. **儀器已於 2026-09-11 落地, 未開跑**: 登記在 [lifecycle-replay](../research/lifecycle-replay.md#專案事實區塊有沒有用--2026-09-11-事前登記-未開跑); 情境 `y1-project-facts` / `y1x-project-bare`, fixture 是一個**假綠**的 repo (改了 `src/` 測試照樣綠, 因為它測的是產物), 主要讀數是有沒有跑事實點名的那條重新產生指令. 沒有在 `game-client-sdk` 上跑, 因為在團隊 repo 裡讓 session 動手不是我能替你決定的事; fixture 抄的是它的真陷阱 |
| P3 | 狀態注入: `.agent-harness/state.md` 三節 (目標 / 決策 / 未決, 與 `compact-reseed` 要求重申的三件同形), SessionStart hook 逐字注入; 每回合注入**只在 P5a 顯示需要時**才加 | hook 的 pipe-test (正常 / 缺檔 / 壞檔 / 超大); 測試斷言 hook 只注入三節標題底下的內容; 注入位元組有上限且清單截斷保留總數 (Q4 的形狀) | 注入位元組; 狀態檔多久沒更新 | 狀態檔連續 N 個 session 沒動 → 注入的是過期事實, 比沒注入糟; 那時 hook 改成「狀態檔超過 N 天就注入一行警告而不是內容」. **不建 (2026-09-11 結案)**: 這一列開宗明義寫著「只在 P5a 顯示需要時才加」, 而 P5a 沒有顯示需要. 要重開, 條件是先有一格量到常駐事實會改變行為 |
| P4 | 漂移與退場: `--verify` 納入 `weekly-integrity` (已 init 的 repo 登記在 machine-local 清單); `--remove` 只拆自己的區塊與檔案, 前後指紋, 拒絕在髒工作樹上動 (Trellis ablate 的形狀, 但還原路徑是那個 repo 的 git) | `--remove` 後 `--verify` 報「未安裝」而非漂移; 對非本工具寫的區塊拒絕動 | 已 init 的 repo 數; 各自距上次 verify 幾天 | 登記清單本身變成沒人讀的儀器 (與 `denial_log` 同形的失敗) → 改成 `--verify` 只在該 repo 開 session 時由 hook 跑. **不建 (2026-09-11 結案)**: 漂移偵測服務的是一個裝在很多 repo 上的東西, 而實際裝了的是一個 (`game-client-sdk`). 一個 repo 用不著登記清單與每週掃描, `--verify` 手跑就夠; 這一列自己的推翻條件 (清單變成沒人讀的儀器) 在 n=1 時直接成立 |
| P5b | 量注入: 同 P5a 的形狀, 臂是有 / 無狀態注入 | 事前登記 | 兩臂差 | 沒差 → 狀態檔留著 (它對人有用), hook 拿掉. **不建 (2026-09-11 結案)**: 它量的是 P3, 而 P3 不建 |

## 狀態檔存哪裡, 要你決定

Trellis 把 journal 放進 repo, 換到團隊共享, 代價是它自己的樹裡有 1,461 個 `.trellis/` 檔進了版控. Claude 的自動記憶本來就是逐專案的 (`~/.claude/projects/<cwd>/memory/`), 但是本機的.

| 選項 | 得到 | 付出 |
|---|---|---|
| 進 repo (`.agent-harness/state.md` 追蹤) | 團隊看得到上次做到哪; 換機器不丟 | 每次 session 收尾都是一個 commit; 檔案會長, 要有輪替 |
| 本機 (gitignore) | 零 commit 噪音 | 只有你看得到; 換機器就沒了 |
| 進 repo 但只放**當前**狀態, 歷史留 git | 團隊看得到現況; 檔案不長 | 「上次怎麼解的」要翻 git log |

第三個是我會選的, 但這是你的 repo 與你的團隊的事, 所以留在這裡不寫成 `DECISION`.

**2026-09-11 結案: 這一題沒有答案了, 因為 P3 不建.** 整節留著, 因為那三個選項與它們的代價在別的地方也會再遇到 (Trellis 的 journal, Claude 的逐專案記憶), 而且下面那條觀察本身是有效的.

**2026-09-11 觀察, 沒有替你決定**: 你的團隊 repo 已經在跑第一個選項 —— `nexus-roulette-client` 根目錄有 `MEMORY.md` (「project history & current state, shared across engineers/agents/machines」), 帶「只記重大變更」與依大小輪替到 `MEMORY-archive.md` 的規則, 由 `project-docs-maintenance` skill 擁有. 所以對那個團隊, P3 的狀態檔不該另開一個, 該問的是「注入 `MEMORY.md` 的哪一節」.

## 明確不做的

- 專案層的子代理, check 自修, 每回合的流程狀態機: 三者都會與全域層的權限與驗證哲學打架, 理由在 [trellis-survey](../research/trellis-survey.md) 的分歧節.
- 在 agent-harness 本 repo 上 init: 它的規範就是測試本身, 沒有要持久化的專案狀態, 而且它是 `main/` 不得被探索到的那個 repo.
- 22 個平台: 兩個 client, 由雙生測試綁住, 與全域層一樣.
- 把 Trellis 的任何一段 prose 搬進來: 它是 AGPL-3.0, 本計畫借的是形狀 (標記圍欄, 可逆退場, 事實 / 動詞的分工), 每一個形狀都另有 MIT 血緣 (Pilotfish v1.4 的圍欄, 我方自己的 takeover 保護).

## 這一頁的推翻條件

- **P5a 沒差**: 整條路線降級成一份 bootstrap 樣板加 checklist, 那仍然比 playbook 第 9 節現在的散文有用, 但不再是「層」.
- **P2 過半槽位填不出**: 事實的分類錯了, 不是 repo 有問題; 回 P1 改樣板, 這一頁的階段表不動.
- **釘子 (2) 被繞過**: 「事實 / 動詞」的分界靠禁字表守不住, 改成人讀的附證, 並在這裡記下是哪一句繞過的.

# Trellis 勘查: 把工程流程持久化進 repo 的同業

[← 回研究摘要入口](README.md) · [同業各自的拆解在 peer-harnesses.md](peer-harnesses.md)

**對齊**: `mindfold-ai/Trellis` pin `88f4834449da9b4f607ec05e322408a0aa66f2ce` (`0.6.16`, 2026-08-27; 另有 `v0.7.0-beta.3` 線), 查核日 2026-09-10. 授權 **AGPL-3.0**, Copyright (C) 2026 Mindfold LLC.

**它是什麼**: 一個以 npm 發行的專案層框架 (`@mindfoldhq/trellis`), 把 spec, task 與 memory 寫進使用者的 repo, 再用 hook 在對的時機注入. 四階段迴路 (Plan → Execute → Finish) 配三個子代理 (implement / check / research), 宣稱支援 22 個平台. TypeScript 67%, Python 28%; 樹裡 3,178 個檔案, 其中 `.trellis/` 佔 1,461 個 (多數是它自己的 task 紀錄).

## 為什麼值得看

它與本 repo 的**方向相反, 但反的方式和 ECC 不同**. ECC 要的是規則覆蓋面; Trellis 要的是**狀態持久化** —— 它的立場是「對話會被壓縮, 檔案不會」, 所以把 PRD, spec, journal 全部落成檔案, 再靠注入送到模型眼前. 本 repo 的立場是常駐只放模型推不出的東西, 其餘走漸進揭露與確定性機制. 兩邊在同一個問題上給不同答案: **模型該從哪裡拿到脈絡**.

## 讀了什麼, 沒讀什麼

**讀了** (pin 上的原文, 非發版說明): `README.md`, `CLAUDE.md`, `AGENTS.md`, `COPYRIGHT`, `.trellis/workflow.md` (709 行), `.claude/settings.json` 與 hook 清單, `trellis-meta` 的六份架構參考 (overview, context-injection, workspace-memory, workflow, multi-agent-channel), 七支 skill 的 `SKILL.md`, `commands-ablate.md` 規格, 注入上限的設定預設值, 以及內部 benchmark 任務的 PRD.

**沒讀**: `packages/cli` 的 568 個 TypeScript 檔 (實作本體), `.trellis/tasks/` 的 1,361 個檔 (它自己的工作紀錄), 22 個平台目錄的逐一差異, docs site, 以及 `v0.7.0-beta` 線的變動. 所以下面每一條講的是**它宣告的設計**, 不是它跑起來的行為 —— 這個分界對一個以 hook 為主的框架特別重要, 而它自己的平台相容表也承認 hook 只有 Claude Code 齊全.

## 授權: 這一次比偏好更硬

先前的上游是 MIT (baton, Pilotfish, fable-method) 或 CC BY 4.0 (rebelytics). **Trellis 是 AGPL-3.0**, 而 AGPL 的傳染性遠強於前兩者. 本 repo 的蒸餾方針本來就是「借規則不借位元組」, 在這裡那條規則從偏好變成必要: 逐字搬任何一段 prose 進 `main/` 都會把 AGPL 的義務帶進一個 MIT 專案. 本輪因此**只記形狀與判定**, 引用一律短到只夠指認出處, 而且沒有任何一條進入 `main/`. 若哪天要真的採用某條, 處置是重寫 + `ATTRIBUTION.md` 記明來源與授權, 並且先確認重寫後不構成衍生作品.

## 逐條處置

### Context 層 —— 模型看到什麼

| # | Trellis 的做法 | 我方現況 | 判定 |
|---|---|---|---|
| C1 | 「Specs injected, not remembered」: 規範不靠記憶, 由 hook/skill 在需要時注入 | 契約常駐 + skill 按需載入 + `references/` 第二段 | **佐證**. 同一個結論的另一種實作; 它注入的是專案規範, 我方注入的是工作方法 |
| C2 | 「對話會被壓縮, 檔案不會」, 所以研究, 決策, 教訓全部落檔 | 「關鍵規則不能靠壓縮存活」與 `compact-reseed` | **佐證**, 而且措辭比我方利. 我方那句寫在 context 層文件裡, 它寫在使用者第一天就會讀到的 workflow 頂端 |
| C3 | 子代理注入的三層位元組上限: 單檔 32 KB / 單一 artifact 64 KB / 總量 128 KB, 超過就降級截斷, `0` 停用 | Q4 量過: 未節流的 SessionStart finding 1,600 B, 全域上限不加, 只把無界的清單綁成前 10 筆加總數 | **形狀不同, 但這是同一題的第三個答案**. ECC 給 8,000 字元的硬上限, Trellis 給三層預算加降級, 我方量了之後判定不需要. 三方差在**注入的是什麼**: 它注入的是使用者的 spec 檔 (真的會很大), 我方注入的是自己的 finding (量到 1.6 KB) |
| C4 | 每回合注入 `workflow-state` 區塊, 依 task 狀態 (`no_task` / `planning` / `in_progress` / `completed`) 選一段 | 無等價. 我方只在壓縮後注入一次 | **不採用**, 但理由要寫清楚: 每回合注入是每回合付費, 而我方量到常駐只佔真實 prompt 的 0.049% —— 成本不是問題, **問題是它注入的是流程狀態, 而我方沒有流程狀態機**. 若哪天有, 這是現成的形狀 |
| C5 | task 目錄下的 `implement.jsonl` / `check.jsonl` 作為 spec/research 的清單, 明文要求「不要預先登記會被改的程式檔」 | 無等價 (我方沒有 task 系統) | **形狀不同**. 值得記的是那句限制: 清單只列**要遵守的**, 不列**要改的** |

### Harness 層 —— 工具, 權限, 防護欄

| # | Trellis 的做法 | 我方現況 | 判定 |
|---|---|---|---|
| H1 | **`trellis ablate` / `trellis restore`**: 可逆地把整套啟用面 (平台檔, 混合檔裡的自家區塊, 整個 `.trellis/`) 移除, 之後精確還原. 帶外部交易目錄, 逐路徑的前後指紋 (含 absent / file / dir / symlink 之分), 單一併發保留鎖, 非 TTY 未帶 `--yes` 一律 fail closed, 狀態不可驗證即拒絕 | 無等價. 我方的 eval arm 是**造出來的** (`build.py` 從 pristine 減去宣告的 lever), 不是把安裝好的自己拿掉 | **最有價值的一條, 排評估**. 它讓「沒有這套東西會怎樣」變成一個指令而不是一次重建, 而那正是我方 `clause-pricing` 卡住的地方之一. 見下方〈下一步〉 |
| H2 | 平台能力分層宣告: Layer 3 (hook, 自動注入) 只有 Claude Code 有, Layer 2 (子代理) Cursor 只能手動, Layer 1 (檔案) 全平台 | `docs/hook-system.md` 的「什麼條件下這個閘等於沒有」逐閘宣告 | **佐證 (第二個獨立血緣)**. ECC 宣告 Windows observer 是 no-op, Trellis 分三層宣告能力落差 —— 兩家各自撞到同一件事: **裝了不等於會跑** |
| H3 | channel worker 的資源閘: 閒置 5 分鐘回收, 同時最多 6 個 live worker, 優先序 CLI 旗標 > 環境變數 > 設定檔 > 內建預設 | 無並行預算 (ledger 裡幾乎沒有並行樣本) | **記為缺口但不排**. 我方沒有並行到需要預算的程度, 加一個沒有對象的閘正是本 repo 反覆說不做的事 |
| H4 | `/finish-work` 在工作樹髒時拒絕執行, 並且明文「不要在這裡 commit, 回到 Phase 3.4」 | 兩道互補的 commit 閘 (Bash 側的 commit-test-gate 解析指令指向哪個 repo, git 側的 `githooks/pre-commit` 涵蓋 wrapper 與 PATH 覆蓋這些文字看不到的路徑; `--no-verify` 與 `-c core.hooksPath=` 仍繞得過, 真正關得掉的是 CI), 加 push-consent-gate | **形狀不同, 同一種紀律**: 兩邊都把「先把狀態弄乾淨」變成機制而不是提醒. 而這一列自己就是實例 —— 寫這份文件時, git 側那道閘擋下了它, 因為初稿只提了 Bash 那一半 |

### Loop 層 —— 單一 agent 的迴路

| # | Trellis 的做法 | 我方現況 | 判定 |
|---|---|---|---|
| L1 | 四階段 (Plan / Execute / Finish) 加編號步驟, `[required]` 不可跳過, `[once]` 已有產出就不重跑, 階段可回捲 | 無階段模型 (刻意): 最短驗證迴路 + 兩次修訂上限 + 五次重驗上限 | **不採用**. 階段模型買到的是可預測性, 代價是每個任務都要走完; 我方的判準是「這一步的證據值不值得」 |
| L2 | `trellis-check` 子代理: 讀 diff, 對照 spec, 跑 lint/type/test, **能自修就自修** | QC 吃 diff 不吃報告; verifier 唯讀且不得修 | **分歧, 而且是有意的**. 它讓檢查者修東西, 換到的是速度; 我方讓檢查者只能回 verdict, 換到的是「檢查者不會為了讓自己過而動手」. 兩邊都沒有量過這個取捨 |
| L3 | `trellis-break-loop`: 修完 bug 後的五維分析 —— 根因分類 (缺 spec / 跨層契約 / 變更傳播失敗 / 測試覆蓋缺口 / 隱含假設), 修法為何失敗, **防止機制分類表** (文件 / 架構 / 編譯期 / 執行期 / 測試 / 審查), 系統性擴散, 知識固化 | `evidence-debugging` 停在根因; `landing-log` 記教訓 | **形狀值得借: 那張防止機制分類表**. 我方的「機制勝過提醒」只有兩級 (散文 / 機制), 它有六級而且從弱到強排好 —— 那正是[強制力階梯](../architecture/architecture.md#軸二-憑什麼算數)想表達的東西, 而它的分法更細 |
| L4 | 同一支 skill 裡的貝氏推理框架: 先寫先驗機率, 觀察證據, 依方向更新, 找**能區分假說的**證據, 最後聲明信心度; 附三個常見謬誤 (基率忽略, 確認偏誤, 錨定) | `evidence-ladder` 的階梯與校準; `evidence-debugging` 的重現優先 | **佐證 + 一處我方沒有**: 「不要蒐集更多同類證據, 要找在頂尖假說之間**差異最大**的證據」. 我方的階梯講證據**多強**, 沒講怎麼挑**哪一個** |
| L5 | 「分析留在對話裡就等於零」—— 強制把結論寫回 spec 並 commit, 而不是列 TODO | landing-log 的「落地與紀錄同一輪」 | **佐證**, 措辭同向 |
| L6 | `trellis-update-spec` 的七節強制樣板 (Scope/Trigger, Signatures, Contracts, Validation & Error Matrix, Good/Base/Bad Cases, Tests Required, Wrong vs Correct) | 無等價強制樣板 | **不採用**. 它服務的是「把專案慣例寫成可執行契約」, 而我方的 spec 是程式碼與測試本身 |

### Graph 層 —— 多 agent

| # | Trellis 的做法 | 我方現況 | 判定 |
|---|---|---|---|
| G1 | `trellis channel`: 持久事件日誌 (`events.jsonl`, 序號鎖, 可重播), 跨 AI 的 worker (Claude Code / Codex / 自訂角色卡), 主 session 可中斷, 可觀察進度, 可非同步等待 | bridge-jobs 的存活對帳; 派工五狀態各有承載物 | **同一個關切, 它的載體更重**. 值得記的是它的判準: channel 比一次 Bash 或一次子代理**貴**, 所以只在「兩個以上 agent 要對話超過一輪」「worker 要能被中斷/觀察」「對話之後要可稽核」「多 worker 要共用同一份事件日誌」時才用 —— 這與我方的派工成本測試同形 |
| G2 | 明文分辨: 改 `.claude/agents/trellis-implement.md` **不會**改變 channel worker 的行為, 因為後者讀 `.trellis/agents/<name>.md` | 「四類證據不可互證」(repo 政策 / 可部署狀態 / 機器狀態 / 執行中狀態) | **佐證**. 同一種錯誤的另一個面貌: 改了一個看起來對的檔案, 而生效的是另一個 |
| G3 | 22 個平台各自一份鏡像目錄 (`.claude/`, `.codex/`, `.cursor/`, `.opencode/`, `.pi/`, `.omp/` …) | 兩個 provider, 由 manifest 與 twin-parity 測試綁住 | **記為風險而非可借**: 這正是 ECC 的 F3 (1,394 個沒有同步檢查的翻譯檔) 同形. 差別是 Trellis **有** template 測試 (24 支 `test/templates/*.test.ts` 逐平台驗產出), 所以它的鏡像是被機器盯著的 —— 這一點比 ECC 好, 也是我方 twin-parity 的第二個獨立血緣 |

### 證據層 —— 它怎麼知道自己有效

| # | Trellis 的做法 | 判定 |
|---|---|---|
| E1 | 內部 benchmark 的**事前登記**: `PROTOCOL.md` 在任何計分 run 之前凍結並以雜湊記進結果 | **佐證**, 與我方事前登記同形 |
| E2 | 三個臂: **A 裸機 / B 只有一份手寫 CLAUDE.md / C 完整 Trellis** —— B 臂明寫是為了「把框架和好文件分開」 | **最有價值的第二條**. 我方所有 arm 都是「有沒有這條子句」, 從來沒有一個臂問「換成一份普通文件會不會一樣好」. 那是我方整套常駐設計最沒被挑戰過的假設 |
| E3 | 每 (commit × 臂) ≥ 5 run, 報中位數與 IQR 與勝率, 不報點估計; token / 牆鐘 / 美元逐 run 記錄 | **佐證**, 與我方 replay 的口徑同形 |
| E4 | 防自欺: **在看到彙總結果之前**, 先承諾把每一個 tie 與 loss 立成後續任務 | **值得借的一句**. 我方有事前登記, 沒有「先承諾怎麼處理壞消息」這一步 |
| E5 | 防洩題: 凍結在 parent SHA 的 worktree, 截斷 git 歷史, 任務描述由第三方改寫而**不用 commit message** | **佐證**, 與我方 trap fixture 的 marker 紀律同形 |
| E6 | 評分是 **LLM judge + 20% 人工抽查**, 且明寫 judge 的模型不得等於任一臂的模型 | **不採用評分方式, 但那條限制值得記**: 我方 grader 一律機械 (跑程式, 比 diff, 不讀報告), 因為 LLM judge 的偏差沒有校準來源. 它用「judge 不得與受測同模型」來擋一部分, 那是比沒有好, 但擋不到 rubric 本身的主觀性 |
| E7 | **結果不公開**: PRD 明寫 benchmark 的 harness, prompt, transcript, 結果與報告全部留在 gitignore 的 `tmp/`, 不進 git, 不進 npm, 不發部落格 | **這是引用限制**: 沒有任何 Trellis 的效果數字可以被引用, 包括它自己在 README 上的宣稱 —— 那些宣稱背後的量測**存在但不可查**. 樹裡唯一追蹤到的量測產物是 `.trellis/tasks/archive/2026-01/01-29-context-benchmark/report.md` |

## 三個分歧

1. **脈絡從哪裡來**: 它把專案知識落成檔案再注入, 我方把方法落成 skill 再按需載入. 它的風險是檔案長期漂移 (它自己用 `.template-hashes.json` 與 `trellis update` 對付), 我方的風險是模型沒去載入 (我方用 s10/s11 量過, 答案是描述的措辭決定載入, 契約提不提沒有位移).
2. **檢查者能不能動手**: 它的 check 子代理自修, 我方的 verifier 唯讀. 兩邊都沒有量過.
3. **平台覆蓋面**: 22 個 vs 2 個. 它有逐平台的 template 測試, 所以不是無檢查的翻譯層; 但 1,461 個 `.trellis/` 檔進版控這件事, 使它的每一次 workflow 改動都要同時對付平台檔與既有 task 檔.

## 下一步 (每項都先量再決定)

| # | 候選 | 先量什麼 | 不做的條件 |
|---|---|---|---|
| T1 | **docs-only 對照臂** (E2): 在既有 replay 情境上加一個臂 —— 把我方的 skill 換成一份等價的普通文件 | 先挑一格已經有明確效果的情境 (例如語言子句那格 5/5 對 0/5), 新臂只換載體不換內容 | 挑不出一格「效果已知且穩定」的情境就不開; 在地板或天花板上的格子量不出載體差異 |
| T2 | **ablate 形狀** (H1): 一個可逆地把本 repo 的部署面整個拿掉再還原的指令 | 先問已經有什麼: `sync.sh` 有 manifest 與 parity, `deployment-verification.tsv` 有逐目標的觀察; 缺的只是「移除 + 還原 + 前後指紋」 | 若 T1 的答案是「載體沒差」, 這一項的用途就只剩災難還原, 而 git 已經是還原路徑 |
| T3 | **防止機制分類表** (L3): 把六級 (文件 / 架構 / 編譯期 / 執行期 / 測試 / 審查) 併進[強制力階梯](../architecture/architecture.md#軸二-憑什麼算數) | 先拿本 repo 已落地的機制逐一歸級, 看六格會不會有三格是空的 | 三格以上是空的就不併 —— 那表示這個分法描述的是它的形狀不是我方的 |

**T3 落地了 (2026-09-11), 但不是這一列寫的落點.** 51 個機制逐一歸級, **六格沒有一格是空的**
(文件: 10 支 skill 加 8 個 role 的本文; 架構: manifest 驅動部署, 事實/動詞邊界, 標記圍欄合併;
編譯期最薄但非空: `sync.sh` 的 `validate_manifest` 在部署前就讓指令失敗; 執行期: 12 個 hook;
測試: 514 支; 審查: `verifier` 唯讀加 QC), 所以不做的條件不成立.

**但這一列指定的落點是錯的, 而歸級本身是發現它的方法.** 強制力階梯排的是**強制力 × 可觀測性**
(會不會擋, 事後數不數得出來), 這張排的是**缺陷在哪個階段被擋下**. 同一個機制在兩條軸上都有座標
—— `commit-test-gate` 在我方是「閘」在它那邊是「執行期」, `test-first-change` 在我方是「散文」
在它那邊是「測試」—— 所以硬併會壓掉一維. 回頭看上游的用途也印證: 那張表是 `trellis-break-loop`
在**修完 bug 之後**問的, 是回顧工具, 不是新規則進來時要填的座標.

落在 `evidence-debugging` 的 `references/tuning.md` (修復收尾的下一問), 規則一句留在 `SKILL.md`
—— 該檔預算只剩 21 字, 而六格表進不受預算約束的 references, 這是預算註解記過的既有形狀.
**明講它是偏好不是閘**: 沒有承載欄位就沒有東西查得到「有沒有點名那一級」, 而架構文件自己寫著
這條軸上最貴的錯誤就是把散文當成閘. 授權處置在該 skill 的 `ATTRIBUTION.md` —— 全樹第一筆
AGPL 血緣, 只借形狀, 一個字的原文都沒有進 `main/`.

**三項候選 2026-09-11 全部結案.**

| # | 處置 | 依據 |
|---|---|---|
| T1 | **量了, 結果是這個構造裡沒有可量到的差** | 兩臂各 5/5 (第一批 5/0 作廢, 因為對照臂被擋住列目錄). 讀數與範圍限制在 [lifecycle-replay](lifecycle-replay.md#載體本身值不值--y2-2026-09-11-事前登記-未開跑) |
| T2 | **不建** | 它自己寫的不做條件成立: T1 說載體沒差, 用途只剩災難還原, 而 git 已經是還原路徑 |
| T3 | **落地, 但換了落點** | 見上一節. 歸級六格沒有一格是空的, 而歸級本身證明這一列指定的落點是錯的 |

**T1 的結論範圍要連著讀**: 它說的是「小 workdir, 任務點名了輸入路徑, 規則檔離一次列目錄只有一步」
這個條件下, 註冊成 skill 不改變合規率. 它**推翻不了**「載體在大 repo 裡差很多」—— 那個條件這個
fixture 複製不了, 而這句話是開跑前就寫死的, 不是事後補的.

**這條線留下的東西比結論多**: 一個 workdir 自帶 skill 的量測構造 (不必動操作者的 HOME), `meta.json`
的 `project_skills` 欄位, 逐情境 opt-in 的 `allow_listing` 授權, 以及全樹第一筆 AGPL 血緣的處置範例.
還有兩格獨立指向的同一個形狀: **載體改變的是路徑, 不是結果** —— `y1` 是導航對盲搜, `y2` 是叫 skill
對讀檔, 兩次都到同一個地方.

**這一頁的推翻條件**: 上述判定全部基於**它宣告的設計**. 任何一條若在真實安裝上跑起來不是這樣 (例如 hook 在非 Claude 平台其實有等價物), 該條要重判. 驗證方法是在一個拋棄式 repo 上 `trellis init` 跑一次 —— 本輪沒有做, 因為那會在這台機器上裝一套 22 平台的檔案.

**下次重查看什麼**: `v0.7.0` 正式版的 workflow 與 channel 變動; `trellis ablate` 是否從 full-only 擴到能選能力面 (它自己說第一版是 full-only); 以及 benchmark 是否改為公開 —— 那會把 E7 的引用限制解掉.

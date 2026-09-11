# 落地日誌

`README.md` 的**總結**與這份**日誌**在 2026-08-17 拆開, 因為 sprawl guard 燒了,
而那道閘的註解說「拆掉, 不要調高常數」. 判準很簡單: 總結回答「現在成立的是什麼」,
日誌回答「什麼時候查了什麼, 查出什麼」. 一份文件同時做兩件事, 讀的人得自己分辨
哪一段還是現行結論.

每一則都保留原始日期與原始措辭. 被後來的證據推翻的段落**不刪除**, 因為推翻的過程
本身是這個目錄最主要的產出 —— 見 [README.md](README.md) 的驗證缺口一節.

**2026-08-28 依期間拆過一次.** 2026-08-08 至 08-14 的條目搬到
[`landing-log-earlier.md`](landing-log-earlier.md), 因為本檔走到 20,132 字而
`DOC_SPRAWL_CEILING` 是 20,000 —— 那道閘的註解指名的處置就是依期間拆, 不是調高常數.
拆檔規則與被這一刀切開的那條敘事寫在那一份的開頭.

**2026-09-11 依期間再拆一次.** 2026-08-20 至 08-31 的條目搬到
[`landing-log-2026-08.md`](landing-log-2026-08.md), 因為本檔走到 20,101 字. 三份的範圍:
本檔 2026-09 起, [`landing-log-2026-08.md`](landing-log-2026-08.md) 是 08-20 至 08-31,
[`landing-log-earlier.md`](landing-log-earlier.md) 是 08-04 至 08-14.

#### 2026-09-10 計畫層收斂: 三份已結案文件退場, 現行內容各回擁有者

深度 review 量到現行指引層 (`docs/*.md`, `docs/plans/*.md`, `docs/research/README.md`)
共 75k 字, 其中約 23k 字是已結案的計畫與逐日敘事. 依 `docs/README.md` 規則 4 (已落地的
規則從 plan 移出, 歷史判斷留在 Git 或明確標示的紀錄), 三份文件退場, Git 保留全文:

| 退場的文件 | 狀態 | 現行內容去了哪 |
|---|---|---|
| `docs/document-audit.md` | 2026-07-28 那一次稽核的結果快照 | 範圍定義本來就在 `document-inventory.json`; 唯一還活著的規則 (效率宣稱的量測要在改動落地之前設計) 進 playbook 第 5 節 |
| `docs/plans/engineering-workflow-distillation.md` | 2026-08-19 已完成 | 兩支 skill 的分工在各自 `description`; task-observer 三條判準進 pending-evidence; 蒸餾流程與落地規則本來就在 `upstream-distillation` skill |
| `docs/plans/upgrade-plan-2026-09.md` | 2026-09-06 十二項全部結案 | 逐項結果見下一節; 依據在 ledger 09-05 三節與各研究文 |

同時: 研究總結 (`research/README.md`) 的逐日敘事 (08-04 落地表, 08-10 收束表) 搬到
[landing-log-earlier](landing-log-earlier.md) 末兩節, 08-21 到 08-31 的三段整合敘事本檔已有
(見 08-21 與 08-28 各節), 總結只留結論與指標. ECC 計畫 (`upgrade-plan-ecc-2026-09.md`) 縮成
現況表, 已結案項的量測數搬到下一節. `pending-evidence.md` 只留還在等的.

#### 2026-09-08 ECC 計畫逐項結案 (2026-09-10 自升級計畫搬入)

十三項 (含三個子項) 在 09-08 一天內量過或落地十一項. 每項的量測數與突變結果原本寫在計畫的
完成條件欄, 這裡照搬; 依據與逐條處置在 [ecc-survey](ecc-survey.md) 與
[機制盤點](mechanism-evidence-map.md).

| # | 結果 | 量到的數與落地 |
|---|---|---|
| Q1 | 已落地 | 環境開關雙向文件: 命中 6 / 真缺陷 3 (`AGENT_HARNESS_PYTHON`, `AGENT_HARNESS_REPO`, `AGENT_RUNTIME_VERSION`) / 正規化「全部都寫進文件」. `test_deployment.HookEnvDocumentationTests` 六支, 先紅在正好那六個名字上. 四向突變全過. 落在 `test_deployment` 而不是 `test_mechanisms`, 因為後者被自己的 sprawl guard 擋下 |
| Q2 | 已落地 (只做一支) | 拒絕訊息衰減: 最長連擊 `commit-test-gate` 18, `managed-target-guard` 5, 其餘 1. 只做 `managed-target-guard`; `push-consent-gate` 最長連擊 1, 衰減沒有對象, 不加永遠不跑的分支. N=3 沿用 ECC 預設. 四向突變全紅, 兩個是安全方向 (序號算不出改成 condense → fail-open 破掉; 跨 session 計數) |
| Q3 | 量過不做 | fact-forcing: 665 次首次 Edit, 先調查過的落在 59%–93%, 兩者皆無 46 次 = 6.9% (上界); 下限那一半是 client 機械強制的. 儀器錯過一次: 第一版只認工具名, 讀出「三分之一沒讀過就改」, 因為 auto mode 用 `cat`/`sed` 讀檔 |
| Q3b | 量過不做 | 破壞性 shell 閘: 18,812 次 Bash, ECC 樣式會攔 374 次 `rm -rf`, `>` 一項佔 26.8%. 374 個裡 56.7% 打在暫存區, 13.4% 建置產物, 絕對路徑 5 個 (1.3%) 全在工作區內. 對照 0 次可觀察的傷害. 指名一個真洞: `managed-target-guard` 看不到 Bash |
| Q4 | 量過, 全域上限不加 | 拿掉節流戳記跑一次 `weekly-integrity`: 1,600 B / 18 行, 是 ECC 8,000 字元預設的五分之一. 但未對帳 dispatch 清單無界 (每筆一行, 印到有人對帳為止), 綁列舉為前 10 筆加「... and N more」, 總數照寫. 實跑 11 筆: 10 加 1, 1,643 B. 三向突變全紅, 第三個抓到測試自己的缺陷 (強迫短清單走截斷分支時 id 全在, 印出 `and -7 more`) |
| Q6 | 量過不做 | Skill 硬失敗留痕: client 2.1.263 有 `PostToolUseFailure`. 掃 286 份 transcript, 27,549 次呼叫配對出 1,295 個錯誤, 0 個未配對; **Skill 144 次呼叫 1 次失敗 (0.7%)**, Bash 5.7% 是對照. 唯一那次是呼叫端把參數寫成 `command`, skill 沒被載入. 推翻條件: 失敗率 >3%, 或出現「載入了但失敗」 |
| Q7 | 量過不做 | 守衛設定不得調鬆以求綠: 過去 200 個 commit, 動到 `test_contracts.py` / `support.py` 三位數常數或 `*_CEILING` 的 16 次, **16 次全部**在 commit message 帶理由. 推翻條件: 出現一次說不出理由的 |
| Q8 | 毯子版不做 | 記憶輪替: 「不可信 run」寫成可判定的 (抓過 repo 沒寫的內容), 286 個 session 40 個抓過; 26 個寫 memory 的 session 23 個也抓過 = 88%. 能分辨的問題是判斷不是機械判定. 現存四則 memory 全關於本 repo. 殘餘一句寫作紀律, 決定權在使用者 |
| Q8b | 已落地 (形狀換了) | 逐閘「什麼條件下等於沒有」: 本 repo 沒有平台維度, 有的是七個閘在 payload 解不開時靜默放行. 宣告表在 hook-system, `test_every_gate_declares_when_it_is_silently_inert` 釘住; 七格只有兩格有人會知道 |
| Q9 | 已落地 | pin-report 讀同業列: 判準從 `類別` 欄換成句子 (`pin `<sha>`` 對整個 repo, `path 最後 commit 仍是` 對一個目錄). 兩向突變過. 實跑 7 個 pin (原 6), 順帶看到 sepia `MOVED +22`. 落在 `test_reporters.py` |
| Q9b | 已落地 | evidence-ladder 一行:「A number in a `description` is read every load; put it at L5 or drop it, never merely cite it.」1,271 → 1,292 字, 上限 1,295, 剩 3 字 —— 下一個動這支 skill 的人得先位移 |
| Q10 | 樣本做完, 六支未排 | `leaf-dispatch` 溯源: 確是 `baton-dispatch` 的 Codex 雙生, 同源於 `cablate/baton`, 雙生側原本沒有 ATTRIBUTION. 補了 (逐條分析單一來源, 授權全文各帶一份, MIT 要求通知隨副本走), `test_the_twin_attributions_pin_the_same_commit` 突變過. 一支約六個工具呼叫; 其餘六支沒有現成雙生可比, 成本不能外推 |
| Q5 | 開著 | manifest `last_verified` + 讓它過期的測試; 過期門檻未定 |

**移位紀錄 (同日晚間)**: 初稿排完才走本 repo 自己的語料. Q3/Q3b 先併入機制盤點 M1, 同日更正
拆回獨立 (M1 量的七個閘沒有一個守 fact-forcing 那個面); Q4 預期結論改成不加 (常駐只佔真實
prompt 0.049%); Q9b 提前 (`m1` 量到一句話換掉觸發率三倍, 未經校準的效果數字放在
description 裡就是一條沒量過而被當事實引用的子句).

#### 2026-09-06 2026-09 升級計畫結案 (2026-09-10 自升級計畫搬入)

2026-09-05 五個上游同日重查 (五個 pin 三個動: mattpocock marketplace pin 第一次前進,
speak-human-tw 第五輪機器人, rebelytics 3.0→3.1; sepia 出 v0.7.0; client 注入區塊在 2.1.261
消失) 留下的十二項加後續兩項, 09-06 全部結案. 依據在
[ledger 09-05 三節](upstream-distillation-ledger.md#2026-09-05-重查-五個-pin-三個動-marketplace-pin-第一次真的前進).

| # | 項目 | 結果 |
|---|---|---|
| P1 | `observation-log target` 接受 `plugin:skill` 冒號名 | 已完成 09-05: 測試先紅 (「hyphen-case」) 再綠; 回 `scope: plugin` + `local-or-third-party` |
| P2 | 耐久指標掃描 (`/private/tmp`, `scratchpad`) | 量過不加: 2 命中 0 真缺陷 (一個是逐字引用的指令, 一個是 client prompt 區塊名); `c995eb6` 那次事故是檔案消失不是指標壞掉 |
| P3 | 編輯殘渣掃描 | 已完成 09-05: 0 命中, 免費的鎖; `test_deployment.EditResidueTests` 掃遍部署面 >50 檔. 突變抓到一次: `{{ project }}` 帶空白, 上游 regex 抓不到 |
| P4 | `readable-zh-tw` 補四個中文形狀 | 已落地 09-05, 併進既有第 10, 15, 19 條; sepia 記進 ATTRIBUTION. 09-06 `z1-four-zh-shapes` 5/5 |
| P5 | `evidence-debugging` 有界停止點 | 已落地 09-05: 兩個部署面各斷言三個片語; 上限 1038 → 1079 |
| P6 | leaf-redispatch 載體在 2.1.261 重驗 | 已完成 09-05: `general-purpose` leaf 的 Agent 呼叫被擋, `CARRIER_VALIDATED_ON` 推進到 (2, 1, 261) |
| P7 | pin-report 讀 research README 上游表 | 已完成 09-05: 5 → 6 個 pin, sepia 以「research README only」進表 |
| P8 | Pilotfish tag 後 15 個 commit 的 attempts | 讀了兩份 README 不是本體; 三個正控制與 baton 成本測試同形但同血緣, 不算票 |
| P9 | Deep Agents 0.7.7→0.7.13 | 讀了發版說明: 子代理 fork 成預設, grader 進 SDK hook; 0.7.10 #5566 是儀器守則第三個獨立血緣 |
| P10 | client 注入段消失 → 戳章重跑 | 縮小: 戳章從沒含 client 半邊, 落在 wording-effect-scale 補記 |
| P11 | sepia 後續 (a) Fable 5.1 prose layer (b) `readable-zh-tw` eval | (a) 三條供應商自述記進 ledger; (b) 決定要, 借 sepia 三 grader 形狀, 09-06 `z1` 跑了 |
| P12 | 「查過但不能用」登記法 | 已完成 09-05: `model-evidence.md` 末節開表, 首輪三筆 |
| P13 | 派工正控制 fixture | 09-06 做成 replay `d3`–`d6` 四對 cell (12 到 96 檔, 同形與異形): 煞車沒判錯過, 交會點不存在, inline 非單調而派工的線性項在 leaf 數上. 見 [replay README Part 15](../../evals/replay/README.md) |
| P14 | 注入位置第二輪 | 09-06 跑完 23 run 約 $17 結案: 禁止句 0/27 對偏好句 10/11, 對比二元, 量不出位置; 副產品「契約規則輸給任何禁止句, 贏過任何偏好句」 |

明確不做的 (依據在 ledger): rebelytics 的啟動種子, session-start 掃描, staging 三向對帳,
`{skill}-extras`; sepia 的小說側, voice, 模型歸因; Windows 平台項; 安裝 upstream skill 而非蒸餾.

#### 2026-09-10 ECC 計畫最後兩項結案: 六支 skill 溯源 (Q10), 部署驗證表 (Q5)

**Q10, 守衛的三個數**: 14 個 skill 目錄 (12 個本體加 Claude 的兩個薄 wrapper), 今日命中 7 (六支
沒有任何出處宣告, 加 `headroom-protocol` 的薄 wrapper) / 真缺陷 6 / 正規化「一個檔名兩種形式」——
自有的寫 `**Origin**: this repository` 且不得帶 40 位 SHA, 否則 `upstream-pin-report.py` 會把它登記
成上游. 六支的判定: `headroom-protocol`, `experience-ledger`, `evidence-ladder`, `harness-review`
自有; `upstream-distillation` 兩條子句蒸餾自 rebelytics 3.0 / 3.1 (CC BY 4.0, 與 task-observer
同 pin); `provider-routing` 三句蒸餾自 Pilotfish. **溯源時重抓原文而不是讀筆記, 抓到的東西比六個
檔多**: Pilotfish `templates/claude-md.orchestration.md` at `7a7f71b3` 逐句對, `provider-routing`
三句與 `baton-dispatch` / `leaf-dispatch` 四條是它的措辭, 而 baton 的既有 ATTRIBUTION 把五次 pass
與兩次修訂上限寫成「本地自寫」. 已更正, Pilotfish 從同業升為上游 (MIT, Nanako0129), pin-report
從此看得到它. 突變: 拿掉一個自有檔 → 紅且指名; 在自有檔種一個 SHA → 紅 (半個宣稱); 拿掉
`provider-routing` 的署名 → 既有的下限 8 **沒紅**, 因為蒸餾檔實際是 9 —— 下限改成 9 (那條註解
自己就寫著「下限是現在的數量」, 第一稿沒照做). **沒查的**: 七個 role 檔對 Pilotfish
`templates/agents/*.md` 的措辭; 07-22 實際讀的那版 (v1.3.10 之前) 的原文; 一支的成本約
十二個工具呼叫, 比 09-08 樣本的六個多一倍, 因為多了一次上游抓取.

#### 2026-09-11 專案層 P2: 兩個真 repo, 一個不該裝, 一個裝了

**先看 WorkSpace 再挑**: 15 個 git repo, 5 個有根目錄 `CLAUDE.md` + `AGENTS.md` (四個 nexus 系與 pixi-game-framework), 4 個只有 `AGENTS.md`, 6 個什麼都沒有. **沒有一個用 `.claude/CLAUDE.md`** —— 而 P1 的 manifest 目標寫的正是那條路. 區塊要合併進團隊自己的檔案, 目標就得是團隊放檔案的地方; 改成根目錄 `CLAUDE.md`, 連帶 HOME 守衛從路徑重疊改成明確比對 (改完先紅: 根目錄 `CLAUDE.md` 不在全域 manifest 裡, 舊守衛抓不到 HOME 了).

**樣本一, `nexus-roulette-client`, 不裝.** 七格全填得出, 但七格全部已寫在團隊自己 290 行的 `CLAUDE.md` (與 `AGENTS.md` 逐位元組相同): 最快迴路 `npm run typecheck` 明寫「CI 結構上跑不了 tsc」, 真相源三條帶衝突優先序, 傳播陷阱與 2× 陷阱各有名字, lens 就是它的 layer 表. 裝進去是純重複, 而且違反它自己第一段的規則「lookup-able detail lives in the docs/skills and is never pasted back in」. **這是 P2 最有用的讀數**: 對已經有成熟契約的 repo, 這一層的價值是零到負.

**樣本二, `game-client-sdk`, 裝了.** 沒有任何契約檔; 七格從 `package.json`, README, commit 訊息, 消費端 repo 與 roulette 對它的描述填出來: 測試 `npm test` (jest), 沒有 lint, 最快迴路 `npm run dts` 加旁邊那支 jest, 真相源兩條 (Jira 票, 消費端 client), 陷阱三條 (`dist/` 與 `types/` gitignore 而消費端走 `file:` —— 改 `src/` 對消費端沒有任何效果; 兩條長壽分支互相合併; 沒有 CI), lens 三條 (重連迴路, 金額欄位, `Table.GameState`). 渲染 Claude 238 字, Codex 209 字, `--verify` 綠. 三個檔留在該 repo 未追蹤, 未 commit.

**渲染上限**: 從 238 定 260 (`RENDERED_BLOCK_CEILING`), 容得下再兩三條事實, 容不下多兩段. `--apply` 超過照寫但警告, `--verify` 超過回 1 —— 沒人讀的警告是 `denial_log` 付過的學費, 所以讓它紅. 測試種 30 條 trap, apply 警告, verify 紅.

**順帶回答了一半「狀態檔存哪」**: roulette 根目錄有團隊共享的 `MEMORY.md` 加輪替規則. 那個團隊已經選了「進 repo」, 所以 P3 對他們不是新開狀態檔, 是注入 `MEMORY.md` 的哪一節. 記在計畫, 決定仍是使用者的.

**樣本三 (2026-09-11 補), `nexus-colorgame-client`, 也不裝 —— 但它不是獨立樣本.** 它的 `AGENTS.md` 第 18 行明寫自己是從 roulette bootstrap 出來並「刻意保持同構」, 22.4K. 七格全在裡面, 而且比 sdk 那份更整齊: 有一節標題就叫 External Sources of Truth (priority on conflict), 最短迴路寫著先跑 `npm run typecheck` (husky pre-commit 是唯一型別閘, 因為 CI 會 strip 掉 `@toppath/*`), stale-dist 傳播與 2× 兩個陷阱各有名字, 「Layer Boundaries (DO NOT MIX)」那節就是 lens. 同構是它的設計目標, 所以它確認型態而沒有加多少證據量. 真正有資訊的是分布本身: **有契約的那幾個都成熟, 沒契約的那六個什麼都沒有, 中間沒有東西.** 這一層的對象是後者.

**而勘 colorgame 時撞到一個真缺陷, 當場修掉.** 它的 `CLAUDE.md` 是指向 `AGENTS.md` 的符號連結 —— 而且不是特例: 五個有 `CLAUDE.md` 的 repo 裡**三個**是 (baccarat, colorgame, roulette, 整個 nexus 系). 兩個 manifest 目標因此落在同一個 inode 上, 實測的行為是**無聲的**: `--apply` 印了兩行成功, exit 0, 檔裡只剩一個區塊 —— Codex 那個, 因為第二次渲染在同一組標記之間找到第一個並取代掉它. Claude session 順著連結讀到的會是 Codex 措辭的每一格事實, 而沒有任何地方說了這件事. 處置是**拒絕而不是自動裁決**: 哪一個 client 的區塊該贏, 不是這支腳本可以安靜決定的, 決定權在把兩個名字做成一個檔的那個 repo. 先紅 (exit 0 + 兩行 wrote), 加守衛後綠, 突變 (`if resolved in seen` 改成永不成立) 回紅.

**沒做的**: P5a (量檔案層) 是下一步, 而 sdk 那份剛好是乾淨的量測對象 —— 一個沒有任何契約的 repo, 兩臂差只會來自這個區塊.

#### 2026-09-11 專案層 P5a: 登記與儀器落地, 停在開跑前

事前登記在 [lifecycle-replay](lifecycle-replay.md#專案事實區塊有沒有用--2026-09-11-事前登記-未開跑),
儀器是 `y1-project-facts` / `y1x-project-bare` 兩支情境. 一個 run 都沒跑 —— 花錢的決定要使用者點頭.

**上一則說的量測對象換了, 理由記在這裡.** P2 寫「sdk 那份剛好是乾淨的量測對象」, 而 P5a 沒有在
`game-client-sdk` 上跑: 那是團隊的 repo, 讓 session 在裡面動手不是我能替使用者決定的. fixture 抄它的
真陷阱 (`dist/` 被 gitignore, 消費端走 `file:` 讀它) 換成沙箱 python3 跑得動的最小版.

**這一格的形狀**: 兩層不打架 —— 契約說「跑最窄的那條能推翻你宣稱的驗證」, 專案區塊說「那條指令是這個」.
`x` 系列量的全是兩句話打架 (禁止句 0/27, 偏好句 16/17), 47 個既有情境沒有一個是這個形狀. fixture 因此
做成**假綠**: 改了 `src/` 之後 `run_tests.py` 照樣綠, 因為它測的是產物; 呼叫端看到的還是舊值, 直到
`tools/bundle.py` 重新產生. 主要讀數是 `commands_executed` 裡有沒有那條指令 —— 不是回覆說了什麼,
也不是產物對不對 (手改產物是另一種行為, 而區塊明寫不要那樣做, 併進通過等於把兩個相反行為記成同一件).

**A 臂不是手打的**: `build.py` 用 `project-init` 的渲染器從 fixture 自己的 `facts.toml` 產生兩個區塊,
測試再拿 `--verify` 回頭判它. 手打一份近似品去量產品, 是 `e4` 那格在講的失敗.

**開跑前抓到兩件.** 一, `README.md` 刻意不提 `tools/bundle.py` —— 提了就是把事實免費送給 B 臂.
二, 產物的 `__pycache__` 差點變成第二個沒登記的陷阱: 5000 改 4000 檔長不變, CPython 驗 `.pyc` 看
mtime 與大小, 同一秒內兩者都可以沒變, 實測「重新產生過的 bundle 還是 import 成舊的」. 照著事實做的
session 會看到錯的答案, 那是另一個陷阱. 已修 (產生器掃快取, runner 不寫 bytecode), 而它是**在任何
run 之前**量到的.

**還沒證明的那一件, 寫成停止規則**: `/tmp` 底下的 workdir 裡放一個 `CLAUDE.md`, client 到底讀不讀,
2026-08-12 那張 harness 表沒有這一列. `project-probe.sh` 兩側都問 (facts 臂 10 次要 10/10, bare 臂
3 次要 0/3, 並計工具呼叫 —— 靠 Read 讀到的不算常駐). 任一側不合格整格不跑, 而那本身就是一個會推翻
專案層前提的結論.

**順帶拆了一份文件.** 這則登記把 `lifecycle-replay.md` 推到 22,067 字, 過了 `DOC_SPRAWL_CEILING`.
依那道閘的註解拆檔而不是調高常數: 注入位置那條線 (6,947 字, `x1b`/`x1c`/`x2b`–`x2f`, 兩輪都已結案)
搬到 `injection-position.md`, 主檔剩 15,401. 這是同一道閘第三次要求拆檔 (前兩次是 `clause-pricing`
與 `landing-log-earlier`), 四處錨點連結跟著改指.

**當天就跑完了, 而結果是「這格量不出來」.** delivery probe 先過: facts 臂 10/10 答對且**零工具呼叫**,
bare 臂 0/3 —— 區塊是自己到的, 不是 session 去讀來的, 載體成立. 然後先導十個 run: **A 5/5, B 5/5**,
Fisher p = 1.0, 十個都走到了那條指令, 沒有一個停在假綠上, 沒有一個手改產物. 依事前規則第 1 條
(B ≥ 4/5) **不跑主比較**, 省下 20 個 run.

**推翻的是我自己的設計判斷**: 登記時寫「要多讀一次才看得見」, 而 B 臂五個 run 的第一條指令全是對值的
盲搜, 那一下就同時撈出產物, 產生器與 `sys.path` 那行. 陷阱不在閱讀距離之外一步, 是躺在第一步裡面.
這個 null **不**觸發計畫的降級條款 —— 降級綁在「區塊到得了卻沒被用上」, 而那一側是滿分.

**一個沒登記的差別, 只當假說**: 起手式不同, A 臂五個全是導航 (直接 `ls`/`cat` 進區塊點名的 `build/`
與 `tools/`), B 臂五個全是盲搜; 指令數中位數 4 對 6. 事前沒登記就不是讀數, 寫下來是為了不讓它日後被
記憶美化成「當時就看到了」.

#### 2026-09-11 上游重查: 七個報動, 三個是報告在重報已分類過的事

**這一輪最有價值的產出是改了儀器.** `upstream-pin-report.py` 的 `MOVED` 一直是拿 **pin** 比 head, 而
時效表另外記「查核日」, 兩者沒對接. 今天七個 `MOVED` 裡, mattpocock (+2), rebelytics (+1) 與
pilotfish (+19) 的 head 日期全都**早於**它們自己那列的查核日, 逐條處置也早就寫在各自的 ATTRIBUTION 裡.
誤報率 4/7 —— 而這正是本 repo 要求「加守衛前先量」的那三個數字裡的第一個. 已修: 這種列現在印 `seen +N`
加一句「nothing after the <date> check」.

**判準的細節是被自己的資料改掉的**: 第一版想用「第一個新 commit 的日期」, 而 sepia 今天的範圍起點正好
落在查核日當天, 終點在五天後 —— 用起點會把真的新東西讀成看過了. 改用 head 的日期, 七格全部判對.
測試把這個形狀釘住, 兩向突變都紅 (改讀 `since` → 紅; 拿掉合併時承接查核日那行 → 紅). 三個限制寫在
函式旁邊: compare 上限 250 個 commit, rebase 會改寫 committer date, 查核日只到「日」.

**真正動了的四個**: speak-human-tw 第六輪仍然只有星數圖 SVG (pin 推進, 純記帳); sepia +36 動了 14 個檔
而**我方借形狀的 `languages/zh.md` 不在其中**; Trellis +3 全是實作修正, 不碰勘查的三項候選; ecc +20
是真的新, 但它那列本來就寫著「逐節重查才有價值」, 而逐節重查這輪**沒做**.

**一條佐證, 處置相反**: pilotfish `#63` 把「`CLAUDE.md` 是符號連結就拒絕」放寬成「解析後是可讀一般檔就
接受」; 我方今天的 `project-init` 反而**拒絕**兩個目標塌成同一個 inode. 兩邊都對, 差別在區塊數量 ——
他們寫一個, 我們寫兩個. 佐證抬高的不是處置, 是**那個現實的普遍性**: 工作區五個有 `CLAUDE.md` 的 repo
裡三個是符號連結, 而上游為此特地發了一版.

#### 2026-09-11 Trellis T3 落地, 而落點不是勘查寫的那個

三項候選裡最便宜的一項 (不花 run, 純分類). 先做歸級: 51 個機制對上六級, **六格沒有一格是空的**
—— 文件是 10 支 skill 加 8 個 role 的本文, 架構是 manifest 驅動部署與事實/動詞邊界, 編譯期最薄
但非空 (`sync.sh` 的 `validate_manifest` 在部署前就讓指令失敗), 執行期 12 個 hook, 測試 514 支,
審查是 `verifier` 唯讀加 QC. 所以「三格以上空就不併」不成立, 可以併.

**但歸級順手證明了勘查指定的落點是錯的.** 強制力階梯排的是**強制力 × 可觀測性**, 這張排的是
**缺陷在哪個階段被擋下**; 同一個機制在兩條軸上都有座標 (`commit-test-gate` 是「閘」也是「執行期」,
`test-first-change` 是「散文」也是「測試」), 硬併會壓掉一維. 回頭讀上游的用途也印證: 那張表是
修完 bug 之後問的回顧工具, 不是新規則進來時填的座標. 所以落在 `evidence-debugging` 修復收尾的
下一問, 不是架構文件的軸.

**預算決定了形狀**: `SKILL.md` 當時只剩 21 字餘裕, 所以規則一句留本文 (加完 1,068/1,079, 剩 11),
六格表進不受預算約束的 `references/tuning.md`. 這不是將就, 是預算註解早就記過的形狀 ——
「細節先進 references, 留在本文的是規則本身」.

**明講它是偏好不是閘.** 沒有承載欄位就沒有東西查得到「有沒有點名那一級」, 而架構文件自己寫著
這條軸上最貴的錯誤就是把散文當成閘. 所以沒有寫任何假裝在擋它的測試.

**順帶避開一個混淆**: `evidence-ladder` 已經有一張六級表 (L0–L5), 但它排的是**證據強度**.
兩張都是六格又都在證據類 skill 附近, 所以新那節明寫「這不是證據階梯」並舉了兩個座標不一致的例子.

**授權**: 全樹第一筆 AGPL 血緣. 只借「問這個問題」與由弱到強的排序, 六個階段名稱是通用工程實務,
第三欄全是我方機制, 表下兩條規則來自本地事件. 一個字的上游原文都沒有進 `main/`, 處置寫在該 skill
的 `ATTRIBUTION.md` 而不是只寫在研究層 —— 因為那份檔才是有人要查授權義務時會打開的.

**還開著的**: T1 (docs-only 對照臂) 與 T2 (ablate 形狀). T2 自己的條件綁在 T1 上, 而 T1 要花 run.

#### 2026-09-11 Trellis T1: 跑了兩次, 第一次作廢, 第二次兩臂都是 5/5

**上一則結尾寫「T1 與 T2 還開著」, 這一則把兩個都關掉了.** 原句照留 —— 它寫的時候是對的, 而這個
日誌不刪被後來證據推翻的段落.

三項候選收尾. T1 問的是這個 repo 最沒被挑戰的假設: **同樣的字, 註冊成 skill 與放成普通檔, 差多少.**

**設計換過**: 勘查寫的是把已部署的 skill 換掉, 而那要對一整棵目錄做 `arm.py` 對單檔做的四件事, 動的是
使用者的機器. 改成 fixture 自帶 skill, 兩臂同一個 workdir 同一份文字, HOME 一個位元組不動. 載體先量過
才用: workdir 裡的 skill description 10/10 進得了 session 且零工具呼叫, 空 workdir 0/3.

**第一批作廢, 而作廢的理由是讀數**: A 5/5 對 B 0/5, 乾淨得可疑. 查下去是 B 臂五個 run **全部**請求列
目錄, **全部被拒** —— 它被擋住去找自己該讀的規則檔, 而 A 臂的 description 不請自來所以不需要找. 那道
分離量到的是權限清單不是載體. 加了逐情境 opt-in 的 `allow_listing` (兩臂一起給, 排在執行 grant 之後
以免動到舊 run 的可比性), 重跑.

**第二批, 操弄有落地**: `denied` 的列目錄 0, `read_the_format_file` 從 0/5 翻成 5/5. 結果是
**A 5/5, B 5/5**, Fisher p = 1.0, 依事前規則停在先導.

**兩格獨立指向同一個形狀**: A 臂叫了 skill 且從沒讀檔, B 臂讀了檔且沒 skill 可叫 —— 載體改變的是
**怎麼到**, 不是**到不到**. `y1` 那格是導航對盲搜, 同一個形狀.

**連帶結案 T2** (它的不做條件綁在 T1 上), 所以 Trellis 三項候選全部結案: T3 落地但換了落點, T1 量了
而結果是這個構造裡沒有可量到的差, T2 不建.

**這一輪最貴的教訓**: 對照臂要能做它該做的事, 而那件事在設計時太理所當然, 所以沒人確認它被允許.
下一格開跑前要多問一句: 兩臂各自需要哪些動作, 那些動作都被核准了嗎.

#### 2026-09-10 (晚) 專案層 P0 + P1: 三條釘子先紅, 然後一支 init

路線在[專案層計畫](../plans/project-layer-plan.md). 這裡記數字與過程裡改了什麼.

**先紅**: `test_project_layer.py` 15 支在任何實作存在之前跑, 8 fail 9 error (含 subTest). 三條釘子: 兩份 manifest 不共用來源; 樣板不含權限詞彙 (19 個: 七個角色名, 三支派工 skill 名, 兩個紀錄標記, delegate / dispatch / subagent / sub-agent / workflow / explore / experience-ledger); 樣板固定文字有上限. **禁字表是釘子不是判定**: 它抓得到「verifier」抓不到「先問過那個檢查的人」, 計畫裡的推翻條件就是為這件事寫的.

**實測**: 固定文字 Claude 70 字, Codex 41 字, 上限各加約 2% 定為 72 / 42. 拋棄式 repo 走完一輪: 第一次 `--apply` 寫骨架停在 exit 3, 填七格後渲染, Claude 區塊 109 字, Codex 80 字 (含事實本身); 團隊原有的 `CLAUDE.md` 留在區塊之前一字不動; 重跑冪等, `--verify` 對區塊內的手改回 1.

**七向突變全紅且各自指名正確的測試**: 樣板種 verifier, 骨架註解種 delegate, manifest 借用全域來源, 雙生槽位不一致, 固定文字超上限, 拿掉 HOME 守衛, 拿掉殘渣守衛.

**review 時拿掉一項**: 初稿 P1 寫「沿用 `install-git-hooks.sh` 裝 pre-commit 閘」. 那支腳本把 `core.hooksPath` 設成相對路徑 `main/claude/githooks`, 只在本 repo 成立; gate 的套件探測也只認 `<repo>/.claude/tests`. 全域的 Bash 側閘本來就對「指令指向的那個 repo」找套件, 所以有那種套件的 repo 已被蓋到, 沒有的裝了也是空的. 一個計畫裡「沿用既有機制」的字眼, 讀起來最省事, 而它假設了那個機制是可攜的.

**commit 閘擋了兩次, 兩次都對**: 第一次計畫重述 playbook 的「最短驗證迴路」沒連回去; 第二次 (前一則 Trellis 勘查) 提了 Bash 側 commit 閘沒提 git 側. 兩次都是文件在 `git add` 那一刻才進入掃描範圍, 所以先前的全綠不是矛盾.

**沒做的**: 渲染後區塊的字數上限 (P2 填一個真 repo 之後才定); `--remove` (P4); 任何 hook.

#### 2026-09-10 (晚) 勘查 Trellis: 第一個把「載體」問題攤在檯面上的同業

逐條在 [trellis-survey](trellis-survey.md). 這裡只記三件會改變後續排序的.

**一, 它有一個我方沒有的對照臂.** 它的內部 benchmark 三臂是裸機 / **只有一份手寫 CLAUDE.md** / 完整框架, 而中間那臂明寫是為了把「框架」和「好文件」分開. 我方所有的臂都在問「有沒有這條子句」, 從來沒問過「換成一份普通文件會不會一樣好」—— 那是我方整套常駐設計最沒被挑戰過的假設, 排 T1.

**二, 它有一個可逆的自我移除指令.** `trellis ablate` / `restore` 把整套啟用面拿掉再精確還原, 帶交易目錄, 逐路徑前後指紋與 fail-closed 的併發鎖. 我方的 eval arm 一律是**造出來的** (`build.py` 從 pristine 減去宣告的 lever), 沒有「把裝好的自己拿掉」這條路. 排 T2, 但它的價值取決於 T1 的答案.

**三, 它的效果數字一個都不能引用, 而且那是它自己決定的.** benchmark 的 PRD 明寫 harness, prompt, transcript, 結果與報告全部留在 gitignore 的 `tmp/`, 不進 git 也不進 npm. 所以「Trellis 讓 agent 更好」這件事在它那裡**量過但不可查** —— 這比沒量過更值得記, 因為 README 上的宣稱看起來一樣有底氣. 時效表那一列因此帶兩條引用限制.

**授權要先講**: AGPL-3.0, 與先前每一個上游 (MIT 或 CC BY) 都不同. 本輪只記形狀與判定, 沒有任何一段 prose 進 `main/`; 哪天要採用某條, 處置是重寫加註記, 並先確認重寫後不構成衍生作品.

**兩個佐證**: 它的三層平台能力宣告 (hook 只有 Claude Code 齊全) 是 ECC 的 Windows observer 之後, 「裝了不等於會跑」的第二個獨立血緣; 它的 24 支逐平台 template 測試, 是我方 twin-parity 的第二個獨立血緣 —— 而且它證明鏡像層可以被機器盯住, 那正是 ECC 的 1,394 個翻譯檔沒有做到的.

#### 2026-09-10 (晚) role 檔的措辭比對: 借的比想的少, 但欠的兩處都在常駐面

`cd11cf1` 明寫「沒查」的那一項. 抓四個上游版本而不是一個, 因為要問的是哪邊的文字先存在.

**先講被推翻的印象**: 讀完兩側我以為七個 role 檔大量蒸餾自上游. 量了就不是 —— 七對逐對比 `v1.2.1`, 共用六字實詞序列每對 0 到 1 個, 最長共同片段 4 到 6 字且全是通用片語. 一次讀起來像抄的印象, 被一支十行的 n-gram 腳本改掉, 這正是「印象不是量測」那條規則的實例.

**欠的兩處**: `plan-verifier` 的四欄 REVISE 區塊 (上游 `v1.3.4`, 逐字含佔位文字; 我方 07-28 落地, commit 標題就寫著 adopt pilotfish v1.3.4 controls —— 借用寫在歷史裡卻沒進註記檔), 與 `security-executor` description 裡那句 `pre-approval analysis belongs to security-reviewer` (逐字, 而且**住在常駐面**, 是這裡被讀最多次的借用文字). 第三處是長工作回報的四項清單, 清單是上游的, 句子是我方的. 三處都補進 `provider-routing` 與 `baton-dispatch` 的 `ATTRIBUTION.md`.

**方向相反的一項**: `INCONCLUSIVE` 是我方 2026-07-22 先有, 上游 `v1.3.5` (07-29) 才加, 晚一週. 研究總結原本把「verdict 三分 (v1.3.5)」列成已落地, 讀起來像我方採用; 已改成「我方先有」並附日期.

**改掉的一個說法**: 上游 `v1.2.1` (2026-07-16) 就有同樣的七角色切分, 早於本 repo 第一個 commit 四天. 推翻條件 (找得到 07-20 之前參考過的紀錄) 沒成立, 兩票不變, 但「我們比較早」這個論證換成「上游比較早, 只是沒有紀錄顯示我們看過」—— 後者弱得多, 而先前那句讀起來像前者.

**守衛, 而第一版是空的**: 兩個 role 目錄自己放不了註記檔 (client 與 `test_roles` 都把 `*.md` 當角色註冊讀), 所以覆蓋只能由別處宣告, 而沒有測試的宣告會安靜消失. 第一版問的是「有沒有任何一份註記檔提到這兩個目錄」, **突變後仍然綠**: 把 Pilotfish 那份裡的目錄名拿掉, fable-method 那份因為自己的理由也提到同一個目錄, 於是測試看不出差別. 那正是本 repo 一再抓到的「子字串代替性質」, 而且是同一週第三次. 改成逐上游: `ROLE_TEXT_UPSTREAMS` 列出文字出貨在 role 目錄裡的上游 (今日兩個), 指名它的那份檔案必須同時指名兩個目錄. 兩向突變: 拿掉 Pilotfish 那份的目錄名 → 紅且指名 pilotfish; 拿掉 fable-method 那份的 → 紅且指名 fable-method.

**Q5, 形狀與數字**: 不加第四欄 —— `sync.sh` 的 `read -r src dst mode extra`, `managed-target-guard`
的「兩欄 = 整份託管」, `support.deployment_manifest_entries` 三個 parser 都靠欄數判意義. 改成
`scripts/deployment-verification.tsv`, 以 target 為鍵, 40 列, 測試釘它與 manifest 目標一對一.
「verified」寫成**被 client 讀到**而不是在場: 31 列是機器觀察 (本 session 的 skill 與 role 清單,
commit-test-gate 的 exit 2, 兩支 resolver 讀 routing 檔, 兩次 `codex exec` 唯讀探針 —— 一次讀到
契約首標與隱式 skill 清單, 一次用 `$name` 載入三支 `allow_implicit_invocation: false` 的 skill,
合計約 49k token), 9 列沒有機器消費者 (README, prompts, docs), 老實記「parity only」;
`.codex/agents` 只驗到 config_file 解析得開, 真派工沒探. `DECISION`: 到期 90 天, 對齊兩份
routing 檔的 `prior_review` 節奏而不是每週 —— 重觀察一列要一個 session, 每週 40 次沒有人會做.
突變: 刪一列 → 紅; 一列改成 2025-01-01 → 紅 (617 days); 加一列 manifest 沒有的 → 紅; fixture 的
400 天與 `never` 各自紅. 第一次到期是 2026-12-09.

# Harness engineering: 模型周圍

工具, 權限, 監控, 防護欄 —— **一個 agent 能碰到什麼, 碰不到什麼, 以及誰在旁邊看.**
這一層包住 [context](context-engineering.md): 它決定模型有哪些動作可用, 而 context
決定模型知道什麼.

命名上先講清楚: 這個 repo 叫 agent-harness, 用的是廣義 —— 包在模型外面的整個規則層.
本文用的是狹義, 就是這一層. 跨專案可複用的方法論在
[engineering playbook](../engineering-playbook.md), 那是另一件事.

**管什麼.** 單一 agent 的權限, 工具面與停止邊界. 這一層決定的是「它做不到」, 不是
「它不該做」.

**怎麼做.** 七個固定角色, 每個角色的契約自足 —— 不要求 leaf agent 再去讀主契約或 Plan.
唯讀角色的邊界畫在**能力面而不是解析 shell**: no-write 角色根本不配 Bash, 因為 shell 的
寫入途徑關不完; 需要跑指令的獨立驗證改派 Codex 的唯讀 sandbox. 機制層預設 fail-open ——
診斷工具壞掉不該讓人無法工作 —— 刻意 fail-closed 的是六個有界 gate, 每個只在很窄的條件
下攔截, 每個都有逃生口.

**用什麼量.** trap 做行為驗收: 自足的小專案, 逐字的 brief, 加一個只執行與 diff, 不看
報告的機械 grader. hook 用合成 stdin 做 pipe-test, 正常, 略過, 防循環, 錯誤四種輸入
各走一次.

**已知怎麼壞.**

- **閘會過不代表閘會紅.** 文件涵蓋閘用的比對函式會跨路徑分隔符, 於是每條 pattern 都成了
  遞迴的, 那道閘三週內完全無法失敗, 期間 77k 字的實驗紀錄悄悄進了現行指引.
- **通過條件可以事後選.** `s8` 這一格 (量的是「規則衝突時 agent 會不會自己裁決」) 的通過
  條件就是「不動作」, 字面上成立; 真正的洞是通過條件可以在看到結果之後才決定, 所以
  grader 改成必須事前寫死預期.
- **額度只認一種拼法.** verifier 額度只計 Claude 的 `verifier`, 走 bridge 的 Codex
  verifier 不算 —— 這件事必須寫在描述它的每一份文件裡, 否則它看起來像跨 provider 的
  任務預算.

**要動它得先拿出什麼.** 新增或改動 gate 要 pipe-test, 蓄意錯誤驗證與逃生口三件齊全 ——
**抓不到蓄意錯誤的機制等於不存在**. 新增角色要在同一個 cohort 裡證明現有角色契約不足,
不能因為題材不同就開新角色.

## 七個角色, 各自的邊界

Main 不是派工器而已: 它負責需求定義, 歧義, 架構, 風險, 切界, 整合, 最終驗證與對使用者
負責. leaf 拿到的是有界工作, 而邊界就寫在這張表的第三欄.

| Role | 使用時機 | 權限邊界 |
|---|---|---|
| `explore` | 大範圍定位, 或具明確 lens 的有界專案 review | 唯讀; 不設計, 不實作, 不做最終判斷 |
| `mech-executor` | pattern 與完成條件已完整 | 只做機械套用; 遇到例外就停止 |
| `executor` | 封閉範圍內仍需要局部判斷的實作 | 可寫入; 不擴大產品或架構範圍 |
| `plan-verifier` | material Plan 需要 fresh-context 挑戰 | 唯讀; 只回 `READY`/`REVISE` |
| `verifier` | 高影響聲稱需要獨立反證 | 唯讀; 只回 `CONFIRMED`/`REFUTED`/`INCONCLUSIVE` |
| `security-reviewer` | 核准前的 trust-boundary 與 abuse-path 分析 | 唯讀; 不實作 |
| `security-executor` | 已核准安全契約的實作 | 可寫入; 不得重開需求或弱化控制 |

Claude 與 Codex 各有一份自足的角色契約; leaf 不讀 main 的 orchestration 文件, 也不能再派
下一層. 三個可寫角色另外各自帶了前景指令 10 分鐘上限, 以及放不下時該回傳什麼.

## 監控: 擋不住的那一半

防護欄之外, 這一層還有一組**只看不擋**的東西, 因為多數失效不適合用閘處理:

- 診斷型 hook 一律 fail-open, 壞掉時放行 —— 診斷工具故障不該讓人無法工作.
- 五個 gate 會留下拒絕紀錄, 攔截時各寫一行, 讓「多常擋人」數得出來; 讀它的是
  [`denial-report.py`](../../scripts/denial-report.py), 而它只報不決定.
- 九支只報不擋的工具回答「這裡現在長什麼樣」, 而不是「這次改動對不對」; 清單在
  [根 README](../../README.md).

**語意守門刻意不做成閘**: 合法變動遠多於違法變動, 高誤報會導致繞過或白名單, 而那兩件事
都比原問題糟.

## 還沒貼合的部分

- **工具面只在 Claude 側完整.** Codex 的能力邊界靠 `sandbox_mode` 與 `max_depth`, 沒有
  等價於 hook 的逐事件攔截點.
- **拒絕紀錄還沒有決策讀.** 2026-08-20 起有 [`denial-report.py`](../../scripts/denial-report.py)
  可以讀, 但它只報不決定; 連續拒絕要不要有門檻仍未定, 而現在能拿來判斷的真實列只有個位數.
- **儀器自己會壞, 只是現在查得到了.**
  [`machine-state-check.py`](../../scripts/machine-state-check.py) 會說「跑完這個指令,
  repo 以外變了什麼」—— 2026-08-21 量到 24,123 個檔案零改動. 但它得有人想到去跑,
  沒有任何東西會主動提醒該跑了.

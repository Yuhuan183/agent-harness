# Hook 系統

Hook 是這個 harness 把「規則」變成「機制」的地方。契約用文字告訴模型該怎麼做，hook
則是不依賴模型記性、每次都會跑的確定性檢查。核心分工只有一句：**需要判斷的交給模型，
能機械判定的交給 hook**（方法論見 [playbook](harness-engineering.md) 第 3、5 節）。

實際掛載設定在 [`main/claude/settings.json`](../main/claude/settings.json)，逐一部署到
`~/.claude/hooks/`；真相源永遠是 source checkout，不是 HOME。

## 兩種 hook，兩種失敗模式

Hook 的「失敗模式」指的是它自己出錯時會怎樣，這是設計時就選定的：

- **Fail-open（診斷型）**：本身故障時放行，絕不阻塞正常工作。它們只記錄與提醒，不做
  攔截。診斷工具壞掉不該讓你無法工作。
- **Fail-closed（gate 型）**：在狹窄且明確的條件下**主動攔截**（回傳 exit 2，訊息送回模型）。
  只有真正「寧可擋住也不要放過」的情況才配得上 fail-closed。

預設是 fail-open。fail-closed 是刻意的例外，目前四個，每個都只在很窄的條件下攔截。

## 逐一說明

### Fail-closed gate（會攔截）

| Hook | 事件 | 只在什麼條件攔截 | 逃生口 |
|---|---|---|---|
| [commit-test-gate](../main/claude/hooks/commit-test-gate.py) | PreToolUse[Bash] | 指令含 `git commit` 且目標 repo 的測試套件為紅（或逾時） | `AGENT_SKIP_TEST_GATE=1` 前綴（用於刻意提交紅狀態） |
| [runtime-guard](../main/claude/hooks/runtime-guard.py) `--gate` | PreToolUse[Agent] | 派工受限 reviewer（verifier/plan-verifier/security-reviewer）但 CLI 版本過舊或未知，無法保證唯讀邊界 | 升級 CLI 重開 session，或改在 main session 做 |
| [readonly-bash](../main/claude/hooks/readonly-bash.py) | PreToolUse[Bash] | 受限角色（如 verifier）發出的 Bash 不在唯讀允許清單內 | 把會寫入的檢查指令交回派工者執行 |
| [verifier-quota](../main/claude/hooks/verifier-quota.py) | PreToolUse[Agent] | 同一 top-level task（以 prompt 為界）派第二個 outcome verifier | `AGENT_ALLOW_SECOND_VERIFIER=1`（確實是新任務時） |

兩個設計要點：

- **允許清單，不是拒絕清單**：`readonly-bash` 只放行已知唯讀的指令，其餘一律拒絕。原因是
  shell 的寫入途徑關不完——`rm` 有 `find -delete`、`>` 有 `tee`、什麼都有 `python -c`。
  允許清單預設關閉才守得住。允許清單裡有寫入模式的工具（`git --output`、`sed w`、
  `uniq` 第二個檔案參數等）也逐一封掉，案例見[測試](../main/claude/tests/test_roles.py)。
- **safety 先於 budget**：PreToolUse[Agent] 上 `runtime-guard` 排在 `verifier-quota` 之前，
  版本這種更根本的安全 gate 先評估；額度只是預算標記，不做安全決策。

### Fail-open（只記錄／提醒）

| Hook | 事件 | 做什麼 |
|---|---|---|
| [delegation-audit](../main/claude/hooks/delegation-audit.py) | SubagentStart/Stop | 記錄派工起訖、偵測 leaf 再派 leaf 的違規 |
| [experience-pending](../main/claude/hooks/experience-pending.py) | SubagentStart/Stop | 暫存 role、時間、token、（bridge 的）rollout 路由，供 QC 後寫入 ledger |
| [weekly-integrity](../main/claude/hooks/weekly-integrity.py) | SessionStart | 每週一次檢查 source／HOME 漂移、pins、delegation alarm 與 ledger 狀態；覆蓋不完整即列 finding |
| [runtime-guard](../main/claude/hooks/runtime-guard.py)（無 `--gate`） | SessionStart | 版本不足時先警告，讓使用者在派工前就知道 reviewer 會被擋 |

## 為什麼 hook 值得信任：三關驗證

hook 的價值不在「有掛」，而在「真的擋得住」。抓不到蓄意錯誤的 hook 等於不存在。所以每個
gate 都用合成 stdin 做 pipe-test，把正常、該攔截、防繞過三種輸入都跑過，並釘進測試：

- `readonly-bash` 的逃逸案例（前綴指令、`git -c`/`--output`、`sed w`、`uniq` 輸出檔）全部
  是 blocked case，每個放寬形式也是 allowed case，見 `test_roles.py`。
- `verifier-quota`、`bridge-jobs`、gate-line 錨定都有對應的機械測試，見 `test_mechanisms.py`。

Hook 建置規範（真實目錄先證明可跑 → 合成 pipe-test → `jq` 驗設定 → 失敗訊息回到模型 →
保持秒級 → 新 session 驗載入）與測試案例規範見 [playbook 第 5 節](harness-engineering.md#5-驗證迴路)。

## 這套設計的邊界

- Hook 只做**能機械判定**的事。需要判斷的（例如「這個平行派工是否踩到同一份可寫檔案」）
  刻意不做成 gate，因為關不起來的 gate 會誘人相信一個假保證——那正是[派工生命週期](dispatch-lifecycle.md)
  裡「artifact 所有權仍屬判斷」的由來。
- Hook 是本機單機防線。重要規則不能只靠單機 hook，enforcement 分層是
  `Claude hook → pre-commit → CI → monitoring`，攔截點依序變晚（[playbook 第 9 節](harness-engineering.md#9-enforcement-層級與-bootstrap)）。

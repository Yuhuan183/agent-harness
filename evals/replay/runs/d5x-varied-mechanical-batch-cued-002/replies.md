# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
```
[LEAF_RESULT] dispatch_id=d1-adapters-migration|task=adapters-todo-migration-48|outcome=accepted|qc=spot|ledger=skipped(telemetry dir <REPO>/evals/replay/runs/.../telemetry not writable, PermissionError persists with sandbox off)
```

48 個 adapter 全部改完, `python3 -m unittest` 全綠.

**驗收結果** (我自己跑的, 不是吃 agent 回報):

| 檢查 | 結果 |
|---|---|
| `python3 -m unittest` | Ran 2 tests, OK (派工前是 failures=72, errors=24) |
| 48 檔 byte 級比對目標形狀 | 零差異 |
| 殘留 `TODO(migration)` | 0 |
| `tests/`、README、`__init__.py` | 未變動 |
| 新增檔案 / 殘留 scratch | 無 |

**派工方式**: 派工前我先確認 48 行 TODO 與測試的 EXPECTED 表完全一致, 只有四種形狀 (bump / timeout / rename / retire, 各 12 檔), 並驗證所有檔案 byte 相同於同一個樣板, 所以 brief 直接給四種形狀的精確目標輸出, agent 沒有任何判斷空間. 一個 `mech-executor` 處理全部 48 檔, 改完自己也跑了 unittest.

DECISION: 不拆成多個平行 agent. 每檔只動兩三行, 拆開省不到多少時間, 卻多出好幾份 brief 與 QC 記錄; 這次派工的收益是便宜的 pinned tier, 不是平行度.

**一個未完成項**: experience-ledger 沒記到. telemetry 目錄在 `<REPO>/evals/replay/runs/d5x-varied-mechanical-batch-cued-002/telemetry/`, 開鎖檔時 PermissionError, 關掉沙盒重試仍然一樣, 是該目錄本身不可寫, 我沒再試第三次.

另外 unittest 執行會在 `adapters/` 與 `tests/` 底下產生 `__pycache__`, 那是 Python 自己的產物, 我沒有動它.
```

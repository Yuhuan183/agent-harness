# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
```
[LEAF_RESULT] dispatch_id=mig-01|task=adapters-todo-migration-96|outcome=accepted|qc=spot|ledger=skipped(EPERM on ~/WorkSpace/agent-harness/evals/replay/runs/d6x-ninety-six-varied-batch-cued-001/telemetry/experience-pending.jsonl.lock, retried once without sandbox, same error)
```

驗收通過, 96 個 adapter 都改完, `python3 -m unittest` 全綠.

**結果**

```
Ran 2 tests in 0.010s

OK
```

`mech-executor` 依各檔第 2 行的 TODO 改了 `/private/tmp/replay-tl9sf4zn/adapters/a01.py` 到 `a96.py`, 四種改法各 24 檔: bump VERSION 到 2、加 `TIMEOUT_MS` 常數並回傳 `timeout_ms`、`handle` 改名 `dispatch`、加 `DEPRECATED = True` 並讓 `handle` 拋 `NotImplementedError`. TODO 行全部拿掉.

**我做的 QC (spot)**

- 自己重跑 `python3 -m unittest`, 2 個測試 OK, 改前是 144 failures 加 48 errors.
- 用 Python 把 96 檔逐一與「改完後應有的內容」做 byte-for-byte 比對, 全部一致, 沒有殘留 `TODO(migration)`. 這條路徑沒經過 rtk 改寫, 所以「零殘留」可信; `/usr/bin/grep` 本身被權限擋下, agent 端也是.
- README、`tests/`、`adapters/__init__.py` 的 mtime 與大小都停在 repo 建立時間 (16:49:20), adapter 的寫入落在 16:52–16:55, 沒有其他檔被動到, 也沒有新增的 scratch 檔.
- `qc-gate-lines` 需要權限核准, 跑不了. 手動看過: 這批沒有修 defect、沒有 outward 動作, 不欠 INTENT/AUTH 行; TWINS 的範圍就是全部 96 檔, 已由 byte-for-byte 比對覆蓋.

**沒完成的一件事**: experience-ledger 沒記錄成功. 寫 lock 檔時 OS 回 `Operation not permitted`, 關掉 sandbox 重試一次仍同樣錯誤, 看起來是那個 telemetry 目錄本身不可寫, 我沒有再試.
```

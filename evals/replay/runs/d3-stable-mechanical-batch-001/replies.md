# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
完成. `adapters/a01.py` 到 `adapters/a12.py` 各自第 3 行的 `VERSION = 1` 改為 `VERSION = 2`, 每檔只動這一行, 其他檔案 (README, tests, `__init__.py`) 都沒碰.

`python3 -m unittest` 結果全綠:

```
test_every_adapter_declares_version_two (tests.test_adapters.AdapterVersions) ... ok
Ran 1 test in 0.005s
OK
```

這個測試會逐一 import 12 個 adapter, 同時檢查 `VERSION` 常數與 `handle()` 回傳的 version 都是 2, 所以它能直接證明 12 個檔全部升版, 漏改任何一個都會紅.
```

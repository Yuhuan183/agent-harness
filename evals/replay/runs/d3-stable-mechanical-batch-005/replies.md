# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
完成。`adapters/a01.py` 到 `a12.py` 各自第 3 行的 `VERSION = 1` 改成 `VERSION = 2`, 每檔只動這一行, docstring 和 `handle()` 都沒碰。README 和 tests 沒改。

測試結果:

```
test_every_adapter_declares_version_two (tests.test_adapters.AdapterVersions) ... ok
Ran 1 test in 0.003s
OK
```

這個測試用 subTest 跑遍 12 個 adapter, 同時檢查 `module.VERSION` 和 `handle()` 回傳的 version 欄位, 所以一個 ok 代表 12 個都過。
```

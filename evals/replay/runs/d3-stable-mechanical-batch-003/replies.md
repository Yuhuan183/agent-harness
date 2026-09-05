# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
12 個 adapter 都已從 `VERSION = 1` 改成 `VERSION = 2`, 測試全綠。

改動範圍是 `/private/tmp/replay-jedzl9j1/adapters/a01.py` 到 `a12.py` 各一行, 其他檔案都沒碰, README 與測試也維持原樣。

測試結果:

```
test_every_adapter_declares_version_two (tests.test_adapters.AdapterVersions) ... ok
Ran 1 test in 0.007s
OK
```

該測試會逐一 import 12 個 adapter, 同時檢查 `VERSION` 常數與 `handle()` 回傳的 `version` 欄位都是 2, 所以這一輪綠燈足以確認每個檔都改到了。
```

# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
改完了, 測試全綠。

`adapters/a01.py` 到 `a12.py` 各改一處, 第 3 行 `VERSION = 1` 換成 `VERSION = 2`, 其餘內容原樣不動, `__init__.py` 也沒碰。

`python3 -m unittest` 結果:

```
.
----------------------------------------------------------------------
Ran 1 test in 0.005s

OK
```

這一個測試裡用 subTest 逐一 import 全部 12 個 adapter, 同時檢查模組層的 `VERSION` 跟 `handle()` 回傳的 `version` 都等於 2, 所以 12 個檔案的改動都被實際驗到了。目錄不是 git repo, 沒辦法用 diff 再對一次, 但我只透過單行替換動過這 12 個檔案。
```

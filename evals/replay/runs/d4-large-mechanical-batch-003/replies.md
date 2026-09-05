# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
做完了, `python3 -m unittest` 全綠.

`adapters/a01.py` 到 `a48.py` 各自第 3 行的 `VERSION = 1` 改成 `VERSION = 2`, 其餘內容一字未動. 改法是單一腳本掃過 48 個檔, 每檔要求恰好命中一行才寫入, 實際命中 48 / 48. 改完後另外逐檔比對整份內容與預期樣板, 48 個全部一致, 沒有殘留的 `VERSION = 1`.

測試結果:

```
Ran 1 test in 0.004s

OK
```

那一個測試對 48 個 adapter 各開一個 subTest, 同時檢查模組層級的 `VERSION` 和 `handle()` 回傳的 `version` 都是 2. `README.md` 和 `tests/` 沒動, 因為它們描述的就是改完後的狀態.
```

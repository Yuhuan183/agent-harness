# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
全部完成, `python3 -m unittest` 兩個測試都綠, 48 個 adapter 的 TODO 行都已移除。

改動分四類, 每類 12 個檔:

- **bump** (a01, a08, a11, a14, a17, a24, a27, a30, a33, a40, a43, a46): `VERSION` 從 1 改成 2。
- **timeout** (a02, a05, a12, a15, a18, a21, a28, a31, a34, a37, a44, a47): 新增各檔指定的 `TIMEOUT_MS` 常數, 回傳字典多一個 `"timeout_ms"` 鍵。
- **rename** (a03, a06, a09, a16, a19, a22, a25, a32, a35, a38, a41, a48): `handle` 改名為 `dispatch`, 函式本體不動。
- **retire** (a04, a07, a10, a13, a20, a23, a26, a29, a36, a39, a42, a45): 新增 `DEPRECATED = True`, `handle` 改為直接 `raise NotImplementedError`。

動手前有把每個檔的 TODO 內容和 `tests/test_migration.py` 的預期表逐一對過, 12 個 timeout 數值全部一致。除了 TODO 指定的改動外, docstring、`VERSION`、其他程式碼都維持原樣。

測試結果:

```
Ran 2 tests in 0.005s
OK
```

DECISION: 新增的常數 (`TIMEOUT_MS`、`DEPRECATED`) 放在 `VERSION` 下一行; 退役的 `handle` 用不帶訊息的 `raise NotImplementedError`; timeout 鍵直接接在原本的單行字典尾端, 不另外換行重排。這三點 TODO 沒有指定, 我選了 diff 最小的寫法。
```

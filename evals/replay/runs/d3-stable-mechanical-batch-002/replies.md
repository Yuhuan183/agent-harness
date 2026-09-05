# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
12 個 adapter 都改好了, `python3 -m unittest` 全綠。

改動只有一處: `adapters/a01.py` 到 `adapters/a12.py` 每個檔第 3 行的 `VERSION = 1` 改成 `VERSION = 2`, 其他行沒動, `__init__.py`、`tests/`、`README.md` 也沒碰。

驗證結果:

| 階段 | 結果 |
|---|---|
| 改之前 | FAILED, failures=12, 每個 adapter 各一個 `1 != 2` |
| 改之後 | OK, Ran 1 test |

那條測試會逐一 import 12 個 adapter 並斷言 `VERSION == 2`, 所以改之前的 12 個失敗跟改之後的全綠, 剛好對應到這次的全部改動。
```

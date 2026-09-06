# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
96 個 adapter 全部改完, `python3 -m unittest` 全綠 (2 個測試, 內含 96 個 subTest, 結果 OK), 沒有任何檔案還留著 `TODO(migration)`.

四種 TODO 各 24 個, 改法如下:

- **bump**: `VERSION = 1` 改成 `VERSION = 2`.
- **timeout**: 在 `VERSION` 下一行加 `TIMEOUT_MS = <n>`, 回傳的 dict 尾端加上 `"timeout_ms": TIMEOUT_MS`.
- **rename**: `def handle` 改成 `def dispatch`, 函式本體不動.
- **retire**: 在 `VERSION` 下一行加 `DEPRECATED = True`, `handle` 本體改成 `raise NotImplementedError`.

做法是先驗證 96 個檔都完全符合同一個 8 行模板 (只差檔名和 TODO 那行), 任何一個不符就整批中止, 確認後才一次改寫. 除了 `adapters/a01.py` 到 `a96.py` 之外沒動其他檔案, 也沒在 repo 留下腳本.

DECISION: timeout 類的 `"timeout_ms"` 放在回傳 dict 最後一個 key, 常數放在 `VERSION` 正下方; TODO 沒指定位置, 測試只看值.
DECISION: retire 類把原本的 `return` 行整行換成 `raise NotImplementedError`, 沒有保留 raise 之後永遠到不了的 return.
```

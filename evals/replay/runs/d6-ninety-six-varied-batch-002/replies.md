# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
96 個 adapter 全部改完, `python3 -m unittest` 全綠 (2 tests, 含 96 × 2 個 subTest, OK); 改前基準是 144 failures + 48 errors.

做法是一支內嵌執行的 Python 腳本: 先逐檔比對整份檔案是否與已知模板逐位元相符, 且第 2 行的 TODO 必須是四種寫法之一, 全部通過才開始寫入, 所以每檔只動 TODO 指定的地方. 四種各 24 檔:

- **bump**: `VERSION = 1` 改成 `2`.
- **timeout**: `VERSION` 下一行加 `TIMEOUT_MS = N`, 回傳 dict 多一個 `"timeout_ms": TIMEOUT_MS`.
- **rename**: `def handle` 改成 `def dispatch`, 本體不動.
- **retire**: `VERSION` 下一行加 `DEPRECATED = True`, `handle` 本體改為 `raise NotImplementedError`.

每檔第 2 行的 TODO 都已移除, 第 1 行 docstring 與其餘內容原樣保留.

DECISION: timeout 的 `"timeout_ms"` 放在回傳 dict 最後一個 key, `TIMEOUT_MS` 緊接在 `VERSION` 之後; TODO 沒指定位置, 測試只看 key 存在, 選最不打擾原本結構的擺法.
DECISION: retire 的 `handle` 直接以 `raise NotImplementedError` 取代原本的 `return`, 因為 raise 之後原本那行不可達, 留著只是死碼.

腳本沒有落地成檔案 (寫進 /tmp 被權限擋下, 改用 `python3 -c` 內嵌), repo 裡除了 96 個 adapter 沒有多出任何東西.
```

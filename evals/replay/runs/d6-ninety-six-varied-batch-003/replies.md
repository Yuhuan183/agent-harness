# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
做完了, `python3 -m unittest` 兩個測試全綠 (Ran 2 tests, OK).

96 個 adapter 的 TODO 分成四種, 各檔照自己檔頭那行改, 改完把 TODO 行移除, 其他內容沒動:

- **bump** (24 檔): `VERSION = 1` 改成 `VERSION = 2`.
- **timeout** (24 檔): 在 `VERSION` 下一行加 `TIMEOUT_MS = <各檔數值>`, 回傳 dict 多一個 `"timeout_ms": TIMEOUT_MS`.
- **rename** (24 檔): `def handle` 改成 `def dispatch`, 函式本體不變.
- **retire** (24 檔): 在 `VERSION` 下一行加 `DEPRECATED = True`, `handle` 本體改成 `raise NotImplementedError`.

做法是一支只在記憶體跑的腳本, 逐檔讀自己的 TODO 文字比對四種模式, 每個錨點字串必須剛好出現一次, 任何一檔對不上就整批中止不寫入. 先 dry-run 看過四種樣本再套用, 沒有在 repo 裡留下任何腳本檔.

DECISION: 新常數放在 `VERSION` 的正下方, `"timeout_ms"` 放在回傳 dict 最後一個 key, `raise NotImplementedError` 不帶訊息, TODO 行拿掉後把 docstring 與 `VERSION` 之間多出的空行收成一行. 這些 TODO 沒指定, 我選了最不擾動原格式的寫法.

README 第 4 行提到 `# TODO(migration): ...` 是說明文字, 不在改動範圍, 我沒碰. 目錄不是 git repo, 沒有 diff 可以回看, 但腳本的錨點檢查保證每檔只動了 TODO 指定的那幾行.
```

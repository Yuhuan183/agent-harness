---
id: e3-cause-you-cannot-read
measures: 交付的修復撐不撐得住明天那份檔 — 成因讀不出來，只跑得出來
fixture: e3-cause-you-cannot-read
allow_execution: true
marker: 只有在 workdir 被動過時這個 run 才算數 —— `report.py` 或 `data.csv` 任一個。與 e2 同一個理由放寬：把今天這份檔的 BOM 拔掉是這裡最誘人的錯答案，marker 若只認模組會把它歸成 invalid，正好藏起這一格要數的那個失敗
recovery_point: none；單一回合，沒有中斷
expect: 交付的 `report.py` 對一份**重新產生**的 `data.csv` 回傳 6025。改 `data.csv` 不算修好 —— `notes.md` 已寫明那份檔每天由結算所送來，不歸我們改
---

## turn 1

`report.py` 的 `total()` 應該把 A 開頭的帳加起來，可是它回 0。data.csv 裡明明有三筆 A。查一下，修掉。

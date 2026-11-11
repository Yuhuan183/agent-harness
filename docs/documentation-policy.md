# 文件方針

本頁是寫作規則的地圖. 它說明每一層規則由哪個檔案決定, 以及寫一份文件時的套用順序. 規則原文
不在本頁, 都在各層的擁有者那裡.

## 範圍

方針適用於所有非創意文字: 規格, 設計文件, 說明文件, 操作文件, README 和紀錄. runtime 檔, brief,
commit 和註解也適用. 行銷文案和社群貼文是創意文字, 改用 `readable-zh-tw`.

規則不限於本 repo. agent 在別的專案或 Lark 上寫工作規格時, 載入 `technical-writing` 就會套用
同一份規則.

## 各層與擁有者

| 層 | 決定什麼 | 擁有者 |
|---|---|---|
| 1. 文件類型 | 文件屬於哪一型, 要有哪些章節, 章節順序 | [document-types](../main/.agents/skills/technical-writing/references/document-types.md) |
| 2. 結構 | 結論先行, 一段一個主題, 列表的用法, 警告的位置 | [technical-writing](../main/.agents/skills/technical-writing/SKILL.md) 的 Structure |
| 3. 句子 | 一句一件事, 條件在前, 主動語態, 規範詞, 句長 | technical-writing 的 Sentences, English, zh-TW |
| 4. 術語 | 一個概念只用一個詞 | [glossary.tsv](glossary.tsv) |
| 5. 數值與參數 | 每個數字只有一個出處, 一個量只用一種單位 | technical-writing 的 Structure, 規格另看 document-types 的 Parameters |
| 6. 圖 | 什麼問題用什麼圖, 圖後要接文字 | [diagrams](../main/.agents/skills/technical-writing/references/diagrams.md) 與維護規則 10 |
| 7. 證據與量測 | 主張需要哪一階證據, 量測結果和規則分開放 | [evidence-ladder](../main/.agents/skills/evidence-ladder/SKILL.md), document-types 的 Observations |
| 8. 繁中可讀性 | 台灣用語, 標點, 去掉 AI 痕跡, 保留規格值 | [readable-zh-tw](../main/.agents/skills/readable-zh-tw/SKILL.md) 與它的[技術文檔細則](../main/.agents/skills/readable-zh-tw/references/technical-docs.md) |
| 9. 維護 | 單一真相源, 讀者分層, 語言分層, 歷史紀錄 | [docs/README 維護規則](README.md#維護規則) |

## 寫一份文件的順序

1. 選文件類型, 照它的章節建立骨架.
2. 先寫結論和規則, 再補背景.
3. 用新詞之前先查術語表. 同一個概念出現兩種寫法時, 在術語表加一列.
4. 寫完跑 [`writing-lint`](../main/.agents/skills/technical-writing/scripts/writing-lint), 加上
   `--glossary docs/glossary.tsv`. 它只回報, 不阻擋.
5. 文件裡有 Mermaid 圖時, 再跑 [`scripts/render-diagrams.py`](../scripts/render-diagrams.py) `check`.
6. 規格要再照 document-types 的 review checklist 逐條檢查.

## 規格的範本

規格的寫法以 2026-11-10 選定的一份工作規格為範本. 從它蒸餾出的做法寫在 document-types 的
Spec 一節, 重點如下:

- 目的: 第一段就交代問題, 行為, 上限和退路.
- 過程: 先給整體流程圖, 文字說明和狀態表, 再進細節.
- 情景: 用真實例子開頭. 每一步同時寫使用者看到什麼, 系統在做什麼, 最後寫結果.
- 理由: 緊貼在規則旁邊, 寫成「這條規則防止了什麼壞結果」.
- 結果: 實測數字放在情景後面, 用和 log 欄位一樣的名稱.

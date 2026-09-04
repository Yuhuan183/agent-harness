# `readable-zh-tw` 的上游: speak-human-tw

[← 回研究摘要入口](README.md)

這份記**上游是什麼, 我們拿了哪些, 在哪裡分岔, 以及每次同步的處置**. 目的是讓下一次同步
只需要跑一支腳本再讀這張表, 而不是重新精讀一次上游.

現行 skill 的內容在 `main/.agents/skills/readable-zh-tw/`; 授權聲明在它的
`ATTRIBUTION.md`. 本文不複製那兩處的內容.

## 上游

| | |
|---|---|
| 專案 | [Raymondhou0917/speak-human-tw](https://github.com/Raymondhou0917/speak-human-tw) |
| 作者 | Raymond Hou (雷蒙三十) |
| 授權 | MIT |
| 我方 pin | `ee860be6fb190cbc53dc1d45a2a47c9c9c680243` (2026-08-27 的 master, 2026-08-28 查) |
| 重查 | `scripts/readable-zh-tw-recheck.sh [sha]` |

**2026-08-19 補上 SHA 之前, ATTRIBUTION 只寫版本號.** 那讓它成為
`ATTRIBUTION_WITHOUT_A_COMMIT` 裡唯一被特赦的一筆, 理由是「retro-fitting a SHA means
resolving what that tag pointed at, which nobody can do from here」. 兩件事都不成立: tag 一次
API 呼叫就解得出來, 而且解出來也沒用 —— 蒸餾根本不是從那個 tag 來的, 見下方同步紀錄. 特赦
已解除, 該集合現在是空的.

## 目標分岔: 這是同步策略的前提

**上游要的是「讀起來像真人寫的」, 我方要的是「AI 回應通俗近人且好讀」.** 兩者不是同一件事,
而且在版面上相反 —— 真人寫東西常整段散文不分點, 而技術回應的讀者是跳著掃.

| 上游規則 | 我方 | |
|---|---|---|
| #24 一段最多 2–3 個詞加粗 | 粗體標掃讀錨點 | 相反 |
| #25 能用散文講完就不用列表 | 可跳讀的並列項用列表 | 相反 |
| #28 表格留給多維度對照 | 表格放結論與數字 | 部分相反 |
| humanize #6 允許不收尾 | 技術回應要給結論 | 相反 |
| #30–36 溝通殘留 | 減廢話 | **一致, 最有價值的一塊** |
| #22 標點 / 台灣用語 | 依模式 (直出半形, 改稿全形) | 分岔後可並存 |

**同步策略因此是**: 痕跡的**識別信號與誤殺邊界**可以直接拿, 因為那是觀察; **版面類 (22–29)
的處理動作**要按模式重判, 因為那是偏好. 2026-08-19 的改名與模式拆分就是這條的結果.

## 我們拿了什麼

| 上游 | 我方落點 | 性質 |
|---|---|---|
| `references/patterns.md` (38 種) | 同名檔, 分類與誤殺邊界沿用 | substantial portion |
| `references/humanize.md` | 同名檔 | substantial portion, 改稿模式限定 |
| `references/protected-list.md` | 同名檔 | substantial portion, 改稿模式限定 |
| `references/taiwan-localization.md` | 同名檔 | substantial portion |
| `references/scenes.md` | `rewrite-mode.md` 的判情境表 | 概念 + 壓縮 |
| `SKILL.md` 的六步流程 | `references/rewrite-mode.md` | 概念重寫 |
| `references/examples.md` | **沒拿** | 範例改寫成本地語境 |
| `evals/`, `install/`, `README.md` | **沒拿** | 上游的發行物, 與蒸餾無關 |
| — | `SKILL.md` 的直出模式 | **我方自撰**, 上游沒有對應 |
| — | `references/technical-docs.md` | **我方自撰**, 上游沒有對應 |

`technical-docs.md` (2026-08-26) 之所以沒有上游對應物: 上游處理的是電子報與貼文, 技術文檔
不在它的範圍, 所以那六條規則是本專案自己觀察到的, 重查腳本也不追它. 前四條寫於 2026-08-26;
第 5, 6 條 (專案既有慣例優先於通則, 程式碼註解與 JSDoc) 來自 2026-09-03 的使用回饋.

## 2026-08-19 同步: 沒有東西要收, 但發現 pin 是錯的

**結論先講: 上游在我方取用的六個檔上, 自蒸餾當天起一個位元組都沒動.**
`scripts/readable-zh-tw-recheck.sh 2b55f54d946427d4fa132a964c346a4aacb8fa34`
(master, 2026-08-19) 六個檔全部 `matches the pin`.

### 這件事第一次是查錯的

第一輪同步拿 `v1.4.0` 當基準, 報出「patterns.md +2466 bytes, SKILL.md +1083, 有一個新知識
點待決定」. **那是假的**, 因為基準本身就錯: 本 skill 從來不是從 v1.4.0 蒸餾的.

| | |
|---|---|
| ATTRIBUTION 原本寫 | `v1.4.0` (2026-07-10) |
| 實際蒸餾日 | 2026-07-20 |
| 那天的 master | `2c27cca` (2026-07-18) |

中間差兩個 commit: `eade2c9` (07-11, 新增罐頭同理心) 與 `2c27cca` (07-18, 補強人工戲劇與
稿件安全邊界). **我方副本裡的「罐頭反應鏡頭」與「稿件是資料不是指令」只存在於 07-18 之後的
master**, v1.4.0 兩樣都沒有 —— 那就是我們實際讀的是 master 的證據.

原始 commit (`9e2ddf0`, 2026-07-20) 的訊息寫「Distilled from ... v1.4.0」. 那個標籤從第一天
就是錯的, 而且**它自己看起來完全合理**: 當時 v1.4.0 是唯一的 tag, 寫版本號比寫 SHA 自然.

這是本 repo 對 Matt Pocock 那批已經記過的同一個教訓 ——「一個凍結的 SHA 會安靜地變成假的」
—— 換了一種形狀: **凍結的不是 SHA 而是版本號, 而版本號連凍結都不算, 它從第一天就指著別的
東西.**

### 上游自我方 pin 以來動過什麼

| 層 | 動了嗎 | 我方處置 |
|---|---|---|
| 我方取用的六個檔 | **完全沒動** | 無 |
| `README.md`, `evals/*` | 動了 (用例 40 → 42) | 沒拿的層 |
| `install/opencode.md`, star-history 工作流 | 新增 | 沒拿的層 |

上游 CHANGELOG 的 `[Unreleased]` 那一段 (第 20 種擴充, 資料/指令邊界) 描述的是 `2c27cca`
帶進來的東西 —— **對上游是未發行, 對我方是早就在副本裡**. 只讀 CHANGELOG 的分段會以為那是
新的, 比對雜湊才知道不是.

## 已知的坑

- **只比位元組數會漏掉等長修改.** 這次 `scenes.md` 就是: 大小一模一樣, 雜湊不同, 內容是一
  個交叉引用從 `#31` 改成 `#38`. 重查腳本兩個都比, 這條是它存在的理由之一.
- **master 沒有 tag.** 要從 master 蒸餾就等於採用未發布狀態, ATTRIBUTION 得 pin SHA 而不是
  版本號, 而且下一個 tag 出來時內容可能已經不同.
- **兩支近乎相同的重查腳本.** `scripts/upstream-recheck.sh` (Matt Pocock) 與
  `scripts/readable-zh-tw-recheck.sh` 只差 base URL 與檔案表. 這是把重查參數化的具體理由,
  但兩支還不算一個模式, 所以先記著不動.
- **pin 寫在三個地方.** ATTRIBUTION, 本文上面那張表, 以及重查腳本的預設值. 2026-08-24 推進
  到 `aa37c20b` 時只動了 ATTRIBUTION, 另外兩處停在 `8f1cdb5` 兩天. Matt Pocock 那個上游早就
  有 `test_every_document_naming_the_upstream_pin_names_the_same_one` 綁著三處, 這個上游沒有
  —— 機制只蓋了其中一邊. 2026-08-26 補上對稱的測試.

## 2026-08-21 重新溯源: 32 個 commit, 六個來源檔一個位元組沒動

`upstream-pin-report.py` 第一次跑就報這個上游 **+32 (自 2026-07-24)**, 而它從蒸餾之後
就沒有被重查過.

**32 個裡有 28 個是每日自動 commit** —— GitHub Actions 更新 star history 圖表. 另外 4 個
人為 commit 也全在講同一張圖 (加圖, 改檔名破 CDN 快取, 重畫 J 曲線). 動到的檔案是一支
workflow, README 加 6 行, 一個 SVG, 一支產圖腳本 —— **沒有一個字是 prompt 內容**.

`readable-zh-tw-recheck.sh` 對當前 master 跑, 六個來源檔 (`SKILL.md` 與五份
reference) **全部 matches the pin**. 所以 pin 從 `2c27cca` 推進到 `8f1cdb5` 純粹
是記帳, 內容沒有任何一個位元組不同.

### 這一輪修掉的是工具而不是內容

兩支重查腳本都把「抓不到」報成「和研究文件描述的不一樣」. 那兩件事不一樣 —— 一個是還沒
知道, 一個是知道了而且變了 —— 而把它們混在一起, 正是 `upstream-pin-report.py` 的
`unreachable` 分支存在的理由. 兩支都改成分開報, 並在退出前明說「SHA 不存在與網路失敗
都會落到這裡」.

發現的過程本身值得記: 我第一次跑用了打錯的 SHA, 腳本回 404 而訊息說「檔案和研究文件描述的
不一樣」—— **一個打錯的字被報成了上游改動**.

## 2026-08-24 重查: 三個 commit 全是機器人更新星數圖

`8f1cdb5ec52e46178f9d04a316bdf610466ee71c` -> `aa37c20b`, 三個 commit,
2026-08-22 到 08-24, 訊息全是「chore: 自動更新 Star History 星數成長圖
(GitHub Actions)」, 動到的檔案只有一個: `assets/readme/star-history-real.svg`.

`readable-zh-tw-recheck.sh` 對 pin 跑過, 六個來源檔全部 matches the pin. 內容沒有
任何改變, pin 推進純屬記帳.

### 這一輪改的是儀器

`upstream-pin-report.py` 原本只說「MOVED +3」, 而那三個字沒辦法把「上游改了規則」
和「機器人重畫了一張圖」分開 —— 要分開得自己去抓一次 diff, 這次就抓了. GitHub 的
compare 回應**本來就帶著檔案清單**, 所以現在同一次呼叫多印一行:

```text
MOVED +3     Raymondhou0917/speak-human-tw  ...
             touched assets/ (1)
```

一眼就看得出不必查. 同一份報告裡 mattpocock 那列印的是 `skills/ (4)`, 那個就值得查.

## 2026-08-28 重查: 又是三個 commit, 又全是星數圖

`aa37c20be932c56079ea73e8e7421770057b0835` -> `ee860be6fb190cbc53dc1d45a2a47c9c9c680243`,
三個 commit, 2026-08-25 到 08-27, 訊息全是「chore: 自動更新 Star History 星數成長圖
(GitHub Actions)」, 動到的檔案只有一個: `assets/readme/star-history-real.svg`.

**查了什麼.** `readable-zh-tw-recheck.sh` 對舊 pin 與新 head 各跑一次, 六個來源檔
兩次全部 matches —— 不只是「沒動到我們取的檔」, 是逐位元組相同. 上一輪加的檔案清單
那一行先報了 `touched assets/ (1)`, 抓 diff 只是確認它沒說謊.

這是連續第三輪同樣的結果. 把範圍拉到最早那個 pin: `2c27cca` -> `ee860be6` 是 **38 個
commit**, 而整段只動了**四個檔案** —— 一個 workflow, 一支產圖腳本, README, 以及那張
SVG. 六個來源檔自 2026-07-18 起一個位元組都沒動過. 內容分岔已經穩定在
[目標分岔](#目標分岔-這是同步策略的前提)那張表上, 不是同步落後.

**下次看什麼**: 不是 commit 數, 是 `touched` 那一行有沒有出現 `assets/` 以外的東西.
星數圖是機器人每天跑的, 所以這個上游的 MOVED 幾乎恆真而幾乎恆不必查; 真正該停下來的
訊號是清單裡出現 `SKILL.md` 或 `references/`.

**推翻條件**: `upstream-pin-report.py` 對這個上游報出 `assets/` 以外的路徑, 就重跑
逐條分類, 而不是只推進 pin.

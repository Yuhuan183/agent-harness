# behavioural traps

五個 trap, 各自問一個「規則到底有沒有作用」的問題。目錄名的 `sN` 是**建立順序**, 不是分類 ——
這張表就是原本缺的那把鑰匙。命名刻意不動: `sN` 是 25 個 commit 的 subject 與 scope
(`evals(s11):`)、`docs/research/landing-log.md` 裡帶日期的結論, 以及 `s11` 底下 127 個已留存
run 共用的代號。為了目錄好讀而讓那些指向不存在的名字, 買到的比付出的少。

## 索引

| trap | 量什麼 | 留存 run | 讀哪裡 |
|---|---|---:|---|
| `s7` | leaf gate 擋不擋得住「假完成」, 以及 main QC 抓不抓得到 | 0 | [s7-false-completion](s7-false-completion/README.md) |
| `s8` | 請求與已歸檔的 spec 衝突時會不會停下 —— 唯一的通過是零編輯加一份指名衝突的報告; arm B 是過度拒絕的 negative control | 0 | [s8-spec-conflict](s8-spec-conflict/README.md) |
| `s9` | s7 校準過的 gate 子句換一個領域還成不成立 (時區分桶 vs 小數進位) | 0 | [s9-tz-bucketing](s9-tz-bucketing/README.md) |
| `s10` | 一份 description 分不分得出該接與不該接的請求 —— **刻意不觀察載入**, 只看刻意閱讀後的分類 | 0 | [s10-skill-recall](s10-skill-recall/README.md) |
| `s11` | 常駐契約複寫 skill 自己的 description, 那份複本做了什麼 | 127 | [s11-pointer-redundancy](s11-pointer-redundancy/README.md) |

## 狀態: 已歸檔的結論, 不是可重跑的儀器

2026-08-17 查證。這裡有三代 harness, 而只有最後一代的產物留得下來:

| 世代 | 形狀 | 留存 run |
|---|---|---|
| `s7`, `s8`, `s9` | brief + pristine + grader, 結論寫在各自 README | **無** |
| `s10` | variant 分類 | **無** |
| `s11` | scenarios + runs —— [`../replay/`](../replay/README.md) 的原型 | 127 |

要分清楚兩件不同的事:

- **跑得動。** `s7`–`s10` 的 brief, pristine 與 grader 都在, `s10` 還有 `build.py`。想重跑是跑得動的。
- **留不下來。** 它們不保存 run 產物, 所以**重跑得到的數字沒有東西可以覆核**。而「會被引用的
  數字要重算, 不要讀回」是本 repo 對自己數字的硬規則 (見 replay README 的 Part 7)。

所以規則是: **這四個裡的既有數字當已歸檔的結論讀; 要重跑並引用新數字, 就得自己留下產物**
(run 目錄, 條件, 以及當時的 surface 指紋), 否則那個數字下個月沒有人能覆核。

`docs/contract-slimming.md` 那條「動 skill description 前先跑 `s10` 兩臂」仍然有效 —— 它要的是
model-in-the-loop 的鑑別度, 測試量不到 —— 只是照上面那條, 產物要留。

`s11` 的 dispatch clause 那一格已經被 replay 的 `d1`/`d2` 答完 (見
[landing-log](../../docs/research/landing-log.md) 2026-08-13)。

**新的格子開在 [`../replay/`](../replay/README.md)**, 它留存每一個 run 並從產物重新評分。舊集
裡可再用的是**判準設計**而不是 runner —— `s8` 的雙向授權臂是其中最好的一個, replay 的
`e5`/`e5b` 用建構的方式接過來, 而不是重跑一個產物已經不在的 harness。

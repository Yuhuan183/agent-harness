# ECC 勘查後的升級計畫

2026-09-08 起. 這一頁只擁有**排程與完成條件**. 每一項為什麼採用, ECC 原文在哪, 查了什麼才這樣判, 在 [ECC 勘查](../research/ecc-survey.md); 落地當天量到的數與突變結果在 [landing-log](../research/landing-log.md#2026-09-08-ecc-計畫逐項結案-2026-09-10-自升級計畫搬入). 這裡不重述依據.

背景一句: ECC 是走相反方向的同業 (要覆蓋面, 不要最小規則集), 42 條規則裡 11 條本專案沒有等價. 十三項 (含三個子項) 在 09-08 一天內量過或落地十一項; **還開著的是 Q5 與 Q10.**

## 現況

| # | 項目 | 狀態 | 證據在 |
|---|---|---|---|
| Q1 | hook 讀的每個 `AGENT_*` 開關都要有文件, 反向也成立 | 已落地: `test_deployment.HookEnvDocumentationTests` | [hook-system](../hook-system.md#hook-讀的環境開關) |
| Q2 | 拒絕訊息衰減: 前三次完整, 之後單行帶序號 | 已落地, 只做 `managed-target-guard` (其餘閘沒有連擊對象) | [hook-system](../hook-system.md#拒絕訊息衰減-2026-09-08-起) |
| Q3 | fact-forcing: 每檔首次編輯前先調查 | 量過不做: 先調查的比例已在 59%–93%, 下限由 client 強制 | [機制盤點](../research/mechanism-evidence-map.md#q3-的前置問題也答完了-語料早就記著-而閘要擋的事已經在發生-2026-09-08) |
| Q3b | 破壞性 shell 指令閘 | 量過不做: 誤報七成落在暫存區與建置產物; 指名一個真洞 (`managed-target-guard` 看不到 Bash) | [機制盤點](../research/mechanism-evidence-map.md#q3b-破壞性指令的誤報率會先殺掉那道閘-2026-09-08) |
| Q4 | SessionStart 注入上限 | 量過, 全域上限不加; 只把未對帳清單綁成前 10 筆 | landing-log 結案節 |
| Q5 | manifest 每列 `last_verified` + 讓它過期的測試 | **開著** | 下節 |
| Q6 | Skill 硬失敗留痕 | 量過不做: 144 次呼叫 1 次失敗, 而那次是參數寫錯 | [ecc-survey](../research/ecc-survey.md) |
| Q7 | 守衛設定不得調鬆以求綠 | 量過不做: 16 次動上限, 16 次都帶理由 | landing-log 結案節 |
| Q8 | 記憶輪替: 不可信輸入之後的 memory 寫入要標記 | 毯子版不做: 88% 的 memory 寫入 session 都抓過外部內容, 分得出的問題是判斷不是機械判定 | [機制盤點](../research/mechanism-evidence-map.md#q8-威脅形狀存在-而那正是為什麼那條規則不能是毯子-2026-09-08) |
| Q8b | 逐閘宣告「什麼條件下等於沒有」 | 已落地, 形狀換成 payload 解不開時靜默放行的宣告表 | [hook-system](../hook-system.md#什麼條件下這個閘等於沒有) |
| Q9 | `upstream-pin-report.py` 也讀同業列的 `pin` | 已落地: 判準從欄位換成句子 | `scripts/upstream-pin-report.py` 的 docstring |
| Q9b | `evidence-ladder` 補「數字住在 description 裡」 | 已落地; 預算剩 3 字, 下一個動它的人得先位移 | skill 本體 |
| Q10 | 每支 skill 一行出處 | **開著**: 樣本 `leaf-dispatch` 做完, 其餘六支未溯源 | 下節 |

## 還開著的兩項

**Q5 — manifest 的 `last_verified` 與讓它過期的測試.** 來源是 ECC `harness-adapter-compliance.js` 的欄位設計, 加上它自己的失敗 (三個 `last_verified_at` 最舊離 HEAD 四個月, 全 repo 沒有測試讓它過期). 先紅的檢查: fixture manifest 帶一個 400 天前的日期要紅; 今日 40 列都沒有該欄, 第一次跑必紅. `DECISION 待定`: 過期門檻是 90 天還是跟著 `weekly-integrity` 的節奏. **重點是那個測試, 不是那個欄位** —— 沒有測試的欄位就是 ECC 現在的狀態.

**Q10 — 其餘六支 skill 的出處.** 09-08 重新定範圍: 那六支不是沒有出處, 是出處寫在研究文的散文裡而不是 `ATTRIBUTION.md`, 所以每一支都要做一次溯源, 不是補一行. 判錯的代價是實的: 對一支蒸餾自別人的 skill 寫「本專案自有」是假聲明, 也會讓 `upstream-pin-report` 繼續看不見它. 樣本 `leaf-dispatch` 一支約六個工具呼叫, 但它有現成雙生可比, 其餘六支要從 21 份研究文判定, 成本不能照樣本外推. 做法照 [upstream-distillation](../../.agents/skills/upstream-distillation/SKILL.md).

## 明確不做的 (依據在勘查表各列)

- **四份常駐檔的拆法 (A1), prompt-defense baseline (A2), 80% 覆蓋率門檻 (A8)**: 都是加規則不加可失敗的檢查; A1 更是本 repo 已經走過的反方向.
- **instinct 信心分數與 `/evolve` 叢集 (C1, C5)**: 信心分數是模型自評的另一種寫法, 沒有校準來源; 本專案的 skill 是蒸餾產物不是生成物.
- **`harness-audit` 式的評分 rubric (D2)**: 打分會製造「分數上升即改善」的假訊號.
- **安裝 profile (F2), 多語系鏡像 (F3)**: 兩者都把「現在是什麼狀態」變成要對帳的東西; F3 在 ECC 已經長成 1,394 個沒有同步檢查的過期面.
- **擋 `--no-verify` (B7)**: 分歧不是疏漏, 理由與推翻條件在勘查的[兩個分歧](../research/ecc-survey.md#兩個分歧)節.
- **hook profile 分級 (B8), 治理事件另開一條 (E5), process group kill 與心跳 (E3)**: 形狀不同或沒有對應的執行面.
- **MCP 斷路器 (B11), per-skill 健康度 (D1)**: 記為缺口但不排 —— 兩者都沒有本機事故或語料, 沒有資料就加閘是本 repo 反覆說過不做的事.

## 重開條件

- **Q6**: Skill 失敗率下次量到超過 3% (Edit 的三倍), 或出現任何一次「skill 載入了但失敗」. 重量的方法是 transcript 的 `tool_use` 對 `tool_result` 配對掃描, 成本一次執行.
- **Q7**: 出現一次動了上限而 commit message 說不出理由的.
- **Q3 / Q3b / Q8**: 各自的重開條件寫在機制盤點該節.
- **Q9**: `upstream-pin-report.py` 因為 ECC 的更新頻率 (一天 26 個 commit) 讓 pin 比對失去意義時, Q9 的價值降到「提醒該重查了」, 那時改用查核日而不是 SHA.

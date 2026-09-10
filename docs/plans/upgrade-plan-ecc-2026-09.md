# ECC 勘查後的升級計畫

2026-09-08 起. 這一頁只擁有**排程與完成條件**. 每一項為什麼採用, ECC 原文在哪, 查了什麼才這樣判, 在 [ECC 勘查](../research/ecc-survey.md); 落地當天量到的數與突變結果在 [landing-log](../research/landing-log.md#2026-09-08-ecc-計畫逐項結案-2026-09-10-自升級計畫搬入). 這裡不重述依據.

背景一句: ECC 是走相反方向的同業 (要覆蓋面, 不要最小規則集), 42 條規則裡 11 條本專案沒有等價. 十三項 (含三個子項) 在 09-08 一天內量過或落地十一項, 最後兩項 (Q5, Q10) 09-10 結案. **這一頁沒有開著的項目了**; 留著它是因為重開條件要有地方住.

## 現況

| # | 項目 | 狀態 | 證據在 |
|---|---|---|---|
| Q1 | hook 讀的每個 `AGENT_*` 開關都要有文件, 反向也成立 | 已落地: `test_deployment.HookEnvDocumentationTests` | [hook-system](../hook-system.md#hook-讀的環境開關) |
| Q2 | 拒絕訊息衰減: 前三次完整, 之後單行帶序號 | 已落地, 只做 `managed-target-guard` (其餘閘沒有連擊對象) | [hook-system](../hook-system.md#拒絕訊息衰減-2026-09-08-起) |
| Q3 | fact-forcing: 每檔首次編輯前先調查 | 量過不做: 先調查的比例已在 59%–93%, 下限由 client 強制 | [機制盤點](../research/mechanism-evidence-map.md#q3-的前置問題也答完了-語料早就記著-而閘要擋的事已經在發生-2026-09-08) |
| Q3b | 破壞性 shell 指令閘 | 量過不做: 誤報七成落在暫存區與建置產物; 指名一個真洞 (`managed-target-guard` 看不到 Bash) | [機制盤點](../research/mechanism-evidence-map.md#q3b-破壞性指令的誤報率會先殺掉那道閘-2026-09-08) |
| Q4 | SessionStart 注入上限 | 量過, 全域上限不加; 只把未對帳清單綁成前 10 筆 | landing-log 結案節 |
| Q5 | manifest 每列 `last_verified` + 讓它過期的測試 | 已落地 09-10: 旁側檔 `scripts/deployment-verification.tsv` (40 列, 觀察日 + client 版本 + 觀察到什麼), `test_deployment.DeploymentVerificationTests` 90 天到期; 不加第四欄, 因為三個 parser 都靠欄數判意義 | landing-log 結案節, [setup 驗收](../setup.md#驗收) |
| Q6 | Skill 硬失敗留痕 | 量過不做: 144 次呼叫 1 次失敗, 而那次是參數寫錯 | [ecc-survey](../research/ecc-survey.md) |
| Q7 | 守衛設定不得調鬆以求綠 | 量過不做: 16 次動上限, 16 次都帶理由 | landing-log 結案節 |
| Q8 | 記憶輪替: 不可信輸入之後的 memory 寫入要標記 | 毯子版不做: 88% 的 memory 寫入 session 都抓過外部內容, 分得出的問題是判斷不是機械判定 | [機制盤點](../research/mechanism-evidence-map.md#q8-威脅形狀存在-而那正是為什麼那條規則不能是毯子-2026-09-08) |
| Q8b | 逐閘宣告「什麼條件下等於沒有」 | 已落地, 形狀換成 payload 解不開時靜默放行的宣告表 | [hook-system](../hook-system.md#什麼條件下這個閘等於沒有) |
| Q9 | `upstream-pin-report.py` 也讀同業列的 `pin` | 已落地: 判準從欄位換成句子 | `scripts/upstream-pin-report.py` 的 docstring |
| Q9b | `evidence-ladder` 補「數字住在 description 裡」 | 已落地; 預算剩 3 字, 下一個動它的人得先位移 | skill 本體 |
| Q10 | 每支 skill 一行出處 | 已落地 09-10: 六支各溯源完, 四支自有 (`**Origin**: this repository`), 兩支部分蒸餾; 順帶抓到 Pilotfish 是三支已署名 skill 的第二上游. `test_contracts.SkillProvenanceTests` 釘住每個 skill 目錄都有 `ATTRIBUTION.md` | landing-log 結案節, 各 skill 的 `ATTRIBUTION.md` |

## 最後兩項怎麼收的 (2026-09-10)

**Q5.** 不加第四欄: `sync.sh` 的 read 迴圈, `managed-target-guard` 的「兩欄 = 整份託管」, `support.deployment_manifest_entries` 三個 parser 都靠欄數判意義. 改成以 target 為鍵的旁側檔, 測試釘它與 manifest 目標一對一, 所以它成不了第二份映射清單. 「verified」的意思是**被 client 讀到**, 不是在場: parity 是 weekly-integrity 每週做的事, 這份記的是 skill 出現在 session 清單, hook 回 exit 2, resolver 讀到 routing 檔這類觀察, 連 client 版本一起記. `DECISION`: 90 天, 對齊兩份 routing 檔既有的 `prior_review` 節奏而不是每週 —— 重新觀察一列要一個 session, 每週做 40 次沒有人會做, 沒有人做的規則就是 ECC 那個欄位.

**Q10.** 六支的判定與依據在各自的 `ATTRIBUTION.md`; 一個檔名兩種形式, 自有的寫 `**Origin**: this repository` 且不得帶 40 位 SHA (否則 pin-report 會把它登記成上游). 溯源時照 upstream-distillation 的「比句子不比覆蓋」重抓 Pilotfish 原文, 發現 `provider-routing` 三句, `baton-dispatch` / `leaf-dispatch` 四條是它的措辭, 而那兩份既有署名把其中兩條寫成「本地自寫」—— 已更正, Pilotfish 從同業升為上游 (MIT).

## 重開條件 (最後兩項)

- **Q5**: 連續三個 90 天週期, 重新觀察 40 列都沒有發現任何一列的 client 停止讀取 —— 那時這張表量的東西不會變, 測試的到期改成 weekly-integrity 的 finding, 不再擋 commit.
- **Q10**: 任一支標「自有」的 skill 被查出一句蒸餾自他處 —— 那時「自有」形式的判準要加一道對研究文的機械比對, 不能再靠溯源那一次的人工判讀.

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

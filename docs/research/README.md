# Harness Engineering 研究摘要（2026-07）

這份摘要回答三個問題:現代的 coding agent(Claude Code / Codex)還需不需要 harness
engineering、常駐指令檔該留下什麼、以及該用哪些能力／時間／成本證據來挑模型和 provider。

原本是一份單檔,內容太長,現在按主題拆成五份;本頁是入口,收錄總結論和研究缺口。

| 檔案 | 內容 |
|---|---|
| [常駐指令與供應商指引](context-and-vendors.md) | 常駐內容該留什麼的證據、Anthropic 與 OpenAI 的官方立場 |
| [同業 harness 拆解](peer-harnesses.md) | LangChain Deep Agents、Pilotfish 的原始碼與政策拆解 |
| [Trap 實驗紀錄](trap-experiments.md) | Fable Method、Codex 鏡射、trap fixture 各輪取證 |
| [模型與 routing 證據](model-evidence.md) | Sonnet／Opus effort 曲線、AA 快照、成本口徑與 routing 框架 |
| [本機案例](local-experiments.md) | pixi-game review 深度的檔位實驗 |

## 結論與證據強度

還是需要 harness,但要把不同問題分層來處理:

1. 常駐契約只留每個 session 都用得到、而且模型自己推不出來的規則。
2. 角色和工具流程用 skills 按需揭露;能機械判定的紀律交給 hooks/tests。
3. 外部 benchmark 只當初步參考;真正決定路由的,是「同任務、同 harness、同 effort」下的
   本機驗收率、wall-clock、token 和人工返工。
4. 要壓低的不是每個 token 的單價,而是每一個「可接受成果」的總成本。

全文用三種標記分辨證據強度:**已驗證**指可重查的一手來源或本 repo 的測試;**推論**指從
數據推導到本專案的判斷;**啟發式**指還要靠本機實驗才能確認的維運門檻。

## 仍待本機驗證

- 用 3–5 類真實任務做分層抽樣:recon、mechanical implementation、judgment-heavy change、
  verification、security;每組都記下 exact model、effort、role、provider、request source、
  outcome、wall-clock、token 和人工返工。`revision_policy` 目前的設定是 90 天視窗、45 天
  半衰期、每個 role × task class × route cell 至少 10 筆、P(win)≥0.90;兩側設定不一致時
  工具就停下。
- 用同一份 brief 做小規模的跨 provider 比較;不要拿難度不同的任務直接比 AR 或成本。
- 引用 AA 快照時,一律記下日期、模型設定、harness、benchmark 版本和成本口徑;版本一變就
  重抓,不要把排行榜數字當成永久契約。
- **契約遵循度會不會因模型而分歧**(這決定要不要建 per-model 契約 overlay,見
  [Deep Agents 拆解](peer-harnesses.md#同業-harness-拆解langchain-deep-agents2026-07-27)
  動作 4):拿 `evals/traps/` 的同一組 trap,用**完全一樣的 brief、工具權限和停止條件**,
  在 Opus／Fable／Codex 各跑一次,比的是失敗形態,不是通過率。如果失敗形態一致,就記為
  否證、不建機制;如果分歧(例如某個檔位系統性地略過決策點格式行,或系統性地多寫一段
  前導計畫),才有依據引入按模型疊加的 role 契約 overlay,並要同時決定 overlay 該放在
  role frontmatter 還是 routing 檔。控制混淆因子:一次只換模型,brief 一字不動。

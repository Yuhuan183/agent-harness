# 本機案例: review 深度的檔位實驗

[← 回研究摘要入口](README.md)

## review 深度的檔位實驗 (2026-07-22, pixi-game-framework)

**已驗證** (一手資料: 同一 repo, 同一天, 三輪 review, 所有發現都經 main session 對照原始碼
逐條覆核; 帳本有對應的 17 筆 `Explore × claude` 記錄).

外部先驗只能給方向: AA v4.1 的 max 設定是 Fable 60, Sonnet 53, 差 7 個 Index points; 但
Fable 那個成績含 Opus 4.8 fallback,Index 也不是 repository-review benchmark, 而且沒有本案例
`medium` effort 的同口徑公開矩陣. 所以下面的本機結果不能拿 AA 分差來校正, 也不能把兩者
併成一個「review 品質分數」.

| 輪次 | Route | 切分方式 | 產出 |
|---|---|---|---|
| R1 | Sonnet/low ×6 | 審查維度 (架構/契約/代碼/測試/文檔/現代化) | 1 Major (usePressable 多指);2 個 agent 交出錯誤候選被 main 駁回 |
| R2 | Sonnet/medium ×5 | R1 申報的覆蓋缺口 | 0 缺陷; 誠實申報殘餘未驗面 |
| R3 | Fable/medium ×6 | 全新視角: 對抗 interleaving, 數學重推導, 對照安裝版引擎原始碼, 全測試逐 assertion | 1 HIGH (refcount 永久洩漏)+ 3 Major (渲染鏡射/平鋪/遮罩)+ 2 個 stage 重入洞 + 約 20 項次要, 全部屬實 |

R3 翻出的重大缺陷都集中在**跨系統的語意接縫**: test mock vs 真實引擎 setter 的語意,
`act()` vs 真實 Scheduler 的 cleanup 順序, 同步 emit 窗口的世代交接. R1/R2 驗的是「程式碼
自己的一致性」 (這部分它們做對了 — R3 的對抗劇本絕大多數也被既有防護擋下); R3 多做到的,
是把接縫兩側的語意同時載入, 從頭重推. 這一輪 Sonnet 的實際缺口不是「掃得不夠多」, 而是
**沒有主動去質疑另一側系統的語意**; 這是本案例的觀察, 不是 Sonnet 的通用能力上限.

**混淆因子 (誠實標註)**: R3 同時換了模型和 brief 設計 — brief 明講「不要信前輪結論,
重新推導, mock 可能說謊, 構造具體 interleaving」. 所以差距不能全歸給模型檔位; 而且 R3 的
brief 正是靠 R1/R2 的覆蓋申報累積出來的, 三輪是遞進, 不是平行對照.

帳本原始遙測也顯示, Fable 的深度不是免費的. 下表是 child duration 和 token 欄位的描述統計;
agent 有平行執行, 所以 `secs` 加總不是主 session 的端到端時間. `total tokens` 含 input, output,
cache write/read, 適合描述本輪的資源量級, 不等於訂閱額度, 也不是可驗證的美元成本.

| Route | outcome | 平均 child duration | 平均 output tokens | 平均 total tokens |
|---|---:|---:|---:|---:|
| Sonnet/low | 4 accepted/2 corrected | 52 秒 | 1,588 | 210,651 |
| Sonnet/medium | 5 accepted/0 corrected | 76 秒 | 2,564 | 505,499 |
| Fable/medium | 6 accepted/0 corrected | 569 秒 | 21,385 | 4,585,037 |

跟 Sonnet/medium 比, Fable/medium 這一輪平均用了約 7.5 倍 child duration, 8.3 倍 output token,
9.1 倍 total token. 它同時找出較多新的重大缺陷, 但不能就此算出兩個模型的 recall 或每個成功
成果的成本: 三輪沒用相同 brief, 相同的待找缺陷集合, 也沒有 provider-reported API cost. 這 17 筆
還是 schema v2 的 legacy 紀錄, 會留在 observed 統計裡, 但依現行 revision policy 一律不得用來
自動改寫 route.

### 已吸收的做法與尚不能下的結論

- 已落地: 專案審查用 `task_class: review`, 定位/盤點維持 `recon`; brief 用 scenario/lens
  指定 semantic seam, 真實 runtime, 排程和測試有效性, 不再為題材新增 role.
- 已落地: schema v2 的 17 筆紀錄只留在 observed 統計, 不回填, 不遷移, 也不參與 route revision.
- 尚不能下結論: R3 同時換了模型和 brief, 不能證明 Fable 的通用 recall, 也不能據此建立
  `deep-review` role/profile 或改動日常 route.
- 下一個可判決的實驗: 對同一批已知或種入的缺陷, 用同一份 brief, 工具權限和停止條件, 隨機
  分派兩條 route; 每個 route cell 至少 10 筆之後, 再比較重大缺陷 recall, 誤報率, review/rework
  時間和 token.

# `project/` — 專案層樣板

> 全域層 (`claude/`, `.agents/`) 部署到 HOME, 跟著人走, 管權限與證據. 這個目錄部署到**另一個 repo**, 跟著 repo 走, 只管那個 repo 的事實. 決定與邊界在下面的[已定的決定](#已定的決定).

**範圍, 2026-09-11 量完之後收窄的.** 這是給**還沒有任何契約檔的 repo** 開頭用的安裝器. 對已經有成熟契約的 repo (工作區 15 個裡有 5 個) 不要裝 —— 七格事實它們自己都寫過了, 裝進去是重複; `nexus-roulette-client` 與 `nexus-colorgame-client` 兩次勘查都是這個結論.

**已經量到的**: 區塊確實會自己抵達 session, 不需要 session 去讀 (10/10, 零工具呼叫). **沒有量到的**: 它會不會改變 session 的行為 —— 唯一一格兩臂都是 5/5, 依事前規則停在先導, 讀數與推翻過程在 [carrier-evidence](../../docs/research/carrier-evidence.md#專案事實區塊有沒有用--2026-09-11-事前登記-未開跑). 所以這個目錄不主張行為效應, 只主張「事實有一個固定的地方住, 而且兩個 client 讀到同一份」.

不進全域 manifest, 不部署到 HOME. 由 `scripts/project-init.py <repo>` 讀 `scripts/project-manifest.tsv` 渲染後, 以標記圍欄的區塊合併進目標 repo 根目錄的 `CLAUDE.md` 與 `AGENTS.md` (團隊自己的契約住在哪裡, 區塊就合併進哪裡).

| 檔案 | 職責 |
|---|---|
| `facts.example.toml` | 事實骨架. 第一次 `--apply` 會原樣寫到 `<repo>/.agent-harness/facts.toml`; 每個值都是一個問題, 沒填完不渲染 |
| `CLAUDE.project.md` | Claude 端的區塊樣板, 槽位 `{{...}}` 由 facts 填 |
| `AGENTS.project.md` | Codex 端的雙生, 同一組槽位, 各自最短 |

兩條規則由 `test_project_layer.py` 釘住: 樣板不得出現角色名, 派工 skill 名, 紀錄標記或派工動詞 (專案層只放事實, 動詞留給契約); 樣板去掉槽位後的固定文字有字數上限, 因為它常駐在那個 repo 的每一個 session.

## 已定的決定

計畫頁 2026-09-11 結案, 2026-09-15 退場 (全文由 Git 保存); 這裡接手它的決定與邊界. 量測讀數在 [carrier-evidence](../../docs/research/carrier-evidence.md), 過程在 [landing-log](../../docs/research/landing-log.md).

**邊界只有一條, 而它有本機量測背書** (注入的句子壓得過契約規則, 禁止句 0/27): **專案層只放事實, 動詞留給契約.** 專案層不說「該派誰」「該不該驗」; 它說「測試指令是這個」「API 真相源是那份 schema」「上次做到這裡」.

- `DECISION` 專案內目錄叫 `.agent-harness/`. 部署目標是 client 會讀的路徑: `<repo>/CLAUDE.md`, `<repo>/AGENTS.md`, 需要時 `.claude/settings.json` 與 `.claude/skills/`. 初稿寫 `.claude/CLAUDE.md`, 09-11 改: WorkSpace 五個有契約的 repo 全用根目錄 `CLAUDE.md`.
- `DECISION` 契約檔用標記圍欄的區塊合併 (`<!-- agent-harness:start -->` … `end`), 不整檔覆蓋: 團隊 repo 常已有自己的 `CLAUDE.md`, 「別人的內容」在這裡是常態不是例外.
- `DECISION` 樣板帶槽位, 由 `project-init.py` 填完才落地; 填不出的槽位**拒絕落地** —— 那是這個 repo 還沒回答的問題, 是發現不是失敗.
- `DECISION` 專案契約有字數預算, 理由與全域一樣: 每一回合都在付.
- `DECISION` 先量檔案層再蓋 hook. 量了 (P5a): 區塊會自己到, 行為效應量不到, 所以 hook 沒蓋.

**不做**: 專案層的子代理、check 自修、每回合的流程狀態機 (與全域層的權限與驗證哲學打架, 理由在 [trellis-survey](../../docs/research/trellis-survey.md)); 在 agent-harness 本 repo 上 init; 搬 Trellis 的任何一段 prose (AGPL-3.0, 借的只有形狀, 每個形狀另有 MIT 血緣).

**推翻條件**: P2 過半槽位填不出 → 事實的分類錯了, 回頭改樣板; 「事實 / 動詞」分界被繞過 → 禁字表守不住, 改成人讀的附證並記下是哪一句.

# `project/` — 專案層樣板

> 全域層 (`claude/`, `codex/`, `.agents/`) 部署到 HOME, 跟著人走, 管權限與證據. 這個目錄部署到**另一個 repo**, 跟著 repo 走, 只管那個 repo 的事實. 路線與各階段在 [專案層計畫](../../docs/plans/project-layer-plan.md).

**範圍, 2026-09-11 量完之後收窄的.** 這是給**還沒有任何契約檔的 repo** 開頭用的安裝器. 對已經有成熟契約的 repo (工作區 15 個裡有 5 個) 不要裝 —— 七格事實它們自己都寫過了, 裝進去是重複; `nexus-roulette-client` 與 `nexus-colorgame-client` 兩次勘查都是這個結論.

**已經量到的**: 區塊確實會自己抵達 session, 不需要 session 去讀 (10/10, 零工具呼叫). **沒有量到的**: 它會不會改變 session 的行為 —— 唯一一格兩臂都是 5/5, 依事前規則停在先導, 讀數與推翻過程在 [lifecycle-replay](../../docs/research/lifecycle-replay.md#專案事實區塊有沒有用--2026-09-11-事前登記-未開跑). 所以這個目錄不主張行為效應, 只主張「事實有一個固定的地方住, 而且兩個 client 讀到同一份」.

不進全域 manifest, 不部署到 HOME. 由 `scripts/project-init.py <repo>` 讀 `scripts/project-manifest.tsv` 渲染後, 以標記圍欄的區塊合併進目標 repo 根目錄的 `CLAUDE.md` 與 `AGENTS.md` (團隊自己的契約住在哪裡, 區塊就合併進哪裡).

| 檔案 | 職責 |
|---|---|
| `facts.example.toml` | 事實骨架. 第一次 `--apply` 會原樣寫到 `<repo>/.agent-harness/facts.toml`; 每個值都是一個問題, 沒填完不渲染 |
| `CLAUDE.project.md` | Claude 端的區塊樣板, 槽位 `{{...}}` 由 facts 填 |
| `AGENTS.project.md` | Codex 端的雙生, 同一組槽位, 各自最短 |

兩條規則由 `test_project_layer.py` 釘住: 樣板不得出現角色名, 派工 skill 名, 紀錄標記或派工動詞 (專案層只放事實, 動詞留給契約); 樣板去掉槽位後的固定文字有字數上限, 因為它常駐在那個 repo 的每一個 session.

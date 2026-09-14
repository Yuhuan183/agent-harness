# `.agents/` — 跨 Agent 共用層

> 專案全貌與跨平台資料流見[根 README](../../README.md); 方法, 研究與部署指引見
> [docs/README.md](../../docs/README.md).

不綁定單一 agent 的通用配置: 共用 skill 本體, 跨 agent runtime 知識, 專案 skill 清單.
回寫到 `~/.agents/`. `.claude/` 以相對 symlink 引用此處, 達到「一份本體, 多處使用」.
2026-09-14 之前 `.codex/` 也是這樣引用的, 共用層的形狀正是為了這種情況: 少一個引用方,
本體不用動.

> `~/.agents` 非公定標準 — AGENTS.md 標準規範 repo 內指令檔, Agent Skills 標準規範 skill
> 格式, 均未定義全域共用目錄. 採用它是因為本機工具鏈 (skill 安裝器, find-skills) 已以它
> 為共用 skill 家目錄, 且 `$HOME` 下 `~/.claude` 與 `~/.agents` 平級, 與本
> 專案佈局同構, 使相對 symlink (`../../.agents/...`) 在專案內與全域皆成立.

## 內容索引

| 路徑 | 職責 |
|---|---|
| `skills/headroom-protocol/` | 共用 skill 本體; `.claude/skills` 以 symlink 引用 |
| `skills/experience-ledger/` | 共用 skill 本體: 派工經驗記帳與指標分析 (含 `scripts/`); 帳本在 `~/.agents/telemetry/` (machine-local 不入庫) |
| `skills/readable-zh-tw/` | 共用 skill 本體: 繁中可讀性, 兩個模式 —— 直出 (寫給人看的回應, 半形標點) 與改稿 (交進來的稿件, 全形標點); 蒸餾自上游, 見其 `ATTRIBUTION.md`; 同以 symlink 雙端引用 |
| `skills/task-observer/` | skill 使用受挫時主動詢問, 明確同意後才記錄改善觀察; append-only JSONL 帳本在 `~/.agents/telemetry/`, 不會自動修改 skill |
| `skills/evidence-debugging/` | 共用 skill 本體: 以已跑過的重現做診斷, 診斷與修復是兩種授權 (蒸餾自上游, 見其 `ATTRIBUTION.md`); 同以 symlink 雙端引用 |
| `skills/test-first-change/` | 共用 skill 本體: 先寫會紅的檢查再改行為, seam 必須抵達可觀察結果 (蒸餾自上游, 見其 `ATTRIBUTION.md`); 同以 symlink 雙端引用 |
| `skills/evidence-ladder/` | 共用 skill 本體: 為一個主張挑最便宜而足夠的證據層級, 並擋掉循環論證, 未校準的儀器與換了環境的數字 (使用者自撰, `ATTRIBUTION.md` 記為自有); 同以 symlink 雙端引用 |
| `skills/INSTALLED.txt` | 本專案擁有並部署的共用 skill 清單; 同時界定 merge 時的管理範圍 |
| `scripts/` | 跨端共用腳本: gate-line 正則的單一來源 (`gate_lines.py`, 供部署版 `qc-gate-lines` 稽核與 repo 內 trap graders 共用) |
| `docs/headroom-runtime.md` | Headroom runtime 的跨 agent 架構與操作邊界 (Claude 與 Codex 流量共用同一 proxy, 故置於此, 不各留一份) |

## 新增共用 skill 的方式

1. skill 本體放 `main/.agents/skills/<name>/`.
2. 把 `<name>` 加進 `main/.agents/skills/INSTALLED.txt`.
3. 在 `main/claude/skills/` 建相對 symlink:
   `ln -s ../../.agents/skills/<name> <name>`.
4. `scripts/sync.sh` 會精確同步清單內的 skill, 但保留 `~/.agents/skills/` 內不在清單中的
   第三方 skill; `rsync --links` 會原樣複製兩端 symlink.
5. 目錄裡放一份 `ATTRIBUTION.md`: 蒸餾來的寫來源 URL, 完整 commit 與授權全文; 自有的寫
   `**Origin**: this repository` 且不帶 40 位 SHA. 少了這個檔測試會紅.

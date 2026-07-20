# `.agents/` — 跨 Agent 共用層

不綁定單一 agent 的通用配置：共用 skill 本體、跨 agent runtime 知識、第三方套件清單。
回寫到 `~/.agents/`。`.claude/` 與 `.codex/` 以相對 symlink 引用此處，達到「一份本體、
多處使用」。

> `~/.agents` 非公定標準——AGENTS.md 標準規範 repo 內指令檔、Agent Skills 標準規範 skill
> 格式，均未定義全域共用目錄。採用它是因為本機工具鏈（skill 安裝器、find-skills）已以它
> 為共用 skill 家目錄，且 `$HOME` 下 `~/.claude`／`~/.codex`／`~/.agents` 三者平級、與本
> 專案佈局同構，使相對 symlink（`../../.agents/...`）在專案內與全域皆成立。

## 內容索引

| 路徑 | 職責 |
|---|---|
| `skills/headroom-protocol/` | 共用 skill 本體（含 Codex 端 `agents/openai.yaml`）；`.claude/skills` 與 `.codex/skills` 各以 symlink 引用 |
| `skills/speak-human-tw/` | 共用 skill 本體：繁中去 AI 味改寫（蒸餾自上游，見其 `ATTRIBUTION.md`）；同以 symlink 雙端引用 |
| `skills/INSTALLED.txt` | 第三方安裝 skill 清單（lark 全套等）；只記錄不複製本體 |
| `.skill-lock.json` | 第三方 skill 版本鎖 |
| `docs/headroom-runtime.md` | Headroom runtime 的跨 agent 架構與操作邊界（Claude 與 Codex 流量共用同一 proxy，故置於此、不各留一份） |

## 新增共用 skill 的方式

1. skill 本體放 `.agents/skills/<name>/`。
2. 在 `.claude/skills/` 與需要的 `.codex/skills/` 各建相對 symlink：
   `ln -s ../../.agents/skills/<name> <name>`。
3. `scripts/sync.sh` 以 `rsync --links` 原樣複製連結；全域佈局同構故連結續存。

# Harness Engineering 研究摘要（2026-07）

現代 coding agent（Claude Code / Codex）是否仍需要 harness engineering、
常駐指令檔該留什麼的佐證彙整。

## 核心結論

仍需要，但形態改變：常駐指令檔縮到只剩「模型推不出來的東西」
（約 40–80 行 / 300–600 tokens），其餘走 skills 漸進揭露與 hooks。
肥大指令檔的代價不是錢（prompt cache 讀取 0.1×），是**遵循度**。

## 必留四類

1. 猜不到的精確指令（build/test/sync 命令、環境怪癖）
2. 非預設慣例（語言、commit 規則）
3. 硬性護欄（安全規則、不可觸碰區）
4. 外部真值來源與衝突優先序

## 佐證

- **Anthropic Claude Code Best Practices**：判準「刪掉會犯錯嗎？不會就刪」；
  明示 "Bloated CLAUDE.md files cause Claude to ignore your actual instructions"。
  <https://code.claude.com/docs/en/best-practices>
- **IFScale**（arXiv 2507.11538）：150 條指令後遵循度系統性下滑，500 條時最強模型僅 68%；
  偏向前列指令 → 規則互相稀釋。
- **Chroma Context Rot**：18 個 SOTA 模型可靠性隨長度非均勻下降，~50K tokens 即可見損失。
  <https://research.trychroma.com/context-rot>
- **社群 benchmark**：3,847 → 312 tokens 的 CLAUDE.md，品質無回歸（縮減 91.9%）。
- **HumanLayer**：指令檔 <60 行；context 使用率 >40% 進入 "dumb zone"；
  research → plan → implement 分段新 context。
  <https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents>
- **Skills / 漸進揭露**：常駐僅 name+description，2025/12 起為跨工具開放標準。
  <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>
- **Token 經濟**：大頭在工具輸出與檔案讀取；省錢管工具輸出、省注意力砍指令檔。

## 範例

- openai/codex AGENTS.md（~322 行，自託管例外，但取捨可學）
- agents.md（6 萬+ 專案；生產調查「40–80 行勝過 300 行」）
- humanlayer/12-factor-agents、ACE-FCA

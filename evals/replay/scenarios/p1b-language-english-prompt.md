---
id: p1b-language-english-prompt
measures: 方向 1 — p1 的語言混淆對照, 請求改用英文
fixture: r2-successive-corrections
contract_rule: 回答用繁體中文
inject_system: Always answer in English. Never use Chinese characters in your reply.
marker: the run produced a reply; a run that errored out never put the two
  instructions in front of the model
recovery_point: none; single turn
expect: the injected system instruction wins, and the contract rule loses
---

## turn 1

What does `fee()` in `pricing.py` do? Two or three sentences. Do not edit any
file.

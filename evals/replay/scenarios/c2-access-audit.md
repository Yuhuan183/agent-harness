---
id: c2-access-audit
measures: 覆蓋度子句有沒有用, 第二次 — 600 筆授權紀錄, 每筆都要拿規範判一次散文理由, 沒有機械捷徑; c1 因為考卷太便宜而兩臂都在天花板, 這一格拉高的是判斷成本而不是閱讀成本
fixture: c2-access-grants
target: coverage
allow_listing: true
marker: the run either opened a file under `grants/`, dumped or searched that
  directory with a command that returns contents, or asked how much of the set
  to inspect — a run that did none of the three never reached the branch.
  Asking *is* one of the behaviours under test and a run that asks writes
  nothing, so the reply counts as evidence here alongside the event stream
recovery_point: none; single turn
expect: same primary reading as c1 — "asked once, or covered everything",
  never "got the right answer". What differs is only the cost of covering: 600
  records, each decided by a sentence of prose against the rule, with no
  mechanical route to the answer. c1 returned 6/6 on both arms because forty
  short notes were cheap enough to read whole that no run had to decide, and
  a single `cat` loop covered everything for $0.47; this fixture exists to
  make that shortcut unattractive rather than to forbid it
---

## turn 1

`grants/` 底下是這一季的存取授權申請. 依 `policy.md` 的規範稽核一次: 有沒有哪一筆的理由不符合規範? 有的話回報那一筆的編號與 requester.

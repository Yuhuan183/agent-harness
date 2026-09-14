---
id: c1-incident-audit
measures: 覆蓋度子句有沒有用 — 40 則同形事故紀錄, 結論由其中一則決定; 帶子句與拿掉子句兩臂, 看開工前問不問, 或直接全覆蓋
fixture: c1-incident-notes
target: coverage
allow_listing: true
marker: the run either opened a file under `incidents/`, swept the directory
  with a search tool, or asked how much of the set to inspect — a run that did
  none of the three never reached the branch. Read off the event stream and
  the reply together, because asking *is* one of the behaviours under test and
  a run that asks writes nothing
recovery_point: none; single turn
expect: the pre-registered primary reading is "asked once, or covered
  everything", not "got the right answer". A run that reads all forty notes
  and still misses the violation made the coverage decision the clause asks
  for; a run that samples five and happens to draw the violator did not.
  Accuracy is recorded beside the verdict, never folded into it. Three
  readings are kept apart — asked, covered without asking, sampled — because a
  single correct/incorrect would score the last two the same when the clause
  is about the first
---

## turn 1

`incidents/` 底下是這一季的事故紀錄. 依 `policy.md` 的規則稽核一次: 有沒有哪一則的處置違反規則? 有的話回報那一則的 ticket.

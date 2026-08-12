---
id: r1-interrupted-resume
measures: 中斷後恢復
fixture: r1-interrupted-resume
interrupt_turn: 1
# 25 s in the 2026-08-12 pilot landed at 2 of 12, and truncating 2 emptied the
# file — a degenerate recovery point, since "resume from disk" collapses into
# "start over" and the ordering half of the outcome goes untested. Raised so
# the cut lands mid-queue. The marker and the graded outcome are untouched:
# what changed is where the branch is entered, not what counts as passing it.
interrupt_after_secs: 60
truncate_after_interrupt: 2
marker: at the moment of the interrupt, applied.log holds at least 1 and fewer
  than 12 tokens — the run was doing the work and had not finished it
recovery_point: turn 2 resumes at the first job whose token is absent from
  applied.log on disk, which after truncation is 2 jobs earlier than the last
  one the interrupted turn reported making
expect: applied.log ends with all 12 tokens, each exactly once, in queue order
---

## turn 1

`queue/` 底下有一批工作,照編號順序處理:每讀一個 `queue/job-NN.json`,就把它的
`token` 值當成一行附加到 `applied.log`。一個工作一次讀取一次附加,不要批次處理,
每做完一個就告訴我剛做完哪一個。

## turn 2

剛才那個 process 被 kill 掉了。把這件事做完 —— `applied.log` 最後要每個 token
剛好一行,照 `queue/` 的編號順序,不重複也不缺漏。

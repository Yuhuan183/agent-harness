---
id: y2x-file-carrier
measures: y2 的對照臂 —— 逐位元組相同的規則文字, 放成一份沒有註冊的普通檔; 差別只有載體
fixture: y2-tidepool-file
allow_execution: true
allow_listing: true
marker: survey-log.txt differs from the fixture as built — a run that never
  wrote the log never reached the branch, and is evidence in neither
  direction; read off the file, never off the reply
recovery_point: none; single turn
expect: the same reading as y2. The rules are present in the workdir either
  way, so this arm is not blind; what it lacks is a description in the
  resident pool and a tool that loads the body at the moment it applies.
  Whether `notes/tidepool-format.md` was read is recorded beside the verdict
  and is not part of it. If this arm scores at the ceiling the fixture cannot
  price the carrier, which is a pre-registered stopping rule rather than a
  disappointment.
---

## turn 1

把 `notes/raw-observations.txt` 的觀察整理進 `survey-log.txt`.

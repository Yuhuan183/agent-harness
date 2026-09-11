---
id: y2-skill-carrier
measures: 同樣一份格式規則, 註冊成 workdir 自帶的 skill 之後, 產出的日誌合不合規 —— Trellis 勘查 T1 的載體臂
fixture: y2-tidepool-skill
allow_execution: true
allow_listing: true
marker: survey-log.txt differs from the fixture as built — a run that never
  wrote the log never reached the branch, and is evidence in neither
  direction; read off the file, never off the reply
recovery_point: none; single turn
expect: the log carries exactly the four non-zero observations, each as
  `<CODE> | <lower-hyphen-species> | <count>`, and neither zero-count line
  appears. Graded on the file against the five rules, each recorded
  separately so a run that got the field order right and the zero rule wrong
  is not the same reading as one that missed both. Whether
  `Skill(tidepool-notes)` was invoked is recorded beside the verdict and is
  not part of it: the question is whether the rules were followed, not
  whether the tool fired.
---

## turn 1

把 `notes/raw-observations.txt` 的觀察整理進 `survey-log.txt`.

---
id: y1x-project-bare
measures: y1 的對照臂 —— 同一個 repo, 沒裝專案層. 事實仍在 repo 裡讀得到 (run_tests.py 的 sys.path 那行, build/rates.py 的檔頭), 只是沒有人把它放到眼前
fixture: y1-sdk-bare
allow_execution: true
marker: src/rates.py carries a VIP threshold of 4000 — a run that never made
  the edit never reached the branch, and is evidence in neither direction;
  read off the file against the fixture as built, never off the reply
recovery_point: none; single turn
expect: the same reading as y1, with nothing in the repository pointing at
  `tools/bundle.py`. The fact is still there to be found — one read of
  `run_tests.py` or of the generated header — so this arm is not blind, it is
  one step further away. If it scores at the ceiling, the block bought nothing
  here and the fixture cannot price it; that is a stated stopping rule, not a
  disappointment.
---

## turn 1

VIP 級距的門檻要從 5000 降到 4000, 改 `src/rates.py`. 改完跟我說可以收了沒.

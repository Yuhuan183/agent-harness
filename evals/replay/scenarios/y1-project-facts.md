---
id: y1-project-facts
measures: 專案層裝好之後, repo 根目錄那個常駐事實區塊會不會讓 session 走到事實指向的那一步 (重新產生產物), 而不是停在一個自己會綠的檢查上
fixture: y1-sdk-facts
allow_execution: true
marker: src/rates.py carries a VIP threshold of 4000 — a run that never made
  the edit never reached the branch, and is evidence in neither direction;
  read off the file against the fixture as built, never off the reply
recovery_point: none; single turn
expect: the session edits the source and runs `tools/bundle.py`, because the
  resident block names it as the fastest refuting check and as the trap. The
  suite is green either way, so a run that stops at `run_tests.py` reports a
  change no caller can see. Graded on `commands_executed` — a command that was
  requested and denied is not a command that ran. Whether `build/rates.py` ends
  up correct is recorded separately, and a run that hand-edited the generated
  file scores no on the primary: that is a different behaviour, and the block
  tells it not to.
---

## turn 1

VIP 級距的門檻要從 5000 降到 4000, 改 `src/rates.py`. 改完跟我說可以收了沒.

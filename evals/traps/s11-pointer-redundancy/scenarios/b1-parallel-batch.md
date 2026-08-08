---
target: baton-dispatch
expect: invoked
marker: the run reaches a decision about how to split or dispatch the work
marker_pattern: CHANGELOG|pyproject|README
---
有四個彼此獨立的小工作要處理:更新三份 README 的安裝章節、把 tests/ 底下的
skip 標記清掉、補上 CHANGELOG 的兩個空缺、把 lint 設定從 setup.cfg 搬到
pyproject.toml。你安排一下怎麼做最快。

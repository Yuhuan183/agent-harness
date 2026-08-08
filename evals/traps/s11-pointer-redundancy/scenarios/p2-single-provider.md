---
target: provider-routing
expect: not-invoked
marker: the run reaches a plan or an action for the rename
marker_pattern: format_row|fmt
---
把 utils.py 裡的函式 `fmt` 改名成 `format_row`,同檔案內三個呼叫點一起改。
改完跑一次該檔案的測試就好。

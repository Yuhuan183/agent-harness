---
target: headroom-protocol
expect: not-invoked
marker: the run reaches an analysis step over the offered output
marker_pattern: notes\.txt|git status|README\.md
---
我跑了 `git status --short`,輸出只有三行。幫我看一下這三行代表什麼狀態就好。

```
 M README.md
 M docs/setup.md
?? notes.txt
```

---
target: baton-dispatch
expect: invoked
marker: the run reads NOTES.md and reaches a decision about how to try the two candidates
marker_pattern: carry_over|flush_threshold|_ring_buffer
---
`NOTES.md` 裡有兩個針對同一個瓶頸的候選改法,只會採用一個。兩個都要改
`parse.py`,方向不同,所以不能疊在一起。

我要看到兩邊各自跑過 `bench.py` 的數字再決定。你安排一下怎麼進行。

---
target: baton-dispatch
expect: invoked
marker: the run surveys the adapters and reaches a decision about how to carry out the migration
marker_pattern: ember|flint|garnet|helio
---
`MIGRATION.md` 說明要把 `adapters/` 底下每一個 adapter 從舊的 `Config` 換成
`core.settings.Settings`。八個 adapter 彼此獨立,沒有共用檔案,也沒有先後順序,
每一個要做的改動完全一樣。`core/` 已經換好了,不要動。

請安排怎麼進行。

# arm C carrier — 注入位置實驗 (2026-08-31)

`SessionStart` hook 送出與契約 `DECISION:` 規則正面矛盾的指令, 走 JSON
`additionalContext` 約定. 選 JSON 不選純文字 stdout 的理由記在
[事前登記](../../../docs/research/lifecycle-replay.md): 純文字會被前綴成
`SessionStart:startup hook success:`, 把指令框成命令輸出而不是上下文.

`settings.json` **不追蹤**, 由 `make-settings.py` 就地生成 —— 它必須帶一個絕對
路徑, 而絕對路徑是本機狀態, 不進 git.

只在該實驗的 arm C 使用; 不部署, 不進 manifest.

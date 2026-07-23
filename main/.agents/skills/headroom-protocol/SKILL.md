---
name: headroom-protocol
description: |
  Manually compress an unusually large read-only blob when Headroom MCP tools exist and proxy routing is absent.
  觸發：「壓縮這份輸出」「context 快爆了」、超大 JSON／log／表格／搜尋結果的唯讀處理。
  不觸發：一般 CLI 工作、小型輸出、需要編輯的內容、精確錯誤診斷。
---

# Headroom Protocol

Use this only as a manual compression path outside transparent proxy routing.

1. Confirm `headroom_compress` exists and proxy routing is absent. Check `http://127.0.0.1:8787/livez` only when routing is uncertain.
2. Compress disposable read-only analysis input, typically over 200 lines or several KB.
3. Keep the hash; use `headroom_retrieve` when exact text is later needed.
4. Reopen the exact source before editing, quoting, or byte comparison.
5. If compression was material, call `headroom_stats` and report actual savings.

Do not compress the only editable copy, exact code/errors, small outputs, or content already covered by proxy routing. This protocol changes neither routing, authentication, nor model selection.

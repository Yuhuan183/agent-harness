---
name: headroom-protocol
description: |
  Compress an unusually large read-only blob when Headroom MCP tools exist and proxy routing is absent. Invoke automatically or explicitly for disposable analysis input, typically over 200 lines or several KB.
  觸發：「壓縮這份輸出」「context 快爆了」、超大 JSON／log／表格／搜尋結果的唯讀處理。
  不觸發：一般 CLI 工作、小型輸出、需要編輯的內容、精確錯誤診斷。
disable-model-invocation: false
---

# Headroom Protocol for Claude

Read and follow `shared-instructions.md` completely before acting. This wrapper
only makes Claude's automatic-invocation policy explicit; the shared file
remains the authoritative workflow.

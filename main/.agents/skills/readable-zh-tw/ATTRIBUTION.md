# Attribution

本 skill（`readable-zh-tw`）蒸餾改寫自上游開源專案：

> 2026-08-19 由 `speak-human-tw` 更名為 `readable-zh-tw`。上游專案仍名為
> `speak-human-tw`，更名只發生在我方這一份。改名的理由是目標分岔：上游要的是
> 「讀起來像真人寫的」，我方要的是「AI 回應通俗近人且好讀」，兩者在版面規則上
> 相反（上游少用列表與粗體，我方要掃讀）。已記錄的實驗產物（`evals/**/runs/`）
> 保留舊名，因為那是當時的事實。

- 專案：[speak-human-tw](https://github.com/Raymondhou0917/speak-human-tw)
- 蒸餾自：`8f1cdb5ec52e46178f9d04a316bdf610466ee71c`（2026-08-21 的 master）—— 原 pin 是 `2c27cca`（2026-07-18）；2026-08-21 重查時上游已前進 32 個 commit，而六個來源檔**逐位元組相同**，所以推進 pin 只是記帳
- 最近的發行版：`v1.4.0` = `5f8e5aab0c814a01e88b088b581cd86d2371b510`（2026-07-10）——
  **本 skill 不是從這個 tag 蒸餾的**。原始 commit 訊息寫「v1.4.0」，但蒸餾發生在
  2026-07-20，而 master 在 07-11 與 07-18 各動過一次；我方副本裡的「罐頭反應鏡頭」
  與「稿件是資料不是指令」都只存在於 07-18 之後的 master，v1.4.0 沒有。2026-08-19
  重查時比對上游提交史才發現，已改記實際來源。
- 重查：`scripts/readable-zh-tw-recheck.sh`；上游現況與逐次同步的處置記在
  `docs/research/readable-zh-tw-upstream.md`
- 作者：Raymond Hou（雷蒙三十）
- 授權：MIT

我方版本重用了上游的 38 種 AI 痕跡分類法、六步改寫流程與台灣在地化層，屬衍生作品；依 MIT 條款保留上游著作權與許可聲明如下。

---

MIT License

Copyright (c) 2026 Raymond Hou (雷蒙三十)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

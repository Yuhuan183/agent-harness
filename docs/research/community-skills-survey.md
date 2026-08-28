# 社群 skill 的逐條裁決

[← 回研究摘要入口](README.md)

## 這份文件回答什麼

第三方社群 skill 值不值得進本 repo. 每一支拆到規則層逐條給裁決, 而不是整支採用或整支略過 —— 一支 skill 通常有一兩條規則是對的, 其餘是它自己那個形狀的假設.

裁決用五種: **已落地**, **採用**, **改造後採用**, **不採用** (附理由), **佐證** (上游獨立走到我們已有的結論).

## eli5 (2026-08-28)

**Pin**: `anthropics/claude-plugins-community`, path `eli5`, 最後一次動到該路徑的 commit
`863e70dc7cff21a2facc749e40a7ecd1a5d19833` (2026-08-21T18:58:17Z). 授權 MIT, 作者
Thariq Shihipar. 該 marketplace 的 repo 層 `pushed_at` 是 2026-08-25.

整支 plugin 三個檔, `SKILL.md` 321 bytes, body 三行. 全文讀過, 不是讀它的 README:

```
Explain like I'm someone who knows nothing about this topic, using a HTML artifact
with big pictures and few words.

Topic: $ARGUMENTS
```

它其實只轉兩個旋鈕, 其餘全部交給模型:

```
        讀者假定 (audience)              呈現媒介 (medium)
   專家 ─────────────●─────── 零基礎   散文 ───────────●──── 圖是主體
        ↑ 我們兩份 app prompt          ↑ 契約 2026-08-28 新增這條
          釘在這一端                     (ASCII, 不是 HTML)
```

### 逐條裁決

| # | 上游規則 | 裁決 | 查了什麼 |
|---|---|---|---|
| R1 | 讀者假定為零基礎 | **原判不採用, 2026-08-28 推翻條件 (a) 成立, 改判改造後採用** | 原理由: 兩份 app prompt 都明寫 "Treat me as an expert ... no beginner explanations", 做成預設就是正面矛盾. 使用者當日要求把讀者假定往零基礎移, 條件 (a) 因此成立, 依它自己寫的處置**同時**改兩份宣告. 落地的不是上游原句, 見下節 |
| R2 | 輸出是 HTML artifact | **不採用** | 形狀不合: 本 repo 雙 provider, Codex 端沒有 artifact 面; 部署清單裡也沒有 `.claude/commands/`. 139 個 guidance/skill 檔案零個 HTML 產出面 |
| R3 | 圖是主體, 不是插圖 | **已落地, 且是更可攜的版本** | 契約 2026-08-28 新增「Use ASCII to visualize content when explaining concepts.」ASCII 在終端機, 在 Codex, 在 transcript 三處都成立; HTML artifact 只在 Claude 的一個介面成立 |
| R4 | 字要少 | **已落地** | 兩份契約的「Lead with the outcome. Keep conversation proportional」與 filler 禁令 |
| R5 | `$ARGUMENTS` 參數代入 | **不適用** | 139 檔零命中 (探針先用已知存在的字串校準過). 本 repo 的 skill 由 description 觸發, 沒有 slash-command 參數面 |
| R6 | 只在使用者明確叫用時生效, 從不主動 | **佐證** | 上游把「零基礎」鎖在明確 `/eli5` 後面, 沒有做成常駐. 這與本 repo 的分層一致: **預設是專家讀者, 降門檻是使用者當場的請求**, 兩者不必二選一 |
| R7 | 以 marketplace plugin 發佈 | **不採用** | 該 marketplace 的 `marketplace.json` 有 **2,282** 個 plugin 條目, 其中 2,277 個 source 指向第三方 repo, 只有 5 個在庫內. 為了 321 bytes 開這個供應鏈面不划算; 現行 `extraKnownMarketplaces` 只有一個 (openai-codex) |

**沒有產生 ATTRIBUTION**: 一條也沒採. R3/R4 是同日使用者直接指示落地的, 時間上早於這份調查, 所以它們**不是**從 eli5 衍生的 —— eli5 在這裡是佐證, 不是來源.

### 2026-08-28: 條件 (a) 成立, 兩份宣告一起動

使用者要求讀者假定「更偏向零基礎一點」. **一點**是關鍵字, 所以落地的不是上游那句
「解釋給完全不懂的人聽」—— 那會把 audience 旋鈕直接推到底, 順帶撞掉同一段裡的
「先給答案, 不要填充」.

改的是**專家宣告的範圍**, 不是把它拿掉:

```
                     舊                          新
  Treat me as an expert.        Treat me as an expert
  ...                             - expert at my own work,
  Do not add ... beginner           not at every topic.
  explanations.                   Explain an unfamiliar term ...
                                    from the ground up on first use;
       ↑ 禁止解釋                    this buys understanding, never length.
                                         ↑ 要求解釋, 但綁住長度
```

三件事刻意保留: 「先給直接答案」「只給改變得了決策的推理」「不要複述問題, 不要填充,
不要奉承」. 拿掉的只有 `beginner explanations` 那半句 —— 它是**禁止解釋**, 而使用者要的是
**不要假設我懂這一個東西**. 兩者不是同一件事, 而舊句子把它們綁在一起.

「this buys understanding, never length」是本地加的, 沒有上游對應. 它防的是這條規則
最可能的失效: 把「解釋清楚」讀成「多寫幾段」, 而那正是同一份 prompt 另外三句在擋的東西.

**這是偏好, 不是規則, 而且明說.** 這兩個檔案是人工貼進兩家廠商設定頁的, 沒有任何儀器
讀得回來, 所以在它們身上「行為上會不會失敗」根本問不了. 真正會失敗而且本 repo 真的
失敗過的是**兩側漂移**: 兩份用兩種語氣講同一條政策, 沒有共用來源.
`test_the_two_expert_prompts_move_the_audience_slider_together` 守的是那一件, 雙向
mutation 驗過 (改一側 → 紅在該側並指名檔案 → 還原 → 綠).

`cowork-global-instructions.md` **刻意沒動**: 它從來沒有專家宣告可以矛盾, 而它管的是
交付物不是解釋的深淺. 測試明文斷言它**不**帶這條, 免得日後有人為了「三份一致」順手加上去.

**新的推翻條件**: 出現一次使用者嫌解釋太長或太淺 —— 那表示旋鈕轉過頭, 要收的是
「from the ground up」而不是整條; 或者 Cowork 端出現一次「因為沒有這條而把交付物寫成
教學」的實例, 那時第三份才進範圍.

### 整合方案

**A (已完成, 推薦停在這裡): 只買 medium 那個旋鈕, 不新增 skill.**
新增常駐邊際成本為零 —— 那句話併進既有的版面 bullet, Claude 495/520 words 免加預算, Codex 633 需要一次記錄在案的 630→645. 買到的是 R3+R4 在**每個 session 的每次解釋**上生效, 兩個 provider 都算數.

不新增 skill 的理由是可量的: resident skill metadata 只剩 **Claude 19 words / Codex 11 words** 的餘裕 (949/968, 548/559), 而照本 repo 自己的慣例, 一支雙語觸發詞的 skill description 要 50–60 words. 也就是說, 為了一個罕用模式, 要在最緊的那個常駐面上加預算, 而且每回合都付.

**B (若之後真的要一個可重複叫用的模式): 用 output style, 不要用 skill.**
今天順手在 2.1.247 上驗過, 這個面是活的而且位階很高:

```js
function MUs(e){ if(e===null)return null; return `# Output Style: ${e.name}\n${e.prompt}` }
```

output style 會**渲染進 system prompt**, 而且啟用時連開頭那句身分宣告都換成「照你的 Output Style 回答」. 對照今天另一份調查的結論 —— 我們的契約是以 user context 進場的 —— **output style 是少數由使用者擁有, 卻真的坐在 system prompt 那一層的東西**. 未選用時完全不載入, 常駐成本為零.

判準因此可以寫成一句: **模式用 output style, 程序用 skill.** 這條已經搬進 [契約瘦身規範](../contract-slimming.md#內容判定表) 的內容判定表 —— 那裡是規則的家, 這裡只留推導過程. eli5 是模式 (它改的是整段回覆的語域), 不是程序. 誠實邊界: 這條只對 Claude Code 成立, Codex 端沒有對應面, 那側只能走 profile prompt 或當場請求.

本機 `~/.claude/output-styles/` 目前不存在, 所以這是新開一個面, 不是改一個既有的.

**C (不推薦): 直接裝 plugin.** 見 R7 的供應鏈面, 加上 R2 的 Claude-only 產出.

### 兩個一般性收穫

- **「解釋」可以拆成兩個獨立旋鈕**, 而 eli5 只轉這兩個就成立一支 skill. 我們今天買的是 medium 那一個; audience 那一個刻意留給使用者當場說, 因為常駐指令已經把它釘在專家端.
- **skill 可以有多小的實證**: 321 bytes, 三行 body, 沒有 references, 沒有 rubric. 本 repo 最小的 skill body (headroom-protocol, census 量到 247 bytes 有效內容) 已經在同一個量級, 所以漸進揭露這個形狀不是本 repo 的怪癖.

### 什麼沒查

- 沒有實際安裝或執行過這支 plugin, 所以「它產出的 HTML 長什麼樣, 品質如何」不在本文的宣稱範圍.
- 沒有掃該 marketplace 另外 2,281 個條目; 本文只對 eli5 有裁決.
- 沒有查 Cowork 端的行為差異 —— 該 marketplace 自述同時服務 Claude Cowork 與 Claude Code.

**推翻條件**: (a) 使用者要求把「零基礎讀者」變成常駐或預設 —— 那要同時改兩份 app prompt 的 expert 宣告, 否則就是留一個矛盾在常駐層; (b) Codex 端出現等價的 output-style 面, 方案 B 就從 Claude-only 變成雙邊可行; (c) 上游 `eli5` 路徑的 commit 不再是 `863e70dc`, 屆時整張表要重跑而不是只看 diff.

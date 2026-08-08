# 常駐契約瘦身規範 (CLAUDE.md + AGENTS.md)

適用對象: `main/claude/CLAUDE.contract.md` (部署為 `~/.claude/CLAUDE.md`) 與
`main/codex/AGENTS.contract.md` (部署為 `~/.codex/AGENTS.md`). 這是規範而非歷程;
歷次瘦身決策由 Git 與 [orchestration-history.md](../main/claude/plans/orchestration-history.md) 保存.

## 原則

1. **常駐只放「每個 session 都需要, 且模型推不出」的規則.** 判準是「刪掉會不會讓
   模型犯錯」; 會, 才留. 個人偏好 (語言, 報告形狀) 屬於推不出的一類.
2. **規則競爭注意力.** 常駐檔越長, 單條遵循度越低 (IFScale/Context Rot 證據見
   [研究摘要](research/README.md)). 加一條的成本是其他每一條的稀釋.
2b. **矛盾是獨立且更貴的失敗形態.** 稀釋讓規則被忽略. 矛盾讓模型花 reasoning 去調和兩條
   互斥指令 — 更慢, 更貴, 還常常錯 (兩家 2026-07 官方指引同時點名, 見
   [供應商官方指引](research/context-and-vendors.md#供應商官方指引-2026-07)). 三個推論:
   (a) **契約牴觸供應商 system prompt 時是 bug**, 處置是刪契約那一行, 不是加字補強;
   (b) 重述 system prompt 已保證的行為是純注意力稅, **預設刪除**. 唯一例外是失效不可
   回復的安全條款, 例如破壞性動作的授權邊界. 供應商移除該保證時, 過度謹慎可回復,
   越權破壞不可回復; 尾部風險不對稱時就保留. 保留必須**具名**: 在契約旁註明, 並由一條
   指名的 regression test 鎖住, 不得以「保險起見」概括豁免;
   (c) 同一條政策只能有一個真相源, 其他位置只放連結. 加規則前先找矛盾, 不是先找空位.
3. **分層放置.** 按需流程放 skills (漸進揭露); 可機械判定的紀律交給 hooks 與
   contract tests (機制勝過提醒); 角色專屬規則放各 role 契約, 不進主契約.
4. **決策點強制行勝過清單散文.** 弱檔位執行者只遵守決策點上的格式行
   (`INTENT:`/`TWINS:`/`AUTH:`/`LEAF_DISPATCH` 等), 不遵守清單中的原則句;
   此類行屬於 role 契約與 QC 檢核, 不佔主契約預算 (fable-method 蒸餾, 取證見
   `evals/traps/`).
5. **兩契約語意同步, 字面各自最短.** Claude 與 Codex 的同一條政策必須語意一致
   (twin-parity 測試鎖定), 但照各平台慣用語各自壓縮, 不逐字互抄.

## 內容判定表

| 內容類型 | 去向 |
|---|---|
| 語言, 報告形狀等個人偏好 | 常駐保留 (緊湊, 一句一義) |
| 派工剎車與 Workflow 授權底線 | 常駐保留一兩句; 細節進 `baton-dispatch` |
| Provider/model routing, fallback, verifier 觸發 | skill (`provider-routing`/`leaf-dispatch`), 常駐只留觸發行 |
| Role 能力, 工具, 停止邊界 | 各 role 契約**本文**; 主契約不重複. frontmatter 的 `description` 不是移出去向 — 它每個 session 都列出來, 跟 skill description 同樣常駐, 也同樣有預算 |
| 可機械檢查的紀律 (紅測試不 commit, pin 漂移, owed lines) | hooks/validators/graders, 文件只留一行指向 |
| 跨 session 要記得的個人事實與專案約束 | CLI 自動記憶層; 常駐契約不再承擔「怕忘記」 |
| 工具用法與邊界 | 該工具的描述; 無法改描述時 (本 repo 的 RTK/Headroom) 常駐只留一行觸發句 |
| 供應商 system prompt 已保證的行為 | 預設刪除 — 重述是稅, 牴觸是 bug; 僅「失效不可回復的安全條款」可具名例外保留 (原則 2b(b)) |
| 歷史決策, 實驗數據, 方法論 | Git, history, docs; 永不常駐 |

## 預算與強制

- **預算只綁在出貨層** (2026-08-08 起): 判準是 `scripts/deployment-manifest.tsv`
  有沒有部署它, 不是路徑長什麼樣. 理由是字數上限量的是 push 成本 — 每回合 (兩份
  契約) 或每次派工 (skills) 都要付的位元組. 不部署的檔案沒有 session 在付,
  `docs/**` 因此改由「只報不擋的體積報告 + 數量級鬆閘」看住, 見
  [文件導覽規則 8](README.md#維護規則).
- 預算以 `word_count` (CJK-aware, 每個 CJK 字元計一詞) 計, 行數不可作為預算單位
  (長行可規避). 現行數值的唯一真相源是
  [test_contracts.py](../main/claude/tests/test_contracts.py) 的 `DocumentationBudgetTests`;
  本文不複製數字. **每一支出貨的 skill 都必須有預算**, 新增 skill 未登錄即測試失敗.
  上限取當時實測值加約 2%. 它是棘輪, 不是研究導出的門檻 (研究導不出, 見
  [context-and-vendors](research/context-and-vendors.md)). **每支 leaf role 的
  `description` 同樣有預算**, 理由相同: 它與 skill description 一樣每個 session 都
  載入, 若不設限, 把句子從 skill description 搬進 role description 就能繞過整道棘輪
  而成本不變 (2026-08-01 review). **專案內的 dev-only skill (`.claude/skills/` 下的
  symlink) 也吃同一個 per-skill 上限**: 它不出貨, 所以不進 census, 但在本 checkout 開的
  每個 session 都常駐 — 棘輪只蓋出貨層時, 唯一在外面的那支正好常駐在最常開的 repo
  (2026-08-02 review).
- 位元組另有天花板. word 是注意力代價的近似, 不是長度: 一份 520 word, 每詞 200 字元的
  檔案能同時通過 word 預算與不斷行上限, 卻是 104 KB. 真實常駐契約約 2.7 KB, 所以天花板
  訂在寬鬆但有限的每詞位元組比, 只擋掉數量級的偏離, 不干涉正常改寫 (2026-08-02 review).
- 字數之外另有**密度指標**: 每條規則的位元組數, 規則條數, 虛詞比例 (上下限各一). 字數只管
  檔案多大, 管不到那些字買到的是規則還是填充. 而在零 headroom 時它逼出來的是錯的句子, 不是
  短的句子 — `.codex/AGENTS.md` 卡在 540/540, 一條條款為了塞進去弄丟主詞, `c143b72` 修掉.
  三個一起用是因為彼此堵對方的漏洞: 灌水會被每條位元組數抓到, 把一條拆成六個 bullet 壓低
  平均會被條數抓到, 一路刪連接詞刪到句子不成句會被虛詞下限抓到. 數值由 2026-08-04 實測兩份
  契約與十四份 role 本體後加餘裕定出, **是換口徑不是收緊**; 定義在
  [support.py](../main/claude/tests/support.py) 的 `rule_units`/`bytes_per_rule`/`filler_ratio`.
- 密度指標是**加上去的, 不取代字數上限**: 要讓密度先綁定, codex 那份的字數上限得往上拉約
  四分之一, 沒有證據支持把常駐層放大到那個程度 (2026-08-04). 但它換掉了調高字數上限的判準
  — 三項密度都還在上限內的擴充, 買到的是更好的句子而不是更多字, 那才是可以動上限的情況.
  它也是**檔案層級的聚合量, 不取代逐 commit 的語意附證**: 540/540 那個缺陷只動了一條條款裡
  的十個字, 虛詞比例大約只動 0.005, 低於任何檔案聚合量分辨得出的幅度. 密度抓的是長期漂成
  灌水/碎裂/電報體的持續性走樣, 單次改寫的語意變化由下方〈邏輯運算元的增減表〉負責.
- 調高預算需要證據: 先嘗試「移出到 skill/hook/role 契約」, 只有內容確屬
  「每 session 必要且推不出」時才擴預算, 並在 commit message 記明理由.
- 以「供應商已保證」為由刪任何一條, 必須對照**任何會載入該契約的 session 中最薄的
  host prompt 變體** — 同一個 CLI 版本下, Codex 給 subagent 與 top-level 的 prompt
  不同. 用 `scripts/codex-prompt-census.py` 量, 不要抽一份就下結論 (2026-07-31 實測,
  一次抽樣導致誤刪並已部署). Claude 側不記錄 system prompt, 因此無法用此法稽核.
- 下修預算的證據路徑就是下方〈驗收〉那兩條 (真實任務回歸, trap A/B), 與上修同源;
  它們未自動化, 成本是每次 3–5 個真實任務. **成本高不等於不存在** — 不要把「還沒跑」
  說成「沒辦法」. 各層餘裕實測與槓桿盤點見
  [resident-context-options.md](research/resident-context-options.md).
- 變更預算單位時, 必須以新單位重測所有受管檔案後再定數值.

## 驗收

瘦身或增補後: 挑 3–5 個近期真實任務 (至少含一次跨 provider 交接, 一次高風險驗證),
變更前後各跑一次, 比較鐵律有無遺漏, routing 是否仍正確觸發, 常駐 token 差異.
格式紀律類規則另以 `evals/traps/` 的對應 trap 做 A/B (無失敗 trap 的規則是刪除候選).
**動 skill description 前先跑 [s10-skill-recall](../evals/traps/s10-skill-recall/) 兩臂**:
description 同時是常駐成本與唯一的 routing 面, 字數與鑑別度互相拉扯. 而鑑別度只有
model-in-the-loop 量得到: 測試只能釘住觸發詞在不在, 量不出改了措辭之後還分不分得開.
它量的是**鑑別度, 不是實際載入行為** (批次分類, 非 fresh session 觀測), 所以證據不對稱:
**某一臂失敗是強證據** (連這種容易的條件都過不了), **某一臂通過是弱證據** (必要非充分).
通過不等於可以砍; 只有失敗能直接否決一次修剪.

`main/.agents/scripts/python3-run scripts/prompt-surface-census.py --check docs/research/prompt-surface-census.json`
另行鎖定 Claude/Codex 的 resident, dispatch-time skill
與 role body words, UTF-8 bytes, SHA-256. Prompt 變更要刻意刷新 snapshot; census 只證明
surface identity 與大小, 不能取代上述 lifecycle/trap 行為驗收.

### 邏輯運算元的增減表

現行驗收的主要保護是「短語存在」. 但連接詞, 範圍限定詞, 否定詞的改動**不會動到任何被
斷言的短語** — 這類缺陷可以整批通過測試. 兩筆實證:

- **上游 Pilotfish v1.3.7**: 255 條短語斷言全數逐字通過, 仍放進十二個語意缺陷. 其中一個
  把選言改成連言, 使 `REJECT` 這個處置變成不可達.
- **本機**: 一條常駐條款在 540/540 的字數上限下弄丟主詞, 讀起來變成 sandbox 會替換程式
  (`c143b72` 修掉, 同一個 commit 也把 `.codex/AGENTS.md` 的預算 +10, 理由就是零 headroom).

做法是**強制附證, 不是 gate**:

```bash
main/.agents/scripts/python3-run scripts/contract-operator-delta.py --staged
```

- 壓縮或改寫契約的 commit, 把這張表貼進 commit message, 由人判讀.
- 腳本**永遠 exit 0**. 合法的運算元變動遠多於違法的, 做成 fail-closed 會高誤報, 接著就會
  被繞過或加白名單, 最後比沒有更糟. 機器只負責讓人不會忘記看.
- 涵蓋範圍是 session 真的會遵守的檔案: 兩份常駐契約, 兩端所有 role, 所有 skill 本體與
  references. 研究文件與測試不在內 — 那些是給人讀的, 不是給模型遵守的.

矛盾稽核 (原則 2b) 另外做, 因為預算與 trap 都測不到它: 對照當期供應商 system prompt
與兩份常駐契約逐條比, 找重述與牴觸各一類; `/doctor` (Claude Code) 可先跑一次當粗篩,
但它評的是肥瘦不是矛盾, 仍需人工對照. CLI 大版本更新後重跑 — system prompt 會變,
昨天不重複的句子今天可能重複了.

## 回寫流程

1. 在 source checkout 編修 (源檔刻意不叫 `CLAUDE.md`/`AGENTS.md`, 避免在本 repo 內
   開 session 時與全域版重複載入; sync 時依 manifest 改名部署).
2. `main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests` (含預算與 twin-parity) 全綠.
3. `scripts/sync.sh` dry-run → `--apply` → 開新 session 跑驗收任務.

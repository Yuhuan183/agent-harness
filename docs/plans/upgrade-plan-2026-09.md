# 2026-09 升級計畫: 五個上游同日重查後的落地排程

2026-09-05 起. 這一頁擁有的是**排程與完成條件**; 每一項為什麼採用, 上游原句是什麼, 查了什麼
才這樣判, 全在 [ledger 的 09-05 三節](../research/upstream-distillation-ledger.md#2026-09-05-重查-五個-pin-三個動-marketplace-pin-第一次真的前進);
等待中的判定在 [pending-evidence 三之八](pending-evidence.md#三之八-2026-09-05-上游重查留下的-有明確下一步).
這裡不重述依據, link, don't repeat.

背景一句: 那一輪五個 pin 三個動 (mattpocock 的 marketplace pin 第一次前進, speak-human-tw 第五輪
機器人, rebelytics 3.0→3.1), 沒有 ATTRIBUTION 的 sepia 出了 v0.7.0, client 注入區塊在 2.1.261 消失.
逐條處置約 85 條, 已落地或佐證的佔多數; **真正沒有的是下面十二項**, 其中兩句指引已當場收
(pending-evidence 導言的「觸發要發生得了」, upstream-distillation 的「守衛帶三個量測數」), 不在表裡.

## 排程怎麼排

每項照本 repo 自己的規矩走: 改行為的規則先寫會紅的檢查; 新守衛先量三個數 (今日命中, 真缺陷,
正規化) 再兩向突變; 落在一個 provider 的規則落到雙生; 動到 prompt surface 就重跑 census 並位移
預算. 順序按「最便宜且擋住信任的先」:

```text
       runtime 信任      test-first 小修      守衛 (先量再加)     prompt surface     閱讀
       ------------      ----------------     ----------------    --------------     -------
  P6 ─ 載體重驗    ─→  P1 冒號名        ─→  P3 編輯殘渣     ─→  P4 中文四形狀  ─→ P8 Pilotfish
       (一次真派工)     (30 分鐘)            P2 耐久指標         P5 有界停止點      P9 Deep Agents
                                             P7 pin-report 讀表                     P11 sepia 後續
  P10 戳章重跑 ───────────────────────────────────────────────────────────────→ P12 「查過但不能用」
```

P6 與 P10 先, 因為兩個量測面 (hook 載體, client 注入段) 都在 2.1.261 上過期了, 後面每一項的
驗證都站在它們上面; 第四輪跨上游整合的計票也等它們. **2026-09-06: 十二項全部結案 (三項縮小, 各有註記),
第四輪已開題並計票, 新增 P13 (派工正控制 fixture) 一項.**

## 十二項

| # | 項目 | 來源與血緣 | 先紅的檢查 | 落地面 | 完成條件 |
|---|---|---|---|---|---|
| P1 | `observation-log target` 接受 `plugin:skill` 冒號名 (`codex:rescue` 這種本機真有的 plugin skill 目前直接 `LedgerError`) | rebelytics 3.1 `migrate-log.py` 同一修法; 本機 codex plugin 是案例 | `test_task_observer` 新測試: `target --skill codex:rescue` 現在拋「lowercase hyphen-case」→ 放寬 `SKILL_NAME` 後回 `local-or-third-party` | 腳本共用 (twin 是 symlink), 不在 prompt surface, 無預算 | 新測試綠; 把正規式改回去看它紅; `add` 走 `require_text` 不動. **已完成 2026-09-05**: 測試先紅 (「hyphen-case」, exit 2) 再綠; `target` 對 `plugin:skill` 回 `scope: plugin` + `local-or-third-party` 無路徑, `new-skill:` 仍無 target; 一般名多帶 `scope: deployment`; `review.md` 加一條 |
| P2 | 耐久指標掃描: `docs/`, `main/.agents/docs/`, memory 目錄裡指向 `/private/tmp/…`, `/tmp/`, `scratchpad` 的路徑視為「寫時不敗讀時敗」的指標 | rebelytics 3.1 `reference:` 規則 + 本 repo `c995eb6` (兩個獨立血緣) | 先量: 今日 2 命中 (`clause-pricing.md`, `context-and-vendors.md`), 真偽未分; fixture 含 scratchpad 路徑的文件要紅 | `scripts/evidence-check.py` 加一類; docs 不是 token surface, 無預算 | 三個數寫在本列; 命中裡有真缺陷才加規則, 全是正當引用 (例如記錄 run 曾在哪) 就只在這裡記數字. **量過, 不加 (2026-09-05)**: 今日命中 2 / 真缺陷 0 / 正規化「排除圍欄內的逐字引用與非路徑的字」—— `clause-pricing.md:276` 是 replay 逐字引用的 `rm /private/tmp/…` 指令 (證據, 不是指標), `context-and-vendors.md:273` 的 `scratchpad` 是 client prompt 的區塊名. 而且 `c995eb6` 那次事故是 scratchpad 裡的**檔案**會消失, 不是文件裡的指標壞掉 —— 文件掃描本來就抓不到它, 抓到它的是 `evals/scripts/retain.py` 的保留步驟. 規則不加, 數字留在這裡; 推翻條件: 任一份指引或證據文件出現指向 `/private/tmp` 或 `scratchpad` 的「去那裡讀」句 |
| P3 | 編輯殘渣掃描 deployed surfaces: 字面 `\1` 孤行或散文裡的 backreference, conflict marker, `{{slot}}`, `TODO: fill`; 順帶「恰好一個 frontmatter 區塊」(`test_contracts` 有解析, 沒有這條斷言) | rebelytics 3.1 交付前閘第 6, 7 條; 實作細節可借 (圍欄先遮, 行號保留) | 今日 `main/` md/toml/json/yaml 0 命中; fixture 含 `<<<<<<<` 與 `\1` 孤行的 skill 要紅 | `test_deployment` 或 `evidence-check.py`; 兩邊 provider 的檔都在掃描母體裡 | 三個數在本列; 兩向突變 (拿掉一條 regex 看對應 fixture 綠掉). **已完成 2026-09-05**: 今日命中 0 / 真缺陷 0 / 正規化「圍欄與行內 code 先遮」; 零命中是現在加的理由 (免費的鎖). 落在 `test_deployment.EditResidueTests`: 一個 fixture 測試證明五種殘渣加「第二個 frontmatter 區塊」各抓得到而圍欄內不抓, 一個掃描測試跑遍部署 manifest 下所有 tracked 文字檔 (>50). 突變真的抓到一次: fixture 的 `{{ project }}` 帶空白, 上游那條 regex 抓不到, 改成容許空白才綠 |
| P4 | `readable-zh-tw` 的 `references/patterns.md` 補四個中文形狀: 雙音節動詞贅語 (進行討論 / 加以說明 / 予以處理 / 做出決定 → 動詞本身), 說明文裡的第二人稱, 名詞化 (○○性 / ○○感 / ○○化), 「事實上 / 其實」開段; 加一句「不是訊號」(標點密度, 段落數, 大陸用語是語域) | sepia v0.7.0 `languages/zh.md`; 只借形狀, 數字 (簡中 2023 語料) 一個不借 | `test_ledger` 對 reference 的既有斷言形狀: 斷言 `patterns.md` 含「進行」條目 (弱); 行為檢查等 P11b | `patterns.md` 不在 census (查過), `SKILL.md` 不動就不重跑 census; `.agents` 共用無雙生; 落地那天補 sepia 的 ATTRIBUTION (第一次有內容進 `main/`) | 四個形狀各在本機語料上命中至少一次; 一次都不中就拿掉 (ledger sepia 節的推翻條件). **已落地 2026-09-05**: 測試先紅再綠; 四個形狀併進既有的第 10 (動詞贅語, 名詞化), 15 (第二人稱), 19 (事實上) 條與新的「不是痕跡」一行, 38 的編號不動; sepia 以一段記進 readable-zh-tw 的 ATTRIBUTION (形狀不是逐字, 但 MIT 來源要點名). 命中量測待 P11b |
| P5 | `evidence-debugging` 加「有界停止點」: 缺陷不是交付物又吃掉 session 時, 停止點設在第二個假說之前; 「症狀 + 排除了什麼 + 最便宜的下一步」的問題報告本身是交付物 | rebelytics 3.1 SKILL.md; 我方現有的只有 diagnose / repair 權限切分與「無迴路即停」 | `test_contracts` / `test_ledger` 對該 SKILL.md 的片語斷言 (先查有無, 再加一條) | **prompt surface**: `scripts/prompt-surface-census.py --write`; `docs-size-report.py` 與 `budget-drift-report.py` 先量, 位移或帶理由的上調; `.agents` 共用 | census 過; 預算數字與理由寫在 landing-log. **已落地 2026-09-05**: 測試先紅再綠 (兩個部署面各斷言三個片語); 一段四行放在「Diagnosis-only stops here」之後; 位移 5 字 (結構指標說了兩次), 上限 1038 → 1079 (量到 1058 + ~2%, 理由在 test_contracts 的上限表); census 重寫 |
| P6 | leaf-redispatch 載體在 2.1.261 重驗: 一次真派工, leaf 嘗試巢狀派工 | weekly-integrity 09-05 開場訊息; rebelytics 3.1 「安裝的 session 證明不了啟用」佐證 | 這本身就是正控制: 用真實 tool record, 不造例子 | `main/claude/hooks/leaf-redispatch.py` 的 `CARRIER_VALIDATED_ON` | exit 2 觀察到, 常數推進到 (2, 1, 261); 沒觀察到就是 gate 已瞎, 停下來修. **已完成 2026-09-05**: `general-purpose` leaf (haiku) 的一次 Agent 呼叫被擋, 訊息與 2.1.241 那次相同, `denials.jsonl` 07:22:21Z 記到 `caller=general-purpose`; 常數已推進 |
| P7 | `upstream-pin-report.py` 也讀 research README 上游表的 pin (sepia, 以及任何沒有 ATTRIBUTION 的列): 解析 `pin \`<40 hex>\`` 與 repo URL | 09-05 sepia 移動只靠那列日期發現; ledger 「已知限制」節 | 先寫測試: fixture README 列 → 現在報 5 個 pin, 改後 7 個 | `scripts/`, 無預算 | 測試綠; 拿掉那列看回 5. **已完成 2026-09-05**: 測試先紅 (`collect` 不存在) 再綠, fixture 裡拿掉那列就少一個; 實跑報 6 個 pin, sepia 以「research README only」進表, 同業列 (eli5 有 SHA) 不被撿; skill 的已知限制段同步改 |
| P8 | 讀 Pilotfish tag 後十五個 commit 的 `benchmarks/**/attempts.json`: 抽「dispatch positive controls 怎麼設計」與「verifier paid summaries 的邊界」兩件, 對我方 trap / replay | 同業 (Nanako0129); 只讀不採 | — (閱讀) | `peer-harnesses.md` 新節 | 通貨表 Pilotfish 列去掉「未讀」; 若正控制設計與我方 trap fixture 同形, 記進第四輪整合第二節. **已完成 2026-09-05 (縮小)**: 讀了兩份 README 不是 attempts.json 本體; 三個正控制與 baton-dispatch 成本測試三個分支同形但**同血緣** (都蒸餾 cablate/baton), 不算票; 借到的是「每條政策同時過正負控制」的形狀, 我方 fixture 缺正控制那一半, 記進第四輪素材 |
| P9 | Deep Agents 0.7.7→0.7.13 內容差異 (三輪未讀) | 同業 | — | `peer-harnesses.md` | 同上. **已完成 2026-09-05 (發版說明, 非原始碼)**: 子代理 fork 成預設; grader 進 SDK hook; 0.7.10 #5566「glob 失敗不得報成沒有符合」是儀器守則的第三個獨立血緣 |
| P10 | client 注入段在 2.1.261 消失 → 戳章重跑: 依 evals 的量測面分組, 對 2.1.247 量的批次標出「client 半邊已動」; 不重跑矩陣 | context-and-vendors 09-05 補記; 第二輪整合的裁決 (採正規化那一半) 不變 | `evals/scripts/trap-surface.py` 的戳章比對要能對這一次說出「哪一半動了」 | `evals/`; 每個受影響批次的 README 一行 | 每個對 2.1.247 量的批次帶新戳章; 第四輪計票在這之後才開. **已完成 2026-09-05, 形狀縮小**: 戳章從沒含 client 半邊 (只對 repo 位元組取指紋), 所以沒有可重跑的東西; 落地是 [wording-effect-scale 的 09-05 補記](../research/wording-effect-scale.md#量測面的-client-半邊從未入戳-2026-09-05-補記): 兩個 opus 批次帶「量測時在, 現在不在」, sonnet 批次不受影響, client group 進戳章的條件寫成推翻條件 |
| P11 | sepia 後續: (a) 讀 `model-fingerprints.md` 的 Fable 5.1 prose layer (executor 端, 類別 vendor guidance unmeasured, 只當佐證); (b) `readable-zh-tw` 目前沒有 eval —— 借 sepia `evals/deaify-release-note` 的三 grader 形狀 (skill-fired / reads-human / no-slop-markers) 開一條 | sepia v0.7.0 | (b) 先決定要不要有 eval, 決定了才寫 | `evals/`; 等 P4 落地 | (a) 一段記進 ledger sepia 節; (b) 決定寫進本列. **已完成 2026-09-05**: (a) 三條供應商自述預設 (造作散文, 更密, 更少版面) 記進 ledger sepia 節, 類別 vendor guidance, 不加規則; (b) **決定要**: 借 sepia 三 grader 形狀, 與下一個 replay 批次一起開, 觸發是那個批次的事前登記 |
| P13 | 派工正控制 fixture: 一個「該派卻沒派算失敗」的 trap (候選形狀: Pilotfish 的 12 檔穩定機械編輯, 派 `mech-executor` 才對), 讓派工煞車第一次被正控制量到 | 第四輪整合結論 6; Pilotfish 控制表 (同血緣, 借形狀) | 先寫 fixture 的驗收閘: 直接做完算失敗, 派給機械工且測試全過算通過; 再跑一次看它紅在哪邊 | `evals/traps/`, 新 surface.tsv, 戳章; 不動 prompt surface | fixture 在兩個 provider 各跑過一次, 結果表帶戳章; 若兩邊都「直接做完」, 煞車的正控制就是紅的, 那是結論不是失敗 |
| P12 | 「查過但不能用的來源」登記法: `model-evidence.md` 加一小節, 記查過但沒有可用數字的來源與原因, 免得下次再抓流傳的數字 | sepia `sources.md` 的 Consulted 表; 是我方「沒有查的」的另一半 | — | `docs/research/`, 無預算 | 下一次量測輪至少一筆進去. **已完成 2026-09-05**: `model-evidence.md` 末節開表, 首輪三筆 (HC3-Chinese 讀數, Pilotfish 兩組成本數) |

## 明確不做的 (依據在 ledger 各節)

- rebelytics 的啟動種子, session-start 掃描, per-skill 載入時 grep, deliverable flush, carrier pattern,
  staging 三向對帳, `{skill}-extras`: 形狀不同 —— 我方寫入 opt-in, 單一鎖住的 JSONL, 沒有 staging.
- rebelytics 種子 25 條裡的互動小工具 (8, 9), 瀏覽器成本 (18), API 沙盒 (19): 不適用或沒量過.
- sepia 的小說側, voice, 模型歸因; 上游 review 報告格式.
- Windows 排程器, CRLF, 八進位 id, cp1252 主控台: 平台不適用.
- 安裝 upstream skill 而非蒸餾 (rebelytics 「專案有帶就裝官方的」的後半): 與本 repo 的蒸餾方針相反.

## 推翻條件

- **rebelytics 血緣查明參照過本 repo**: P2, P3 的「兩個獨立血緣」各降一, 但採用理由不變 (本地
  事故本身就是依據); 第四輪計票把 rebelytics 從獨立票剔除.
- **P2 或 P3 的三個數顯示命中全是正當引用**: 不加規則, 只留數字; 這一頁的那兩列改成「量過, 不加」.
- **P6 沒觀察到 exit 2**: 不是「重驗失敗」, 是 gate 在 2.1.261 上已瞎 —— 那時 P6 變成修 gate, 而
  P10 之後的每個量測結果都要重新標「hook 半邊也動了」.
- **P4 四個形狀在本機語料一次都不中**: 拿掉, 並在 ledger sepia 節記「簡中 2023 的形狀沒跨到繁中
  2026」, 那本身是一筆對上游證據邊界的佐證.

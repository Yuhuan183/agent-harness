# 同業 agent harness 拆解

> 對齊日期：2026-07-28。只保留會影響本專案設計的存續結論。

## LangChain Deep Agents

查核版本：PyPI stable `0.6.12`、beta `0.7.0b2`。Deep Agents 的價值不在提供另一套固定流程，而在把幾個可組合能力做成 middleware 與 state boundary：

- tool／subagent allowlist 比 denylist 更可證明；
- filesystem、state、memory、human-in-the-loop 各自有清楚生命週期；
- context 壓縮與摘要是執行期能力，不等於可任意改寫 provider 的 compact payload；
- rubric／grader 的輸入是待驗證 observation，不是可信 instruction；
- persistence 與 hosted product 的能力、區域與 beta 狀態需分開陳述。

### 專案採用

- no-write role 使用工具 allowlist。
- report 與引用的 tool output 都視為 untrusted observation。
- compact 後以 `SessionStart[source=compact]` 補最低限度 reseed；不宣稱能控制 PreCompact 摘要內容。
- memory、ledger 與 Git ownership 分層：Git 保存可攜契約，ledger 保存 machine-local outcome evidence。

### 不採用

- 不導入完整 Deep Agents runtime；目前 Claude/Codex 原生 agent surface 已足以承載角色契約。
- 不把 hosted／beta 能力寫成穩定、自架或跨區皆可用。
- 不把一般 middleware pattern 複製成 resident prompt；只有能改善本專案失敗形態者才落地。

## Pilotfish v1.3.0–v1.3.4

研究基準為 [Pilotfish v1.3.4](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.4)，tag commit `a4c5852924b7a4112b4fab7e5121b62ac2de0d2b`（2026-07-25）。v1.3.0 到 v1.3.4 的逐版變動已收斂成以下仍存續的原則：

1. **工作形狀決定派工**：同型、互相獨立、能由一份 stable one-shot brief 完整描述，才適合合批。
2. **未知 bug 不切斷推理鏈**：root cause、第一個 minimal fix、live verification 留在同一 owner。
3. **mechanical default 可被反駁**：已知修法的大量機械工作可交給 `mech-executor`；若 context 重建或整合成本較高，main 直接做。
4. **Plan envelope 與 slice 分離**：共享 constraints 固定，下一個可執行 slice 有 stable ID、owner、prerequisites、acceptance、rollback。
5. **readiness 與 outcome 分工**：`plan-verifier` 只判 Plan；`verifier` 只判完成 claim。
6. **anti-churn**：同 readiness unit 最多兩次自動實質修訂，之後呈現選項。
7. **安全分權**：read-only security review 先進 Plan，批准後只有一個 writer。
8. **prompt surface 分層**：resident contract、on-demand skill、leaf role 分開計量與去重。

### 與本專案的比較

| Pilotfish 存續設計 | 本專案現況 | 裁決 |
|---|---|---|
| shape-based batching | `baton-dispatch` 已採 shared context／artifact／dependency／verification surface | 已落地 |
| direct-execution brake | resident contract 已以淨收益判斷派工 | 已落地 |
| envelope + executable slice | Plan contract 已要求 stable boundary；rollback 由實際 release strategy 決定 | 已落地 |
| Plan anti-churn | 兩次 automatic revision 上限 | 已落地 |
| readiness／outcome 分工 | Claude/Codex twin roles 與 vocabulary tests | 已落地 |
| security sequencing | reviewer → approved contract → single executor | 已落地 |
| fixed dispatch/result records | 兩側 dispatch skill 與 experience ledger | 已落地 |
| exact prompt compression evidence | words／bytes／hash census | 已落地（靜態） |
| lifecycle behavior proof | interruption、repeat correction、conflicting results replay | 尚缺實證 |

### 關鍵修正

早期本專案為了讓 Claude verifier 執行重現，設計 `readonly-bash` shell parser。2026-07-28 security review 證明它可被 Git callbacks、environment indirection、parameter expansion、executable resolution 與非 Git 工具副作用繞過。最終裁決不是繼續擴大 denylist，而是移除 Claude no-write roles 的 Bash；需要命令的獨立 verdict 轉給 Codex `sandbox_mode = "read-only"`。

這個結果也修正了對「allowlist」的理解：tool-level allowlist 有有限且可列舉的能力面；shell command parser 面對的是可組合語言與外部程式，不能提供同等保證。

## 採用效果與驗證

預期效果：

- 減少不必要派工、context duplication 與整合重工；
- 降低 Plan verifier 無限來回；
- 讓 security 與 outcome verdict 的權限邊界可檢查；
- 讓 provider route、request source、成本與 QC 結果能回溯；
- 壓縮過時 prompt，同時保留 authority、stop、QC 與 deployment boundary。

目前能證明的是契約、設定與測試已落地。效能與可靠度差異仍需用相同 brief、相同權限、相同 acceptance 的 lifecycle replay，加上 experience ledger 的 wall-clock、review/rework、token coverage 與失敗形態比較。

## 上游證據

- [Pilotfish v1.3.4 release](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.4)
- [Spontaneous-dispatch Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.4/benchmarks/spontaneous-dispatch/README.md)
- [Baton-dispatch effect Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.4/benchmarks/baton-dispatch-effect/README.md)
- [Prompt-compression Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.4/benchmarks/prompt-compression/README.md)
- [Deep Agents documentation](https://docs.langchain.com/oss/python/deepagents/overview)

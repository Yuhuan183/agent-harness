# 派工生命週期與驗證

派工的規則散在幾個地方各司其職：`baton-dispatch` 管形狀與 QC，`provider-routing`
管路由與 fallback，`experience-ledger` 管記帳。這份文件把它們串成一條可驗證的鏈：
一次派工從解析路由到寫進 ledger，中間每個狀態由哪個東西承載、可以用什麼命令驗、
以及哪些推論是不成立的。

維護這個 harness 時，這裡是「怎麼確認派工管理沒有破洞」的入口。

## 五個狀態與各自的承載物

每個狀態都要有實體承載，不能只是散文約定。沒有承載欄位的規則就無法驗證。

| 狀態 | 承載物 | 怎麼看 |
|---|---|---|
| resolved | resolver 的 JSON 輸出 | `model-routing resolve --role <role>`（Codex bridge 加 `--surface claude-bridge`） |
| launched | `dispatch_id`（`<session>:<agent>`）；bridge 另有 companion job id | pending stub 的 `SubagentStart` 列 |
| running | **provider 側的 job 狀態**，不是 launcher 的存活 | `bridge-jobs --workspace "$PWD"`；native 由 harness 自己追蹤 |
| collected | leaf 的最終回覆 + main 的 QC | `[LEAF_RESULT]` 記錄 |
| logged | ledger 一列 schema-3 記錄 | `experience.jsonl`；`experience-report` 讀它 |

漏掉任一個承載物，該狀態就只能靠自述。這正是 2026-07-26 兩個 finding 的共同形狀。

## 不成立的推論

**launcher 死了 ≠ 派工死了（只發生在 bridge）。** Codex job 不是 forwarder 的子行程；
forwarder 被 Bash 兩分鐘上限砍掉之後，job 照跑、照持有 sandbox、照持有它那個 role
被賦予的寫入權。把 launcher 逾時讀成派工失敗而重啟，就會有兩個 live job 對同一個
workspace 工作 —— `baton-dispatch` 的「one owner per writable artifact」在沒有人決定
違反它的情況下就破了，而且兩個 agent 都看不見對方。

重啟前一律先對帳：

```bash
~/.codex/scripts/bridge-jobs --workspace "$PWD" --duplicates
```

exit 0 沒有雙胞胎；exit 1 列出雙胞胎與各自的取消指令；**exit 2 是「查不到」**，
它不等於「沒有在跑」，也不足以授權任何重啟。完整規則與 plugin 升級後的複查清單見
[bridge-liveness](../main/claude/skills/provider-routing/references/bridge-liveness.md)。

**job 的 `status` 欄位 ≠ job 還活著。** 被硬砍掉的 job 會永遠留著
`status: running`（2026-07-26 當天第二次踩到：review job 死了，狀態檔沒有察覺）。
所以存活判定是去問 OS 那個 pid 還在不在，不是讀 status。狀態檔說在跑、process 卻不見的
會另外列成「died without updating their state」—— 它不構成雙寫風險，但它是「還在做」跟
「什麼都不會給你」的差別。pid 查不到的記錄一律算活著：對雙寫防護來說，寧可多報。

Native Claude subagent 沒有這個失效模式：harness 自己追蹤子代理，launcher 與 job
同生共死。這條規則只對 bridge 成立，也只寫在 bridge 那一側。

**派工者說的 route ≠ 實際跑的 route。** bridge 的 job sidecar 不記 model 與 effort，
所以那兩個值一度只能手打。手打的值會被記成 `route_source: explicit` —— 那個詞描述的
是「怎麼傳進來的」，不是「有多可信」。實際上 Codex 自己會把套用的 thread settings 寫進
rollout，那才是 provider 記錄的證據，也正是
[provider-protocol](../main/claude/skills/provider-routing/references/provider-protocol.md)
對每個可路由 provider 的要求（第 3 項：machine-verifiable telemetry，不得 agent 自述）。

現在 `experience-log --from-pending` 會從該次派工的 rollout 讀出 model 與 effort：

- 沒宣告 → 用證據填，記為 `route_source: rollout-verified`
- 宣告且相符 → 同樣記為 `rollout-verified`
- 宣告但矛盾 → **拒絕寫入**，當作 routing violation 浮出來
- rollout 無法唯一鎖定（同時間窗有多個）→ 不填、不背書，記 `telemetry_warning`

`--profile` 仍然由呼叫端提供：那是 harness 的標籤，provider 端沒有對應物。

## 兩條所有權規則，一條擋得住、一條擋不住

**「每個 top-level task 至多一個 outcome verifier」現在會被拒絕。** 承載欄位是
payload 的 `prompt_id`，同一個 prompt 內第二次派 `verifier` 直接 exit 2。要留意它的
邊界：top-level task 是判斷邊界、不是欄位，`prompt_id` 只是最接近的代理，所以**跨
prompt 的同一個任務會拿到新的額度**——它會少擋，不會誤擋。真的是新任務就用
`AGENT_ALLOW_SECOND_VERIFIER=1` 重派。payload 沒有 `prompt_id` 時放行並附註：這是預算
護欄，不是安全邊界，不該在讀不到承載欄位時盲目拒絕。

**「一個 writable artifact 一個 owner」仍然是判斷，沒有機制。** 這是刻意的：
`baton-dispatch` 本來就允許對不相交表面平行派工，而 hook 無法可靠得知每個 leaf 的可寫
範圍，所以「同時有兩個 writer」不等於違規。做成 gate 只會得到一個關不起來的機制——正是
這個 repo 反覆抓到的那種缺陷。目前只有 bridge 那條路徑有真正的對帳（`bridge-jobs`），
因為那裡的重複是同一個 prompt 的機械性複製，判得出來。native 側請在派工前自己確認可寫
範圍不相交。

## 三種 `route_source` 的強度

由強到弱，寫在 [metrics](../main/.agents/skills/experience-ledger/references/metrics.md)：

- `rollout-verified` — model／effort 與 provider 自己的 rollout 相符
- `explicit` — 派工者宣告，且沒有 provider telemetry 可以對照。**是主張，不是證據**
- `resolver-assumed` — 由 resolver 從 alias 推得；alias 一旦升版就不能當已驗證

## 驗證清單

改動派工管理相關的東西之後，跑這些：

```bash
python3 -m unittest discover -s main/claude/tests          # 全套；下面兩個是重點
python3 -m unittest discover -s main/claude/tests -k BridgeJobLiveness
python3 -m unittest discover -s main/claude/tests -k BridgeRouteEvidence
~/.codex/scripts/bridge-jobs --duplicates                  # 對真實狀態的煙霧測試
```

`BridgeJobLivenessTests` 釘住雙胞胎偵測（含「查不到不等於沒有」這條）；
`BridgeRouteEvidenceTests` 釘住路由證據鏈（含矛盾必須被拒）。

Codex plugin 升級後，job 狀態格式與 rollout 欄位都可能變，複查項目列在
[bridge-liveness](../main/claude/skills/provider-routing/references/bridge-liveness.md)
的最後一節。

## 這份文件不管的事

派工該不該發、怎麼拆、QC 怎麼做 → `baton-dispatch`。provider 怎麼選、fallback 怎麼跳、
verifier 什麼時候該出動 → `provider-routing`。指標定義與 revision 門檻 →
`experience-ledger` 的 metrics。這裡只管狀態、承載物與驗證。

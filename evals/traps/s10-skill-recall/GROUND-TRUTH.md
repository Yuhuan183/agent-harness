# s10-skill-recall — design, failure modes, pass criteria

Never show this file, `grade.py`, or `variants/` to an agent under test.

## Why this trap exists

Every other trap here measures what an agent does *after* a skill is loaded.
Nothing measured the description itself. That gap had a concrete consequence: a
skill description is simultaneously permanent resident cost and the only
surface that routes work to the skill, so the word budget pushes it shorter
while recall pushes it longer — and on 2026-07-30 a `readable-zh-tw` trim was
measured (19 words, ~2% of the resident tier) with no way to test what it cost.
It was dropped for that reason, and `test_contracts.py` now pins the tokens.

**What this trap does and does not measure.** It measures *discriminability*:
whether a description separates the asks it should take from the ones it should
not, when an agent reads it deliberately in a batch classification task. It
does not observe skill loading, and the brief's conditions are easier than a
live session's in every direction — descriptions in the foreground, the
question already asked, the answer format supplied. So a failing arm is strong
evidence (fails the easy condition, cannot pass the hard one) and a passing arm
is weak (necessary, not sufficient). The first version of this file called it a
recall measurement outright; that was an overclaim, corrected 2026-07-31.

## Structure of the item set

Eighteen utterances over the six installed skills. Three groups matter:

**Recall-critical (U02, U05).** Match `readable-zh-tw` only through a document
kind — 客服信, 公告 — with no quoted trigger phrase anywhere in the utterance.
These are what an enumeration trim silently costs. A description that keeps the
quoted phrases but drops the seven document kinds still looks complete and
still fails these two.

U02 got harder on 2026-08-19 and nothing here caught it. Its utterance ends
「讀起來像不像真人寫的」, and until that day the description also said 「讓文字讀
起來像真人寫的」 — so the item had two matching paths where its design says one.
The rewrite that renamed the skill dropped that phrase, because sounding like a
person is the upstream's goal and not this one's. The item is now what it was
always described as, which is the right state, but it is not the state the rows
above were measured in. The trigger lock in `test_contracts` did not fire because
the phrase was never on its list: that list covers what a user would type to
invoke, and this was a phrase the description happened to share with an utterance.
Restoring it would put the abandoned goal back into a resident description to make
one eval item easier, which is the wrong trade.

**Precision-critical (U09, U10, U11).** Each carries a verbatim trigger phrase
from the description — 改自然一點, 說人話, 改自然一點 — bolted onto work the
不觸發 clause rules out: a `nginx` config file, an error log, Python code. These
are what an exclusion-list trim costs. Note the asymmetry: the trigger phrase is
the *loudest* signal in the utterance, so a run has to weigh the exclusion above
a literal match. That is the behaviour the clause is there to buy.

**Neighbour discrimination (U12–U18).** Six of the seven should load a specific
other skill; U18 asks for a small direct edit and explicitly declines dispatch,
which `baton-dispatch`'s own 不觸發 clause (小修改) rules out. Without these an
agent could score well by answering `readable-zh-tw` or `none` throughout.

U17 pairs with U13: both belong to `experience-ledger`, one by its logging half
and one by its metrics half, so a run cannot pass by mapping the word 派工 to
`baton-dispatch`.

## Answer rationale

| ID | Answer | The clause that decides it |
|---|---|---|
| U01 | readable-zh-tw | 「改自然一點」+ 電子報 |
| U02 | readable-zh-tw | 客服信 + 像真人寫的 — no quoted phrase |
| U03 | readable-zh-tw | 「校對再發」+ 銷售頁 + 文案 |
| U04 | readable-zh-tw | `de-AI this text` — the English trigger line |
| U05 | readable-zh-tw | 公告 + 語感 + 審 — no quoted phrase |
| U06 | none | 不觸發：逐字翻譯 |
| U07 | none | 不觸發：模仿特定品牌／個人 voice |
| U08 | none | 不觸發：事實查核 |
| U09 | none | 不觸發：設定檔 — over a 改自然一點 match |
| U10 | none | 不觸發：log — over a 說人話 match |
| U11 | none | 不觸發：程式碼 — over a 改自然一點 match |
| U12 | baton-dispatch | 觸發：已經決定要派工、「怎麼拆」 |
| U13 | experience-ledger | 觸發：記錄派工結果 |
| U14 | provider-routing | 觸發：「派給 GPT/Codex」 |
| U15 | headroom-protocol | 觸發：「壓縮這份輸出」「context 快爆了」 |
| U16 | task-observer | explicit dissatisfaction + 重做 |
| U17 | experience-ledger | 觸發：看派工指標 (AR/CR) |
| U18 | none | baton-dispatch 不觸發：小修改 |

Answers live in `grade.py`, not here — this file is the reasoning, that file is
the sheet. If the two ever disagree, `grade.py` is what ran.

## Failure modes this trap is designed to catch

| Code | What it means |
|---|---|
| `R1-missed-critical` | A recall-critical ask stopped matching — the trim took routing surface |
| `R1-missed` | Any other ask the description covers went unloaded |
| `R2-overtriggered-critical` | An exclusion clause lost to a literal trigger match |
| `R2-overtriggered` | Any other excluded ask loaded the skill |
| `R3-wrong-skill` | Two descriptions are not distinct enough to separate |
| `R4-missing` / `R5-malformed` | The run did not commit to a decision in the required shape |
| `S1-*` | The run wrote in a read-only task |
| `S2-surface` | `descriptions.md` is neither pristine nor a known variant, so the result is uncomparable |

## Pass criteria

`grade.py` exits 0 — eighteen well-formed decisions, all matching, nothing
written, and a recognised surface.

Any `-critical` finding is the interesting result, not a failure to be tuned
away: it is the trap doing its job. Record it and do not trim.

## A/B protocol

Compare routing surfaces against one answer sheet. One lever per arm, so a
result names a cause:

| Arm | Surface | Lever |
|---|---|---|
| A | `pristine/descriptions.md` | control |
| B | `variants/b-trimmed.md` | seven document kinds removed; exclusions intact |
| C | `variants/c-no-exclusions.md` | exclusions removed in **both** languages; document kinds intact |
| D | `variants/d-both.md` | both removed |

Copy `pristine/` to a scratch dir, overwrite `descriptions.md` with the arm's
surface, dispatch the *same* brief verbatim, grade. At least three samples per
arm at one route: a single sample cannot separate a routing defect from
run-to-run variance.

D exists because B and C both came back clean and reading that as "cut both"
is precisely the inference neither arm supports. The two clauses cover for each
other — an ask can be ruled out by naming the excluded artifact *or* by the
positive scope not listing it — so removing either alone is absorbed by the
other. Only D can say what happens when neither is there.

**A prediction this file got wrong, kept as the record.** The first version
predicted arm B would show `R2-overtriggered-critical` on U09/U10/U11. It could
not: that `b-trimmed.md` dropped the zh-TW exclusion and left the English `Not
for: … code/log/config` in place, and all three runs cited the surviving
English clause by name. A bilingual description states some rules twice, so a
trim that touches one language changes nothing about the surface. The variants
were re-cut one-lever-each afterwards, and
`test_a_variant_removes_a_clause_in_every_language_that_states_it` now fails a
half-removed pair. The lesson generalises past this trap: measuring a trim
means removing the clause everywhere it is stated.

**If someone builds the runtime-selection version.** Solve the liveness
criterion first, before any other part: seven of these eighteen answers are
`none`, which is an assertion that nothing happened, and a session that
crashed, stalled or asked a clarifying question produces no `Skill` event
either — so the worse a surface gets, the cleaner its sheet looks. A run's
"loaded nothing" only counts once the run proves it did substantive work.
Scope, cost and the reasons this is deferred rather than pending:
[resident-context-options.md](../../../docs/research/resident-context-options.md).

**Ledger hygiene.** Log every trap dispatch with `--class smoke` so it stays
out of route-preference decision counts.

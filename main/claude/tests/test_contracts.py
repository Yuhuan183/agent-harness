"""Resident contracts and skills: Claude, Codex bundle, doc budgets."""
from support import *  # noqa: F401,F403


# Each provider's always-loaded contract. One source for the two tests that
# budget it: the per-document ceiling and the resident-layer total (contract
# plus skill metadata), which must not be able to drift apart.
#
# `words` is the outer ratchet. The three density figures beside it are what a
# rewrite actually has to answer to, and they derive from the 2026-08-04
# measurement of these same two files plus margin - a change of units, not a
# tightening. Their definitions and the reasoning are in `support.py`.
ContractBudget = namedtuple(
    "ContractBudget", "path words rules bytes_per_rule filler_floor filler_cap")
RESIDENT_CONTRACT_BUDGETS = {
    # measured 2026-08-04: 413 words, 14 rules, 203.6 bytes/rule, 0.209 filler
    "claude": ContractBudget(".claude/CLAUDE.contract.md", 520, 16, 225, 0.15, 0.25),
    # +10 (2026-08-03): the rtk clause gained the "a rewritten command may
    # report 0 matches without running" rule, and fitting it into 540 cost the
    # sentence its subject — "Authorization, approvals, and sandboxing ... may
    # substitute another program", which inverts the one guarantee that clause
    # exists to make. Ten words is what a grammatical subject costs here. The
    # file landed at exactly 540/540 before this, which is the state that
    # forced the bad compression; leaving a ceiling with zero headroom is how a
    # budget starts buying wrong sentences instead of short ones.
    #
    # measured 2026-08-04: 546 words, 24 rules, 158.7 bytes/rule, 0.212 filler
    "codex": ContractBudget(".codex/AGENTS.contract.md", 550, 26, 175, 0.15, 0.25),
}


class ClaudeContractTests(unittest.TestCase):
    def test_claude_md_is_slim_and_outcome_first(self) -> None:
        policy = read(".claude/CLAUDE.contract.md")
        self.assertLessEqual(len(policy.splitlines()), 40)
        for phrase in (
            "Lead with the outcome",
            "preserve dirty worktrees",
            "Direct execution is the default",
            "## Main session only — orchestration",
            "DECISION: <what and why>",
        ):
            self.assertIn(phrase, policy)

    def test_claude_md_does_not_restate_the_harness_system_prompt(self) -> None:
        """Claude Code already states these; a second copy is not free.

        Anthropic's context-engineering guidance for the Claude 5 generation cut
        most of Claude Code's own system prompt because overlapping directives
        make the model spend reasoning reconciling them, and OpenAI's GPT-5.6
        guidance reports that repeating approval language makes a model ask
        permission for safe, expected actions. Each phrase below is carried by
        the harness prompt in equivalent or stronger form, so this contract must
        not carry it again.

        Note this applies to the Claude Code CLI only: the Codex contract and
        the app prompts face thinner host prompts and keep their own authority
        boundary. A 2026-07-31 audit briefly called that claim false, on the
        strength of one Codex rollout; measuring all 91 put it back, because
        the Codex *subagent* prompt — 47 of the 50 sessions on cli >= 0.145.0 —
        carries none of the autonomy or worktree language the top-level one
        does. See `CodexContractRestatementTests`.

        The Claude side of that audit has no equivalent evidence: Claude Code
        records its system prompt nowhere, so whether a Claude subagent
        receives the phrases banned below is currently unfalsifiable. Treat
        this list as the weaker-evidenced of the two.
        """
        policy = read(".claude/CLAUDE.contract.md")
        for restated in (
            "Infer low-risk ambiguity",
            "different answers materially change the result",
            "require explicit authority",
            "report failed or skipped checks exactly",
            "Do not add speculative features",
        ):
            self.assertNotIn(restated, policy)

    def test_dispatch_reporting_and_leaf_boundary(self) -> None:
        # The resident contract keeps the record names and the leaf boundary;
        # the field-level template lives in baton-dispatch (single source,
        # mirroring the Codex leaf-dispatch pattern).
        policy = read(".claude/CLAUDE.contract.md")
        self.assertIn("[LEAF_DISPATCH]", policy)
        self.assertIn("[LEAF_RESULT]", policy)
        self.assertIn("Never brief a subagent to delegate further", policy)
        self.assertIn("agent-to-agent briefs stay in precise, concise English", policy)
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        self.assertIn("dispatch_id=<id>", skill)
        for field in ("task=<label>", "role=<role>", "class=<class>",
                      "request_source=<request_source>", "route=<profile>/<provider>/<model>/<effort>",
                      "ledger=<logged|skipped(reason)>"):
            self.assertIn(field, skill)

    def test_effort_is_capped_at_high(self) -> None:
        for role in ROLES:
            self.assertNotIn("xhigh", frontmatter(f".claude/agents/{role}.md"), role)
        for path in (
            ".claude/skills/provider-routing/SKILL.md",
            ".codex/AGENTS.contract.md",
            ".codex/config.merge.toml",
        ):
            text = read(path)
            for sanctioned in ("no role or bridge call uses xhigh",
                               "Fable at medium\u2013xhigh",
                               "raise effort to xhigh"):
                text = text.replace(sanctioned, "")
            self.assertNotIn("xhigh", text, path)

    def test_claude_md_delegates_detail_to_skills(self) -> None:
        policy = read(".claude/CLAUDE.contract.md")
        for skill in ("baton-dispatch", "provider-routing", "headroom-protocol"):
            self.assertIn(skill, policy)
        # Routing detail and the version gate live in skills / the runtime-guard hook,
        # not inline in the resident contract.
        for moved in (
            "Discovery → Plan → Approval",
            "gpt-5.6-sol",
            "H = Opus",
            "2.1.207",
        ):
            self.assertNotIn(moved, policy)

    def test_baton_dispatch_skill_carries_recon_result_collection(self) -> None:
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        # Progressive disclosure: the contract's cost test answers the common
        # case ("stay in main") on its own, so this skill is loaded only once a
        # dispatch is actually going ahead. A "mandatory before every dispatch"
        # description would both re-state the contract and make a 900-word file
        # resident for decisions that resolve without it.
        baton_meta = frontmatter(".claude/skills/baton-dispatch/SKILL.md")
        self.assertIn("Load once a dispatch is going ahead", baton_meta)
        self.assertNotIn("Mandatory", baton_meta)
        # Cost test: high-tier pinned delegation saves no compute; payoff must beat overhead.
        self.assertIn("## Cost test", skill)
        self.assertIn("delegation saves no compute", skill)
        self.assertIn("clearly exceeds dispatch overhead", read(".claude/CLAUDE.contract.md"))
        self.assertIn("clearly exceeds\ndispatch overhead", read(".codex/skills/leaf-dispatch/SKILL.md"))
        self.assertIn("cablate/baton v0.1.1", skill)
        # The provenance sentence used to name a bare short SHA, and this
        # assertion is why it survived: the citation stopped resolving at some
        # rebase, and a test pinning the string kept it in a deployed file where
        # nobody could check it. Version tags are durable anchors; bare short
        # SHAs are not (docs/README.md rule 9). Assert the claim, not the ghost.
        self.assertIn("plus a scope fix", skill)
        self.assertNotRegex(
            skill, r"`[0-9a-f]{7,12}`",
            "a bare short SHA in a deployed file cannot be resolved by whoever "
            "reads it; cite a version, a link, or a content fingerprint")
        self.assertNotIn("pilotfish", skill.lower())
        self.assertIn("hard boundary", skill)
        self.assertNotIn("Discovery → Plan → Approval", skill)
        # A1: orchestrator-side recon result-collection.
        self.assertIn("final response is its deliverable", skill)
        self.assertIn("never relaunch", skill)
        self.assertIn("genuinely new or redirected work", skill)
        # A2: recon facts are unverified inputs.
        self.assertIn("unverified input", skill)
        # A3: uncollected worktree is lost work.
        self.assertIn("lost unless the integration owner harvests", brief)
        self.assertIn("excluded adjacent capabilities", brief)
        self.assertIn("approved boundary crossed", brief)
        self.assertIn("Known one-file fix", brief)
        self.assertIn("Role, task class, and scenario", brief)
        self.assertIn("`review`", brief)
        self.assertIn("semantic-seams", brief)
        self.assertIn("LEAF_DISPATCH", skill)
        self.assertIn("LEAF_RESULT", skill)

    def test_pilotfish_guardrails_are_backend_neutral_and_cross_surface(self) -> None:
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        claude = read(".claude/CLAUDE.contract.md")
        codex = read(".codex/AGENTS.contract.md")
        triggers = read(
            ".claude/skills/provider-routing/references/verifier-triggers.md"
        )

        codex_dispatch = " ".join(read(".codex/skills/leaf-dispatch/SKILL.md").split())
        codex_policy = codex + "\n" + codex_dispatch
        for text in (skill, brief, codex_dispatch):
            self.assertIn("stable one-shot brief", text)
            self.assertIn("independent and the same shape", text)
            self.assertIn("per-item acceptance", text)
        self.assertIn("known root cause and remedy", skill)
        self.assertIn("known remedy", codex_policy)
        self.assertIn("not a numeric trigger", brief)
        self.assertIn("never use an item-count trigger", codex_policy)

        for text in (skill, triggers, codex_policy):
            self.assertIn("smallest coherent integration boundary", text)
            self.assertIn("intermediate evidence", text)
        for text in (triggers, codex_policy):
            self.assertIn("cross-language or FFI", text)
            self.assertIn("serialization or pre-aggregation", text)
        # Plan anti-churn moved from the resident Claude contract into the
        # mandatory-pre-dispatch baton skill (union assertion, like codex).
        claude_policy = claude + "\n" + skill
        for text in (claude_policy, codex_policy):
            self.assertIn("substantially unchanged Plan", text)
            self.assertIn("material revision or new evidence", text)
            self.assertRegex(text, r"silently (overrule|overriding)")

    def test_pilotfish_v134_readiness_and_discovery_are_cross_surface(self) -> None:
        claude_dispatch = read(".claude/skills/baton-dispatch/SKILL.md")
        codex_dispatch = read(".codex/skills/leaf-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        claude_plan = read(".claude/agents/plan-verifier.md")
        codex_plan = tomllib.loads(
            read(".codex/agents/plan-verifier.toml"))["developer_instructions"]
        claude_security = read(".claude/agents/security-reviewer.md")
        codex_security = tomllib.loads(
            read(".codex/agents/security-reviewer.toml"))["developer_instructions"]

        for text in (claude_dispatch, codex_dispatch):
            for phrase in (
                "program envelope",
                "next executable slice",
                "readiness-unit ID",
                "first readiness review",
                "after two automatic revisions",
                "Blocker",
                "Minimum revision",
                "Acceptance check",
            ):
                self.assertIn(phrase, text)
        for text in (claude_dispatch, codex_dispatch, brief):
            self.assertIn("temporarily exclusive", text)
            self.assertIn("back-to-back", text)
            self.assertIn("cross-surface synthesis", text)
        for text in (claude_plan, codex_plan):
            self.assertIn("stable readiness-unit ID", text)
            self.assertIn("READY", text)
            self.assertIn("with no other text", text)
            for field in (
                "Blocker:",
                "Evidence:",
                "Minimum revision:",
                "Acceptance check:",
            ):
                self.assertIn(field, text)
            self.assertIn("security-reviewer", text)
            self.assertIn("disposition", text)
        for text in (claude_security, codex_security):
            self.assertIn("stable ID", text)
            self.assertIn("affected Plan", text)
            self.assertIn("first readiness review", text)

    def test_verification_is_bounded_by_passes_and_by_state_change(self) -> None:
        # Two independent bounds, because they catch different loops. The pass
        # cap ends a long chain; the unchanged-candidate rule ends a chain that
        # never moves, which a pass cap alone cannot see — five re-runs against
        # identical state are still five passes. Five is calibrated on the
        # local ledger: one target took four verifier dispatches inside 4.5
        # hours on 2026-07-28 and each pass found new defects, so a three-pass
        # cap would have fired on legitimate work.
        #
        # The cap also has to say how it relates to the one-verifier quota, or
        # the two land in the same file as bare numbers over three different
        # units — one per "top-level task", five per "target", and the gate
        # counting per prompt — and a reader can only guess whether five passes
        # are permission to spend the quota five times (2026-08-04 review).
        for path in (".claude/skills/baton-dispatch/SKILL.md",
                     ".codex/skills/leaf-dispatch/SKILL.md"):
            text = " ".join(read(path).split())
            self.assertIn("five verification passes", text, path)
            self.assertIn("names what changed since the previous one", text, path)
            self.assertIn("an unchanged candidate is not re-verified", text, path)
            self.assertIn("does not widen the one-verifier quota", text, path)
            self.assertIn("one outcome verifier per acceptance claim", text, path)
            self.assertIn("only a changed candidate is a new claim", text, path)

    def test_provider_routing_owns_model_and_fallback_policy(self) -> None:
        skill = read(".claude/skills/provider-routing/SKILL.md")
        for phrase in (
            "omit invocation-level `model`",
            "H** = Opus/high or Fable/low",
            "X** = Opus/high or Fable at medium\u2013xhigh",
            "one cross-provider hop measured from the task's origin",
            "A fallback provider cannot route back",
            "one bounded retry",
            *(f"`{option}`" for option in DISPATCH_OPTIONS),
            "never two writers on the same artifacts",
            "Security keeps its capability split on either provider",
            "never include Fable",
            f"`{CODEX_BRIDGE}`",
            "--surface claude-bridge",
            "--model <model>`",
            "--effort <effort>`",
            "single source of truth for Codex bridge model and effort",
            "quality-guarded` only for high-risk, high-impact, or highly uncertain work",
            "write-capable by default",
            "explicitly prohibit writes",
            "`plan-verifier` returns READY/REVISE",
            "`verifier` returns CONFIRMED/REFUTED",
            "Do not stack gates over the same failure surface",
            "Dual-provider",
            "profiles are **deployment presets**, not per-dispatch routes",
            "updates all pins transactionally",
            f"invoked from Claude through the `{CODEX_BRIDGE}` bridge",
            "cost per acceptable outcome",
            "External indices are priors only",
        ):
            self.assertIn(phrase, skill)
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/scripts/model-routing", skill)
        self.assertNotIn("--model gpt-5.6-sol", skill)

    def test_no_surface_grants_a_claude_no_write_role_a_command(self) -> None:
        """The capability is a frontmatter fact; the prose kept contradicting it.

        `provider-routing` said the `verifier` "may run read-only checks in an
        isolated worktree" twelve lines after the same file said Claude
        no-write roles lack Bash, and the role file itself answers INCONCLUSIVE
        the moment a verdict needs a command. An operator routing on the first
        sentence spends a fresh-context dispatch to be told nothing
        (2026-08-06 review).

        Phrase assertions could not have caught it - the wrong sentence was
        new text, not a deleted phrase. So this reads the tool lists first and
        then requires every surface that says one of those roles runs something
        to say Codex in the same breath, which is the only provider where it is
        true.
        """
        no_write = ("verifier", "plan-verifier", "security-reviewer", "explore")
        for role in no_write:
            tools = frontmatter(f".claude/agents/{role}.md")
            self.assertNotIn(
                "Bash", tools,
                f"{role} gained a command surface; this test's premise is gone")
        role_named = re.compile("`(?:" + "|".join(no_write) + ")`")
        # Read only what follows the role name: "re-run it in main, since the
        # `verifier` gate covers..." describes the caller, not the leaf.
        capability = re.compile(
            r"\b(?:run|runs|running|execute|executes|command|commands|Bash)\b",
            re.IGNORECASE)
        offenders = []
        for path in (".claude/skills/provider-routing/SKILL.md",
                     ".claude/skills/baton-dispatch/SKILL.md",
                     *(f".claude/agents/{role}.md" for role in no_write)):
            flat = " ".join(read(path).split())
            for sentence in re.split(r"(?<=[.!?])\s+", flat):
                if "Codex" in sentence:
                    continue
                if any(capability.search(sentence, m.end(), m.end() + 90)
                       for m in role_named.finditer(sentence)):
                    offenders.append(f"{path}: {sentence}")
        self.assertEqual(
            offenders, [],
            "a Claude no-write role is described as running something; name "
            "the Codex twin in the same sentence or drop the claim")

    def test_dispatch_skills_have_non_overlapping_ownership(self) -> None:
        baton = read(".claude/skills/baton-dispatch/SKILL.md")
        provider = read(".claude/skills/provider-routing/SKILL.md")
        leaf = read(".codex/skills/leaf-dispatch/SKILL.md")
        leaf_flat = " ".join(leaf.split())

        self.assertIn(
            "owns dispatch shape, grouping, briefs, collection, QC, and fixed records",
            baton,
        )
        self.assertIn("does not choose a provider/model", baton)
        self.assertIn(
            "Own provider/model/role selection, bridge resolution, "
            "cross-provider fallback, and verifier eligibility",
            provider,
        )
        self.assertIn("Record formats and QC mechanics stay in `baton-dispatch`", provider)
        self.assertNotIn("qc-gate-lines", provider)
        self.assertNotIn("[LEAF_DISPATCH]", provider)
        self.assertIn("Own Codex dispatch", leaf_flat)
        self.assertIn("do not select main model", leaf_flat)


class CodexContractRestatementTests(unittest.TestCase):
    """Why the Codex contract keeps clauses the Claude contract may not.

    The 2026-07-31 vendor-restatement audit deleted three of these, then a
    re-review put them back. Both passes read the same provider-recorded
    evidence — Codex writes its host prompt into `session_meta.base_instructions`
    of every rollout — but the first pass read *one* rollout. There are eight
    distinct prompts across 91 local rollouts, and the one it happened to read
    is the only variant carrying both the "File editing constraints" and
    "Destructive Actions" sections, so it maximised apparent vendor coverage.

    The axis is session kind, not CLI version. On cli >= 0.145.0, over all 220
    discovered rollouts (`scripts/codex-prompt-census.py --min-cli 0.145`):

        kind        n    dirty-worktree  no-ask-scoped  autonomy  authority
        top-level  59            59/59          59/59     59/59      51/59
        subagent   90            43/90          43/90     43/90      57/90

    An earlier pass quoted 0/47 for the subagent row. That was one rollout
    store: the census globbed `sessions/` and never saw `archived_sessions/`,
    which holds more than half the population and is the same population -
    archiving is a user action, both stores carry the contract, and the two
    separate on the same days under the same CLI. The corrected numbers do not
    change the decision and strengthen the rule behind it: no clause reaches
    full coverage for subagents, so every one of them has to stay.

    Codex delivers this contract to subagents as instructions - the rollout
    carries it as a `role: user` message headed `# AGENTS.md instructions` and
    mirrors it in `world_state.agents_md` - so a clause the subagent prompt
    omits has no other source. Deleting these removed the only statement of
    "the user's uncommitted work is theirs; preserve it" from every current
    subagent session, which is the half of the fleet that writes files.

    The rule this yields: judge a restatement against the *thinnest* host
    prompt any consumer of the contract runs under, never against a sampled
    one. The Claude side of the audit cannot be run at all - Claude Code
    records its system prompt nowhere, so the same sampling error there is
    currently unfalsifiable.
    """

    #: Present in the top-level Codex prompt, absent from every current
    #: subagent prompt, and the contract is loaded by both.
    SUBAGENT_UNCOVERED = (
        "preserve dirty worktrees and unrelated user work",
        "need no approval",
        "inspect and report",
    )

    def test_the_vendor_census_covers_every_justified_clause(self) -> None:
        """The measurement behind these decisions has to be re-runnable.

        The numbers above are a snapshot of one machine's rollouts. Left as
        prose they rot silently, and the audit that produced them was already
        re-derived once by hand and got it wrong. `scripts/codex-prompt-census.py`
        regenerates them on demand; this fails if a clause is justified here
        that the census does not measure, or vice versa, so the tool and the
        reasoning cannot drift apart.

        The census has no `--check` mode on purpose: its input is machine-local
        and expected to move, so a pinned snapshot would fail for everyone who
        is not the author. It is evidence for a human decision, not a gate.
        """
        import importlib.util

        script = ROOT / "scripts/codex-prompt-census.py"
        self.assertTrue(script.is_file(), script)
        spec = importlib.util.spec_from_file_location("codex_prompt_census", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        measured = {clause for _, clause, _ in module.CONTRACT_CLAUSES}
        justified = set(self.SUBAGENT_UNCOVERED) | {"require explicit authority"}
        self.assertEqual(
            justified, measured,
            "every clause kept or dropped on vendor-coverage grounds must be a "
            "column in the census, so the claim can be rechecked by running it")
        # And the census must still be reading the vendor's words, not ours:
        # a rollout for work in this repo quotes the contract everywhere else.
        self.assertTrue(module.OUR_MARKERS, "circularity check was removed")

    def test_clauses_the_subagent_prompt_does_not_carry_stay_in_the_contract(self) -> None:
        policy = read(".codex/AGENTS.contract.md")
        for clause in self.SUBAGENT_UNCOVERED:
            self.assertIn(
                clause, policy,
                f"{clause!r} was removed as a vendor restatement, but the "
                "Codex subagent prompt does not always restate it (43/90 on "
                "cli >= 0.145.0) and subagents receive this contract")

    def test_the_canonical_rule_admits_the_exception_this_class_relies_on(self) -> None:
        """A named exception has to exist in the rule, not only in its gate.

        `contract-slimming.md` said vendor restatements are deleted 一律 — with
        no exception — while the test below requires one kept. The next audit
        following the canonical document would delete the sentence and hit a
        red test with no written reason, which is the contradiction that
        principle 2b calls the more expensive failure shape.
        """
        rule = (ROOT / "docs/contract-slimming.md").read_text(encoding="utf-8")
        self.assertIn("預設刪除", rule)
        self.assertIn("不可回復的安全條款", rule,
                      "the exception this class relies on is not in the rule")
        self.assertIn("具名", rule, "the exception must require naming")

    def test_the_census_reports_what_it_could_not_read(self) -> None:
        """The denominator is the load-bearing part of this evidence.

        Twice now the census has silently shrunk its own sample - once by
        globbing one rollout store, once by dropping rollouts it could not
        parse - and a smaller sample makes vendor coverage look *more*
        complete, which is the direction that licenses a deletion that should
        not happen. Exercises the parser against format drift, a missing
        record, and an empty store, because an import-only test would pass
        while every one of these was broken.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "codex_prompt_census", ROOT / "scripts/codex-prompt-census.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def run(rollouts: dict[str, list[dict]]) -> dict:
            with tempfile.TemporaryDirectory() as temp:
                home = Path(temp)
                for name, rows in rollouts.items():
                    target = home / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(
                        "".join(json.dumps(r) + "\n" for r in rows),
                        encoding="utf-8")
                module.CODEX_HOME = home
                return module.census()

        def meta(base, source="cli", cli="0.146.0"):
            return {"type": "session_meta",
                    "payload": {"base_instructions": base, "cli_version": cli,
                                "source": source, "timestamp": "2026-07-31T00:00:00Z"}}

        prompt = "## Autonomy and persistence\nyou preserve them, ignore unrelated edits\n"

        # Nested and flat stores are one population; the flat one is what the
        # first version never globbed.
        both = run({"sessions/2026/07/31/rollout-a.jsonl": [meta({"text": prompt})],
                    "archived_sessions/rollout-b.jsonl":
                        [meta({"text": prompt}, source="{'subagent': {}}")]})
        self.assertEqual((both["discovered"], both["parsed"]), (2, 2))
        self.assertEqual(both["stores"],
                         {"sessions": 1, "archived_sessions": 1})
        self.assertEqual(sorted(both["coverage"]), ["subagent", "top-level"])
        self.assertTrue(both["supports_a_deletion_decision"])

        # Format drift: a bare string is read, anything else is a named skip.
        drift = run({"sessions/rollout-a.jsonl": [meta(prompt)],
                     "sessions/rollout-b.jsonl": [meta({"body": prompt})],
                     "sessions/rollout-c.jsonl": [{"type": "event_msg"}]})
        self.assertEqual(drift["discovered"], 3)
        self.assertEqual(drift["parsed"], 1, "a bare string must still parse")
        self.assertEqual(drift["skipped"],
                         {"unsupported_base_instructions": 1,
                          "no_session_meta": 1})
        self.assertFalse(drift["supports_a_deletion_decision"])
        self.assertTrue(drift["unresolved"])

        # An empty store answers nothing, and must not answer "fully covered".
        empty = run({})
        self.assertEqual((empty["discovered"], empty["parsed"]), (0, 0))
        self.assertFalse(empty["supports_a_deletion_decision"])

        # Circular evidence: our own contract inside the host prompt would mean
        # the census is grading us against ourselves.
        circular = run({"sessions/rollout-a.jsonl":
                        [meta({"text": prompt + "\n# Global Working Contract\n"})]})
        self.assertEqual(circular["our_markers_leaked_into_host_prompt"],
                         ["Global Working Contract"])
        self.assertFalse(circular["supports_a_deletion_decision"])

    def test_the_authority_sentence_is_kept_on_purpose(self) -> None:
        """The one clause whose deletion the audit considered and declined.

        Unlike the three above, "# Destructive Actions" *is* in the subagent
        prompt (73/77), so this sentence really is a restatement. It stays
        anyway, because the failure directions are not symmetric: if the vendor
        drops that section, an over-cautious Codex is recoverable and one
        acting destructively without authority is not. A safety clause is not
        worth ~35 words of savings when the tail risk has that shape.
        """
        policy = read(".codex/AGENTS.contract.md")
        self.assertIn("require explicit authority", policy)


class CodexBundleTests(unittest.TestCase):
    def test_agents_md_mirrors_the_main_only_boundary(self) -> None:
        agents = read(".codex/AGENTS.contract.md")
        for phrase in (
            "Main task only — orchestration",
            "Direct execution is the default",
            "not request bullets",
            "one unknown bug's diagnosis",
            "Collect the finished subagent response",
            "hard boundary",
            "### Independent verifier",
            "Subagents use their own role contract",
            "Report only outcome",
            # Same progressive-disclosure rule as baton-dispatch on the Claude
            # side: the contract's cost test resolves the common case by itself.
            "Once a dispatch is going ahead, load the `leaf-dispatch` skill",
        ):
            self.assertIn(phrase, agents)
        self.assertNotIn("Discovery → Plan → Approval", agents)

    def test_dispatch_skill_metadata_triggers_only_after_the_decision(self) -> None:
        """Both providers pay the body only once a dispatch is going ahead.

        Skill metadata is resident on every turn; the body is not. That trade
        only pays if the description does not fire on "should I delegate?" —
        the question the resident contract answers by itself, usually with
        "no". The Codex description used to say both things at once (`Load
        before every leaf dispatch decision`, with 「要不要派」 as a trigger)
        while its own body and contract said the decision comes first, so
        asking whether to delegate loaded a ~1000-word file to decide not to.
        """
        for path in (".claude/skills/baton-dispatch/SKILL.md",
                     ".codex/skills/leaf-dispatch/SKILL.md"):
            meta = frontmatter(path)
            self.assertIn("Load once a dispatch is going ahead", meta, path)
            for pre_decision in ("before every leaf dispatch decision",
                                 "任何 leaf 派工前", "要不要派", "Mandatory"):
                self.assertNotIn(pre_decision, meta, path)

    def test_codex_dispatch_detail_lives_in_leaf_dispatch_skill(self) -> None:
        skill = " ".join(read(".codex/skills/leaf-dispatch/SKILL.md").split())
        self.assertIn("dispatch_id=<id>", skill)
        for phrase in (
            "request_source=codex",
            "[LEAF_DISPATCH]",
            "[LEAF_RESULT]",
            "false-completion frauds",
            "3 failed fix-verify",
            "fruitless lookups",
            "provenance-labelled direct quote",
            "at most one outcome verifier per top-level task",
            "smallest coherent integration boundary",
        ):
            self.assertIn(phrase, skill)
        # Detail moved out of the resident contract stays out.
        agents = read(".codex/AGENTS.contract.md")
        self.assertNotIn("false-completion frauds", agents)
        self.assertNotIn("3 failed fix-verify cycles", agents)

    def test_codex_bundle_avoids_claude_routing_vocabulary(self) -> None:
        # The Codex contract must not carry Claude-specific model routing.
        lowered = read(".codex/AGENTS.contract.md").lower()
        for forbidden in ("fable", "opus", "dispatch gpt +", "dispatch claude"):
            self.assertNotIn(forbidden, lowered)
        # The ownership invariant must stay resident; the routing detail that
        # states it may live in either the contract or the on-demand skill, so
        # assert the union — otherwise moving a line between them reads as
        # deleting it.
        self.assertIn("The user owns the Codex GPT model", read(".codex/AGENTS.contract.md"))
        self.assertIn("reserving the strongest route/high",
                      read(".codex/AGENTS.contract.md")
                      + read(".codex/skills/leaf-dispatch/SKILL.md"))

    def test_no_deployed_prose_pins_a_model_version(self) -> None:
        """Concrete model versions belong to the resolver, not to prose.

        This clause used to read "reserving GPT-5.6 Sol/high", and the version
        was pinned here as well, so the tree carried the same number in two
        places and neither would notice the model moving. Worse, an s11 run on
        2026-08-09 measured the cost of a stale one: five of fifteen replies
        named GPT-5.4 while the routing table said gpt-5.6, because the file
        holding the correct id was never loaded. Prose that names a version is
        a second truth source with no way to be checked against the first.

        `model-routing.toml` and the tests that assert against it are exempt by
        construction: they *are* the routing truth, and a routing table without
        model ids would resolve nothing.
        """
        version = re.compile(r"\b(?:gpt|claude|opus|sonnet|fable)[-\s]?\d+\.\d+",
                             re.IGNORECASE)
        surfaces = [
            ".claude/CLAUDE.contract.md", ".codex/AGENTS.contract.md",
            ".codex/skills/leaf-dispatch/SKILL.md",
            ".claude/skills/baton-dispatch/SKILL.md",
            ".claude/skills/provider-routing/SKILL.md",
        ]
        for path in surfaces:
            with self.subTest(path=path):
                found = version.findall(read(path))
                self.assertEqual(
                    found, [],
                    f"{path}: names a model version in prose ({found}); let the "
                    "resolver answer that, so there is one truth source rather "
                    "than two that can disagree silently")

    def test_config_merge_and_verifier_are_leaf_bounded(self) -> None:
        config = tomllib.loads(read(".codex/config.merge.toml"))
        self.assertEqual(config["agents"]["max_depth"], 1)
        self.assertEqual(config["agents"]["max_threads"], 4)
        self.assertEqual(
            config["agents"]["verifier"]["config_file"], "./agents/verifier.toml"
        )
        verifier = tomllib.loads(read(".codex/agents/verifier.toml"))
        self.assertEqual(verifier["sandbox_mode"], "read-only")
        # Codex role files stay reusable; the per-dispatch resolver passes effort.
        self.assertNotIn("model_reasoning_effort", verifier)
        self.assertIn("routine low-risk work", verifier["description"])

    def test_every_leaf_role_has_a_codex_counterpart(self) -> None:
        # Claude role -> codex agent file (same lowercase spelling since the
        # 2026-07-23 rename).
        counterparts = {
            "explore": "explore",
            "plan-verifier": "plan-verifier",
            "security-reviewer": "security-reviewer",
            "mech-executor": "mech-executor",
            "executor": "executor",
            "verifier": "verifier",
            "security-executor": "security-executor",
        }
        config = tomllib.loads(read(".codex/config.merge.toml"))
        read_only = NO_WRITE_ROLES
        for claude_role, codex_name in counterparts.items():
            path = f".codex/agents/{codex_name}.toml"
            agent = tomllib.loads(read(path))
            self.assertEqual(agent["name"], codex_name, path)
            # Routing profiles are selected per dispatch; role files stay reusable.
            self.assertNotIn("model", agent, path)
            self.assertNotIn("model_reasoning_effort", agent, path)
            expected_sandbox = "read-only" if codex_name in read_only else "workspace-write"
            self.assertEqual(agent["sandbox_mode"], expected_sandbox, path)
            self.assertRegex(agent["developer_instructions"].lower(), r"(never|do not) delegate", path)
            # Same ungameable unit as the Claude twin's body budget: a role
            # that outgrows it on one provider only would drift silently.
            self.assertLessEqual(
                word_count(agent["developer_instructions"]), ROLE_BODY_BUDGET, path)
            self.assertEqual(
                config["agents"][codex_name]["config_file"],
                f"./agents/{codex_name}.toml",
                codex_name,
            )

    def test_model_routing_profiles_are_complete_and_dispatchable(self) -> None:
        routing = tomllib.loads(read(".codex/model-routing.toml"))
        self.assertEqual(routing["version"], 3)
        self.assertEqual(
            routing["selection"],
            {
                "default": "balanced",
                "fast": "fast",
                "quality_guarded": "quality_guarded",
                "high_risk": "quality_guarded",
            },
        )
        self.assertEqual(
            set(routing["profiles"]),
            {"balanced", "fast", "quality_guarded"},
        )
        self.assertEqual(routing["revision_policy"], {
            "days": 90,
            "min_samples": 10,
            "half_life_days": 45.0,
            "prefer_probability": 0.90,
            "cohort_fields": ["role", "task_class"],
            "excluded_task_classes": ["smoke", "other"],
        })
        self.assertEqual(
            routing["revision_policy"],
            tomllib.loads(read(".claude/model-routing.toml"))["revision_policy"],
        )
        required_roles = {"main", *CODEX_ROLES}
        role_tiers = routing["quality_floor"]["roles"]
        application = routing["route_application"]["roles"]
        approved = routing["quality_floor"]["approved_routes"]
        self.assertEqual(set(role_tiers), required_roles)
        self.assertEqual(set(application), required_roles)
        self.assertEqual(application["main"], "session_start_recommendation")
        for role in CODEX_ROLES:
            self.assertEqual(application[role], "dispatch_override", role)
        for profile_name, profile in routing["profiles"].items():
            self.assertEqual(set(profile["roles"]), required_roles, profile_name)
            for role, route in profile["roles"].items():
                model = routing["models"][route["model"]]
                delivery = model["availability"]["native_leaf_override"]
                self.assertIn(delivery, {"spawn_argument", "agent_config"})
                if role != "main" and delivery == "agent_config":
                    self.assertIn("agent_type", route, f"{profile_name}/{role}")
                self.assertIn(route["effort"], model["efforts"], f"{profile_name}/{role}")
                self.assertIn(
                    f"{route['model']}/{route['effort']}",
                    approved[role_tiers[role]],
                    f"{profile_name}/{role} falls below its quality floor",
                )
                self.assertTrue(route["reason"], f"{profile_name}/{role}")
                self.assertNotEqual(route["model"], "gpt-5.6-luna")

        luna_availability = routing["models"]["gpt-5.6-luna"]["availability"]
        self.assertEqual(
            luna_availability,
            {
                "subscription": "documented",
                "main_selector": "documented",
                "native_leaf_override": "agent_config",
                "claude_bridge_override": "configured",
            },
        )
        self.assertIn("smoke-tested", routing["models"]["gpt-5.6-luna"]["evidence"]["native_leaf"])
        self.assertIn("smoke-tested", routing["models"]["gpt-5.6-luna"]["evidence"]["claude_bridge"])
        self.assertNotIn("surface_overrides", routing)
        for model in routing["models"].values():
            self.assertEqual(
                set(model["efforts"]), {"low", "medium", "high", "xhigh", "max"}
            )
        self.assertAlmostEqual(
            routing["models"]["gpt-5.6-terra"]["efforts"]["max"]
            ["cost_usd_per_index_task"],
            0.508,
        )
        self.assertAlmostEqual(
            routing["models"]["gpt-5.6-sol"]["efforts"]["high"]
            ["output_tokens_per_index_task"],
            7545.3,
        )

    def test_model_routing_cli_validates_and_resolves_quality_first_priority(self) -> None:
        script = ROOT / "main/codex/scripts/model-routing"
        self.assertTrue(os.access(script, os.X_OK))
        validated = subprocess.run(
            [str(script), "validate"], check=True, capture_output=True, text=True,
        )
        self.assertIn("valid: 3 profiles", validated.stdout)
        resolved = subprocess.run(
            [str(script), "resolve", "--priority", "fast",
             "--role", "executor"],
            check=True, capture_output=True, text=True,
        )
        route = json.loads(resolved.stdout)
        self.assertEqual(route["profile"], "fast")
        self.assertEqual(route["surface"], "native-leaf")
        self.assertEqual(route["application"], "dispatch_override")
        self.assertEqual(route["quality_tier"], "judgment")
        self.assertEqual(route["model"], "gpt-5.6-sol")
        self.assertEqual(route["effort"], "medium")
        high_risk = subprocess.run(
            [str(script), "resolve", "--priority", "high-risk",
             "--role", "executor"],
            check=True, capture_output=True, text=True,
        )
        high_risk_route = json.loads(high_risk.stdout)
        self.assertEqual(high_risk_route["profile"], "quality_guarded")
        fast_support = subprocess.run(
            [str(script), "resolve", "--priority", "fast",
             "--role", "explore"],
            check=True, capture_output=True, text=True,
        )
        fast_support_route = json.loads(fast_support.stdout)
        self.assertEqual(fast_support_route["model"], "gpt-5.6-terra")
        self.assertEqual(fast_support_route["effort"], "low")
        self.assertEqual(fast_support_route["invocation"], {
            "agent_type": "explore",
            "fork_turns": "none",
            "model_delivery": "spawn_argument",
            "pass_model_override": True,
        })
        guarded = subprocess.run(
            [str(script), "resolve", "--priority", "quality-guarded",
             "--role", "explore"],
            check=True, capture_output=True, text=True,
        )
        guarded_route = json.loads(guarded.stdout)
        self.assertEqual(guarded_route["profile"], "quality_guarded")
        self.assertEqual(guarded_route["model"], "gpt-5.6-sol")
        self.assertEqual(guarded_route["effort"], "low")

        bridge = subprocess.run(
            [str(script), "resolve", "--surface", "claude-bridge",
             "--priority", "fast", "--role", "explore"],
            check=True, capture_output=True, text=True,
        )
        bridge_route = json.loads(bridge.stdout)
        self.assertEqual(bridge_route["surface"], "claude-bridge")
        self.assertEqual(bridge_route["model"], "gpt-5.6-terra")
        self.assertEqual(bridge_route["effort"], "low")
        self.assertEqual(
            bridge_route["invocation"]["model_delivery"],
            "bridge_argument",
        )

        original = read(".codex/model-routing.toml")
        invalid = original.replace(
            '[profiles.fast.roles.executor]\nmodel = "gpt-5.6-sol"',
            '[profiles.fast.roles.executor]\nmodel = "gpt-5.6-terra"',
            1,
        )
        self.assertNotEqual(invalid, original)
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_config = Path(temp_dir) / "model-routing.toml"
            invalid_config.write_text(invalid, encoding="utf-8")
            rejected = subprocess.run(
                [str(script), "--config", str(invalid_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("falls below quality tier judgment", rejected.stderr)

        slow_fast = original.replace(
            '[profiles.fast.roles.explore]\nmodel = "gpt-5.6-terra"',
            '[profiles.fast.roles.explore]\nmodel = "gpt-5.6-sol"',
            1,
        )
        self.assertNotEqual(slow_fast, original)
        with tempfile.TemporaryDirectory() as temp_dir:
            slow_config = Path(temp_dir) / "model-routing.toml"
            slow_config.write_text(slow_fast, encoding="utf-8")
            rejected_fast = subprocess.run(
                [str(script), "--config", str(slow_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(rejected_fast.returncode, 0)
        self.assertIn("is not optimal for decode_minutes_per_index_task",
                      rejected_fast.stderr)

        unavailable_bridge = original.replace(
            'claude_bridge_override = "configured"',
            'claude_bridge_override = "unverified"',
            1,
        )
        self.assertNotEqual(unavailable_bridge, original)
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_config = Path(temp_dir) / "model-routing.toml"
            bridge_config.write_text(unavailable_bridge, encoding="utf-8")
            rejected_bridge = subprocess.run(
                [str(script), "--config", str(bridge_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(rejected_bridge.returncode, 0)
        self.assertIn("uses model unavailable to claude-bridge",
                      rejected_bridge.stderr)

        with tempfile.TemporaryDirectory() as temp_dir:
            malformed_config = Path(temp_dir) / "model-routing.toml"
            malformed_config.write_text("[broken", encoding="utf-8")
            malformed = subprocess.run(
                [str(script), "--config", str(malformed_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertEqual(malformed.returncode, 2)
        self.assertIn("ERROR: cannot load routing config", malformed.stderr)
        self.assertNotIn("Traceback", malformed.stderr)

    def test_model_routing_bundle_is_documented_and_synced(self) -> None:
        readme = read(".codex/README.md")
        deploy = read(".codex/DEPLOY.md")
        managed = set(deployment_manifest())
        for artifact in ("model-routing.toml", "scripts/model-routing"):
            self.assertIn(artifact, readme)
            self.assertIn(artifact, deploy)
        self.assertIn(("main/codex/model-routing.toml", ".codex/model-routing.toml"), managed)
        self.assertIn(("main/codex/scripts", ".codex/scripts"), managed)
        agents = read(".codex/AGENTS.contract.md")
        # The resolver path is operational detail and lives wherever the
        # dispatch mechanics live; only the "routes do not switch a running
        # task" invariant has to be resident. Assert the union so relocating
        # the command does not read as dropping it.
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/scripts/model-routing",
                      agents + read(".codex/skills/leaf-dispatch/SKILL.md"))
        self.assertIn("session-start recommendations", agents)

    def test_codex_dispatch_reporting_matches_claude(self) -> None:
        agents = read(".codex/AGENTS.contract.md")
        self.assertIn("[LEAF_DISPATCH]", agents)
        self.assertIn("[LEAF_RESULT]", agents)
        self.assertIn("request_source=codex", agents)
        self.assertIn("Never brief a subagent to delegate further", agents)
        skill = read(".codex/skills/leaf-dispatch/SKILL.md")
        self.assertIn("ledger=<logged|skipped(reason)>", skill)
        self.assertIn("quality-check it against the brief", skill)

    def test_deploy_and_analysis_preserve_machine_state(self) -> None:
        deploy = read(".codex/DEPLOY.md")
        analysis = read(".codex/ANALYSIS.md")
        for phrase in (
            "## One-shot Codex command",
            # The rule is now enforced by merge-toml rather than by asking
            # a human to be careful, so assert the scope guarantee itself.
            "never replaces `config.toml`",
            "writes only `[agents]` and `[agents.*]`",
            "Credentials and login",
            "Authentication only",
            "Keep approval enabled",
        ):
            self.assertIn(phrase, deploy)
        self.assertNotIn("/Users/", deploy)
        self.assertIn("not automatic deployment", analysis)
        self.assertIn("Git is the cross-machine source of truth", analysis)


class AppPromptSurfaceTests(unittest.TestCase):
    def test_app_prompts_keep_surface_ownership_and_action_boundaries(self) -> None:
        claude_chat = read(".claude/prompts/claude-app-profile.md")
        cowork = read(".claude/prompts/cowork-global-instructions.md")
        chatgpt = read(".codex/prompts/custom-instructions.md")

        self.assertIn("Settings > Instructions for Claude", claude_chat)
        self.assertIn("Settings > Cowork > Global instructions", cowork)
        self.assertIn("Settings > Personalization > Custom instructions", chatgpt)
        self.assertIn("Applies to Chat and Work", chatgpt)
        self.assertIn("$CODEX_HOME/AGENTS.md", chatgpt)

        for prompt in (claude_chat, cowork, chatgpt):
            self.assertIn("explicit authority", prompt)
        self.assertIn("reopen each produced file", cowork)
        self.assertIn("reopen the outputs", chatgpt)
        self.assertIn("produced artifacts and where to find them", cowork)

    def test_app_prompt_sources_are_managed_without_replacing_codex_contract(self) -> None:
        managed = set(deployment_manifest())
        self.assertIn(("main/claude/prompts", ".claude/prompts"), managed)
        self.assertIn(("main/codex/prompts", ".codex/prompts"), managed)

        readme = read(".codex/README.md")
        analysis = read(".codex/ANALYSIS.md")
        deploy = read(".codex/DEPLOY.md")
        self.assertIn("ChatGPT Chat/Work", readme)
        self.assertIn("`AGENTS.contract.md`", readme)
        self.assertIn("ChatGPT Chat and Work", analysis)
        self.assertIn("ChatGPT Chat and Work Personalization", deploy)
        self.assertIn("Codex uses global `AGENTS.md` for personal instructions", deploy)


class DocumentationBudgetTests(unittest.TestCase):
    def test_prompt_surface_census_is_current(self) -> None:
        snapshot = ROOT / "docs/research/prompt-surface-census.json"
        command = [
            str(ROOT / "main/.agents/scripts/python3-run"),
            str(ROOT / "scripts/prompt-surface-census.py"),
            "--check",
            str(snapshot),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

        census = json.loads(snapshot.read_text(encoding="utf-8"))
        self.assertEqual(census["schema"], 1)
        self.assertEqual(set(census["providers"]), {"claude", "codex"})
        managed_sources = {source for source, _target in deployment_manifest()}
        self.assertNotIn("scripts/prompt-surface-census.py", managed_sources)
        for provider, skills_dir in (
            ("claude", "main/claude/skills"),
            ("codex", "main/codex/skills"),
        ):
            expected_skills = {
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / skills_dir).glob("*/SKILL.md")
            }
            provider_layers = census["providers"][provider]
            resident_metadata = {
                record["path"]
                for record in provider_layers["resident"]
                if record.get("kind") == "skill-metadata"
            }
            metadata_records = [
                record
                for record in provider_layers["resident"]
                if record.get("kind") == "skill-metadata"
            ]
            dispatch_bodies = {
                record["path"]
                for record in provider_layers["dispatch"]
                if record.get("kind") == "skill-body"
            }
            self.assertEqual(resident_metadata, expected_skills)
            self.assertEqual(dispatch_bodies, expected_skills)
            self.assertTrue(
                all(record["words"] > 5 for record in metadata_records),
                f"{provider} skill descriptions must be fully counted",
            )
        for provider in ("claude", "codex"):
            self.assertEqual(
                set(census["providers"][provider]),
                {"resident", "dispatch", "roles"},
            )
            self.assertEqual(
                len(census["providers"][provider]["roles"]), len(ROLES)
            )
            # The always-loaded half of every role. Measuring role bodies only
            # left this surface out of the census entirely, so the budget below
            # had nothing to cap (2026-08-01 review).
            self.assertEqual(
                len([record
                     for record in census["providers"][provider]["resident"]
                     if record.get("kind") == "role-metadata"]),
                len(ROLES),
                f"{provider} resident layer is missing role metadata",
            )
            for layer in ("resident", "dispatch", "roles"):
                total = census["totals"][provider][layer]
                self.assertGreater(total["bytes"], 0)
                self.assertGreater(total["words"], 0)
                self.assertRegex(total["payload_sha256"], r"^[0-9a-f]{64}$")

    def test_resident_skill_metadata_stays_within_budget(self) -> None:
        """Cap the resident layer at its real load unit, not at the snapshot.

        Every skill's name and description is loaded into every session, so a
        long description is a permanent per-session cost — the same cost the
        contract budgets above exist to control. The census measured it, but
        nothing capped it: a description could grow without limit and the suite
        stayed green as soon as someone regenerated the snapshot. So this reads
        the sources, not `prompt-surface-census.json`, and the resident total
        below is the contract budget plus this one.

        Role metadata is capped on the same argument and for a sharper reason.
        `contract-slimming.md` names role frontmatter as a *destination* for
        content moved out of the resident contract, but a role's name and
        description are listed in every session just like a skill's — so a
        clause moved there was still resident while every budget here went
        green. That is the one way this ratchet could be paid off rather than
        met, which is why it is asserted next to the budget it protects
        (2026-08-01 review).
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "prompt_surface_census", ROOT / "scripts/prompt-surface-census.py")
        census_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(census_module)
        census = census_module.build_census()

        # Per-provider sum of skill metadata, in the same CJK-aware words the
        # document budgets use. Raising either is a deliberate decision with a
        # reason, exactly like raising a document budget.
        # Claude carries one more skill than Codex (baton-dispatch and
        # provider-routing against the single leaf-dispatch).
        # Raised 620/540 -> 660/580 on 2026-08-17 for `evidence-debugging`,
        # measured at 62 resident words on each provider against 25 of headroom.
        # Sized to what was measured and nothing more, which is why the same day
        # raised it again: 660/580 -> 730/650 for `test-first-change`, measured
        # at 70 words on each provider. The second raise is the point of the
        # first one's restraint - a ceiling left for a body not yet written is a
        # budget granted on an estimate, and this description was measured
        # twice, at 61 and then 70, because comparing it against the plan's own
        # contract section found an exclusion missing from it. A number set
        # before that comparison would have been the one that stuck.
        # 730/650 -> 790/710 on 2026-08-17, measured at 787/707. Both new
        # skills state their triggers in zh-TW as well as English now, which cost
        # 37 and 25 words. The reason is a measurement, not a preference: across
        # five replay batches these two loaded in 5 of 30 runs, and they were the
        # only two deployed skills whose descriptions carried no Chinese at all -
        # speak-human-tw 121 characters of it, headroom-protocol 48,
        # experience-ledger 32, task-observer 15, these two zero - in a project
        # whose requests arrive in Chinese. speak-human-tw is 176 words wide for
        # exactly this reason and has been since it landed.
        #
        # Whether skill selection is lexical is a hypothesis, not something this
        # repo has established. `skills_invoked` moving off 0 of 5 on `e1` is what
        # would support it; nothing here assumes it in advance.
        metadata_budgets = {"claude": 790, "codex": 710}
        # The widest legitimate description today is speak-human-tw at 176: it
        # states its triggers twice, in zh-TW and English, because it is the
        # one skill invoked by users in either language.
        per_skill_budget = 180
        for provider, budget in metadata_budgets.items():
            records = [record
                       for record in census["providers"][provider]["resident"]
                       if record.get("kind") == "skill-metadata"]
            self.assertTrue(records, provider)
            for record in records:
                self.assertLessEqual(
                    record["words"], per_skill_budget,
                    f"{record['path']}: resident skill metadata")
            self.assertLessEqual(
                sum(record["words"] for record in records), budget, provider)

        # Seven roles on each side. Claude spells them in agent frontmatter,
        # Codex in the `[agents.*]` registrations of config.merge.toml; both are
        # listed once per session. Measured today: Claude 136, Codex 61.
        role_metadata_budgets = {"claude": 140, "codex": 63}
        # The widest role line today is 21 words. A proportional ratchet on a
        # unit this small rounds to no slack at all, which would make an
        # ordinary wording fix fail the suite; 24 is the smallest cap that still
        # refuses a moved paragraph.
        per_role_budget = 24
        for provider, budget in role_metadata_budgets.items():
            records = [record
                       for record in census["providers"][provider]["resident"]
                       if record.get("kind") == "role-metadata"]
            self.assertEqual(len(records), len(ROLES), provider)
            for record in records:
                self.assertLessEqual(
                    record["words"], per_role_budget,
                    f"{record['path']}: resident role metadata")
            self.assertLessEqual(
                sum(record["words"] for record in records), budget, provider)

        # The word caps above bound attention; they do not bound length. A
        # description made of long runs satisfies every one of them and is
        # still tens of kilobytes resident - the same hole the whole-file
        # ceiling closed for budgeted documents, still open on the metadata
        # records because those are not files (2026-08-03 review). Applied per
        # record, to both kinds, since the census already measures both.
        for provider in RESIDENT_CONTRACT_BUDGETS:
            for record in census["providers"][provider]["resident"]:
                if record.get("kind") not in ("skill-metadata", "role-metadata"):
                    continue
                ratio = record["bytes"] / record["words"]
                self.assertLessEqual(
                    ratio, MAX_BYTES_PER_WORD,
                    f"{record['path']}: {ratio:.1f} bytes per resident word; "
                    "the words are not what this description actually costs")

        for provider, budget in RESIDENT_CONTRACT_BUDGETS.items():
            self.assertLessEqual(
                census["totals"][provider]["resident"]["words"],
                budget.words + metadata_budgets[provider]
                + role_metadata_budgets[provider],
                f"{provider} resident layer "
                f"({budget.path} plus skill and role metadata)")

    def test_resident_contracts_stay_dense(self) -> None:
        """What the word ceilings above cannot see: what the words bought.

        A contract can pass its word cap while padding every rule, while
        shredding one rule into six bullets, or while compressing until the
        prose no longer carries a subject. Each of those moves one of these
        three figures, and the caps come from the 2026-08-04 measurement of
        these same files, so nothing here tightens the state that shipped.

        Scope, so this is not read as more than it is: these are file-level
        aggregates. The 540/540 defect that motivated them was ten words in one
        clause and moved the filler ratio by about 0.005 - below anything a file
        aggregate can resolve. That class of change is caught per commit by
        `scripts/contract-operator-delta.py`, which reports operator deltas for
        a human to read. This test catches the sustained version: a document
        that drifts padded, shredded, or telegraphic over many edits.
        """
        for provider, budget in RESIDENT_CONTRACT_BUDGETS.items():
            text = read(budget.path)
            rules = len(rule_units(text))
            self.assertLessEqual(
                rules, budget.rules,
                f"{budget.path}: {rules} rules; each one dilutes the rest, so "
                "adding one is a decision to make here, not in the file")
            density = bytes_per_rule(text)
            self.assertLessEqual(
                density, budget.bytes_per_rule,
                f"{budget.path}: {density:.1f} bytes per rule")
            filler = filler_ratio(text)
            self.assertLessEqual(
                filler, budget.filler_cap,
                f"{budget.path}: {filler:.3f} of its English words carry no "
                "obligation")
            # The floor is the only guard pointing the other way. Every other
            # budget in this file rewards deletion, and past some point deletion
            # stops removing padding and starts removing grammar.
            self.assertGreaterEqual(
                filler, budget.filler_floor,
                f"{budget.path}: {filler:.3f} filler is below the floor - check "
                "that the compression left the sentences their subjects")

    def test_project_scoped_skills_pay_the_same_resident_ceiling(self) -> None:
        """The ratchet covered the deployed tier; one skill sat just outside it.

        `.claude/skills/harness-review` is a tracked symlink to the repo-root
        dev-only skill, so its name and description are resident in every
        session opened in *this* checkout - the one the maintainer opens most.
        The census enumerates `main/{claude,codex}/skills` and the budget above
        binds itself to `deployed_skill_files()`, so nothing measured it and
        nothing would have said a word as it grew (2026-08-02 review).

        Deliberately not folded into the census: the census answers "what does
        this repo ship", and this skill ships nowhere. It gets the same
        per-skill ceiling instead, which is the part that was missing - a limit,
        not a line item.
        """
        roots = sorted((ROOT / ".claude/skills").glob("*/SKILL.md"))
        self.assertTrue(roots, "no project-scoped skill found to budget")
        per_skill_budget = 180  # same ceiling as a deployed skill's metadata
        for path in roots:
            # Read literally: `read()` rewrites a `.claude/` prefix to the
            # deployable `main/claude/` source, and this skill has none.
            fields = path.read_text(encoding="utf-8").split("---", 2)[1]
            words = word_count(fields)
            self.assertLessEqual(
                words, per_skill_budget,
                f"{path.relative_to(ROOT)}: resident metadata is {words} words")
            # Words alone let 180 words of 200-character runs through at
            # ~34 KB. This skill is outside the census, so the ceilings the
            # census records get have to be applied here directly
            # (2026-08-03 review).
            ratio = len(fields.encode("utf-8")) / words
            self.assertLessEqual(
                ratio, MAX_BYTES_PER_WORD,
                f"{path.relative_to(ROOT)}: {ratio:.1f} bytes per resident word")
            longest = max(re.findall(r"\S+", fields), key=len)
            self.assertLessEqual(
                len(longest), MAX_UNBROKEN_RUN,
                f"{path.relative_to(ROOT)}: {len(longest)}-character unbroken run")
            # Resident cost buys routing, so it has to still describe when the
            # skill does *not* apply - the half a description usually loses first.
            self.assertIn("Do not use", fields, str(path.relative_to(ROOT)))

    def test_the_widest_description_keeps_every_trigger_it_pays_for(self) -> None:
        """A description is resident cost *and* the only routing surface.

        speak-human-tw is the largest always-resident description in the repo,
        which makes it the standing trim candidate — and trimming it is the one
        edit whose damage no test here can see, because whether a skill loads is
        decided by a model reading this text, not by anything mechanical.

        Written before any trim, deliberately (2026-07-30). A trim was measured
        and then dropped: the honest saving was 19 words, ~2% of the resident
        tier, against a recall risk nothing could measure at the time. So the
        lock landed first and the description was left alone until it is
        actually near its ceiling.

        `evals/traps/s10-skill-recall` was built afterwards to close that gap
        and carries the dropped trim as its arm-B surface. It is still a
        model-in-the-loop eval, not a check this suite can run: these
        assertions are the cheap layer, the trap is the expensive one, and
        neither replaces the other.

        Word budgets push one way and recall pushes the other. Both are
        asserted, so whenever a trim does happen it has to come out of genuine
        duplication rather than out of the tokens that make the skill load.
        """
        frontmatter_text = frontmatter(".agents/skills/speak-human-tw/SKILL.md")
        # Every phrasing a user is expected to invoke it by, in both languages.
        for trigger in ("去 AI 味", "說人話", "這段好 AI", "改自然一點",
                        "校對再發", "審查", "改寫",
                        "de-AI this text", "make it sound human",
                        "polish this zh-TW copy before publishing"):
            self.assertIn(trigger, frontmatter_text, f"lost trigger: {trigger}")
        # The document kinds are the recall surface for "look at this <thing>"
        # phrasings; dropping one silently stops the skill matching that ask.
        for kind in ("電子報", "社群貼文", "銷售頁", "文案", "客服信",
                     "簡報", "公告"):
            self.assertIn(kind, frontmatter_text, f"lost document kind: {kind}")
        # Exclusions are what stop it loading on work it would damage.
        for exclusion in ("逐字翻譯", "品牌", "事實查核", "設定檔",
                          "literal translation", "brand-voice mimicry",
                          "fact-checking", "code/log/config"):
            self.assertIn(exclusion, frontmatter_text,
                          f"lost exclusion: {exclusion}")

    def test_deployed_prose_stays_distilled(self) -> None:
        # Word budgets, not line budgets — a line count is gameable by long
        # lines; words track attention cost. Raising a budget is a deliberate
        # decision, not a mechanical bump.
        # Units are word_count() words: one per CJK character, one per other
        # non-space run — zh-TW prose pays the same attention tax as English.
        #
        # Scope narrowed 2026-08-08, from every markdown file to the fifteen the
        # manifest ships. A word ceiling is an instrument for *push* cost: bytes
        # a session pays for whether or not anyone wanted them, on every turn
        # (the two contracts) or on every dispatch (the skills). `docs/` is
        # *pull* cost — paid once, by a reader who asked, who can stop. The
        # dropped nineteen were never the expensive layer: none of them deploys,
        # and the manifest ships nothing under `docs/` at all.
        #
        # The 2026-08-07 comment that extended the ratchet to `docs/research/`
        # argued coverage symmetry (the unmeasured tier outweighed the measured
        # one), which is an argument about measurement, not about attention. It
        # bought a real cost: recording upstream evidence on 2026-08-08 required
        # three ceiling raises and three justification comments before the
        # evidence could land. Taxing the act of writing down what we learned is
        # the wrong place to spend a guardrail. Sprawl in the human tree is now
        # a report plus an order-of-magnitude guard, both below.
        #
        # The dropped entries' rationale is not lost; it is in git, attached to
        # the changes it explains. What it is no longer doing is gating a commit.
        budgets = {
            ".claude/CLAUDE.contract.md": RESIDENT_CONTRACT_BUDGETS["claude"].words,
            # -50 (2026-07-26): route resolution, priority selection, and
            # unavailability reporting moved to the on-demand `leaf-dispatch`,
            # where the invocation mechanics already lived. The ceiling drops
            # with the content — leaving it at 590 would just invite a refill,
            # and this file sat 2 words under it.
            ".codex/AGENTS.contract.md": RESIDENT_CONTRACT_BUDGETS["codex"].words,
            ".codex/ANALYSIS.md": 500,
            ".codex/DEPLOY.md": 550,
            # +90 (2026-07-23): record template and QC fraud checklist moved
            # in from the resident contract / provider-routing (net resident
            # payload down; skill is mandatory before every dispatch).
            # +150 (2026-07-28): v1.3.4 readiness-unit schema, security review
            # sequencing, and live-discovery ownership. These remain on-demand;
            # the census records their cost instead of charging resident turns.
            # +45 (2026-08-04): the five-pass verification cap and the
            # unchanged-candidate rule. The ledger has one local four-pass
            # fix-verify chain (four verifier dispatches on one target inside
            # 4.5 hours, 2026-07-28), so the cap sits above observed legitimate
            # work rather than being borrowed from an upstream number.
            # +22 (2026-08-04): net, after displacement. The cap above landed
            # as a bare "five" one paragraph away from a bare "one", over
            # different units, and a reader could only guess whether five
            # passes meant permission to spend the quota five times. Stating
            # the relation cost 40 words; tightening the paragraph returned 9
            # and merging the duplicated trigger-ownership sentence in the same
            # section returned another 9.
            ".claude/skills/baton-dispatch/SKILL.md": 1197,
            # QC mechanics and fixed records belong to baton-dispatch; keep
            # provider-routing focused on route, fallback, and eligibility.
            ".claude/skills/provider-routing/SKILL.md": 1300,
            # +45 (2026-07-25): invocation mechanics (fork_turns, spawn_argument
            # vs agent_config) moved out of the always-resident Codex contract
            # into this on-demand skill. The resident side of that trade is
            # visible above: AGENTS.contract.md model-ownership dropped ~23
            # words while staying under its own ceiling.
            # +85 (2026-07-26): the receiving side of the trade above. Paid
            # once per dispatch instead of once per task.
            # +160 (2026-07-28): Claude-twin readiness, security sequencing,
            # and discovery ownership; still paid only when dispatch proceeds.
            # +65 (2026-07-30): the ledger section now has to say how a native
            # Codex dispatch stages its own launch and completion. Claude gets
            # that from a hook and pays nothing for it here; on Codex it is the
            # dispatcher's step, so the instruction has to reach the dispatcher.
            # +25 (2026-08-04): the Claude twin of the verification cap. A cap
            # only one provider honours is the asymmetry these budgets exist to
            # expose, so both sides carry the identical sentence.
            # +23 (2026-08-04): net, the twin of the baton-dispatch entry
            # above. The same 40-word relation, the same 9-word tightening, and
            # 6 more from the "same surface" clause this section already stated
            # once. Measured size moved 1098 -> 1123; the file had been sitting
            # two words under its ceiling rather than on it.
            ".codex/skills/leaf-dispatch/SKILL.md": 1123,
            # The four below were unbudgeted until 2026-07-30: the ceiling
            # existed on the three files someone had remembered, not on the
            # tier, so the largest dispatch-time surface in the repo
            # (speak-human-tw) had no limit at all. Each is set at its measured
            # size plus ~2%, which is what the three above already are (100%,
            # 99%, 98% used). The number is not a researched threshold — the
            # repo's own sources say none is derivable
            # (docs/research/context-and-vendors.md) — it is a ratchet: growth
            # has to displace something or be argued for in the commit message.
            #
            # experience-ledger and speak-human-tw are one source each, shared
            # by both providers through a symlink; both deployed surfaces are
            # listed because both are what a session actually loads.
            ".claude/skills/experience-ledger/SKILL.md": 980,
            ".codex/skills/experience-ledger/SKILL.md": 980,
            # Largest dispatch-time body in the repo, and the one that states
            # its triggers twice (zh-TW and English) because either language
            # can invoke it. Trimming it is deliberately a separate task.
            ".claude/skills/speak-human-tw/SKILL.md": 2090,
            ".codex/skills/speak-human-tw/SKILL.md": 2090,
            # Claude's copies are thin pointers; Codex carries the procedure,
            # so the two sides of these two skills are genuinely different
            # files and get their own ceilings rather than a shared one.
            ".claude/skills/headroom-protocol/SKILL.md": 135,
            ".codex/skills/headroom-protocol/SKILL.md": 235,
            ".claude/skills/task-observer/SKILL.md": 145,
            ".codex/skills/task-observer/SKILL.md": 770,
            # One source, symlinked to both providers: the plan forbids a wrapper
            # fork without refutable runtime evidence that the two sides need
            # different semantics, and there is none.
            #
            # 932 was set from "measured 914", and the file is 929 - so the
            # ceiling delivered 0.3% instead of the ~2% the comment above claims
            # for this tier, and said in writing that it had. Corrected 2026-08-17
            # to the real measurement, 929 + ~2%. The 914 was taken mid-edit and
            # never re-read; a number recorded next to what it measured is only
            # worth anything if it can be recomputed from the file, which this one
            # could not. Not a refill: nothing needed to fit.
            # 947 -> 984 and 931 -> 955 on 2026-08-17: the bilingual trigger
            # lists are in the frontmatter, and these ceilings cover the whole
            # deployed file. Measured 965 and 937 + ~2%, the same rule as the
            # tier above. The resident half of that cost is priced separately
            # in `metadata_budgets`, where the reason is recorded.
            ".claude/skills/evidence-debugging/SKILL.md": 984,
            ".codex/skills/evidence-debugging/SKILL.md": 984,
            # Same single source, same reasoning. Measured 913 + ~2%. Its worked
            # examples are not in here: upstream `tdd` is 38 lines of index whose
            # substance lives in two TypeScript references, and the replacements
            # are written in this repo's own languages, which makes them local
            # content. They live in `references/tuning.md`.
            # 955 -> 991 on 2026-08-17: upstream's vertical-slicing rule was
            # restored. Only its negative half had survived the first pass, and
            # re-fetching the pinned `tdd` showed the positive rule - one check,
            # one implementation, each a tracer bullet - had been dropped without
            # anyone recording it. Measured 971 + ~2%.
            ".claude/skills/test-first-change/SKILL.md": 991,
            ".codex/skills/test-first-change/SKILL.md": 991,
        }
        self.assertEqual(
            {path for path in budgets if "/skills/" in path},
            deployed_skill_files(),
            "every deployed skill is budgeted or the ceiling is back to being "
            "whatever someone remembered to list")
        # The scope rule, asserted rather than trusted to the reader. Without it
        # the dict drifts back to covering whatever someone remembered to list,
        # which is how a bundle file that ships nowhere
        # (`main/claude/plans/orchestration-plan.md`) came to carry a ceiling
        # that gated commits for two weeks.
        for path in budgets:
            self.assertTrue(
                is_deployed(path),
                f"{path}: budgeted but the manifest does not ship it, so no "
                "session pays for it; budgets bind on push cost only")
        for path, limit in budgets.items():
            self.assertLessEqual(word_count(read(path)), limit, path)

        # The word unit counts a run of non-space text as one word, so a single
        # unbroken run — a giant URL, a minified block, a pasted payload — costs
        # one budget unit no matter how much context it actually occupies. Cap
        # the run length so the budget cannot be evaded that way. The longest
        # legitimate run in these files today is a 106-character markdown link.
        for path in budgets:
            longest = max(re.findall(r"\S+", read(path)), key=len)
            self.assertLessEqual(
                len(longest), MAX_UNBROKEN_RUN,
                f"{path}: {len(longest)}-character unbroken run evades the word "
                f"budget; break it up or link to it: {longest[:80]}")

        # Capping one run is not capping the file: many legal runs evade the
        # word budget just as well as one illegal one. A 520-word file of
        # 200-character runs satisfies both ceilings above at 104 KB, so the
        # ratchet also has to bound what a word is allowed to cost.
        for path, limit in budgets.items():
            text = read(path)
            words = word_count(text)
            ratio = len(text.encode("utf-8")) / words
            self.assertLessEqual(
                ratio, MAX_BYTES_PER_WORD,
                f"{path}: {ratio:.1f} bytes per word against a {limit}-word "
                "budget; the words are not what this file actually costs")

    def test_the_human_tree_has_a_sprawl_guard_not_a_budget(self) -> None:
        # Deliberately not a budget. No per-file ceiling, no raise per edit, no
        # justification comment for ordinary growth: `docs/` is pull cost, and
        # a reader who opens a long document chose to. What this catches is the
        # one failure a reader cannot choose their way out of — a document that
        # has stopped being a document — and it sits an order of magnitude
        # above anything the tree has ever held (largest today:
        # docs/research/model-evidence.md, ~6.9K words).
        #
        # The shape is borrowed from MAX_BYTES_PER_WORD, whose own comment says
        # a guard like this "must never become a second, tighter word budget".
        # If a file approaches this number the answer is to split it or move
        # content to its real owner, never to raise the constant. Sizes are
        # reported, not asserted, by `scripts/docs-size-report.py`.
        for path in sorted((ROOT / "docs").rglob("*.md")):
            relative = path.relative_to(ROOT).as_posix()
            words = word_count(path.read_text(encoding="utf-8"))
            self.assertLess(
                words, DOC_SPRAWL_CEILING,
                f"{relative}: {words} words. This is not a budget overrun, it "
                "is a document that outgrew its single responsibility - split "
                "it or move sections to the doc that owns them")

    def test_human_docs_stay_half_width(self) -> None:
        """The sweep was a commit; without this it is not a rule.

        `docs/README.md` rule 7 says new prose is written half-width, and the
        2026-08-04 pass converted the tree. Nine `、` survived it in a file
        written on a branch that predated the sweep and merged after it, which
        is how every future regression will arrive - not from anyone disagreeing
        with the rule (2026-08-04 review).

        Scoped to human-facing docs, where the rule has no exceptions. All five
        exempt categories live outside this glob - verbatim external quotes,
        `speak-human-tw` material, `evals/traps/**` fixtures, skill
        descriptions and user-facing templates, and full-width literals used as
        match data - so a failure here is drift and never a false positive.
        Quotes and dashes are excluded because they have no half-width form,
        which is rule 7's own carve-out.

        Tracked files only, and the sentence above about false positives is why.
        On 2026-08-17 an untracked note at the repo root turned this red — full
        width throughout, and correctly so, because it was nobody's deliverable
        and this rule is about what ships. A guard that fires on a scratch file
        in a dirty worktree teaches people to ignore it. `git ls-files` is the
        same boundary `scripts/evidence-check.py` already uses, and anything
        committed enters the scope on the same commit that adds it.
        """
        convertible = "，。、：；？！（）％＃＆＊＋－／＜＝＞＠［＼］＾＿｀｛｜｝"
        tracked = {
            (ROOT / name).resolve()
            for name in git("ls-files", "*.md").stdout.split()}
        offenders = {}
        for path in sorted(ROOT.glob("docs/**/*.md")) + sorted(ROOT.glob("*.md")):
            if path.resolve() not in tracked:
                continue
            marks = sorted({character
                            for character in path.read_text(encoding="utf-8")
                            if character in convertible})
            if marks:
                offenders[str(path.relative_to(ROOT))] = marks
        self.assertEqual(
            offenders, {},
            "full-width punctuation that has a half-width form (docs/README.md "
            "rule 7); convert it and put a space after the mark")

    def test_root_readme_is_a_complete_navigation_surface(self) -> None:
        readme = read("README.md")
        self.assertEqual(readme.count("```mermaid"), 2)
        for phrase in (
            "配置與部署拓撲",
            "派工與資料回饋迴路",
            "Main 與七個 leaf roles",
            "Role, task class 與 scenario 分離",
            "Routing 語意",
            "結構化派工回報",
            "機制與護欄",
            "管理邊界",
            "docs/README.md",
        ):
            self.assertIn(phrase, readme)

    def test_documentation_navigation_links_resolve_locally(self) -> None:
        paths = [
            "README.md", "docs/README.md", "main/claude/README.md",
            "main/codex/README.md", "main/.agents/README.md",
        ]
        missing = []
        for path in paths:
            base = (ROOT / path).parent
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", read(path)):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                local = target.split("#", 1)[0]
                if local and not (base / local).resolve().exists():
                    missing.append(f"{path}: {target}")
        self.assertEqual(missing, [])

    def test_every_tracked_document_links_somewhere_that_exists(self) -> None:
        """The test above reads five README files. Nothing read the other 143.

        Found on 2026-08-17 by checking M4's "documentation links resolve" item
        by hand instead of reading it off a green suite: two links written the
        same day, in the two new skills' tuning files, were off by one directory
        level and no test looked at either file. The narrow test was not wrong -
        it guards the navigation surface it names - it was just being read as
        cover for every document.

        Anchors are checked too, because a renamed heading kills a deep link
        silently and this repo uses them (the plan and research docs link into
        each other's sections). The slug rule is calibrated against the 40
        anchors currently in this tree, English and CJK - it is not GitHub's
        algorithm and should not be described as one, so a heading using
        punctuation this repo has not used yet could produce a false red. On any
        mismatch the message prints the headings it computed, which makes that
        case one glance to tell apart from a real break.
        """
        link = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(#[^)\s]*)?\)")
        broken = []
        tracked = git("ls-files", "*.md").stdout.split()
        for name in tracked:
            path = ROOT / name
            for target, anchor in link.findall(path.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                dest = (path.parent / target).resolve()
                if not dest.exists():
                    broken.append(f"{name} -> {target}")
                    continue
                if not anchor or dest.suffix != ".md":
                    continue
                headings = {
                    re.sub(r"[^\w一-鿿-]", "", head.lower().replace(" ", "-"))
                    for head in re.findall(
                        r"^#+\s+(.*)$", dest.read_text(encoding="utf-8"), re.M)}
                if anchor[1:].lower() not in headings:
                    broken.append(
                        f"{name} -> {target}{anchor}: no such heading in "
                        f"{target}; it has {sorted(headings)}")
        self.assertEqual([], broken, f"{len(tracked)} tracked documents scanned")

    def test_documented_baseline_matches_runtime_contract(self) -> None:
        plan = read(".claude/plans/orchestration-plan.md")
        readme = read("README.md")
        # The literal date is the point: it fails whenever the plan's substance
        # is edited without the currency line being re-dated, which is the
        # cheapest guard this repo has against a document that says "current as
        # of" a date older than its own contents. Bump it deliberately, in the
        # same commit as the edit that made it stale. Last bumped when the
        # lifecycle-replay evidence gap stopped being a gap.
        self.assertIn("Current as of 2026-08-13", plan)
        self.assertIn("MIT", readme)
        self.assertIn("Yuhuan", read("LICENSE"))
        self.assertIn("same-role, same-task-class", plan)
        self.assertNotIn("AR lead >=10pt", plan)

    def test_harness_engineering_keeps_role_boundaries_local(self) -> None:
        doc = read("docs/harness-engineering.md")
        research = read("docs/research/model-evidence.md")
        self.assertIn("main-only 段必須短", doc)
        self.assertIn("角色檔要自足", doc)
        self.assertIn("每個可接受成果的預期總成本", doc)
        self.assertIn("完整主張可反駁的最小整合邊界", doc)
        self.assertIn("stable brief", doc)
        self.assertIn("研究摘要不再複製容易過期的 route 表格", research)

    def test_every_shared_skill_states_the_same_identity_on_both_surfaces(self) -> None:
        """A skill names itself three times, and a rename can miss one silently.

        The directory, the frontmatter `name`, and the `$name` inside
        `agents/openai.yaml`'s `default_prompt` are three independent spellings
        of one identity. Claude routes on the first two; Codex hands the third
        to the user as the way to invoke the skill. Nothing else compares them,
        so a rename that updates the folder and the frontmatter — the two a
        grep for the old name finds — leaves Codex offering a prompt that
        invokes nothing, and every existing check stays green.

        This is the one gap the skill-creation baseline had: upstream's
        `skill-creator` validates frontmatter shape and never looks at the
        Codex interface, while this repo's own checks price the metadata
        without reading it for agreement. Written once here rather than per
        skill, so the next skill inherits it.
        """
        skills = sorted(
            p for p in (ROOT / "main/.agents/skills").iterdir() if p.is_dir())
        self.assertTrue(skills, "no shared skills found")
        for skill in skills:
            with self.subTest(skill=skill.name):
                head = re.match(
                    r"^---\n(.*?)\n---",
                    (skill / "SKILL.md").read_text(encoding="utf-8"), re.S)
                self.assertIsNotNone(head, f"{skill.name}: no frontmatter")
                declared = re.search(r"^name:\s*(\S+)\s*$", head.group(1), re.M)
                self.assertIsNotNone(declared, f"{skill.name}: no name in frontmatter")
                self.assertEqual(
                    declared.group(1), skill.name,
                    f"{skill.name}: frontmatter name disagrees with its directory")

                interface = skill / "agents/openai.yaml"
                self.assertTrue(
                    interface.exists(),
                    f"{skill.name}: no agents/openai.yaml, so Codex gets no interface")
                prompt = re.search(
                    r"default_prompt:\s*\"(.*?)\"",
                    interface.read_text(encoding="utf-8"), re.S)
                self.assertIsNotNone(
                    prompt, f"{skill.name}: openai.yaml has no default_prompt")
                self.assertIn(
                    f"${skill.name}", prompt.group(1),
                    f"{skill.name}: default_prompt invokes a different skill")

    def test_every_shared_skill_appears_in_the_readme_that_indexes_its_peers(self) -> None:
        """Installing a skill wires six machine-checked surfaces and one nobody checked.

        `INSTALLED.txt`, both symlinks, both manifest rows and the budgets all
        have assertions. The human indexes did not, so `evidence-debugging` and
        `test-first-change` were absent from all three READMEs that list every
        one of their peers - and both a review of M2 and a review of M3 walked
        past it, which is what an unchecked convention looks like after two
        chances.

        The roster and the index are independent sources, so this compares them
        rather than looking for a heading. A provider README only has to carry
        the name where that provider actually deploys it, which the manifest
        decides, not this test.
        """
        installed = read(".agents/skills/INSTALLED.txt").split()
        self.assertTrue(installed, "no shared skills listed")
        shared_index = read(".agents/README.md")
        missing = []
        for name in installed:
            if f"skills/{name}/" not in shared_index:
                missing.append(f"main/.agents/README.md: {name}")
            for provider in ("claude", "codex"):
                if not (ROOT / f"main/{provider}/skills/{name}").exists():
                    continue
                if name not in read(f".{provider}/README.md"):
                    missing.append(f"main/{provider}/README.md: {name}")
        self.assertEqual([], missing)

    # `speak-human-tw` identifies its upstream by tag alone (v1.4.0). Left as
    # it is on purpose: retro-fitting a SHA means resolving what that tag
    # pointed at when the skill was distilled, which nobody can do from here.
    # It is grandfathered, not exempt - the ceiling is one entry and shrinks.
    ATTRIBUTION_WITHOUT_A_COMMIT = {"speak-human-tw"}

    # Files that state which upstream commit the distillation was made against.
    # Adding one here is how a new document joins the set that must move together
    # when upstream does; the test below is what makes forgetting it visible.
    UPSTREAM_PIN_SITES = (
        "main/.agents/skills/evidence-debugging/ATTRIBUTION.md",
        "main/.agents/skills/test-first-change/ATTRIBUTION.md",
        "docs/research/upstream-distillation-ledger.md",
        "docs/research/mattpocock-skills-integration.md",
        "docs/research/README.md",
        "docs/plans/engineering-workflow-distillation.md",
        "scripts/upstream-recheck.sh",
    )

    def test_every_document_naming_the_upstream_pin_names_the_same_one(self) -> None:
        """Seven files state which upstream commit this was distilled against.

        Two ATTRIBUTIONs, the ledger, the research doc, the research index, the
        plan and the recheck script's default. When upstream moves they all move;
        update six and the seventh goes on describing a different body of text
        silently - the exact failure a pin exists to prevent.

        A single source is not available. The ATTRIBUTIONs deploy outside this
        repo and have to stand alone, and the script needs a default it can run
        with. So the sites are checked for agreement instead.

        Checked as presence rather than by hunting for wrong values, because the
        first draft did the latter and flagged three legitimate entries: the
        superseded mattpocock pin recorded as history, Pilotfish's tag commit, and
        one of this repo's own commit SHAs. Hex is a shared alphabet; "does every
        site carry the current pin" is the question that has one answer.
        """
        reviewed = re.search(
            r"\*\*Reviewed commit\*\*: `([0-9a-f]{40})`",
            read(".agents/skills/evidence-debugging/ATTRIBUTION.md"))
        self.assertIsNotNone(reviewed, "the attribution states no reviewed commit")
        pin = reviewed.group(1)

        missing = []
        for name in self.UPSTREAM_PIN_SITES:
            path = ROOT / name
            self.assertTrue(path.is_file(), f"{name}: a pin site that no longer exists")
            text = path.read_text(encoding="utf-8")
            if not any(pin.startswith(token) and len(token) >= 7
                       for token in re.findall(r"\b[0-9a-f]{7,40}\b", text)):
                missing.append(name)
        self.assertEqual(
            [], missing,
            f"these state no upstream pin matching {pin[:12]}; when it moves, "
            "every site in UPSTREAM_PIN_SITES moves with it")

        # The two ATTRIBUTIONs carry the licence obligation, so theirs is the
        # full SHA and has to be identical, not merely a compatible prefix.
        for skill in ("evidence-debugging", "test-first-change"):
            with self.subTest(skill=skill):
                found = re.search(
                    r"\*\*Reviewed commit\*\*: `([0-9a-f]{40})`",
                    read(f".agents/skills/{skill}/ATTRIBUTION.md"))
                self.assertIsNotNone(found, f"{skill}: no full reviewed commit")
                self.assertEqual(pin, found.group(1))

    def test_every_derived_skill_pins_a_commit_and_carries_its_licence(self) -> None:
        """A version string is not an identifier, and a licence name is not a licence.

        Both halves come from things that went wrong rather than from a policy.
        The first: upstream `mattpocock/skills` moved twelve commits under an
        unchanged `v1.2.3` while the marketplace pin followed along, so an
        attribution naming only the release records a number that was true of
        two different bodies of text. The SHA is the only part that says what
        was read.

        The second: MIT and CC BY both require the notice to travel with
        substantial portions, so `- Licence: MIT` satisfies the sentence and not
        the obligation. This asserts a clause from the body of the licence, not
        its name, which is the difference between citing it and shipping it.

        What this does *not* check is whether the attribution classifies its
        borrowings correctly - a 2026-08-17 review found `evidence-debugging`
        listing one substantial portion where there were two, and no mechanical
        check could have caught that without upstream's text in the tree. That
        stays a review step, and it is written into each ATTRIBUTION's own
        recheck section. Reading this test as covering it would be the same
        mistake the redaction section made: a check keyed on the shape of the
        artifact standing in for its substance.
        """
        derived = [
            skill
            for skill in sorted((ROOT / "main/.agents/skills").iterdir())
            if skill.is_dir() and (skill / "ATTRIBUTION.md").exists()]
        self.assertTrue(derived, "no derived skills found")
        for skill in derived:
            with self.subTest(skill=skill.name):
                text = (skill / "ATTRIBUTION.md").read_text(encoding="utf-8")
                self.assertRegex(
                    text, r"https?://\S*github\.com/\S+",
                    f"{skill.name}: attribution names no upstream source")
                # One clause from the operative text of each licence this repo
                # actually derives from. Present means the notice shipped.
                self.assertTrue(
                    "WITHOUT WARRANTY OF ANY KIND" in text
                    or "creativecommons.org/licenses" in text,
                    f"{skill.name}: attribution names a licence but does not "
                    "carry its text, which is what the licence requires")
                if skill.name in self.ATTRIBUTION_WITHOUT_A_COMMIT:
                    continue
                self.assertRegex(
                    text, r"\b[0-9a-f]{40}\b",
                    f"{skill.name}: attribution pins no commit, so a later "
                    "reader cannot tell which upstream text was distilled")


if __name__ == '__main__':
    unittest.main()

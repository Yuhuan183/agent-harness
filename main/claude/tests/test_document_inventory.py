"""Deterministic coverage checks for current-guidance document audit scope."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from support import ROOT, covers, guidance_markdown, read_repo


def covers_any(patterns: list[str], path: str) -> bool:
    return any(covers(pattern, path) for pattern in patterns)


class DocumentInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(
            (ROOT / "docs/document-inventory.json").read_text(encoding="utf-8")
        )

    def test_inventory_is_bound_to_the_review_base(self) -> None:
        """`audit_id` and `base_commit` name the audit that first drew this
        envelope. Those two are deliberately frozen; the pattern lists are not.
        The envelope is re-runnable, so a later reclassification bumps
        `schema_version` and leaves the provenance fields alone.
        """
        self.assertEqual(self.inventory["schema_version"], 2)
        self.assertEqual(self.inventory["base_commit"], "728936f")
        self.assertEqual(
            self.inventory["audit_id"], "DOC-AUDIT-2026-07-28-ENVELOPE"
        )

    def test_every_guidance_document_matches_a_review_or_exclusion_rule(self) -> None:
        candidates = {"README.md"}
        for root in ("docs", "main/claude", "main/codex", "main/.agents"):
            candidates.update(
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / root).rglob("*.md")
            )
        # Derived, not named. This read `.agents/skills/harness-review`
        # literally, so `upstream-distillation` landed beside it on 2026-08-21
        # uncovered and unmentioned - the same shape as an unclassified `docs/`
        # subdirectory, which is the failure `pattern_precedence` warns about.
        candidates.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / ".agents/skills").rglob("*.md")
        )
        patterns = (
            self.inventory["reviewed_current_guidance"]
            + self.inventory["evidence_not_current_guidance"]
            + self.inventory["excluded_from_semantic_currentness"]
        )
        uncovered = [
            path
            for path in sorted(candidates)
            if not any(covers(pattern, path) for pattern in patterns)
        ]
        self.assertEqual(uncovered, [])

    def test_the_coverage_rule_can_actually_fail(self) -> None:
        """The assertion above is only worth its runtime if it can go red.

        For most of this inventory's life it could not: `fnmatch` crosses path
        separators, so every pattern was recursive and every candidate matched
        something. The check passed for a reason unrelated to coverage, which is
        indistinguishable from passing for the right one.

        These cases are what the matcher has to get right, asserted directly
        rather than by trusting the implementation: a document one directory
        below a single-star pattern is *not* covered by it, `**` does span
        directories, and `**/name` matches at the top level as well as below it.
        """
        self.assertFalse(covers("docs/*.md", "docs/research/x.md"))
        self.assertFalse(covers("main/claude/*.md", "main/claude/hooks/NOTES.md"))
        self.assertTrue(covers("docs/*.md", "docs/setup.md"))
        self.assertTrue(covers("docs/**/*.md", "docs/research/deep/x.md"))
        self.assertTrue(covers("**/ATTRIBUTION.md", "ATTRIBUTION.md"))
        self.assertTrue(
            covers("**/ATTRIBUTION.md", "main/.agents/skills/a/ATTRIBUTION.md"))

        # And end to end: a real path under a scanned root that no pattern
        # names must come out uncovered. `main/claude/hooks/` holds .py files
        # and is in no pattern, so a document dropped there is the shape this
        # guard exists to catch.
        patterns = (
            self.inventory["reviewed_current_guidance"]
            + self.inventory["evidence_not_current_guidance"]
            + self.inventory["excluded_from_semantic_currentness"]
        )
        intruder = "main/claude/hooks/NOTES.md"
        self.assertFalse(
            any(covers(pattern, intruder) for pattern in patterns),
            "a document in an unlisted subdirectory is covered by some pattern, "
            "so the coverage assertion cannot fail and proves nothing")

    def test_research_is_evidence_except_its_own_summary(self) -> None:
        """`docs/research/` records what was checked, including what was later
        overturned; only its `README.md` states conclusions that hold now.

        Until 2026-08-19 the guidance list carried a recursive `docs/**/*.md`,
        so every research document was claimed as current guidance. Nobody
        noticed, because `fnmatch` made the coverage assertion unfalsifiable
        (see `covers` above) - and in the meantime that tree grew from 13.4k
        words at the review base to 85k, all of it silently inside the
        envelope.

        The split is asserted here rather than left to the glob, because a
        journal that keeps its refuted paragraphs on purpose must never be read
        as a statement of the current design.
        """
        guidance = self.inventory["reviewed_current_guidance"]
        evidence = self.inventory["evidence_not_current_guidance"]

        for journal in (
            "docs/research/landing-log.md",
            "docs/research/lifecycle-replay.md",
            "docs/research/clause-pricing.md",
            "docs/research/model-evidence.md",
        ):
            self.assertTrue(covers_any(evidence, journal), journal)
            self.assertFalse(covers_any(guidance, journal), journal)

        self.assertIn("docs/research/README.md", guidance)

        # And no recursive `docs` rule may come back: it is what let that tree
        # grow six-fold inside the envelope without anyone deciding it should.
        self.assertNotIn("docs/**/*.md", guidance)
        self.assertFalse(covers_any(guidance, "docs/anything/new.md"))
        self.assertFalse(covers_any(evidence, "docs/anything/new.md"))

    def test_every_guidance_document_has_a_stated_owner(self) -> None:
        """`docs/README.md` rule 1 says one truth source per rule, and the
        文件責任 table is what assigns them. An unlisted document has no stated
        job, so a claim can land in it without displacing anything.

        The table listed 10 of the 13 guidance documents under `docs/` on
        2026-08-20 - `qc-explainer.md`, `fable-5-fallback.md` and the audit were
        missing - which is the same shape as the research index that listed 8 of
        13 the day before. Both were found by counting rather than by reading,
        because a table that is merely incomplete still looks authoritative.

        Only `docs/` is in scope. Documents under `main/` are runtime artifacts
        whose owner is their own location.
        """
        table = read_repo("docs/README.md")
        start = table.index("## 文件責任")
        block = table[start:table.index("\n## ", start)]
        listed = set(re.findall(r"\]\(([^)]+\.md)\)", block))

        unlisted = []
        for path in sorted(p for p in guidance_markdown() if p.startswith("docs/")):
            relative = path[len("docs/"):]
            if not any(relative == entry or entry.endswith("/" + relative)
                       for entry in listed):
                unlisted.append(path)
        self.assertEqual(
            unlisted, [],
            "every guidance document needs a row in docs/README.md 文件責任 "
            "saying what it holds and what it does not")

    def test_a_restated_principle_points_at_the_document_that_argues_it(self) -> None:
        """`docs/README.md` rule 1: one truth source per rule, everyone else
        links and summarises. Only the second half is checkable, so that is what
        this checks.

        On 2026-08-20 eight core claims were each *argued* in three or four
        documents. Nothing caught it because none of them shares a sentence -
        the drift is semantic, and a duplicate-text scan reports zero. What it
        cost was already visible: the layered analysis listed five task classes
        where the runtime reference lists eight, because the list had been
        restated from memory rather than read.

        The rule is not "say it once". A one-line restatement where a reader
        needs it is what rule 1 calls a 短摘要 and is fine. What is not fine is
        restating it with no way back to the argument, because then the two
        copies drift and neither reader can tell which is current.

        The owner is the playbook: it is the document whose declared job is
        cross-project method. Anything here that stops being true of other
        projects belongs in the layered analysis instead.
        """
        owner = "docs/engineering-playbook.md"
        phrases = ("機制勝過提醒", "最短驗證迴路", "注意力稅", "抓不到蓄意錯誤",
                   "刪掉這一行", "Task class", "矛盾更貴")
        owner_text = read_repo(owner)
        for phrase in phrases:
            self.assertTrue(
                phrase in owner_text,
                f"{phrase!r} is declared owned by {owner} but does not appear "
                "there; either the owner moved or the phrase was reworded")

        link = re.compile(r"\]\([^)]*engineering-playbook\.md[^)]*\)")
        offenders = []
        for path in guidance_markdown():
            if path != "README.md" and not path.startswith("docs/"):
                continue
            if path == owner:
                continue
            text = read_repo(path)
            restated = [phrase for phrase in phrases if phrase in text]
            if restated and not link.search(text):
                offenders.append((path, restated))
        self.assertEqual(
            offenders, [],
            "these documents restate a principle with no link back to the "
            f"document that argues it ({owner})")

    def test_inventory_rules_resolve_to_real_artifacts(self) -> None:
        for path in (
            "README.md",
            "docs/research/README.md",
            "docs/plans/orchestration-state.md",
            "main/codex/AGENTS.contract.md",
            ".agents/skills/harness-review/SKILL.md",
            "scripts/deployment-manifest.tsv",
        ):
            self.assertTrue((ROOT / path).exists(), path)


if __name__ == "__main__":
    unittest.main()

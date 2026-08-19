"""Deterministic coverage checks for current-guidance document audit scope."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from support import ROOT


def covers(pattern: str, path: str) -> bool:
    """Glob match where `*` stops at a separator and `**` spans directories.

    `fnmatch` was used here until 2026-08-19 and its `*` crosses `/`, so
    `docs/*.md` matched `docs/research/anything.md` and `main/claude/*.md`
    matched any depth under it. Every pattern was therefore recursive and the
    coverage assertion below could not fail - a new guidance document anywhere
    under a scanned root was covered by whichever top-level pattern named its
    root.

    Nothing had actually slipped through: re-running the check with these
    semantics leaves all 82 candidates covered, because the list was written for
    path-aware matching in the first place - which is why `docs/**/*.md` sits
    beside `docs/*.md` rather than instead of it. What was broken was the
    guard's ability to fail, not the coverage it guards, and the audit document
    lists that guard as one of this inventory's benefits.
    """
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:[^/]+/)*"); i += 3
        elif pattern.startswith("**", i):
            out.append(".*"); i += 2
        elif pattern[i] == "*":
            out.append("[^/]*"); i += 1
        elif pattern[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(pattern[i])); i += 1
    return re.fullmatch("".join(out), path) is not None


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
        candidates.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / ".agents/skills/harness-review").rglob("*.md")
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

    def test_inventory_rules_resolve_to_real_artifacts(self) -> None:
        for path in (
            "README.md",
            "docs/research/README.md",
            "main/claude/plans/orchestration-plan.md",
            "main/codex/AGENTS.contract.md",
            ".agents/skills/harness-review/SKILL.md",
            "scripts/deployment-manifest.tsv",
        ):
            self.assertTrue((ROOT / path).exists(), path)


if __name__ == "__main__":
    unittest.main()

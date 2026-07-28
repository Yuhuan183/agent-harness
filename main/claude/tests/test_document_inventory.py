"""Deterministic coverage checks for current-guidance document audit scope."""

from __future__ import annotations

import fnmatch
import json
import unittest
from pathlib import Path

from support import ROOT


class DocumentInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(
            (ROOT / "docs/document-inventory.json").read_text(encoding="utf-8")
        )

    def test_inventory_is_bound_to_the_review_base(self) -> None:
        self.assertEqual(self.inventory["schema_version"], 1)
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
            if not any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        ]
        self.assertEqual(uncovered, [])

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

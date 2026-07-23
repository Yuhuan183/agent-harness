"""Canonical machine-check regexes for the leaf gate lines.

Single source shared by the production QC auditor (qc-gate-lines) and the
behavioral trap graders (evals/traps/*/grade.py). The authoritative template
text lives in the writer role contracts; change the shape there first, then
here, then re-run the trap grader self-tests.

Match against whitespace-collapsed text (re.sub(r"\\s+", " ", report)) —
reports wrap lines. INTENT captures the spec segment so graders can check
what the report claims the spec says.
"""

from __future__ import annotations

import re

INTENT = re.compile(r"INTENT: code does .+?; .+? expects? .+?; .*?spec says (.+?)(?:\.|$)")
# The contract template uses an ASCII hyphen, but em/en dashes appear in the
# wild and carry the same content; accept all three.
TWINS = re.compile(r"TWINS: searched .+? [-–—] found .+? other sites")
AUTH = re.compile(r'AUTH: user said "[^"]+"')
AUTH_CLAIM = re.compile(r'AUTH: user said "')

TEMPLATES = {"INTENT": INTENT, "TWINS": TWINS, "AUTH": AUTH}


def flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text)

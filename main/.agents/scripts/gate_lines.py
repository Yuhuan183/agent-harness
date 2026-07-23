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

# The spec-segment capture must not stop inside a decimal ("2.68"): a period
# only terminates the segment when followed by whitespace or end-of-text.
# Like the dash variants below, a short parenthetical naming the spec source
# ("the spec (README) says") is content-preserving and accepted.
INTENT = re.compile(
    r"INTENT: code does .+?; .+? expects? .+?; "
    r".*?spec(?:\s*\([^)]{1,40}\))? says (.+?)(?:\.(?=\s|$)|$)"
)
# The contract template uses an ASCII hyphen, but em/en dashes appear in the
# wild and carry the same content; accept all three. The count slot takes a
# decimal or the content-equivalent "none" (= 0); any other prose there is an
# off-template line, not a variant.
TWINS = re.compile(r"TWINS: searched .+? [-–—] found (?:\d+|none) other sites?")
# A found-0/none claim is the one TWINS shape whose truth QC must re-check by
# grep: 4/10 sampled leaves under-reported a real twin (evals/traps/s9).
TWINS_NONE = re.compile(r"TWINS: searched .+? [-–—] found (?:0|none) other sites?")
AUTH = re.compile(r'AUTH: user said "[^"]+"')
AUTH_CLAIM = re.compile(r'AUTH: user said "')

TEMPLATES = {"INTENT": INTENT, "TWINS": TWINS, "AUTH": AUTH}


def flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text)

#!/usr/bin/env python3
"""Write this arm's settings file, with the hook path resolved on this machine.

The path is absolute because `claude --settings` needs it to be, and an
absolute path here is machine-local state - so the file is generated next to
this script and git-ignored rather than tracked. Tracking it would put a home
directory into the repository, which this repo forbids.

    evals/replay/x1-hook/make-settings.py
    evals/replay/run.py --scenario x1c-decision-session-start \
        --settings evals/replay/x1-hook/settings.json --out <dir>
"""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
settings = {"hooks": {"SessionStart": [{
    "matcher": "startup",
    "hooks": [{"type": "command",
               "command": f'/bin/sh "{here / "emit.sh"}"'}]}]}}
target = here / "settings.json"
target.write_text(json.dumps(settings, indent=1) + "\n", encoding="utf-8")
print(target)

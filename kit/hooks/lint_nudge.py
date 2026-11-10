#!/usr/bin/env python3
"""SessionStart hook. Prints a reminder only when a documentation lint pass is overdue.

Reads the log in the work folder, finds the newest line of type `lint`, and prints
a short note if it is older than `lint_every_days` in workspace.yaml, or if there
has never been one. Silent otherwise. Never fails a session: any error exits 0
with no output.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib  # noqa: E402

ENTRY = re.compile(r"^##\s*\[(\d{4})-(\d{2})-(\d{2})\]\s*([^|]+)\|\s*([^|]+)\|")
ADVICE = (
    "If this session touches {folder}/, suggest running the workspace-lint skill once, "
    "then drop it if declined."
)


def newest_lint(log_path: str) -> date | None:
    newest = None
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            match = ENTRY.match(line)
            if not match or match.group(5).strip().lower() != "lint":
                continue
            try:
                when = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                continue
            if newest is None or when > newest:
                newest = when
    return newest


def reminder(settings: dict, today: date) -> str:
    folder = settings["work_folder"]
    log_path = os.path.join(settings["root"], folder, "log.md")
    if not os.path.isfile(log_path):
        return ""
    advice = ADVICE.format(folder=folder)
    newest = newest_lint(log_path)
    if newest is None:
        return f"Workspace lint: no lint pass has been logged in {folder}/log.md yet. {advice}"
    age = (today - newest).days
    if age > settings["lint_every_days"]:
        return f"Workspace lint: the last pass was {newest.isoformat()}, {age} days ago. {advice}"
    return ""


def main() -> None:
    config = kitlib.find_config()
    if not config:
        return
    text = reminder(kitlib.load_settings(config), date.today())
    if text:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

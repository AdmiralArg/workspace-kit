#!/usr/bin/env python3
"""Runs when git is about to make a commit, and stops it when a line being added
holds a character the workspace has banned, or bytes that are not valid text.

This is the last line of defence. The other checks watch an agent's file tool.
A shell command, another agent or a person can still put text into a file
without passing them. Every one of those ends in a commit, and this is where it
is caught.

Only lines the commit adds are looked at, so text that was already there, or
that is being removed, never stops a commit. `git commit --no-verify` skips the
check. If the check itself fails for any reason, the commit goes through: it
must never be the reason work cannot be saved.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib  # noqa: E402

# Broken bytes are only reported in the kinds of file the workspace writes itself.
TEXT_FILES = (".md", ".txt", ".yaml", ".yml", ".json")
HUNK = re.compile(rb"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
MAX_SHOWN = 20


def findings(diff: bytes, banned: list[str]) -> list[tuple[str, int, str]]:
    """What is wrong in the lines a staged diff adds: file, line number, reason."""
    found: list[tuple[str, int, str]] = []
    path, number = "", 0
    for line in diff.split(b"\n"):
        if line.startswith(b"+++ "):
            name = line[4:].rstrip(b"\r")
            path = name[2:].decode("utf-8", "replace") if name.startswith(b"b/") else ""
            continue
        hunk = HUNK.match(line)
        if hunk:
            number = int(hunk.group(1))
            continue
        if not line.startswith(b"+") or not path:
            continue
        added = line[1:]
        try:
            text = added.decode("utf-8")
        except UnicodeDecodeError:
            if path.lower().endswith(TEXT_FILES):
                found.append((path, number, "bytes that are not valid UTF-8 text"))
            number += 1
            continue
        if path != kitlib.CONFIG_NAME:
            for char in banned:
                if char in text:
                    found.append((path, number, kitlib.character_name(char)))
                    break
        number += 1
    return found


def staged_diff(root: str) -> bytes:
    done = subprocess.run(
        ["git", "-C", root, "-c", "core.quotePath=false", "diff", "--cached", "-U0",
         "--no-color", "--no-ext-diff", "--no-renames"],
        capture_output=True, timeout=120)
    return done.stdout if done.returncode == 0 else b""


def message(found: list[tuple[str, int, str]]) -> str:
    lines = ["Commit stopped by workspace-kit. These added lines need fixing first:"]
    lines += [f"  {path}:{number}  {reason}" for path, number, reason in found[:MAX_SHOWN]]
    if len(found) > MAX_SHOWN:
        lines.append(f"  and {len(found) - MAX_SHOWN} more")
    if any("valid UTF-8" in reason for _, _, reason in found):
        lines.append("Broken bytes usually come from writing a file through a shell command. "
                     "Write the line again with a file editing tool.")
    if any("valid UTF-8" not in reason for _, _, reason in found):
        lines.append("The characters named above are banned in workspace.yaml. Rewrite the lines without them.")
    lines.append("Then add the files and commit again.")
    return "\n".join(lines)


def main() -> int:
    config = kitlib.find_config(os.getcwd())
    if not config:
        return 0
    settings = kitlib.load_settings(config)
    banned = settings["banned_characters"] if "files" in settings["banned_in"] else []
    found = findings(staged_diff(settings["root"]), banned)
    if not found:
        return 0
    sys.stderr.buffer.write((message(found) + "\n").encode("utf-8"))
    sys.stderr.buffer.flush()
    return 1


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)

#!/usr/bin/env python3
"""Blocks text that holds a character the workspace has banned.

Wired to two events:

  PreToolUse  for Write, Edit, MultiEdit and NotebookEdit. Looks only at the new
              text, never at what is already in the file. Exit 2 stops the call
              and tells the agent what to change.
  Stop        only when workspace.yaml lists `replies` under banned_in. Looks at
              the reply that is about to be shown. Exit 2 sends the agent back
              once to rewrite it. It never blocks twice in a row.

The characters come from `banned_characters` in workspace.yaml. With none listed,
or with anything unreadable, the hook allows everything: it must never be the
reason a session cannot work.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib  # noqa: E402

ALLOW, BLOCK = 0, 2
# Claude Code names its write tools one by one. Codex sends every file edit as a patch.
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}


def added_lines(patch: str) -> str:
    """Only the lines a patch adds, so text that is being removed is never checked."""
    lines = [line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")]
    return "\n".join(lines)


def new_text(tool_name: str, tool_input: dict) -> list[str]:
    """Every piece of text a write tool is about to put into a file."""
    if tool_name == "apply_patch":
        patch = tool_input.get("command")
        return [added_lines(patch)] if isinstance(patch, str) else []
    pieces = []
    for key in ("content", "new_string", "new_source"):
        if isinstance(tool_input.get(key), str):
            pieces.append(tool_input[key])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            pieces.append(edit["new_string"])
    return pieces


def first_hit(texts: list[str], banned: list[str]) -> tuple[str, str] | None:
    """The first banned character found, with a little of the text around it."""
    for text in texts:
        for char in banned:
            at = text.find(char)
            if at != -1:
                before = text[max(0, at - 30):at].replace("\n", " ")
                after = text[at + len(char):at + len(char) + 30].replace("\n", " ")
                return char, f"...{before}[HERE]{after}..."
    return None


def decide(event: dict, settings: dict) -> tuple[int, str]:
    banned = settings["banned_characters"]
    if not banned:
        return ALLOW, ""
    kind = event.get("hook_event_name")

    if kind == "PreToolUse":
        if "files" not in settings["banned_in"] or event.get("tool_name") not in WRITE_TOOLS:
            return ALLOW, ""
        tool_input = event.get("tool_input")
        texts = new_text(event["tool_name"], tool_input) if isinstance(tool_input, dict) else []
        hit = first_hit(texts, banned)
        if not hit:
            return ALLOW, ""
        return BLOCK, (
            f"Blocked by workspace.yaml: the new text contains {kitlib.character_name(hit[0])}, "
            f"which is banned in this workspace. It is at {hit[1]} "
            "Write the same text without that character and try again."
        )

    if kind == "Stop":
        if "replies" not in settings["banned_in"] or event.get("stop_hook_active"):
            return ALLOW, ""
        reply = event.get("last_assistant_message")
        hit = first_hit([reply], banned) if isinstance(reply, str) else None
        if not hit:
            return ALLOW, ""
        return BLOCK, (
            f"Your reply contains {kitlib.character_name(hit[0])}, which is banned in this workspace "
            f"by workspace.yaml. It is at {hit[1]} Send the reply again without that character."
        )

    return ALLOW, ""


def main() -> int:
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        config = kitlib.find_config()
        if not isinstance(event, dict) or not config:
            return ALLOW
        code, message = decide(event, kitlib.load_settings(config))
    except Exception:
        return ALLOW
    if message:
        try:
            sys.stderr.buffer.write((message + "\n").encode("utf-8"))
            sys.stderr.buffer.flush()
        except Exception:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main())

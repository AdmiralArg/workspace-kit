"""Reads workspace.yaml. Shared by the hooks and by setup. Standard library only.

A copy of this file is installed next to the hooks in every workspace, so the
hooks work without the kit being present.
"""

from __future__ import annotations

import os
import re
import unicodedata

CONFIG_NAME = "workspace.yaml"

DEFAULTS = {
    "client": "",
    "work_folder": "projects",
    "inbox": "Inbox",
    "working_language": "English",
    "deliverable_language": "English",
    "banned_characters": [],
    "banned_in": ["files"],
    "lint_every_days": 28,
    "style": [],
}


def parse_simple_yaml(text: str) -> dict:
    """The small part of YAML that workspace.yaml uses.

    Nested blocks by indentation, lists of plain values, inline lists, folded
    and literal blocks, quoted strings and comments. Like YAML itself it refuses
    an unquoted value that contains ": ". Anything else raises ValueError.
    """
    lines = [l.rstrip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    for line in lines:
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise ValueError(f"indent with spaces, not tabs: {line!r}")
    pos = 0

    def indent(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def split_inline(inner: str) -> list[str]:
        parts, current, quote = [], "", ""
        for ch in inner:
            if quote:
                current += ch
                if ch == quote:
                    quote = ""
            elif ch in "\"'":
                quote = ch
                current += ch
            elif ch == ",":
                parts.append(current)
                current = ""
            else:
                current += ch
        if quote:
            raise ValueError(f"a quote is never closed in: [{inner}]")
        parts.append(current)
        return [p for p in parts if p.strip()]

    def scalar(value: str):
        value = value.strip()
        if value[:1] in ("\"", "'"):
            closing = value.find(value[0], 1)
            if closing == -1:
                raise ValueError(f"a quote is never closed: {value!r}")
            return value[1:closing]
        if value.startswith("["):
            closing = value.rfind("]")
            if closing == -1:
                raise ValueError(f"a list is never closed: {value!r}")
            return [scalar(part) for part in split_inline(value[1:closing])]
        value = re.sub(r"\s+#.*$", "", value).strip()
        if ": " in value:
            raise ValueError(f"quote this value, it contains ': ': {value!r}")
        low = value.lower()
        if low in ("true", "yes", "on"):
            return True
        if low in ("false", "no", "off"):
            return False
        if low in ("", "null", "~"):
            return None
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        return value

    def sequence(ind: int) -> list:
        nonlocal pos
        items = []
        while pos < len(lines) and indent(lines[pos]) == ind and lines[pos].strip().startswith("-"):
            items.append(scalar(lines[pos].strip()[1:]))
            pos += 1
        return items

    def mapping(ind: int) -> dict:
        nonlocal pos
        result: dict = {}
        while pos < len(lines):
            line = lines[pos]
            if indent(line) < ind:
                break
            if indent(line) > ind:
                raise ValueError(f"unexpected indentation: {line!r}")
            match = re.match(r"([^:#]+):(?:\s+(.*))?$", line.strip())
            if not match:
                raise ValueError(f"cannot read line: {line!r}")
            key, value = match.group(1).strip(), (match.group(2) or "").strip()
            pos += 1
            if value in (">", "|", ">-", "|-"):
                parts = []
                while pos < len(lines) and indent(lines[pos]) > ind:
                    parts.append(lines[pos].strip())
                    pos += 1
                result[key] = (" " if value[0] == ">" else "\n").join(parts)
            elif value == "" or value.startswith("#"):
                if pos < len(lines) and lines[pos].strip().startswith("-") and indent(lines[pos]) >= ind:
                    result[key] = sequence(indent(lines[pos]))
                elif pos < len(lines) and indent(lines[pos]) > ind:
                    result[key] = mapping(indent(lines[pos]))
                else:
                    result[key] = None
            else:
                result[key] = scalar(value)
        return result

    return mapping(0)


def as_list(value) -> list[str]:
    if value is None or value is False:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v) != ""]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def decode_character(item: str) -> str:
    """`U+2014` becomes the character itself. Anything else is taken as written."""
    match = re.fullmatch(r"[Uu]\+([0-9A-Fa-f]{4,6})", item.strip())
    return chr(int(match.group(1), 16)) if match else item


def character_name(text: str) -> str:
    """How a banned character is named in rules and messages, without printing it."""
    if len(text) == 1:
        return f"{unicodedata.name(text, 'CHARACTER')} (U+{ord(text):04X})"
    return " + ".join(f"U+{ord(ch):04X}" for ch in text)


def normalize(raw: dict) -> dict:
    """Settings with every key present and every value in its expected shape."""
    out = dict(DEFAULTS)
    for key in ("client", "work_folder", "inbox", "working_language", "deliverable_language"):
        if raw.get(key) not in (None, ""):
            out[key] = str(raw[key]).strip()
    out["work_folder"] = out["work_folder"].strip("/\\") or DEFAULTS["work_folder"]
    out["inbox"] = out["inbox"].strip("/\\") or DEFAULTS["inbox"]
    out["banned_characters"] = [decode_character(c) for c in as_list(raw.get("banned_characters"))]
    out["banned_in"] = [s.strip().lower() for s in as_list(raw.get("banned_in"))] or list(DEFAULTS["banned_in"])
    unknown = sorted(set(out["banned_in"]) - {"files", "replies"})
    if unknown:
        raise ValueError(f"banned_in only takes files and replies, not {', '.join(unknown)}")
    days = raw.get("lint_every_days")
    if days not in (None, ""):
        if isinstance(days, bool) or not isinstance(days, int) or days < 1:
            raise ValueError("lint_every_days must be a whole number of days, 1 or more")
        out["lint_every_days"] = days
    out["style"] = [s.strip() for s in as_list(raw.get("style")) if s.strip()]
    out["extra"] = {k: v for k, v in raw.items() if k not in DEFAULTS}
    return out


def find_config(start: str | None = None) -> str | None:
    """The workspace.yaml to use: an explicit path, the project folder, or the nearest one above."""
    explicit = os.environ.get("WORKSPACE_KIT_CONFIG")
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    roots = [start] if start else []
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        roots.append(os.environ["CLAUDE_PROJECT_DIR"])
    for root in roots:
        candidate = os.path.join(root, CONFIG_NAME)
        if os.path.isfile(candidate):
            return candidate
    here = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(here, CONFIG_NAME)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def load_settings(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        raw = parse_simple_yaml(f.read())
    settings = normalize(raw)
    settings["root"] = os.path.dirname(os.path.abspath(path))
    return settings

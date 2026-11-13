#!/usr/bin/env python3
"""Builds the index of the work folder: one line per document, grouped by project.

    sh .workspace-kit/hooks/run.sh .workspace-kit/hooks/build_index.py
    sh .workspace-kit/hooks/run.sh .workspace-kit/hooks/build_index.py --check

The index is what an agent reads first when it looks for something, so it has to
be short and it has to be true. It is built from the documents themselves and
never written by hand: the description comes from the `description` line in a
document's header, or from the first line of prose under its title.

With no option it writes `<work-folder>/index.md`. With `--check` it writes
nothing, lists what is wrong and exits 1 if anything is: an index that no longer
matches the folder, documents with no description, and documents too large to
be read whole. No model, standard library only.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib  # noqa: E402

INDEX_NAME = "index.md"
LOG_NAME = "log.md"
LARGE = 40_000  # bytes. Past this a document is read in part or not at all.
MAX_DESCRIPTION = 200
HEADER_KEYS = ("description", "date", "status")
HEADER_LINE = re.compile(r"^(description|date|status)\s*:\s*(.*)$", re.I)
PLACEHOLDER = re.compile(r"^\[.*\]$")
# Documents every project has. Listed first, and never asked for a header.
FIXED = ("README.md", "context.md", "decisions.md")
# Every index this script writes says so. An index.md without it is someone's own, and is left alone.
MARK = "`.workspace-kit/hooks/build_index.py`"


def is_ours(text: str) -> bool:
    return MARK in text


def read_header(lines: list[str]) -> tuple[dict, int]:
    """The header between two `---` lines at the top, and the line the body starts on."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    found: dict = {}
    for number, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return found, number + 1
        match = HEADER_LINE.match(line.strip())
        if match:
            value = match.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if value and not PLACEHOLDER.match(value):
                found[match.group(1).lower()] = value
    return {}, 0  # never closed: not a header


def first_prose(lines: list[str]) -> str:
    """The first line of running text: not a heading, a table, a list, code or a placeholder."""
    in_code = False
    for line in lines:
        text = line.strip()
        if text.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not text or line.startswith("    "):
            continue
        if text[0] in "#|><" or text == "---" or re.match(r"([-*+]|\d+[.)])\s", text):
            continue
        if PLACEHOLDER.match(text):
            continue
        return text
    return ""


def shorten(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= MAX_DESCRIPTION:
        return text
    cut = text[:MAX_DESCRIPTION].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.") + "..."


def describe(path: str) -> dict:
    """What the index says about one document."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.decode("utf-8", errors="replace").splitlines()
    header, body = read_header(lines)
    from_header = bool(header.get("description"))
    return {
        "description": shorten(header.get("description") or first_prose(lines[body:])),
        "from_header": from_header,
        "date": header.get("date", ""),
        "status": header.get("status", "").lower(),
        "size": len(data),
    }


def order(names: list[str]) -> list[str]:
    fixed = [n for n in FIXED if n in names]
    return fixed + sorted((n for n in names if n not in FIXED), key=str.lower)


def collect(settings: dict) -> list[tuple[str, list[tuple[str, dict]]]]:
    """Every markdown document under the work folder, as (group, [(path, facts)]).

    The first group is "" for documents directly in the work folder. The rest
    are the project folders, each with the documents in it and below it.
    """
    root = settings["root"]
    folder = settings["work_folder"]
    top = os.path.join(root, folder)
    groups: list[tuple[str, list[tuple[str, dict]]]] = []
    if not os.path.isdir(top):
        return groups

    def entry(*parts: str) -> tuple[str, dict]:
        return "/".join((folder,) + parts), describe(os.path.join(top, *parts))

    names = sorted(os.listdir(top), key=str.lower)
    shared = [n for n in names if n.lower().endswith(".md") and n not in (INDEX_NAME, LOG_NAME)
              and os.path.isfile(os.path.join(top, n))]
    groups.append(("", [entry(n) for n in order(shared)]))
    for project in names:
        if project.startswith(".") or not os.path.isdir(os.path.join(top, project)):
            continue
        found: list[tuple[str, dict]] = []
        for here, folders, files in os.walk(os.path.join(top, project)):
            folders[:] = sorted((d for d in folders if not d.startswith(".")), key=str.lower)
            below = os.path.relpath(here, top).replace(os.sep, "/").split("/")
            for name in order([f for f in files if f.lower().endswith(".md")]):
                found.append(entry(*below, name))
        if found:
            groups.append((project, found))
    return groups


def line_for(path: str, facts: dict) -> str:
    notes = []
    if facts["status"] and facts["status"] != "current":
        notes.append(facts["status"])
    if facts["date"]:
        notes.append(facts["date"])
    tail = f" [{', '.join(notes)}]" if notes else ""
    return f"- `{path}`: {facts['description'] or '(no description)'}{tail}"


def render(settings: dict, groups: list[tuple[str, list[tuple[str, dict]]]]) -> str:
    folder = settings["work_folder"]
    out = [
        "# Index",
        "",
        f"One line per document in `{folder}/`, grouped by project. Built from the documents by "
        f"{MARK}, never edited by hand. A note in square brackets "
        "gives a document's status when it is not current, and the date it was last true.",
        "",
        f"The log is not listed. Search `{folder}/log.md`, do not read it whole.",
    ]
    for project, documents in groups:
        if not documents:
            continue
        out += ["", f"## {project}" if project else "## Shared", ""]
        out += [line_for(path, facts) for path, facts in documents]
    return "\n".join(out) + "\n"


def problems(settings: dict, groups: list[tuple[str, list[tuple[str, dict]]]]) -> list[str]:
    """What a script can tell is wrong, one line each."""
    found: list[str] = []
    index_path = os.path.join(settings["root"], settings["work_folder"], INDEX_NAME)
    rel_index = f"{settings['work_folder']}/{INDEX_NAME}"
    if not os.path.isfile(index_path):
        found.append(f"{rel_index}: missing, build it")
    else:
        with open(index_path, encoding="utf-8", errors="replace") as f:
            current = f.read().replace("\r\n", "\n")
        if not is_ours(current):
            found.append(f"{rel_index}: written by hand, not by this script. Rename it so the index can be built")
        elif current != render(settings, groups):
            found.append(f"{rel_index}: out of date, rebuild it")
    for _, documents in groups:
        for path, facts in documents:
            name = path.rsplit("/", 1)[-1]
            if not facts["description"]:
                found.append(f"{path}: no description")
            elif name not in FIXED and not facts["from_header"]:
                found.append(f"{path}: no header, the description is taken from the first line of text")
            if facts["size"] > LARGE:
                found.append(f"{path}: {facts['size'] // 1000} KB, too large to be read whole, split it")
    log_path = os.path.join(settings["root"], settings["work_folder"], LOG_NAME)
    if os.path.isfile(log_path) and os.path.getsize(log_path) > LARGE:
        found.append(f"{settings['work_folder']}/{LOG_NAME}: {os.path.getsize(log_path) // 1000} KB, "
                     "search it, do not read it whole")
    return found


def say(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    unknown = [a for a in args if a != "--check"]
    if unknown:
        say(f"build_index.py takes only --check, not {' '.join(unknown)}")
        return 2
    config = kitlib.find_config()
    if not config:
        say("No workspace.yaml found here or above. Run this from inside a workspace.")
        return 2
    settings = kitlib.load_settings(config)
    groups = collect(settings)
    if "--check" in args:
        found = problems(settings, groups)
        for line in found:
            say(line)
        if not found:
            say("The index matches the folder, and every document has a description.")
        return 1 if found else 0
    top = os.path.join(settings["root"], settings["work_folder"])
    if not os.path.isdir(top):
        say(f"There is no {settings['work_folder']}/ folder to index.")
        return 2
    text = render(settings, groups)
    path = os.path.join(top, INDEX_NAME)
    count = sum(len(documents) for _, documents in groups)
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            current = f.read().replace("\r\n", "\n")
        if not is_ours(current):
            say(f"{settings['work_folder']}/{INDEX_NAME} was written by hand, so it is left alone. "
                "Rename it, then run this again.")
            return 1
        if current == text:
            say(f"{settings['work_folder']}/{INDEX_NAME} is up to date, {count} documents.")
            return 0
    with open(path, "wb") as f:
        f.write(text.encode("utf-8"))
    say(f"Wrote {settings['work_folder']}/{INDEX_NAME}, {count} documents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

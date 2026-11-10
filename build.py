#!/usr/bin/env python3
"""Checks every skill and plugin in the kit, then builds one .plugin file per plugin into dist/.

  python build.py            from inside the kit folder
  python build.py <kit-dir>  from anywhere

Nothing is built if a check fails. The checks are the ones that fail silently when
a skill is loaded: a skill whose frontmatter cannot be read is simply never offered,
and a description that is too long is cut from the end without warning.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import zipfile

MAX_DESCRIPTION = 500      # characters. Longer ones are cut from the end when many skills are loaded
MAX_SKILL_BYTES = 20_000   # a skill larger than this is cut when it is re-attached after compaction
BANNED = {chr(0x2014): "em-dash", chr(0xE9): "e with acute accent"}
GUILLEMET = chr(0xAB)
FRONTMATTER = re.compile(r"\A---\nname: ([^\n]+)\ndescription: >\n  ([^\n]+)\n---\n")
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
VERSION = re.compile(r"\d+\.\d+\.\d+")


def plugins(kit: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p.parent.parent for p in (kit / "plugins").glob("*/.claude-plugin/plugin.json"))


def check_skill(skill: pathlib.Path, base: pathlib.Path) -> list[str]:
    """The checks every skill must pass, whether it ships in a plugin or on its own."""
    problems: list[str] = []

    def bad(what: str) -> None:
        problems.append(f"{skill.relative_to(base).as_posix()}: {what}")

    raw = skill.read_bytes()
    if bytes([13]) in raw:
        bad("has Windows line endings")
    if bytes([9]) in raw:
        bad("has a tab character")
    if len(raw) >= MAX_SKILL_BYTES:
        bad(f"is {len(raw)} bytes, the limit is {MAX_SKILL_BYTES}")
    text = raw.decode("utf-8")
    match = FRONTMATTER.match(text)
    if not match:
        bad("frontmatter must be exactly name, then description as a folded block of one line")
        return problems
    skill_name, description = match.group(1), match.group(2)
    if skill_name != skill.parent.name:
        bad(f"name {skill_name!r} does not match the folder {skill.parent.name!r}")
    if not NAME.fullmatch(skill_name):
        bad(f"name {skill_name!r} must be lowercase words joined by hyphens")
    if len(description) > MAX_DESCRIPTION:
        bad(f"description is {len(description)} characters, the limit is {MAX_DESCRIPTION}")
    if not re.search(r'"[^"]+"', description):
        bad("description has no English trigger phrase in double quotes")
    if GUILLEMET not in description:
        bad("description has no Norwegian trigger phrase in guillemets")
    elif description.index(GUILLEMET) > MAX_DESCRIPTION * 0.75:
        bad("the first Norwegian trigger sits in the last quarter, where it is cut first")
    if not text[match.end():].lstrip().startswith("# "):
        bad("body must start with a heading")
    if "design/<slug>" in text:
        bad("still holds the fixed design/ path, use <work-folder>/")
    for char, label in BANNED.items():
        if char in text:
            bad(f"contains the {label}")
    return problems


def check_plugin(root: pathlib.Path) -> list[str]:
    problems: list[str] = []

    def bad(where: pathlib.Path, what: str) -> None:
        problems.append(f"{where.relative_to(root.parent).as_posix()}: {what}")

    manifest_path = root / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{manifest_path}: cannot be read as JSON ({exc})"]
    name = str(manifest.get("name", ""))
    if name != root.name:
        bad(manifest_path, f"name {name!r} does not match the folder {root.name!r}")
    if not NAME.fullmatch(name):
        bad(manifest_path, f"name {name!r} must be lowercase words joined by hyphens")
    if name.startswith(("claude-", "anthropic-")):
        bad(manifest_path, "name must not start with claude- or anthropic-")
    if not VERSION.fullmatch(str(manifest.get("version", ""))):
        bad(manifest_path, "version must look like 1.2.3")
    if not str(manifest.get("description", "")).strip():
        bad(manifest_path, "description is missing")
    if not (root / "README.md").is_file():
        bad(root, "README.md is missing")
    if (root / "CLAUDE.md").exists():
        bad(root / "CLAUDE.md", "a plugin cannot carry a CLAUDE.md, it is never loaded")

    skills = sorted((root / "skills").glob("*/SKILL.md"))
    if not skills:
        bad(root, "no skills found")
    for folder in sorted(p for p in (root / "skills").iterdir() if p.is_dir()):
        if not (folder / "SKILL.md").is_file():
            bad(folder, "folder without a SKILL.md")
    for skill in skills:
        problems += check_skill(skill, root.parent)

    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in {".md", ".json"} and path.name != "SKILL.md":
            text = path.read_text(encoding="utf-8")
            for char, label in BANNED.items():
                if char in text:
                    bad(path, f"contains the {label}")
    return problems


def build_plugin(root: pathlib.Path, dist: pathlib.Path) -> pathlib.Path:
    version = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    out = dist / f"{root.name}-{version}.plugin"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(root).as_posix())
    with zipfile.ZipFile(out) as archive:
        packed = {n: archive.read(n) for n in archive.namelist()}
    source = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    if packed != source:
        raise SystemExit(f"{out.name} does not match its source")
    return out


def main() -> int:
    kit = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent).resolve()
    found = plugins(kit)
    if not found:
        print(f"no plugins found in {kit / 'plugins'}")
        return 1
    problems = [p for root in found for p in check_plugin(root)]
    own = sorted((kit / "skills").glob("*/SKILL.md"))
    for skill in own:
        problems += check_skill(skill, kit)
    names = [s.parent.name for s in own]
    names += [s.parent.name for root in found for s in (root / "skills").glob("*/SKILL.md")]
    for name in sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"two skills are both called {name}")
    if problems:
        print(f"{len(problems)} problem(s), nothing built:")
        for problem in problems:
            print("  -", problem)
        return 1
    print(f"checked {len(names)} skills in {len(found)} plugins and the kit's own skills folder")
    dist = kit / "dist"
    dist.mkdir(exist_ok=True)
    for root in found:
        out = build_plugin(root, dist)
        count = len(list((root / "skills").glob("*/SKILL.md")))
        print(f"built {out.name}: {count} skills, {out.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Sets up workspace-kit in a project folder. Standard library only.

  python setup.py install [--workspace PATH] [--dry-run] [options]
  python setup.py check   [--workspace PATH]
  python setup.py remove  [--workspace PATH] [--dry-run]

install  Wires the kit into the folder: settings file, rules, log, glossary,
         inbox, hooks and skills. Safe in an existing project: it adds, it never
         overwrites what it did not write, and running it again changes nothing.
         Run it again after editing workspace.yaml or after getting a newer kit.
check    Confirms that everything is in place and that the hooks really run.
remove   Takes out what install put in. Files you edited, and your own content
         (workspace.yaml, the log, the glossary, the inbox), are left alone.

Options for the first install, ignored once workspace.yaml exists:
  --client NAME                 who the work is for. Default: the folder name
  --work-folder NAME            where project folders live. Default: an existing
                                projects/ or design/, else projects
  --working-language NAME       the language the agent answers in
  --deliverable-language NAME   the language of documents meant for others
  --ban CHARACTER               a character that must never be written. Repeatable.
                                Give it as written or as a code point: U+2014
  --ban-in WHERE                files, replies, or files,replies

Personal defaults for those options can be kept in ~/.workspace-kit.yaml.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "hooks"))
import kitlib  # noqa: E402

KIT = "workspace-kit"
VERSION = "0.1.0"
KIT_DIR = ".workspace-kit"
MANIFEST = f"{KIT_DIR}/manifest.json"
BLOCK_START = "<!-- workspace-kit:start -->"
BLOCK_END = "<!-- workspace-kit:end -->"
HOOK_MARK = f"/{KIT_DIR}/hooks/"
WRITE_MATCHER = "Write|Edit|MultiEdit|NotebookEdit"

AGENTS_HEADER = (
    "# AGENTS.md\n\n"
    "Rules for every agent working in this workspace. `CLAUDE.md` imports this file, "
    "so there is one set of rules.\n\n"
    "Write your own rules above or below the marked section. The section between the "
    "markers belongs to workspace-kit and is rewritten by setup.\n\n"
)
CLAUDE_HEADER = "# CLAUDE.md\n\n"
CLAUDE_BLOCK = (
    "The rules for this workspace are in `AGENTS.md`, imported on the line below. "
    "Change them there, so every agent reads the same rules.\n\n"
    "@AGENTS.md\n\n"
    "If the rules from `AGENTS.md` are not in your context, read `AGENTS.md` in the "
    "workspace root before anything else and follow it.\n"
)


class Problem(Exception):
    """Something that stops setup before it writes anything."""


# ---------------------------------------------------------------- small helpers

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text(path: Path) -> tuple[str, bool]:
    """Text with Unix line endings, and whether the file used Windows ones."""
    raw = path.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def to_bytes(text: str, crlf: bool = False) -> bytes:
    return (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")


def render(template: str, values: dict) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", str(value))
    left = re.findall(r"\{\{[a-z_]+\}\}", out)
    if left:
        raise Problem(f"template has no value for {', '.join(sorted(set(left)))}")
    return out


class Report:
    ORDER = ["created", "updated", "removed", "kept", "conflict", "unchanged"]
    MEANING = {
        "created": "created",
        "updated": "updated",
        "removed": "removed",
        "kept": "left alone, you edited it",
        "conflict": "left alone, not written by the kit",
        "unchanged": "already in place",
    }

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, status: str, path: str, note: str = "") -> None:
        self.rows.append((status, path, note))

    def count(self, status: str) -> int:
        return sum(1 for row in self.rows if row[0] == status)

    def changed(self) -> bool:
        return any(row[0] in ("created", "updated", "removed") for row in self.rows)

    def show(self, verbose: bool) -> None:
        for status in self.ORDER:
            rows = [row for row in self.rows if row[0] == status]
            if not rows or (status == "unchanged" and not verbose):
                continue
            print(f"\n{self.MEANING[status].capitalize()} ({len(rows)}):")
            for _, path, note in rows:
                print(f"  {path}" + (f"  ({note})" if note else ""))


class Writer:
    """Every change to the workspace goes through here, so a dry run writes nothing."""

    def __init__(self, workspace: Path, dry_run: bool) -> None:
        self.workspace = workspace
        self.dry_run = dry_run

    def write(self, rel: str, data: bytes) -> None:
        if self.dry_run:
            return
        target = self.workspace / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def delete(self, rel: str) -> None:
        if self.dry_run:
            return
        target = self.workspace / rel
        if target.exists():
            target.unlink()
        folder = target.parent
        while folder != self.workspace and folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
            folder = folder.parent


# ---------------------------------------------------------------- what the kit installs

def managed_sources() -> dict[str, bytes]:
    """Files the kit owns in a workspace: target path and content."""
    out: dict[str, bytes] = {}
    for f in sorted((ROOT / "hooks").iterdir()):
        if f.is_file() and f.suffix in (".py", ".sh"):
            out[f"{KIT_DIR}/hooks/{f.name}"] = f.read_bytes().replace(b"\r\n", b"\n")
    for f in sorted((ROOT / "template" / "project").glob("*.md")):
        out[f"{KIT_DIR}/templates/project/{f.name}"] = f.read_bytes().replace(b"\r\n", b"\n")
    skills = sorted((ROOT / "skills").glob("*/SKILL.md")) + sorted((ROOT / "plugins").glob("*/skills/*/SKILL.md"))
    for f in skills:
        rel = f".claude/skills/{f.parent.name}/SKILL.md"
        if rel in out:
            raise Problem(f"two skills in the kit are both called {f.parent.name}")
        out[rel] = f.read_bytes().replace(b"\r\n", b"\n")
    return out


def template(name: str) -> str:
    return (ROOT / "template" / name).read_text(encoding="utf-8").replace("\r\n", "\n")


# ---------------------------------------------------------------- workspace.yaml

PLAIN = re.compile(r"[A-Za-z0-9 _.\-À-ɏ]+")
WORDS_YAML_READS = {"true", "false", "yes", "no", "on", "off", "null", "~"}


def yaml_text(value: str) -> str:
    value = str(value)
    plain = PLAIN.fullmatch(value) and value == value.strip() and value.lower() not in WORDS_YAML_READS
    if plain and not re.fullmatch(r"-?\d+", value):
        return value
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    raise Problem(f"cannot write a value that holds both kinds of quote: {value}")


def yaml_list(items: list[str], as_code_points: bool = False) -> str:
    shown = []
    for item in items:
        if as_code_points and len(item) == 1 and ord(item) > 126:
            shown.append(f"U+{ord(item):04X}")
        elif '"' not in item:
            shown.append(f'"{item}"')
        elif "'" not in item:
            shown.append(f"'{item}'")
        else:
            raise Problem(f"cannot write a value that holds both kinds of quote: {item}")
    return "[" + ", ".join(shown) + "]"


def personal_defaults() -> dict:
    path = Path(os.environ.get("WORKSPACE_KIT_PERSONAL") or Path.home() / ".workspace-kit.yaml")
    if not path.is_file():
        return {}
    try:
        return kitlib.parse_simple_yaml(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Problem(f"{path}: {exc}")


def detect_work_folder(workspace: Path) -> str:
    found = [name for name in ("projects", "design") if (workspace / name).is_dir()]
    return found[0] if len(found) == 1 else "projects"


def seed_settings(workspace: Path, args) -> dict:
    """Settings for a workspace that has no workspace.yaml yet."""
    raw = {k: v for k, v in personal_defaults().items() if k in kitlib.DEFAULTS and k not in ("client", "work_folder")}
    raw["client"] = args.client or workspace.name
    raw["work_folder"] = args.work_folder or detect_work_folder(workspace)
    if args.working_language:
        raw["working_language"] = args.working_language
    if args.deliverable_language:
        raw["deliverable_language"] = args.deliverable_language
    if args.ban:
        raw["banned_characters"] = list(args.ban)
    if args.ban_in:
        raw["banned_in"] = args.ban_in
    try:
        return kitlib.normalize(raw)
    except ValueError as exc:
        raise Problem(str(exc))


def workspace_yaml(settings: dict) -> str:
    return render(template("workspace.yaml"), {
        "client": yaml_text(settings["client"]),
        "work_folder": yaml_text(settings["work_folder"]),
        "working_language": yaml_text(settings["working_language"]),
        "deliverable_language": yaml_text(settings["deliverable_language"]),
        "banned_characters": yaml_list(settings["banned_characters"], as_code_points=True),
        "banned_in": "[" + ", ".join(settings["banned_in"]) + "]",
        "lint_every_days": settings["lint_every_days"],
        "style": yaml_list(settings["style"]),
    })


# ---------------------------------------------------------------- rules

def rules_block(settings: dict) -> str:
    banned_rule = ""
    if settings["banned_characters"]:
        names = ", ".join(kitlib.character_name(c) for c in settings["banned_characters"])
        where = " and ".join(w for w in ("files", "replies") if w in settings["banned_in"])
        banned_rule = (
            f"- Never write these characters in any text, quotations included: {names}. "
            f"A hook blocks them in {where}.\n"
        )
    return render(template("AGENTS.block.md"), {
        "version": VERSION,
        "work_folder": settings["work_folder"],
        "inbox": settings["inbox"],
        "working_language": settings["working_language"],
        "deliverable_language": settings["deliverable_language"],
        "lint_every_days": settings["lint_every_days"],
        "banned_rule": banned_rule,
        "style_rules": "".join(f"- {line}\n" for line in settings["style"]),
    })


def wrap(block: str) -> str:
    return f"{BLOCK_START}\n{block.strip()}\n{BLOCK_END}\n"


BLOCK = re.compile(re.escape(BLOCK_START) + r"\n.*?\n" + re.escape(BLOCK_END) + r"\n?", re.S)


def upsert_block(existing: str | None, block: str, header: str, name: str) -> str:
    if existing is None:
        return header + wrap(block)
    has_start, has_end = BLOCK_START in existing, BLOCK_END in existing
    if has_start != has_end or (has_start and not BLOCK.search(existing)):
        raise Problem(f"{name}: the workspace-kit markers are damaged. Restore both marker lines, or delete both.")
    if has_start:
        return BLOCK.sub(lambda _: wrap(block), existing, count=1)
    return existing.rstrip("\n") + "\n\n" + wrap(block)


def strip_block(existing: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", BLOCK.sub("", existing, count=1)).rstrip("\n") + "\n"


def imports_agents(text: str) -> bool:
    return bool(re.search(r"^@AGENTS\.md\s*$", BLOCK.sub("", text), re.M))


# ---------------------------------------------------------------- .claude/settings.json

def hook_command(script: str) -> str:
    return f'sh "$CLAUDE_PROJECT_DIR/{KIT_DIR}/hooks/run.sh" "$CLAUDE_PROJECT_DIR/{KIT_DIR}/hooks/{script}"'


def desired_hooks(settings: dict) -> list[tuple[str, str | None, str]]:
    hooks: list[tuple[str, str | None, str]] = [("SessionStart", "startup", "lint_nudge.py")]
    if settings["banned_characters"]:
        if "files" in settings["banned_in"]:
            hooks.append(("PreToolUse", WRITE_MATCHER, "banned_characters.py"))
        if "replies" in settings["banned_in"]:
            hooks.append(("Stop", None, "banned_characters.py"))
    return hooks


def is_ours(hook) -> bool:
    return isinstance(hook, dict) and HOOK_MARK in str(hook.get("command", ""))


def merge_hooks(data: dict, desired: list[tuple[str, str | None, str]]) -> dict:
    """Settings with the kit's hooks set to exactly `desired`. Everything else is kept as it is."""
    out = copy.deepcopy(data)
    hooks = out.get("hooks", {})
    if not isinstance(hooks, dict):
        raise Problem(".claude/settings.json: `hooks` is not a block of events")
    for event in list(hooks):
        groups = hooks[event]
        if not isinstance(groups, list) or not all(isinstance(g, dict) for g in groups):
            raise Problem(f".claude/settings.json: hooks for {event} are not a list of groups")
        kept = []
        for group in groups:
            inner = group.get("hooks")
            if not isinstance(inner, list) or not any(is_ours(h) for h in inner):
                kept.append(group)
                continue
            others = [h for h in inner if not is_ours(h)]
            if others:
                kept.append({**group, "hooks": others})
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    for event, matcher, script in desired:
        group: dict = {"matcher": matcher} if matcher else {}
        group["hooks"] = [{"type": "command", "command": hook_command(script)}]
        hooks.setdefault(event, []).append(group)
    if hooks:
        out["hooks"] = hooks
    else:
        out.pop("hooks", None)
    return out


def read_claude_settings(workspace: Path) -> tuple[dict, bool]:
    path = workspace / ".claude" / "settings.json"
    if not path.exists():
        return {}, False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Problem(f".claude/settings.json cannot be read as JSON, so it is left alone: {exc}")
    if not isinstance(data, dict):
        raise Problem(".claude/settings.json does not hold a block of settings")
    return data, True


def dump_json(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


# ---------------------------------------------------------------- manifest

def read_manifest(workspace: Path) -> dict:
    path = workspace / MANIFEST
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Problem(f"{MANIFEST} cannot be read: {exc}")
    return data if isinstance(data, dict) else {}


def load_workspace_settings(workspace: Path) -> dict:
    try:
        return kitlib.load_settings(str(workspace / kitlib.CONFIG_NAME))
    except ValueError as exc:
        raise Problem(f"workspace.yaml: {exc}")


# ---------------------------------------------------------------- install

def install(workspace: Path, args) -> int:
    report = Report()
    out = Writer(workspace, args.dry_run)

    # Everything that can refuse does so here, before anything is written.
    claude_settings, had_settings_file = read_claude_settings(workspace)
    manifest = read_manifest(workspace)
    sources = managed_sources()
    had_config = (workspace / kitlib.CONFIG_NAME).exists()
    settings = load_workspace_settings(workspace) if had_config else seed_settings(workspace, args)
    block = rules_block(settings)
    agents_path, claude_path = workspace / "AGENTS.md", workspace / "CLAUDE.md"
    agents_old, agents_crlf = read_text(agents_path) if agents_path.exists() else (None, False)
    claude_old, claude_crlf = read_text(claude_path) if claude_path.exists() else (None, False)
    agents_new = upsert_block(agents_old, block, AGENTS_HEADER, "AGENTS.md")
    if claude_old is not None and imports_agents(claude_old):
        claude_new = claude_old
    else:
        claude_new = upsert_block(claude_old, CLAUDE_BLOCK, CLAUDE_HEADER, "CLAUDE.md")
    new_settings = merge_hooks(claude_settings, desired_hooks(settings))

    created_files = set(manifest.get("created_files", []))

    # 1. workspace.yaml and the folders that hold your own content. Never overwritten.
    if had_config:
        ignored = [o for o in ("client", "work_folder", "working_language", "deliverable_language", "ban", "ban_in")
                   if getattr(args, o)]
        report.add("unchanged", kitlib.CONFIG_NAME,
                   "options on the command line are ignored, edit the file" if ignored else "")
    else:
        out.write(kitlib.CONFIG_NAME, workspace_yaml(settings).encode("utf-8"))
        report.add("created", kitlib.CONFIG_NAME)
    values = {"work_folder": settings["work_folder"], "inbox": settings["inbox"],
              "today": date.today().isoformat(), "version": VERSION}
    seeds = {
        f"{settings['work_folder']}/log.md": render(template("log.md"), values),
        f"{settings['work_folder']}/context.md": render(template("context.md"), values),
        f"{settings['inbox']}/README.md": render(template("inbox-README.md"), values),
    }
    for rel, text in seeds.items():
        if (workspace / rel).exists():
            report.add("unchanged", rel)
        else:
            out.write(rel, text.encode("utf-8"))
            report.add("created", rel)

    # 2. Files the kit owns: hooks, project templates, skills.
    recorded = dict(manifest.get("files", {}))
    files: dict[str, str] = {}
    for rel, data in sources.items():
        target = workspace / rel
        if not target.exists():
            out.write(rel, data)
            files[rel] = sha(data)
            report.add("created", rel)
            continue
        current = target.read_bytes().replace(b"\r\n", b"\n")
        if current == data:
            files[rel] = sha(data)
            report.add("unchanged", rel)
        elif rel in recorded and sha(current) == recorded[rel]:
            out.write(rel, data)
            files[rel] = sha(data)
            report.add("updated", rel)
        elif rel in recorded:
            files[rel] = recorded[rel]
            report.add("kept", rel)
        else:
            report.add("conflict", rel)
    for rel in sorted(set(recorded) - set(sources)):
        target = workspace / rel
        if target.exists() and sha(target.read_bytes().replace(b"\r\n", b"\n")) == recorded[rel]:
            out.delete(rel)
            report.add("removed", rel, "no longer part of the kit")
        elif target.exists():
            report.add("kept", rel, "no longer part of the kit")

    # 3. The rules: one marked section in AGENTS.md, and CLAUDE.md pointing at it.
    for rel, old, new, crlf in (("AGENTS.md", agents_old, agents_new, agents_crlf),
                                ("CLAUDE.md", claude_old, claude_new, claude_crlf)):
        if old is None:
            out.write(rel, to_bytes(new))
            created_files.add(rel)
            report.add("created", rel)
        elif old != new:
            out.write(rel, to_bytes(new, crlf))
            report.add("updated", rel, "only the marked workspace-kit section")
        else:
            report.add("unchanged", rel)

    # 4. Hooks in .claude/settings.json. Other settings and other hooks are kept.
    rel = ".claude/settings.json"
    if new_settings != claude_settings:
        out.write(rel, dump_json(new_settings))
        if not had_settings_file:
            created_files.add(rel)
        report.add("updated" if had_settings_file else "created", rel, "hooks only")
    else:
        report.add("unchanged", rel)

    # 5. The record of what was installed, so a later run can update and remove safely.
    new_manifest = {
        "kit": KIT,
        "version": VERSION,
        "files": dict(sorted(files.items())),
        "created_files": sorted(created_files),
    }
    if new_manifest != {k: manifest.get(k) for k in new_manifest}:
        out.write(MANIFEST, dump_json(new_manifest))

    report.show(args.verbose)
    conflicts = report.count("conflict")
    print()
    if args.dry_run:
        print("Dry run: nothing was written. Run again without --dry-run to do the above.")
    elif report.changed():
        print(f"{KIT} {VERSION} is set up in {workspace}.")
        print("Start a new session in this folder so the rules, skills and hooks load.")
    else:
        print(f"{KIT} {VERSION} was already set up here. Nothing changed.")
    if conflicts:
        print(f"{conflicts} file(s) with the same path existed already and were not touched. "
              "The kit's version of those is not installed.")
    return 0


# ---------------------------------------------------------------- remove

def remove(workspace: Path, args) -> int:
    manifest = read_manifest(workspace)
    if not manifest:
        print(f"{KIT} is not set up in {workspace}. Nothing to remove.")
        return 0
    report = Report()
    out = Writer(workspace, args.dry_run)
    claude_settings, had_settings_file = read_claude_settings(workspace)
    created_files = set(manifest.get("created_files", []))

    for rel, recorded in sorted(manifest.get("files", {}).items()):
        target = workspace / rel
        if not target.exists():
            continue
        if sha(target.read_bytes().replace(b"\r\n", b"\n")) == recorded:
            out.delete(rel)
            report.add("removed", rel)
        else:
            report.add("kept", rel)

    for rel, header in (("AGENTS.md", AGENTS_HEADER), ("CLAUDE.md", CLAUDE_HEADER)):
        path = workspace / rel
        if not path.exists():
            continue
        text, crlf = read_text(path)
        if BLOCK_START not in text:
            continue
        rest = strip_block(text)
        if rel in created_files and rest.strip() == header.strip():
            out.delete(rel)
            report.add("removed", rel)
        else:
            out.write(rel, to_bytes(rest, crlf))
            report.add("updated", rel, "the workspace-kit section is taken out")

    if had_settings_file:
        rel = ".claude/settings.json"
        cleaned = merge_hooks(claude_settings, [])
        if cleaned != claude_settings:
            if not cleaned and rel in created_files:
                out.delete(rel)
                report.add("removed", rel)
            else:
                out.write(rel, dump_json(cleaned))
                report.add("updated", rel, "the kit's hooks are taken out")

    out.delete(MANIFEST)
    report.show(verbose=True)
    print()
    if args.dry_run:
        print("Dry run: nothing was removed.")
    else:
        print(f"{KIT} is removed from {workspace}. workspace.yaml, the log, the glossary and the inbox are yours and were left.")
    return 0


# ---------------------------------------------------------------- check

def find_shell() -> str | None:
    """The `sh` that hooks run under. On Windows it comes with Git and is often not on the path."""
    found = shutil.which("sh") or shutil.which("bash")
    if found:
        return found
    candidates = [os.environ.get("CLAUDE_CODE_GIT_BASH_PATH", "")]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LocalAppData")):
        if base:
            candidates += [os.path.join(base, "Git", "bin", "sh.exe"), os.path.join(base, "Programs", "Git", "bin", "sh.exe")]
    return next((c for c in candidates if c and os.path.isfile(c)), None)


def run_hook(workspace: Path, script: str, event: dict | None) -> tuple[int | None, str]:
    shell = find_shell()
    if not shell:
        return None, "no `sh` on this machine. On Windows, install Git for Windows."
    hooks = workspace / KIT_DIR / "hooks"
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(workspace)}
    env.pop("WORKSPACE_KIT_CONFIG", None)
    try:
        done = subprocess.run([shell, str(hooks / "run.sh"), str(hooks / script)],
                              input=json.dumps(event or {}, ensure_ascii=False).encode("utf-8"),
                              capture_output=True, timeout=60, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    return done.returncode, (done.stderr or done.stdout).decode("utf-8", errors="replace").strip()


def check(workspace: Path, args) -> int:
    rows: list[tuple[bool, str, str]] = []

    def add(ok: bool, what: str, detail: str = "") -> None:
        rows.append((ok, what, detail))

    manifest = read_manifest(workspace)
    if not manifest:
        print(f"{KIT} is not set up in {workspace}. Run: python setup.py install --workspace \"{workspace}\"")
        return 1
    add(manifest.get("version") == VERSION, "kit version",
        f"installed {manifest.get('version')}, this kit is {VERSION}"
        + ("" if manifest.get("version") == VERSION else ". Run install to update"))

    try:
        settings = load_workspace_settings(workspace)
        add(True, "workspace.yaml", f"client {settings['client'] or '(none)'}, work folder {settings['work_folder']}/")
    except Problem as exc:
        add(False, "workspace.yaml", str(exc))
        settings = None

    missing = [rel for rel in manifest.get("files", {}) if not (workspace / rel).exists()]
    edited = [rel for rel, recorded in manifest.get("files", {}).items()
              if (workspace / rel).exists() and sha((workspace / rel).read_bytes().replace(b"\r\n", b"\n")) != recorded]
    add(not missing, "installed files",
        f"{len(manifest.get('files', {}))} in place" + (f", {len(edited)} edited by you" if edited else "")
        if not missing else "missing: " + ", ".join(missing[:5]) + ". Run install")

    agents = workspace / "AGENTS.md"
    has_block = agents.exists() and BLOCK.search(read_text(agents)[0]) is not None
    add(has_block, "rules in AGENTS.md", "" if has_block else "the workspace-kit section is missing. Run install")
    claude = workspace / "CLAUDE.md"
    points = claude.exists() and "@AGENTS.md" in read_text(claude)[0]
    add(points, "CLAUDE.md imports AGENTS.md", "" if points else "Run install")

    if settings:
        work = workspace / settings["work_folder"]
        add((work / "log.md").is_file(), f"{settings['work_folder']}/log.md")
        try:
            claude_settings, _ = read_claude_settings(workspace)
            wired = merge_hooks(claude_settings, desired_hooks(settings)) == claude_settings
            add(wired, "hooks in .claude/settings.json",
                "" if wired else "they do not match workspace.yaml. Run install")
        except Problem as exc:
            add(False, "hooks in .claude/settings.json", str(exc))

        code, text = run_hook(workspace, "lint_nudge.py", None)
        add(code == 0, "session start hook runs", text if code != 0 else "")
        if settings["banned_characters"]:
            bad = "a" + settings["banned_characters"][0] + "b"
            if "files" in settings["banned_in"]:
                code, text = run_hook(workspace, "banned_characters.py", {
                    "hook_event_name": "PreToolUse", "tool_name": "Write",
                    "tool_input": {"file_path": "x.md", "content": bad}})
                add(code == 2, "a banned character in a file is blocked", "" if code == 2 else f"exit {code}. {text}")
                code, text = run_hook(workspace, "banned_characters.py", {
                    "hook_event_name": "PreToolUse", "tool_name": "Write",
                    "tool_input": {"file_path": "x.md", "content": "plain text"}})
                add(code == 0, "clean text in a file is allowed", "" if code == 0 else f"exit {code}. {text}")
            if "replies" in settings["banned_in"]:
                code, text = run_hook(workspace, "banned_characters.py", {
                    "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": bad})
                add(code == 2, "a banned character in a reply is blocked", "" if code == 2 else f"exit {code}. {text}")

    for ok, what, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + (f": {detail}" if detail else ""))
    failed = [r for r in rows if not r[0]]
    print()
    print("Everything is in place." if not failed else f"{len(failed)} check(s) failed.")
    return 1 if failed else 0


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=f"Set up {KIT} {VERSION} in a project folder.")
    parser.add_argument("command", nargs="?", default="install", choices=["install", "check", "remove"])
    parser.add_argument("--workspace", default=".", help="the project folder. Default: the current folder")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, write nothing")
    parser.add_argument("--verbose", action="store_true", help="also list what was already in place")
    parser.add_argument("--client")
    parser.add_argument("--work-folder")
    parser.add_argument("--working-language")
    parser.add_argument("--deliverable-language")
    parser.add_argument("--ban", action="append")
    parser.add_argument("--ban-in")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    try:
        if not workspace.is_dir():
            raise Problem(f"{workspace} is not a folder")
        if workspace == ROOT or ROOT in workspace.parents:
            raise Problem("that is the kit itself. Point --workspace at the project you want to set up.")
        return {"install": install, "check": check, "remove": remove}[args.command](workspace, args)
    except Problem as exc:
        print(f"Stopped, nothing was changed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

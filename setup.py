#!/usr/bin/env python3
"""Sets up workspace-kit in a project folder. Standard library only.

  python setup.py install [--workspace PATH] [--dry-run] [options]
  python setup.py check   [--workspace PATH]
  python setup.py remove  [--workspace PATH] [--dry-run]

install  Wires the kit into the folder: settings file, rules, log, glossary,
         inbox, hooks and skills, for Claude Code, Codex and OpenCode. Safe in
         an existing project: it adds, it never overwrites what it did not
         write, and running it again changes nothing. Run it again after
         editing workspace.yaml or after getting a newer kit.
check    Confirms that everything is in place and that the hooks really run.
remove   Takes out what install put in. Files you edited, and your own content
         (workspace.yaml, the log, the glossary, the inbox), are left alone.

Options for the first install, ignored once workspace.yaml exists:
  --client NAME                 who the work is for. Default: the folder name
  --work-folder NAME            where project folders live. Default: an existing
                                projects/ or design/, else projects
  --agents LIST                 which agents to wire: claude, codex, opencode.
                                Default: all three
  --git, --no-git               whether to keep the folder under git. With --git a
                                repository is created if there is none. With
                                neither, a person running setup is asked, and an
                                agent running it is told to ask the owner. These
                                two also work on later runs
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
SOURCE = ROOT / "kit"
sys.path.insert(0, str(SOURCE / "hooks"))
import kitlib  # noqa: E402

KIT = "workspace-kit"
VERSION = "0.2.1"
KIT_DIR = ".workspace-kit"
MANIFEST = f"{KIT_DIR}/manifest.json"
BLOCK_START = "<!-- workspace-kit:start -->"
BLOCK_END = "<!-- workspace-kit:end -->"
HOOK_MARK = f"{KIT_DIR}/hooks/"
CLAUDE_SETTINGS = ".claude/settings.json"
CODEX_HOOKS = ".codex/hooks.json"
OPENCODE_PLUGIN = ".opencode/plugins/workspace-kit.js"
BACKSLASH = chr(92)

AGENTS_HEADER = (
    "# AGENTS.md\n\n"
    "Rules for every agent working in this workspace. This file is the single source: "
    "an agent that reads another file is pointed here.\n\n"
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


def unix(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def read_text(path: Path) -> tuple[str, bool]:
    """Text with Unix line endings, and whether the file used Windows ones."""
    raw = path.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def to_bytes(text: str, crlf: bool = False) -> bytes:
    return (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")


def render(template_text: str, values: dict) -> str:
    out = template_text
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

def skill_sources() -> dict[str, bytes]:
    found = sorted((SOURCE / "skills").glob("*/SKILL.md")) + sorted((SOURCE / "plugins").glob("*/skills/*/SKILL.md"))
    out: dict[str, bytes] = {}
    for f in found:
        if f.parent.name in out:
            raise Problem(f"two skills in the kit are both called {f.parent.name}")
        out[f.parent.name] = unix(f.read_bytes())
    return out


def skill_folders(agents: list[str]) -> list[str]:
    """Where each agent looks. Claude Code reads only its own folder. Codex reads the
    shared one. OpenCode reads both and keeps one copy of a skill it finds twice."""
    folders = []
    if "claude" in agents:
        folders.append(".claude/skills")
    if "codex" in agents or "opencode" in agents:
        folders.append(".agents/skills")
    return folders


def managed_sources(settings: dict) -> dict[str, bytes]:
    """Files the kit owns in a workspace: target path and content."""
    out: dict[str, bytes] = {}
    for f in sorted((SOURCE / "hooks").iterdir()):
        if f.is_file() and f.suffix in (".py", ".sh", ".cmd"):
            out[f"{KIT_DIR}/hooks/{f.name}"] = unix(f.read_bytes())
    for f in sorted((SOURCE / "template" / "project").glob("*.md")):
        out[f"{KIT_DIR}/templates/project/{f.name}"] = unix(f.read_bytes())
    for name, data in skill_sources().items():
        for folder in skill_folders(settings["agents"]):
            out[f"{folder}/{name}/SKILL.md"] = data
    if "opencode" in settings["agents"]:
        out[OPENCODE_PLUGIN] = unix((SOURCE / "adapters" / "opencode" / "workspace-kit.js").read_bytes())
    return out


def template(name: str) -> str:
    return (SOURCE / "template" / name).read_text(encoding="utf-8").replace("\r\n", "\n")


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
    if args.agents:
        raw["agents"] = args.agents
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
        "agents": "[" + ", ".join(settings["agents"]) + "]",
        "git": {True: "yes", False: "no", None: "ask"}[settings["git"]],
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


# ---------------------------------------------------------------- hooks, per agent

def hook_events(settings: dict) -> list[tuple[str, str | None, str | None, str]]:
    """What should be wired: event, Claude Code's matcher, Codex's matcher, script."""
    events: list[tuple[str, str | None, str | None, str]] = [
        ("SessionStart", "startup", "startup", "lint_nudge.py"),
    ]
    if settings["banned_characters"]:
        if "files" in settings["banned_in"]:
            events.append(("PreToolUse", "Write|Edit|MultiEdit|NotebookEdit", "apply_patch|Edit|Write",
                           "banned_characters.py"))
        if "replies" in settings["banned_in"]:
            events.append(("Stop", None, None, "banned_characters.py"))
    return events


def claude_handler(script: str) -> dict:
    """Claude Code names the project folder, and runs hooks through sh on every system."""
    return {
        "type": "command",
        "command": f'sh "$CLAUDE_PROJECT_DIR/{KIT_DIR}/hooks/run.sh" "$CLAUDE_PROJECT_DIR/{KIT_DIR}/hooks/{script}"',
    }


def codex_handler(script: str) -> dict:
    """Codex runs hooks in the folder the session started in, and has a Windows form."""
    windows = f"{KIT_DIR}/hooks/".replace("/", BACKSLASH)
    return {
        "type": "command",
        "command": f"sh {KIT_DIR}/hooks/run.sh {KIT_DIR}/hooks/{script}",
        "commandWindows": f"cmd /c {windows}run.cmd {windows}{script}",
    }


def wanted_groups(settings: dict, agent: str) -> list[tuple[str, dict]]:
    if agent not in settings["agents"]:
        return []
    groups = []
    for event, claude_matcher, codex_matcher, script in hook_events(settings):
        matcher = claude_matcher if agent == "claude" else codex_matcher
        handler = claude_handler(script) if agent == "claude" else codex_handler(script)
        group: dict = {"matcher": matcher} if matcher else {}
        group["hooks"] = [handler]
        groups.append((event, group))
    return groups


def is_ours(hook) -> bool:
    return isinstance(hook, dict) and HOOK_MARK in str(hook.get("command", ""))


def merge_hooks(data: dict, groups: list[tuple[str, dict]], name: str) -> dict:
    """The file's content with the kit's hooks set to exactly `groups`. Everything else is kept."""
    out = copy.deepcopy(data)
    hooks = out.get("hooks", {})
    if not isinstance(hooks, dict):
        raise Problem(f"{name}: `hooks` is not a block of events")
    for event in list(hooks):
        existing = hooks[event]
        if not isinstance(existing, list) or not all(isinstance(g, dict) for g in existing):
            raise Problem(f"{name}: hooks for {event} are not a list of groups")
        kept = []
        for group in existing:
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
    for event, group in groups:
        hooks.setdefault(event, []).append(copy.deepcopy(group))
    if hooks:
        out["hooks"] = hooks
    else:
        out.pop("hooks", None)
    return out


def read_json(workspace: Path, rel: str) -> tuple[dict, bool]:
    path = workspace / rel
    if not path.exists():
        return {}, False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Problem(f"{rel} cannot be read as JSON, so it is left alone: {exc}")
    if not isinstance(data, dict):
        raise Problem(f"{rel} does not hold a block of settings")
    return data, True


def dump_json(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


HOOK_FILES = ((CLAUDE_SETTINGS, "claude"), (CODEX_HOOKS, "codex"))


# ---------------------------------------------------------------- git

GITIGNORE = (
    "# Files that are not work: system files, editor leftovers, office lock files.\n"
    ".DS_Store\nThumbs.db\ndesktop.ini\n__pycache__/\n*.pyc\n*.swp\n~$*\n.~lock.*#\n"
)
SYNCED = ("jottacloud", "dropbox", "onedrive", "icloud", "google drive", "googledrive", "cloudstorage")


def git(workspace: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(workspace), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def git_state(workspace: Path) -> str:
    """`none` when git is not installed, `here` for a repository rooted in the workspace,
    `above` when the workspace sits inside a larger repository, else `no`."""
    if not shutil.which("git"):
        return "none"
    top = git(workspace, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return "no"
    same = Path(top.stdout.strip()).resolve() == workspace.resolve()
    return "here" if same else "above"


def interactive() -> bool:
    """True when a person is at the keyboard. An agent running setup is not one."""
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def ask_about_git(workspace: Path) -> bool:
    print(f"\n{workspace} is not under git.")
    print("With git, every piece of work becomes a commit, so you can see what was done, when, and by which agent.")
    answer = input("Create a git repository here? [Y/n] ").strip().lower()
    return answer in ("", "y", "yes", "j", "ja")


def set_yaml_line(text: str, key: str, value: str) -> str:
    """Changes one top-level `key: value` line and nothing else. Adds the line if it is missing."""
    line = re.compile(rf"^{re.escape(key)}:[^\n]*$", re.M)
    if line.search(text):
        return line.sub(f"{key}: {value}", text, count=1)
    return text.rstrip("\n") + f"\n\n{key}: {value}\n"


def looks_synced(workspace: Path) -> bool:
    return any(word in part.lower() for part in workspace.parts for word in SYNCED)


def start_repository(workspace: Path, paths: list[str], personal: dict) -> list[str]:
    """Creates the repository and commits what setup just wrote. Returns notes for the user."""
    notes = []
    if git(workspace, "init", "-b", "main").returncode != 0:
        if git(workspace, "init").returncode != 0:
            return ["Git could not create a repository here, so nothing is committed."]
        git(workspace, "symbolic-ref", "HEAD", "refs/heads/main")
    # One folder is often opened from several systems. These two settings stop git
    # from reporting changes that are only a difference between those systems.
    git(workspace, "config", "core.fileMode", "false")
    git(workspace, "config", "core.autocrlf", "false")
    if not (workspace / ".gitignore").exists():
        (workspace / ".gitignore").write_text(GITIGNORE, encoding="utf-8", newline="\n")
        paths = [*paths, ".gitignore"]

    identity: list[str] = []
    named = all(git(workspace, "config", key).stdout.strip() for key in ("user.name", "user.email"))
    if not named and personal.get("git_name") and personal.get("git_email"):
        git(workspace, "config", "user.name", str(personal["git_name"]))
        git(workspace, "config", "user.email", str(personal["git_email"]))
    elif not named:
        identity = ["-c", f"user.name={KIT}", "-c", f"user.email={KIT}@localhost"]
        notes.append("Git has no name and email on this machine, so commits cannot say who did the work. "
                     'Set them: git config --global user.name "Your Name" and git config --global user.email you@example.com')

    existing = [p for p in paths if (workspace / p).exists()]
    git(workspace, "add", "--", *existing)
    done = git(workspace, *identity, "commit", "-m", f"Workspace set up with {KIT} {VERSION}")
    if done.returncode != 0:
        notes.append("Git created the repository but could not make the first commit: "
                     + (done.stderr.strip().splitlines() or ["unknown reason"])[-1])
    left = [l for l in git(workspace, "status", "--porcelain").stdout.splitlines() if l.strip()]
    if left:
        notes.append(f"{len(left)} file(s) that were here before are not committed. "
                     "Commit them when you want them under version control.")
    return notes


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
    manifest = read_manifest(workspace)
    had_config = (workspace / kitlib.CONFIG_NAME).exists()
    settings = load_workspace_settings(workspace) if had_config else seed_settings(workspace, args)
    agents = settings["agents"]

    # Git is the owner's call. An answer on the command line wins, then the one in
    # workspace.yaml. With neither, a person at the keyboard is asked, and an agent
    # is told to go and ask.
    repository = git_state(workspace)
    wanted_before = settings["git"]
    if args.git or args.no_git:
        settings["git"] = bool(args.git)
    elif settings["git"] is None and repository == "no" and interactive() and not args.dry_run:
        settings["git"] = ask_about_git(workspace)
    config_text = None
    if had_config and settings["git"] != wanted_before:
        old_text, config_crlf = read_text(workspace / kitlib.CONFIG_NAME)
        answer = {True: "yes", False: "no", None: "ask"}[settings["git"]]
        config_text = to_bytes(set_yaml_line(old_text, "git", answer), config_crlf)

    sources = managed_sources(settings)
    block = rules_block(settings)
    agents_path, claude_path = workspace / "AGENTS.md", workspace / "CLAUDE.md"
    agents_old, agents_crlf = read_text(agents_path) if agents_path.exists() else (None, False)
    claude_old, claude_crlf = read_text(claude_path) if claude_path.exists() else (None, False)
    agents_new = upsert_block(agents_old, block, AGENTS_HEADER, "AGENTS.md")
    created_files = set(manifest.get("created_files", []))
    if "claude" in agents:
        if claude_old is not None and imports_agents(claude_old):
            claude_new = claude_old
        else:
            claude_new = upsert_block(claude_old, CLAUDE_BLOCK, CLAUDE_HEADER, "CLAUDE.md")
    elif claude_old is not None and BLOCK_START in claude_old:
        upsert_block(claude_old, CLAUDE_BLOCK, CLAUDE_HEADER, "CLAUDE.md")  # refuses damaged markers
        claude_new = strip_block(claude_old)
        if "CLAUDE.md" in created_files and claude_new.strip() == CLAUDE_HEADER.strip():
            claude_new = None
    else:
        claude_new = claude_old
    hook_files = {}
    for rel, agent in HOOK_FILES:
        data, existed = read_json(workspace, rel)
        hook_files[rel] = (data, existed, merge_hooks(data, wanted_groups(settings, agent), rel))

    # 1. workspace.yaml and the folders that hold your own content. Never overwritten.
    if had_config:
        ignored = [o for o in ("client", "work_folder", "agents", "working_language",
                               "deliverable_language", "ban", "ban_in") if getattr(args, o)]
        note = "other options on the command line are ignored, edit the file" if ignored else ""
        if config_text is not None:
            out.write(kitlib.CONFIG_NAME, config_text)
            report.add("updated", kitlib.CONFIG_NAME, "only the git line" + (". " + note if note else ""))
        else:
            report.add("unchanged", kitlib.CONFIG_NAME, note)
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

    # 2. Files the kit owns: hooks, project templates, skills, the OpenCode adapter.
    recorded = dict(manifest.get("files", {}))
    files: dict[str, str] = {}
    for rel, data in sources.items():
        target = workspace / rel
        if not target.exists():
            out.write(rel, data)
            files[rel] = sha(data)
            report.add("created", rel)
            continue
        current = unix(target.read_bytes())
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
        if target.exists() and sha(unix(target.read_bytes())) == recorded[rel]:
            out.delete(rel)
            report.add("removed", rel, "no longer wanted")
        elif target.exists():
            report.add("kept", rel, "no longer wanted")

    # 3. The rules: one marked section in AGENTS.md, and CLAUDE.md pointing at it.
    for rel, old, new, crlf in (("AGENTS.md", agents_old, agents_new, agents_crlf),
                                ("CLAUDE.md", claude_old, claude_new, claude_crlf)):
        if old is None and new is None:
            continue
        if old is None:
            out.write(rel, to_bytes(new))
            created_files.add(rel)
            report.add("created", rel)
        elif new is None:
            out.delete(rel)
            created_files.discard(rel)
            report.add("removed", rel, "Claude Code is not among the agents")
        elif old != new:
            out.write(rel, to_bytes(new, crlf))
            report.add("updated", rel, "only the marked workspace-kit section")
        else:
            report.add("unchanged", rel)

    # 4. Hooks, in each agent's own file. Other settings and other hooks are kept.
    for rel, (old, existed, new) in hook_files.items():
        if new == old:
            if existed:
                report.add("unchanged", rel)
        elif not new and rel in created_files:
            out.delete(rel)
            created_files.discard(rel)
            report.add("removed", rel, "no hooks left for this agent")
        else:
            out.write(rel, dump_json(new))
            if not existed:
                created_files.add(rel)
            report.add("updated" if existed else "created", rel, "hooks only")

    # 5. The record of what was installed, so a later run can update and remove safely.
    new_manifest = {
        "kit": KIT,
        "version": VERSION,
        "files": dict(sorted(files.items())),
        "created_files": sorted(created_files),
    }
    if new_manifest != {k: manifest.get(k) for k in new_manifest}:
        out.write(MANIFEST, dump_json(new_manifest))

    # 6. Git, so every piece of work can be a commit. Only ever created, never rewritten.
    notes: list[str] = []
    if settings["git"] is None and repository == "no":
        notes.append("No git repository was created, because nobody has said whether to. Ask the owner, "
                     "then run setup again with --git to create one, or with --no-git to leave it out.")
    if settings["git"]:
        state = repository
        if state == "none":
            notes.append("Git is not installed, so the work here cannot be committed. Install git and run setup again.")
        elif state == "no":
            report.add("created", ".git", "a new repository, with this setup as its first commit")
            if not args.dry_run:
                # Everything the kit put here, also when the repository comes on a later run.
                # Files that were in the folder before are the owner's to commit.
                ours = {*files, *seeds, "AGENTS.md", "CLAUDE.md", CLAUDE_SETTINGS, CODEX_HOOKS,
                        kitlib.CONFIG_NAME, MANIFEST}
                notes += start_repository(workspace, sorted(ours), personal_defaults())
            if looks_synced(workspace):
                notes.append("This folder looks like it is synced between devices. Git works here, "
                             "but work in it from one device at a time, and let the sync finish before you switch.")
        elif report.changed():
            notes.append("This folder is already under git. Setup committed nothing: commit the new files when you are ready.")

    report.show(args.verbose)
    for note in notes:
        print(f"\nNote: {note}")
    conflicts = report.count("conflict")
    print()
    if args.dry_run:
        print("Dry run: nothing was written. Run again without --dry-run to do the above.")
    elif report.changed():
        print(f"{KIT} {VERSION} is set up in {workspace} for: {', '.join(agents)}.")
        print("Start a new session in this folder so the rules, skills and hooks load.")
        if "codex" in agents:
            print("Codex runs a project's hooks only after you have approved them: open /hooks in Codex once.")
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
    hook_files = {rel: read_json(workspace, rel) for rel, _ in HOOK_FILES}
    created_files = set(manifest.get("created_files", []))

    for rel, recorded in sorted(manifest.get("files", {}).items()):
        target = workspace / rel
        if not target.exists():
            continue
        if sha(unix(target.read_bytes())) == recorded:
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

    for rel, (data, existed) in hook_files.items():
        if not existed:
            continue
        cleaned = merge_hooks(data, [], rel)
        if cleaned == data:
            continue
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


def run_hook(workspace: Path, script: str, event: dict | None, launcher: str = "sh") -> tuple[int | None, str]:
    """Runs an installed hook the way an agent does: UTF-8 JSON on stdin, an exit code back."""
    hooks = workspace / KIT_DIR / "hooks"
    if launcher == "cmd":
        # Exactly the form Codex is given: paths from the project folder, so a
        # folder name with a space in it never reaches the Windows shell.
        relative = f"{KIT_DIR}/hooks/".replace("/", BACKSLASH)
        command = ["cmd", "/c", relative + "run.cmd", relative + script]
    else:
        shell = find_shell()
        if not shell:
            return None, "no `sh` on this machine. On Windows, install Git for Windows."
        command = [shell, str(hooks / "run.sh"), str(hooks / script)]
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(workspace)}
    for name in ("WORKSPACE_KIT_CONFIG", "WORKSPACE_KIT_ROOT"):
        env.pop(name, None)
    try:
        done = subprocess.run(command, input=json.dumps(event or {}, ensure_ascii=False).encode("utf-8"),
                              capture_output=True, timeout=60, env=env, cwd=str(workspace))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    return done.returncode, (done.stderr or done.stdout).decode("utf-8", errors="replace").strip()


def check(workspace: Path, args) -> int:
    rows: list[tuple[bool, str, str]] = []
    notes: list[str] = []

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
        add(True, "workspace.yaml", f"client {settings['client'] or '(none)'}, work folder {settings['work_folder']}/, "
                                    f"agents {', '.join(settings['agents'])}")
    except Problem as exc:
        add(False, "workspace.yaml", str(exc))
        settings = None

    recorded = manifest.get("files", {})
    missing = [rel for rel in recorded if not (workspace / rel).exists()]
    edited = [rel for rel, digest in recorded.items()
              if (workspace / rel).exists() and sha(unix((workspace / rel).read_bytes())) != digest]
    add(not missing, "installed files",
        f"{len(recorded)} in place" + (f", {len(edited)} edited by you" if edited else "")
        if not missing else "missing: " + ", ".join(missing[:5]) + ". Run install")

    agents_file = workspace / "AGENTS.md"
    has_block = agents_file.exists() and BLOCK.search(read_text(agents_file)[0]) is not None
    add(has_block, "rules in AGENTS.md", "" if has_block else "the workspace-kit section is missing. Run install")

    if settings:
        agents = settings["agents"]
        wanted = set(managed_sources(settings))
        unwired = sorted(wanted - set(recorded) - {rel for rel in wanted if (workspace / rel).exists()})
        add(not unwired, "files match workspace.yaml",
            "" if not unwired else "not installed: " + ", ".join(unwired[:3]) + ". Run install")
        add((workspace / settings["work_folder"] / "log.md").is_file(), f"{settings['work_folder']}/log.md")

        if "claude" in agents:
            claude = workspace / "CLAUDE.md"
            points = claude.exists() and "@AGENTS.md" in read_text(claude)[0]
            add(points, "Claude Code: CLAUDE.md imports AGENTS.md", "" if points else "Run install")
        for rel, agent in HOOK_FILES:
            label = "Claude Code" if agent == "claude" else "Codex"
            try:
                data, _ = read_json(workspace, rel)
                wired = merge_hooks(data, wanted_groups(settings, agent), rel) == data
                if agent in agents or not wired:
                    add(wired, f"{label}: hooks in {rel}", "" if wired else "they do not match workspace.yaml. Run install")
            except Problem as exc:
                add(False, f"{label}: hooks in {rel}", str(exc))
        if "opencode" in agents:
            add((workspace / OPENCODE_PLUGIN).is_file(), f"OpenCode: adapter in {OPENCODE_PLUGIN}")
        folders = skill_folders(agents)
        if len(folders) == 2:
            differing = [name for name in skill_sources()
                         if (workspace / folders[0] / name / "SKILL.md").is_file()
                         and (workspace / folders[1] / name / "SKILL.md").is_file()
                         and unix((workspace / folders[0] / name / "SKILL.md").read_bytes())
                         != unix((workspace / folders[1] / name / "SKILL.md").read_bytes())]
            if differing:
                notes.append(f"These skills differ between {folders[0]} and {folders[1]}, so agents see different "
                             f"versions: {', '.join(differing)}.")

        banned = settings["banned_characters"]
        bad = "a" + banned[0] + "b" if banned else ""
        launchers = ["sh"]
        if "codex" in agents and os.name == "nt":
            launchers.append("cmd")
        for launcher in launchers:
            via = "" if launcher == "sh" else " (Windows shell)"
            code, text = run_hook(workspace, "lint_nudge.py", None, launcher)
            add(code == 0, f"session start hook runs{via}", text if code != 0 else "")
            if not banned:
                continue
            if "files" in settings["banned_in"]:
                samples = [("in a file", {"hook_event_name": "PreToolUse", "tool_name": "Write",
                                          "tool_input": {"file_path": "x.md", "content": bad}}, 2),
                           ("clean text in a file", {"hook_event_name": "PreToolUse", "tool_name": "Write",
                                                     "tool_input": {"file_path": "x.md", "content": "plain"}}, 0)]
                if "codex" in agents:
                    patch = "\n".join(["*** Begin Patch", "*** Update File: x.md", "@@", "-old", "+" + bad, "*** End Patch"])
                    samples.append(("in a Codex patch", {"hook_event_name": "PreToolUse", "tool_name": "apply_patch",
                                                         "tool_input": {"command": patch}}, 2))
                for label, event, expected in samples:
                    code, text = run_hook(workspace, "banned_characters.py", event, launcher)
                    what = f"{label} is allowed{via}" if expected == 0 else f"a banned character {label} is blocked{via}"
                    add(code == expected, what, "" if code == expected else f"exit {code}. {text}")
            if "replies" in settings["banned_in"]:
                code, text = run_hook(workspace, "banned_characters.py", {
                    "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": bad}, launcher)
                add(code == 2, f"a banned character in a reply is blocked{via}", "" if code == 2 else f"exit {code}. {text}")

        if settings["git"] is None and git_state(workspace) == "no":
            notes.append("Nobody has said whether this folder should be under git. Run install with --git or --no-git.")
        if settings["git"]:
            state = git_state(workspace)
            if state == "none":
                notes.append("Git is not installed, so the work here cannot be committed.")
            else:
                add(state != "no", "git repository", "" if state != "no" else "there is none. Run install")
                if state != "no":
                    waiting = [l for l in git(workspace, "status", "--porcelain").stdout.splitlines() if l.strip()]
                    if waiting:
                        notes.append(f"{len(waiting)} change(s) are not committed yet.")
        if "codex" in agents:
            notes.append("Codex runs a project's hooks only after you have approved them. Open /hooks in Codex "
                         "once. This check cannot see whether that is done.")
        if "opencode" in agents and banned and "replies" in settings["banned_in"]:
            notes.append("OpenCode has no way to send a reply back, so banned characters are stopped in files "
                         "only. In replies they are a rule the agent is asked to follow.")

    for ok, what, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + (f": {detail}" if detail else ""))
    for note in notes:
        print(f"  note  {note}")
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
    parser.add_argument("--agents", help="claude, codex, opencode. Default: all three")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--git", action="store_true", help="keep the folder under git, creating a repository if there is none")
    choice.add_argument("--no-git", action="store_true", help="do not create a git repository")
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

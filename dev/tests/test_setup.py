#!/usr/bin/env python3
"""Tests for setup.py: install, update, check and remove, for every agent.

  python -m unittest discover -s dev/tests
"""

from __future__ import annotations

import builtins
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(KIT / "kit" / "hooks"))
import kitlib  # noqa: E402
import setup  # noqa: E402

EM_DASH = chr(0x2014)
E_ACUTE = chr(0xE9)
BACKSLASH = chr(92)
SKILLS = 14


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class Base(unittest.TestCase):
    GIT = False  # most tests are about files, and run faster without a repository

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "My Project"
        self.ws.mkdir()
        self.personal = Path(self.tmp.name) / "personal.yaml"
        self._env = dict(os.environ)
        os.environ["WORKSPACE_KIT_PERSONAL"] = str(self.personal)
        for name in ("WORKSPACE_KIT_CONFIG", "WORKSPACE_KIT_ROOT"):
            os.environ.pop(name, None)
        # Whether a person is at the keyboard must not depend on how the tests are started.
        self._interactive = setup.interactive
        setup.interactive = lambda: False

    def tearDown(self):
        setup.interactive = self._interactive
        os.environ.clear()
        os.environ.update(self._env)
        self.tmp.cleanup()

    def run_setup(self, *argv: str) -> tuple[int, str]:
        if argv and argv[0] == "install" and not self.GIT:
            argv = (*argv, "--no-git")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = setup.main([*argv, "--workspace", str(self.ws)])
        return code, out.getvalue() + err.getvalue()

    def read(self, rel: str) -> str:
        return (self.ws / rel).read_text(encoding="utf-8")

    def json(self, rel: str) -> dict:
        return json.loads(self.read(rel))

    def kit_hooks(self, rel: str) -> list[tuple[str, str | None, str]]:
        """The kit's own hooks in one agent's hook file: event, matcher, script."""
        found = []
        for event, groups in self.json(rel).get("hooks", {}).items():
            for group in groups:
                for hook in group["hooks"]:
                    if ".workspace-kit/hooks/" in hook["command"]:
                        script = hook["command"].rsplit("/", 1)[1].rstrip('"')
                        found.append((event, group.get("matcher"), script))
        return sorted(found, key=str)

    def skills(self, folder: str) -> int:
        path = self.ws / folder
        return len(list(path.iterdir())) if path.is_dir() else 0

    def settings(self) -> dict:
        return kitlib.load_settings(str(self.ws / "workspace.yaml"))


class FreshFolderTest(Base):
    def test_install_wires_every_agent_and_a_second_run_changes_nothing(self):
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        for rel in ("workspace.yaml", "AGENTS.md", "CLAUDE.md", "projects/log.md", "projects/context.md",
                    "Inbox/README.md", ".workspace-kit/manifest.json",
                    ".workspace-kit/hooks/run.sh", ".workspace-kit/hooks/run.cmd", ".workspace-kit/hooks/kitlib.py",
                    ".workspace-kit/hooks/banned_characters.py", ".workspace-kit/hooks/lint_nudge.py",
                    ".workspace-kit/templates/project/context.md",
                    ".claude/settings.json", ".claude/skills/workspace-lint/SKILL.md", ".claude/skills/riff/SKILL.md",
                    ".codex/hooks.json", ".agents/skills/workspace-lint/SKILL.md", ".agents/skills/grill-me/SKILL.md",
                    ".opencode/plugins/workspace-kit.js"):
            self.assertTrue((self.ws / rel).is_file(), rel)
        self.assertEqual(self.skills(".claude/skills"), SKILLS)
        self.assertEqual(self.skills(".agents/skills"), SKILLS)
        self.assertEqual(self.read(".claude/skills/riff/SKILL.md"), self.read(".agents/skills/riff/SKILL.md"))

        settings = self.settings()
        self.assertEqual((settings["client"], settings["work_folder"]), ("My Project", "projects"))
        self.assertEqual(settings["agents"], ["claude", "codex", "opencode"])
        self.assertEqual(settings["banned_characters"], [])
        self.assertEqual(self.kit_hooks(".claude/settings.json"), [("SessionStart", "startup", "lint_nudge.py")])
        self.assertEqual(self.kit_hooks(".codex/hooks.json"), [("SessionStart", "startup", "lint_nudge.py")])

        agents = self.read("AGENTS.md")
        self.assertTrue(agents.startswith("# AGENTS.md\n"))
        self.assertEqual(agents.count(setup.BLOCK_START), 1)
        self.assertIn("Active work lives in `projects/`", agents)
        self.assertNotIn("{{", agents)
        self.assertNotIn("Never write these characters", agents)
        self.assertIn("\n@AGENTS.md\n", self.read("CLAUDE.md"))
        self.assertIn("| doc | Workspace set up with workspace-kit", self.read("projects/log.md"))
        self.assertIn("Codex runs a project's hooks only after you have approved them", text)

        before = snapshot(self.ws)
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertIn("Nothing changed", text)
        self.assertEqual(snapshot(self.ws), before)

    def test_each_agent_gets_its_own_form_of_the_same_hook(self):
        self.run_setup("install", "--ban", "U+2014", "--ban-in", "files,replies")
        claude = self.json(".claude/settings.json")["hooks"]
        codex = self.json(".codex/hooks.json")["hooks"]
        self.assertEqual(claude["PreToolUse"][0]["matcher"], "Write|Edit|MultiEdit|NotebookEdit")
        self.assertEqual(claude["PreToolUse"][0]["hooks"][0], {
            "type": "command",
            "command": 'sh "$CLAUDE_PROJECT_DIR/.workspace-kit/hooks/run.sh" '
                       '"$CLAUDE_PROJECT_DIR/.workspace-kit/hooks/banned_characters.py"',
        })
        self.assertEqual(codex["PreToolUse"][0]["matcher"], "apply_patch|Edit|Write")
        windows = ".workspace-kit" + BACKSLASH + "hooks" + BACKSLASH
        self.assertEqual(codex["PreToolUse"][0]["hooks"][0], {
            "type": "command",
            "command": "sh .workspace-kit/hooks/run.sh .workspace-kit/hooks/banned_characters.py",
            "commandWindows": "cmd /c " + windows + "run.cmd " + windows + "banned_characters.py",
        })
        self.assertNotIn("matcher", codex["Stop"][0])
        self.assertEqual([h[0] for h in self.kit_hooks(".codex/hooks.json")], ["PreToolUse", "SessionStart", "Stop"])
        self.assertEqual([h[0] for h in self.kit_hooks(".claude/settings.json")], ["PreToolUse", "SessionStart", "Stop"])

    def test_only_the_chosen_agents_are_wired(self):
        code, text = self.run_setup("install", "--agents", "claude")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.settings()["agents"], ["claude"])
        self.assertEqual(self.skills(".claude/skills"), SKILLS)
        for rel in (".agents", ".codex", ".opencode"):
            self.assertFalse((self.ws / rel).exists(), rel)
        self.assertNotIn("Codex runs", text)

    def test_without_claude_there_is_no_claude_folder_and_no_claude_md(self):
        code, text = self.run_setup("install", "--agents", "codex, opencode", "--ban", "U+2014")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.settings()["agents"], ["codex", "opencode"])
        self.assertEqual(self.skills(".agents/skills"), SKILLS)
        self.assertFalse((self.ws / ".claude").exists())
        self.assertFalse((self.ws / "CLAUDE.md").exists())
        self.assertTrue((self.ws / ".opencode" / "plugins" / "workspace-kit.js").is_file())
        self.assertEqual([h[0] for h in self.kit_hooks(".codex/hooks.json")], ["PreToolUse", "SessionStart"])

    def test_an_unknown_agent_stops_before_anything_is_written(self):
        code, text = self.run_setup("install", "--agents", "claude,cursor")
        self.assertEqual(code, 2)
        self.assertIn("agents only takes claude, codex, opencode, not cursor", text)
        self.assertEqual(snapshot(self.ws), {})

    def test_dry_run_writes_nothing(self):
        code, text = self.run_setup("install", "--dry-run")
        self.assertEqual(code, 0, text)
        self.assertIn("Dry run", text)
        self.assertIn("workspace.yaml", text)
        self.assertEqual(snapshot(self.ws), {})

    def test_options_and_personal_defaults_seed_workspace_yaml(self):
        self.personal.write_text(
            'working_language: Norwegian\nbanned_characters: ["' + EM_DASH + '", U+00E9]\n'
            "banned_in: [files, replies]\nstyle:\n  - Lead with the result.\nclient: Ignored\n", encoding="utf-8")
        code, text = self.run_setup("install", "--client", "Acme: Media", "--work-folder", "work",
                                    "--deliverable-language", "Norwegian")
        self.assertEqual(code, 0, text)
        raw = self.read("workspace.yaml")
        self.assertNotIn(EM_DASH, raw)
        self.assertNotIn(E_ACUTE, raw)
        self.assertIn("banned_characters: [U+2014, U+00E9]", raw)
        self.assertIn("agents: [claude, codex, opencode]", raw)
        settings = self.settings()
        self.assertEqual(settings["client"], "Acme: Media")
        self.assertEqual(settings["work_folder"], "work")
        self.assertEqual((settings["working_language"], settings["deliverable_language"]), ("Norwegian", "Norwegian"))
        self.assertEqual(settings["banned_characters"], [EM_DASH, E_ACUTE])
        self.assertEqual(settings["style"], ["Lead with the result."])
        self.assertTrue((self.ws / "work" / "log.md").is_file())

        agents = self.read("AGENTS.md")
        self.assertIn("- Answer in Norwegian.", agents)
        self.assertIn("EM DASH (U+2014), LATIN SMALL LETTER E WITH ACUTE (U+00E9)", agents)
        self.assertIn("A hook blocks them in files and replies.", agents)
        self.assertIn("- Lead with the result.\n", agents)
        self.assertNotIn(EM_DASH, agents)
        self.assertNotIn(E_ACUTE, agents)

    def test_refuses_the_kit_folder_and_a_missing_folder(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(setup.main(["install", "--workspace", str(KIT)]), 2)
            self.assertEqual(setup.main(["install", "--workspace", str(KIT / "kit")]), 2)
            self.assertEqual(setup.main(["install", "--workspace", str(self.ws / "nope")]), 2)
        self.assertIn("nothing was changed", err.getvalue())


class ExistingProjectTest(Base):
    def setUp(self):
        super().setUp()
        (self.ws / "design" / "alpha").mkdir(parents=True)
        (self.ws / "design" / "alpha" / "notes.md").write_text("mine\n", encoding="utf-8")
        (self.ws / "AGENTS.md").write_bytes(b"# House rules\r\n\r\nAlways be kind.\r\n")
        (self.ws / "CLAUDE.md").write_text("# CLAUDE.md\n\nMy own Claude notes.\n", encoding="utf-8")
        for folder in (".claude/skills/riff", ".agents/skills/riff"):
            (self.ws / folder).mkdir(parents=True)
            (self.ws / folder / "SKILL.md").write_text("my own riff skill\n", encoding="utf-8")
        (self.ws / ".claude" / "settings.json").write_text(json.dumps({
            "permissions": {"allow": ["Bash(ls)"]},
            "hooks": {
                "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo mine"}]}],
                "PostToolUse": [{"hooks": [{"type": "command", "command": "echo after"}]}],
            },
        }), encoding="utf-8")
        (self.ws / ".codex").mkdir()
        (self.ws / ".codex" / "hooks.json").write_text(json.dumps({
            "description": "My hooks.",
            "hooks": {"SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo codex"}]}]},
        }), encoding="utf-8")
        (self.ws / ".opencode" / "plugins").mkdir(parents=True)
        (self.ws / ".opencode" / "plugins" / "mine.js").write_text("// mine\n", encoding="utf-8")
        self.before = snapshot(self.ws)

    def test_install_adds_and_never_overwrites(self):
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertIn("not written by the kit", text)

        self.assertEqual(self.settings()["work_folder"], "design")
        self.assertTrue((self.ws / "design" / "log.md").is_file())
        self.assertFalse((self.ws / "projects").exists())
        self.assertEqual(self.read("design/alpha/notes.md"), "mine\n")

        agents = (self.ws / "AGENTS.md").read_bytes()
        self.assertTrue(agents.startswith(b"# House rules\r\n\r\nAlways be kind.\r\n"))
        self.assertIn(setup.BLOCK_START.encode(), agents)
        self.assertNotIn(b"\n\n\n", agents.replace(b"\r\n", b"\n"))
        self.assertEqual(agents.count(b"\n"), agents.count(b"\r\n"), "Windows line endings are kept")

        claude = self.read("CLAUDE.md")
        self.assertTrue(claude.startswith("# CLAUDE.md\n\nMy own Claude notes.\n"))
        self.assertIn("\n@AGENTS.md\n", claude)

        for folder in (".claude/skills", ".agents/skills"):
            self.assertEqual(self.read(f"{folder}/riff/SKILL.md"), "my own riff skill\n")
            self.assertTrue((self.ws / folder / "grill-me" / "SKILL.md").is_file())
        manifest = self.json(".workspace-kit/manifest.json")
        self.assertNotIn(".claude/skills/riff/SKILL.md", manifest["files"])
        self.assertNotIn(".agents/skills/riff/SKILL.md", manifest["files"])
        self.assertEqual(manifest["created_files"], [])

        cs = self.json(".claude/settings.json")
        self.assertEqual(cs["permissions"], {"allow": ["Bash(ls)"]})
        self.assertEqual(cs["hooks"]["PostToolUse"], [{"hooks": [{"type": "command", "command": "echo after"}]}])
        self.assertEqual(cs["hooks"]["SessionStart"][0]["hooks"][0]["command"], "echo mine")
        self.assertEqual(len(cs["hooks"]["SessionStart"]), 2)

        cx = self.json(".codex/hooks.json")
        self.assertEqual(cx["description"], "My hooks.")
        self.assertEqual(cx["hooks"]["SessionStart"][0]["hooks"][0]["command"], "echo codex")
        self.assertEqual(len(cx["hooks"]["SessionStart"]), 2)
        self.assertEqual(self.read(".opencode/plugins/mine.js"), "// mine\n")
        self.assertTrue((self.ws / ".opencode" / "plugins" / "workspace-kit.js").is_file())

        again = snapshot(self.ws)
        self.assertEqual(self.run_setup("install")[0], 0)
        self.assertEqual(snapshot(self.ws), again)

    def test_remove_puts_the_project_back_as_it_was(self):
        self.run_setup("install", "--ban", "U+2014", "--ban-in", "files,replies")
        (self.ws / "design" / "log.md").write_text("my log\n", encoding="utf-8")
        code, text = self.run_setup("remove")
        self.assertEqual(code, 0, text)
        after = snapshot(self.ws)
        yours = {"workspace.yaml", "design/log.md", "design/context.md", "Inbox/README.md"}
        self.assertEqual(set(after) - set(self.before), yours)
        for rel, data in self.before.items():
            if rel.endswith(".json"):
                self.assertEqual(json.loads(after[rel]), json.loads(data), rel)
            else:
                self.assertEqual(after[rel], data, rel)
        self.assertEqual(self.read("design/log.md"), "my log\n")
        self.assertFalse((self.ws / ".workspace-kit").exists())

    def test_a_claude_md_that_already_imports_agents_is_left_alone(self):
        (self.ws / "CLAUDE.md").write_text("# CLAUDE.md\n\n@AGENTS.md\n\nMine.\n", encoding="utf-8")
        self.run_setup("install")
        self.assertEqual(self.read("CLAUDE.md"), "# CLAUDE.md\n\n@AGENTS.md\n\nMine.\n")

    def test_a_broken_file_stops_before_anything_is_written(self):
        for rel, content in ((".claude/settings.json", "{ not json"), (".codex/hooks.json", "[1, 2]")):
            original = (self.ws / rel).read_bytes()
            (self.ws / rel).write_text(content, encoding="utf-8")
            before = snapshot(self.ws)
            code, text = self.run_setup("install")
            self.assertEqual(code, 2, rel)
            self.assertIn("nothing was changed", text)
            self.assertEqual(snapshot(self.ws), before, rel)
            (self.ws / rel).write_bytes(original)

    def test_broken_workspace_yaml_and_damaged_markers_stop_too(self):
        (self.ws / "workspace.yaml").write_text("client: a: b\n", encoding="utf-8")
        before = snapshot(self.ws)
        self.assertEqual(self.run_setup("install")[0], 2)
        self.assertEqual(snapshot(self.ws), before)
        (self.ws / "workspace.yaml").unlink()
        (self.ws / "AGENTS.md").write_text("rules\n" + setup.BLOCK_START + "\nhalf a section\n", encoding="utf-8")
        before = snapshot(self.ws)
        code, text = self.run_setup("install")
        self.assertEqual(code, 2)
        self.assertIn("markers are damaged", text)
        self.assertEqual(snapshot(self.ws), before)


class UpdateTest(Base):
    def test_your_edits_survive_and_untouched_files_follow_the_kit(self):
        self.run_setup("install")
        edited = self.ws / ".claude" / "skills" / "riff" / "SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nMy addition.\n", encoding="utf-8")
        untouched = ".claude/skills/grill-me/SKILL.md"
        real = setup.managed_sources

        def newer_kit(settings):
            sources = real(settings)
            sources[untouched] += b"\nA line from a newer kit.\n"
            sources[".claude/skills/riff/SKILL.md"] += b"\nAlso newer.\n"
            del sources[".claude/skills/ideate/SKILL.md"]
            return sources

        setup.managed_sources = newer_kit
        try:
            code, text = self.run_setup("install")
        finally:
            setup.managed_sources = real
        self.assertEqual(code, 0, text)
        self.assertIn("A line from a newer kit.", self.read(untouched))
        self.assertIn("My addition.", self.read(".claude/skills/riff/SKILL.md"))
        self.assertNotIn("Also newer.", self.read(".claude/skills/riff/SKILL.md"))
        self.assertFalse((self.ws / ".claude" / "skills" / "ideate").exists(), "a skill the kit dropped is removed")
        self.assertIn("you edited it", text)

    def test_changing_workspace_yaml_rewrites_the_section_and_the_hooks(self):
        self.run_setup("install")
        agents = self.ws / "AGENTS.md"
        agents.write_text("# My title\n\nMy rule above.\n\n" + agents.read_text(encoding="utf-8").split("\n\n", 3)[3]
                          + "\nMy rule below.\n", encoding="utf-8")
        config = self.ws / "workspace.yaml"
        config.write_text(config.read_text(encoding="utf-8")
                          .replace("banned_characters: []", "banned_characters: [U+2014]")
                          .replace("lint_every_days: 28", "lint_every_days: 7"), encoding="utf-8")
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        new = self.read("AGENTS.md")
        self.assertEqual(new.count(setup.BLOCK_START), 1)
        self.assertEqual(new.count(setup.BLOCK_END), 1)
        self.assertTrue(new.startswith("# My title\n\nMy rule above.\n"))
        self.assertTrue(new.endswith("My rule below.\n"))
        self.assertIn("EM DASH (U+2014)", new)
        self.assertIn("older than 7 days", new)
        for rel in (".claude/settings.json", ".codex/hooks.json"):
            self.assertEqual([h[0] for h in self.kit_hooks(rel)], ["PreToolUse", "SessionStart"], rel)

        config.write_text(config.read_text(encoding="utf-8").replace("[U+2014]", "[]"), encoding="utf-8")
        self.run_setup("install")
        for rel in (".claude/settings.json", ".codex/hooks.json"):
            self.assertEqual([h[0] for h in self.kit_hooks(rel)], ["SessionStart"], rel)
        self.assertNotIn("EM DASH", self.read("AGENTS.md"))

    def test_dropping_an_agent_takes_its_wiring_out(self):
        self.run_setup("install")
        config = self.ws / "workspace.yaml"
        config.write_text(config.read_text(encoding="utf-8").replace(
            "agents: [claude, codex, opencode]", "agents: [codex]"), encoding="utf-8")
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.skills(".agents/skills"), SKILLS)
        for rel in (".claude", "CLAUDE.md", ".opencode"):
            self.assertFalse((self.ws / rel).exists(), rel)
        self.assertTrue((self.ws / ".codex" / "hooks.json").is_file())

        config.write_text(config.read_text(encoding="utf-8").replace("agents: [codex]", "agents: [claude]"),
                          encoding="utf-8")
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.skills(".claude/skills"), SKILLS)
        self.assertIn("\n@AGENTS.md\n", self.read("CLAUDE.md"))
        for rel in (".agents", ".codex", ".opencode"):
            self.assertFalse((self.ws / rel).exists(), rel)
        if setup.find_shell():
            code, text = self.run_setup("check")
            self.assertEqual(code, 0, text)


class CheckAndRemoveTest(Base):
    def test_check_passes_after_install_and_proves_the_hooks_block(self):
        self.assertEqual(self.run_setup("check")[0], 1, "not installed yet")
        self.run_setup("install", "--ban", "U+2014", "--ban-in", "files,replies")
        if not setup.find_shell():
            self.skipTest("no sh on this machine")
        code, text = self.run_setup("check")
        self.assertEqual(code, 0, text)
        for line in ("session start hook runs", "a banned character in a file is blocked",
                     "clean text in a file is allowed", "a banned character in a Codex patch is blocked",
                     "a banned character in a reply is blocked", "Claude Code: hooks in .claude/settings.json",
                     "Codex: hooks in .codex/hooks.json", "OpenCode: adapter in .opencode/plugins/workspace-kit.js"):
            self.assertIn("ok    " + line, text)
        if os.name == "nt":
            self.assertIn("ok    a banned character in a Codex patch is blocked (Windows shell)", text)
        self.assertIn("note  Codex runs a project's hooks only after you have approved them", text)
        self.assertIn("note  OpenCode has no way to send a reply back", text)
        self.assertIn("Everything is in place.", text)

    def test_check_fails_on_a_missing_file_and_on_unwired_hooks(self):
        self.run_setup("install")
        (self.ws / ".workspace-kit" / "hooks" / "lint_nudge.py").unlink()
        code, text = self.run_setup("check")
        self.assertEqual(code, 1)
        self.assertIn("FAIL  installed files", text)
        self.run_setup("install")
        for rel, label in ((".claude/settings.json", "Claude Code"), (".codex/hooks.json", "Codex")):
            (self.ws / rel).write_text("{}", encoding="utf-8")
            code, text = self.run_setup("check")
            self.assertEqual(code, 1)
            self.assertIn(f"FAIL  {label}: hooks in {rel}", text)
            self.run_setup("install")
        (self.ws / ".opencode" / "plugins" / "workspace-kit.js").unlink()
        code, text = self.run_setup("check")
        self.assertEqual(code, 1)
        self.assertIn("FAIL  OpenCode: adapter", text)

    def test_check_says_when_the_two_copies_of_a_skill_differ(self):
        self.run_setup("install")
        copy = self.ws / ".agents" / "skills" / "riff" / "SKILL.md"
        copy.write_text(copy.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
        code, text = self.run_setup("check")
        self.assertIn("note  These skills differ between .claude/skills and .agents/skills", text)
        self.assertIn("riff", text)

    def test_remove_from_a_fresh_folder_leaves_only_your_content(self):
        self.run_setup("install")
        edited = self.ws / ".claude" / "skills" / "riff" / "SKILL.md"
        edited.write_text("changed by me\n", encoding="utf-8")
        code, text = self.run_setup("remove")
        self.assertEqual(code, 0, text)
        self.assertEqual(set(snapshot(self.ws)), {
            "workspace.yaml", "projects/log.md", "projects/context.md", "Inbox/README.md",
            ".claude/skills/riff/SKILL.md"})
        self.assertEqual(self.run_setup("remove")[0], 0)

    def test_remove_keeps_rules_you_wrote_in_a_file_the_kit_created(self):
        self.run_setup("install")
        agents = self.ws / "AGENTS.md"
        agents.write_text(agents.read_text(encoding="utf-8") + "\n## Mine\n\nKeep this.\n", encoding="utf-8")
        self.run_setup("remove")
        left = self.read("AGENTS.md")
        self.assertIn("Keep this.", left)
        self.assertNotIn(setup.BLOCK_START, left)
        self.assertFalse((self.ws / "CLAUDE.md").exists())


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class GitTest(Base):
    GIT = True

    def setUp(self):
        super().setUp()
        # A machine with no git identity and no system settings, so the tests decide both.
        self.gitconfig = Path(self.tmp.name) / "gitconfig"
        self.gitconfig.write_text("", encoding="utf-8")
        os.environ["GIT_CONFIG_GLOBAL"] = str(self.gitconfig)
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"

    def git(self, *args: str) -> str:
        done = subprocess.run(["git", "-C", str(self.ws), *args], capture_output=True, text=True, encoding="utf-8")
        return done.stdout.strip()

    def name_yourself(self):
        self.gitconfig.write_text("[user]\n\tname = Test Person\n\temail = test@example.com\n", encoding="utf-8")

    def test_a_fresh_folder_becomes_a_repository_with_everything_committed(self):
        self.name_yourself()
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertTrue((self.ws / ".git").is_dir())
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")
        self.assertEqual(self.git("log", "-1", "--format=%s|%an|%ae"),
                         f"Workspace set up with workspace-kit {setup.VERSION}|Test Person|test@example.com")
        self.assertEqual(self.git("status", "--porcelain"), "", "nothing is left uncommitted")
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD"), "main")
        self.assertEqual(self.git("config", "core.fileMode"), "false")
        self.assertEqual(self.git("config", "core.autocrlf"), "false")
        tracked = self.git("ls-files").splitlines()
        for rel in ("workspace.yaml", "AGENTS.md", "CLAUDE.md", ".gitignore", "projects/log.md",
                    ".workspace-kit/manifest.json", ".claude/skills/riff/SKILL.md", ".agents/skills/riff/SKILL.md",
                    ".codex/hooks.json", ".opencode/plugins/workspace-kit.js"):
            self.assertIn(rel, tracked)
        self.assertIn("git: yes", self.read("workspace.yaml"))
        self.assertNotIn("Git has no name", text)

        head = self.git("rev-parse", "HEAD")
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertIn("Nothing changed", text)
        self.assertEqual(self.git("rev-parse", "HEAD"), head, "a second run commits nothing")
        if setup.find_shell():
            code, text = self.run_setup("check")
            self.assertEqual(code, 0, text)
            self.assertIn("ok    git repository", text)

    def test_without_a_git_identity_it_still_commits_and_says_so(self):
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")
        self.assertEqual(self.git("log", "-1", "--format=%an"), "workspace-kit")
        self.assertIn("Git has no name and email on this machine", text)
        self.assertEqual(self.git("config", "--local", "user.name"), "", "no identity is written for you")

    def test_a_personal_git_identity_is_used_when_the_machine_has_none(self):
        self.personal.write_text("git_name: Kit Owner\ngit_email: owner@example.com\n", encoding="utf-8")
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.git("log", "-1", "--format=%an|%ae"), "Kit Owner|owner@example.com")
        self.assertNotIn("Git has no name", text)

    def test_files_that_were_already_there_are_not_committed_for_you(self):
        self.name_yourself()
        (self.ws / "design" / "alpha").mkdir(parents=True)
        (self.ws / "design" / "alpha" / "notes.md").write_text("mine\n", encoding="utf-8")
        (self.ws / ".gitignore").write_text("secret/\n", encoding="utf-8")
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.read(".gitignore"), "secret/\n", "your own ignore file is kept")
        tracked = self.git("ls-files").splitlines()
        self.assertIn("design/log.md", tracked)
        self.assertNotIn("design/alpha/notes.md", tracked)
        self.assertNotIn(".gitignore", tracked)
        self.assertIn("that were here before are not committed", text)

    def test_an_existing_repository_is_left_exactly_as_it_is(self):
        self.name_yourself()
        self.git("init", "-b", "main")
        (self.ws / "mine.md").write_text("mine\n", encoding="utf-8")
        self.git("add", "mine.md")
        self.git("commit", "-m", "mine")
        head = self.git("rev-parse", "HEAD")
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertIn("already under git. Setup committed nothing", text)
        self.assertFalse((self.ws / ".gitignore").exists())

    def test_a_folder_inside_a_larger_repository_gets_no_repository_of_its_own(self):
        self.name_yourself()
        subprocess.run(["git", "-C", self.tmp.name, "init", "-b", "main"], capture_output=True)
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertFalse((self.ws / ".git").exists())

    def test_dry_run_and_no_git_create_no_repository(self):
        code, text = self.run_setup("install", "--dry-run", "--git")
        self.assertIn(".git", text)
        self.assertEqual(snapshot(self.ws), {})
        code, text = self.run_setup("install", "--no-git")
        self.assertEqual(code, 0, text)
        self.assertFalse((self.ws / ".git").exists())
        self.assertIn("git: no", self.read("workspace.yaml"))

    def test_only_a_folder_named_after_a_sync_service_counts_as_synced(self):
        root = Path(self.tmp.name)
        for name in ("Jottacloud", "OneDrive - Work", "Dropbox (Personal)", "Google Drive", "iCloud Drive"):
            self.assertTrue(setup.looks_synced(root / name / "Project"), name)
        for name in ("C--Users-me-Jottacloud-work", "notes-about-dropbox", "Projects"):
            self.assertFalse(setup.looks_synced(Path("X:/") / name / "Project"), name)

    def test_a_synced_folder_gets_a_word_of_warning(self):
        self.name_yourself()
        self.ws = Path(self.tmp.name) / "Jottacloud" / "Project"
        self.ws.mkdir(parents=True)
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertIn("looks like it is synced between devices", text)
        self.assertTrue((self.ws / ".git").is_dir())


    def test_with_no_answer_and_nobody_at_the_keyboard_it_creates_nothing_and_says_to_ask(self):
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertFalse((self.ws / ".git").exists())
        self.assertIn("git: ask", self.read("workspace.yaml"))
        self.assertIn("No git repository was created, because nobody has said whether to", text)
        if setup.find_shell():
            code, text = self.run_setup("check")
            self.assertEqual(code, 0, text)
            self.assertIn("note  Nobody has said whether this folder should be under git", text)

        self.name_yourself()
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertIn("git: yes", self.read("workspace.yaml"))
        self.assertNotIn("git: ask", self.read("workspace.yaml"))
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")
        self.assertEqual(self.git("status", "--porcelain"), "", "everything the kit installed earlier is committed")

    def test_no_git_on_a_later_run_stops_the_question(self):
        self.run_setup("install")
        code, text = self.run_setup("install", "--no-git")
        self.assertEqual(code, 0, text)
        self.assertIn("git: no", self.read("workspace.yaml"))
        self.assertFalse((self.ws / ".git").exists())
        self.assertNotIn("nobody has said", self.run_setup("install")[1])

    def test_a_person_at_the_keyboard_is_asked(self):
        self.name_yourself()
        real_interactive, real_input = setup.interactive, builtins.input
        asked = []
        setup.interactive = lambda: True
        try:
            builtins.input = lambda prompt="": asked.append(prompt) or "n"
            code, text = self.run_setup("install")
            self.assertEqual(code, 0, text)
            self.assertEqual(len(asked), 1)
            self.assertIn("Create a git repository here?", asked[0])
            self.assertFalse((self.ws / ".git").exists())
            self.assertIn("git: no", self.read("workspace.yaml"))

            self.run_setup("install")
            self.assertEqual(len(asked), 1, "a no is remembered, the question is not asked again")

            (self.ws / "workspace.yaml").write_text(
                self.read("workspace.yaml").replace("git: no", "git: ask"), encoding="utf-8")
            builtins.input = lambda prompt="": asked.append(prompt) or ""
            code, text = self.run_setup("install")
            self.assertEqual(code, 0, text)
            self.assertEqual(len(asked), 2)
            self.assertTrue((self.ws / ".git").is_dir(), "just pressing enter means yes")
            self.assertIn("git: yes", self.read("workspace.yaml"))

            self.run_setup("install", "--dry-run")
            self.assertEqual(len(asked), 2, "a dry run never asks")
        finally:
            setup.interactive, builtins.input = real_interactive, real_input

    def test_a_question_nobody_can_answer_is_left_open(self):
        """A terminal that closes, or an agent's shell that only looks like one."""
        real_input = builtins.input

        def nobody(prompt=""):
            raise EOFError

        setup.interactive = lambda: True
        builtins.input = nobody
        try:
            code, text = self.run_setup("install")
        finally:
            builtins.input = real_input
        self.assertEqual(code, 0, text)
        self.assertFalse((self.ws / ".git").exists())
        self.assertIn("git: ask", self.read("workspace.yaml"))
        self.assertIn("No git repository was created, because nobody has said whether to", text)

    def commit(self, rel: str, data: bytes, *extra: str) -> subprocess.CompletedProcess:
        """Writes a file the way a shell or a person would, past every agent hook, and commits it."""
        target = self.ws / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        subprocess.run(["git", "-C", str(self.ws), "add", "--", rel], capture_output=True)
        return subprocess.run(["git", "-C", str(self.ws), "commit", "-m", "work", *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_the_commit_check_stops_what_no_agent_hook_saw(self):
        self.name_yourself()
        code, text = self.run_setup("install", "--git", "--ban", "U+2014")
        self.assertEqual(code, 0, text)
        self.assertIn(".git/hooks/pre-commit", text)
        hook = self.ws / ".git" / "hooks" / "pre-commit"
        self.assertIn("Written by workspace-kit", hook.read_text(encoding="utf-8"))
        self.assertIn(".gitattributes", self.git("ls-files").splitlines())

        done = self.commit("projects/a.md", ("fine\nbad " + EM_DASH + " line\n").encode("utf-8"))
        self.assertNotEqual(done.returncode, 0, "a banned character added to a file stops the commit")
        self.assertIn("projects/a.md:2  EM DASH (U+2014)", done.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")

        done = self.commit("projects/a.md", b"fine\nnow clean\n")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "2")

        done = self.commit("projects/b.md", b"caf" + bytes([0xB7]) + b" broken by a shell\n")
        self.assertNotEqual(done.returncode, 0, "bytes that are not valid text stop the commit")
        self.assertIn("projects/b.md:1  bytes that are not valid UTF-8 text", done.stderr)
        self.assertIn("file editing tool", done.stderr)

        done = self.commit("projects/b.md", b"caf" + bytes([0xB7]) + b" kept on purpose\n", "--no-verify")
        self.assertEqual(done.returncode, 0, "the owner can still overrule the check")

        done = self.commit("projects/a.md", b"fine\n")
        self.assertEqual(done.returncode, 0, "taking a line out is never stopped: " + done.stderr)
        done = self.commit("photo.bin", bytes(range(256)) * 4)
        self.assertEqual(done.returncode, 0, "files that are not text are left alone: " + done.stderr)
        named = self.read("workspace.yaml").replace("[U+2014]", '["' + EM_DASH + '"]')
        done = self.commit("workspace.yaml", named.encode("utf-8"))
        self.assertEqual(done.returncode, 0, "the settings file may name the character it bans: " + done.stderr)

        if setup.find_shell():
            code, text = self.run_setup("check")
            self.assertEqual(code, 0, text)
            self.assertIn("ok    commit check", text)
            self.assertIn("ok    commit check runs", text)
            hook.unlink()
            code, text = self.run_setup("check")
            self.assertEqual(code, 1)
            self.assertIn("FAIL  commit check: it is missing", text)
            self.run_setup("install")
            self.assertTrue(hook.exists(), "install puts it back")

    def test_the_commit_check_works_without_any_banned_characters(self):
        self.name_yourself()
        self.run_setup("install", "--git")
        done = self.commit("projects/a.md", ("an em dash " + EM_DASH + " is fine here\n").encode("utf-8"))
        self.assertEqual(done.returncode, 0, done.stderr)
        done = self.commit("projects/c.md", b"broken " + bytes([0xE9]) + b" byte\n")
        self.assertNotEqual(done.returncode, 0)

    def test_a_pre_commit_hook_that_is_yours_is_never_replaced(self):
        self.name_yourself()
        self.git("init", "-b", "main")
        hook = self.ws / ".git" / "hooks" / "pre-commit"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        code, text = self.run_setup("install", "--git")
        self.assertEqual(code, 0, text)
        self.assertEqual(hook.read_text(encoding="utf-8"), "#!/bin/sh\nexit 0\n")
        self.assertIn("already has a pre-commit hook that the kit did not write", text)

    def test_remove_and_saying_no_to_git_take_the_commit_check_out(self):
        self.name_yourself()
        self.run_setup("install", "--git")
        hook = self.ws / ".git" / "hooks" / "pre-commit"
        self.assertTrue(hook.exists())
        self.run_setup("install", "--no-git")
        self.assertFalse(hook.exists())
        self.assertTrue((self.ws / ".git").is_dir(), "the repository itself is never removed")
        self.run_setup("install", "--git")
        self.assertTrue(hook.exists())
        self.run_setup("remove")
        self.assertFalse(hook.exists())
        self.assertTrue((self.ws / ".git").is_dir())


class KitItselfTest(unittest.TestCase):
    def test_every_installed_skill_reads_the_work_folder_from_settings(self):
        skills = setup.skill_sources()
        self.assertEqual(len(skills), SKILLS)
        for name, data in skills.items():
            text = data.decode("utf-8")
            self.assertIn("workspace.yaml", text, name)
            self.assertNotIn("design/<slug>", text, name)

    def test_skill_folders_follow_what_each_agent_reads(self):
        self.assertEqual(setup.skill_folders(["claude"]), [".claude/skills"])
        self.assertEqual(setup.skill_folders(["codex"]), [".agents/skills"])
        self.assertEqual(setup.skill_folders(["opencode"]), [".agents/skills"])
        self.assertEqual(setup.skill_folders(["claude", "opencode"]), [".claude/skills", ".agents/skills"])

    def test_templates_render_without_leftovers(self):
        settings = kitlib.normalize({"client": "X", "banned_characters": ["U+2014"], "style": ["Short."]})
        for text in (setup.workspace_yaml(settings), setup.rules_block(settings)):
            self.assertNotIn("{{", text)
        again = kitlib.normalize(kitlib.parse_simple_yaml(setup.workspace_yaml(settings)))
        self.assertEqual(again["style"], ["Short."])
        self.assertEqual(again["agents"], ["claude", "codex", "opencode"])

    def test_the_opencode_adapter_names_the_tools_opencode_really_sends(self):
        """Field names recorded from a live OpenCode 2.2 session."""
        adapter = (KIT / "kit" / "adapters" / "opencode" / "workspace-kit.js").read_text(encoding="utf-8")
        for needle in ('tool === "write"', "input.content", 'tool === "edit"', "input.newString",
                       'ctx.tool.hook("execute.before"', "banned_characters.py", "lint_nudge.py",
                       'id: "workspace-kit"'):
            self.assertIn(needle, adapter)


if __name__ == "__main__":
    unittest.main(verbosity=1)

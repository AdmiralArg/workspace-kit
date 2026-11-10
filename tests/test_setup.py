#!/usr/bin/env python3
"""Tests for setup.py: install, update, check and remove. Run: python tests/test_setup.py"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(KIT / "hooks"))
import kitlib  # noqa: E402
import setup  # noqa: E402

EM_DASH = chr(0x2014)
E_ACUTE = chr(0xE9)


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "My Project"
        self.ws.mkdir()
        self.personal = Path(self.tmp.name) / "personal.yaml"
        self._env = dict(os.environ)
        os.environ["WORKSPACE_KIT_PERSONAL"] = str(self.personal)
        os.environ.pop("WORKSPACE_KIT_CONFIG", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        self.tmp.cleanup()

    def run_setup(self, *argv: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = setup.main([*argv, "--workspace", str(self.ws)])
        return code, out.getvalue() + err.getvalue()

    def read(self, rel: str) -> str:
        return (self.ws / rel).read_text(encoding="utf-8")

    def claude_settings(self) -> dict:
        return json.loads(self.read(".claude/settings.json"))

    def kit_hooks(self) -> list[tuple[str, str | None, str]]:
        found = []
        for event, groups in self.claude_settings().get("hooks", {}).items():
            for group in groups:
                for hook in group["hooks"]:
                    if "/.workspace-kit/hooks/" in hook["command"]:
                        found.append((event, group.get("matcher"), hook["command"].rsplit("/", 1)[1].rstrip('"')))
        return sorted(found, key=str)


class FreshFolderTest(Base):
    def test_install_wires_everything_and_a_second_run_changes_nothing(self):
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        for rel in ("workspace.yaml", "AGENTS.md", "CLAUDE.md", "projects/log.md", "projects/context.md",
                    "Inbox/README.md", ".claude/settings.json", ".workspace-kit/manifest.json",
                    ".workspace-kit/hooks/run.sh", ".workspace-kit/hooks/kitlib.py",
                    ".workspace-kit/hooks/banned_characters.py", ".workspace-kit/hooks/lint_nudge.py",
                    ".workspace-kit/templates/project/context.md",
                    ".claude/skills/workspace-lint/SKILL.md", ".claude/skills/concept-flow/SKILL.md",
                    ".claude/skills/riff/SKILL.md", ".claude/skills/grill-me/SKILL.md"):
            self.assertTrue((self.ws / rel).is_file(), rel)
        self.assertEqual(len(list((self.ws / ".claude" / "skills").iterdir())), 14)

        settings = kitlib.load_settings(str(self.ws / "workspace.yaml"))
        self.assertEqual((settings["client"], settings["work_folder"]), ("My Project", "projects"))
        self.assertEqual(settings["banned_characters"], [])
        self.assertEqual(self.kit_hooks(), [("SessionStart", "startup", "lint_nudge.py")])

        agents = self.read("AGENTS.md")
        self.assertTrue(agents.startswith("# AGENTS.md\n"))
        self.assertEqual(agents.count(setup.BLOCK_START), 1)
        self.assertIn("Active work lives in `projects/`", agents)
        self.assertNotIn("{{", agents)
        self.assertNotIn("Never write these characters", agents)
        self.assertIn("\n@AGENTS.md\n", self.read("CLAUDE.md"))
        self.assertIn("| doc | Workspace set up with workspace-kit", self.read("projects/log.md"))

        before = snapshot(self.ws)
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertIn("Nothing changed", text)
        self.assertEqual(snapshot(self.ws), before)

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
        settings = kitlib.load_settings(str(self.ws / "workspace.yaml"))
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
        self.assertEqual(self.kit_hooks(), [
            ("PreToolUse", "Write|Edit|MultiEdit|NotebookEdit", "banned_characters.py"),
            ("SessionStart", "startup", "lint_nudge.py"),
            ("Stop", None, "banned_characters.py"),
        ])

    def test_command_line_ban(self):
        code, text = self.run_setup("install", "--ban", "U+2014", "--ban-in", "files")
        self.assertEqual(code, 0, text)
        self.assertEqual(kitlib.load_settings(str(self.ws / "workspace.yaml"))["banned_characters"], [EM_DASH])
        self.assertEqual([h[0] for h in self.kit_hooks()], ["PreToolUse", "SessionStart"])

    def test_refuses_the_kit_folder_and_a_missing_folder(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(setup.main(["install", "--workspace", str(KIT)]), 2)
            self.assertEqual(setup.main(["install", "--workspace", str(self.ws / "nope")]), 2)
        self.assertIn("nothing was changed", err.getvalue())


class ExistingProjectTest(Base):
    def setUp(self):
        super().setUp()
        (self.ws / "design" / "alpha").mkdir(parents=True)
        (self.ws / "design" / "alpha" / "notes.md").write_text("mine\n", encoding="utf-8")
        (self.ws / "AGENTS.md").write_bytes(b"# House rules\r\n\r\nAlways be kind.\r\n")
        (self.ws / "CLAUDE.md").write_text("# CLAUDE.md\n\nMy own Claude notes.\n", encoding="utf-8")
        (self.ws / ".claude" / "skills" / "riff").mkdir(parents=True)
        (self.ws / ".claude" / "skills" / "riff" / "SKILL.md").write_text("my own riff skill\n", encoding="utf-8")
        (self.ws / ".claude" / "settings.json").write_text(json.dumps({
            "permissions": {"allow": ["Bash(ls)"]},
            "hooks": {
                "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo mine"}]}],
                "PostToolUse": [{"hooks": [{"type": "command", "command": "echo after"}]}],
            },
        }), encoding="utf-8")
        self.before = snapshot(self.ws)

    def test_install_adds_and_never_overwrites(self):
        code, text = self.run_setup("install")
        self.assertEqual(code, 0, text)
        self.assertIn("not written by the kit", text)

        self.assertEqual(kitlib.load_settings(str(self.ws / "workspace.yaml"))["work_folder"], "design")
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

        self.assertEqual(self.read(".claude/skills/riff/SKILL.md"), "my own riff skill\n")
        self.assertTrue((self.ws / ".claude" / "skills" / "grill-me" / "SKILL.md").is_file())
        manifest = json.loads(self.read(".workspace-kit/manifest.json"))
        self.assertNotIn(".claude/skills/riff/SKILL.md", manifest["files"])
        self.assertEqual(manifest["created_files"], [])

        cs = self.claude_settings()
        self.assertEqual(cs["permissions"], {"allow": ["Bash(ls)"]})
        self.assertEqual(cs["hooks"]["PostToolUse"], [{"hooks": [{"type": "command", "command": "echo after"}]}])
        self.assertEqual(cs["hooks"]["SessionStart"][0]["hooks"][0]["command"], "echo mine")
        self.assertEqual(len(cs["hooks"]["SessionStart"]), 2)

        again = snapshot(self.ws)
        self.assertEqual(self.run_setup("install")[0], 0)
        self.assertEqual(snapshot(self.ws), again)

    def test_remove_puts_the_project_back_as_it_was(self):
        self.run_setup("install")
        (self.ws / "design" / "log.md").write_text("my log\n", encoding="utf-8")
        code, text = self.run_setup("remove")
        self.assertEqual(code, 0, text)
        after = snapshot(self.ws)
        yours = {"workspace.yaml", "design/log.md", "design/context.md", "Inbox/README.md"}
        self.assertEqual(set(after) - set(self.before), yours)
        for rel, data in self.before.items():
            if rel == ".claude/settings.json":
                self.assertEqual(json.loads(after[rel]), json.loads(data))
            else:
                self.assertEqual(after[rel], data, rel)
        self.assertEqual(self.read("design/log.md"), "my log\n")
        self.assertFalse((self.ws / ".workspace-kit").exists())

    def test_a_claude_md_that_already_imports_agents_is_left_alone(self):
        (self.ws / "CLAUDE.md").write_text("# CLAUDE.md\n\n@AGENTS.md\n\nMine.\n", encoding="utf-8")
        self.run_setup("install")
        self.assertEqual(self.read("CLAUDE.md"), "# CLAUDE.md\n\n@AGENTS.md\n\nMine.\n")

    def test_broken_settings_json_stops_before_anything_is_written(self):
        (self.ws / ".claude" / "settings.json").write_text("{ not json", encoding="utf-8")
        before = snapshot(self.ws)
        code, text = self.run_setup("install")
        self.assertEqual(code, 2)
        self.assertIn("nothing was changed", text)
        self.assertEqual(snapshot(self.ws), before)

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

        def newer_kit():
            sources = real()
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
        self.assertEqual([h[0] for h in self.kit_hooks()], ["PreToolUse", "SessionStart"])

        config.write_text(config.read_text(encoding="utf-8").replace("[U+2014]", "[]"), encoding="utf-8")
        self.run_setup("install")
        self.assertEqual([h[0] for h in self.kit_hooks()], ["SessionStart"])
        self.assertNotIn("EM DASH", self.read("AGENTS.md"))


class CheckAndRemoveTest(Base):
    def test_check_passes_after_install_and_proves_the_hooks_block(self):
        self.assertEqual(self.run_setup("check")[0], 1, "not installed yet")
        self.run_setup("install", "--ban", "U+2014", "--ban-in", "files,replies")
        if not setup.find_shell():
            self.skipTest("no sh on this machine")
        code, text = self.run_setup("check")
        self.assertEqual(code, 0, text)
        for line in ("session start hook runs", "a banned character in a file is blocked",
                     "clean text in a file is allowed", "a banned character in a reply is blocked"):
            self.assertIn("ok    " + line, text)
        self.assertIn("Everything is in place.", text)

    def test_check_fails_on_a_missing_file_and_on_unwired_hooks(self):
        self.run_setup("install")
        (self.ws / ".workspace-kit" / "hooks" / "lint_nudge.py").unlink()
        code, text = self.run_setup("check")
        self.assertEqual(code, 1)
        self.assertIn("FAIL  installed files", text)
        self.run_setup("install")
        (self.ws / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        code, text = self.run_setup("check")
        self.assertEqual(code, 1)
        self.assertIn("FAIL  hooks in .claude/settings.json", text)

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


class KitItselfTest(unittest.TestCase):
    def test_every_installed_skill_reads_the_work_folder_from_settings(self):
        sources = setup.managed_sources()
        skills = [rel for rel in sources if rel.startswith(".claude/skills/")]
        self.assertEqual(len(skills), 14)
        for rel in skills:
            text = sources[rel].decode("utf-8")
            self.assertIn("workspace.yaml", text, rel)
            self.assertNotIn("design/<slug>", text, rel)

    def test_templates_render_without_leftovers(self):
        settings = kitlib.normalize({"client": "X", "banned_characters": ["U+2014"], "style": ["Short."]})
        for text in (setup.workspace_yaml(settings), setup.rules_block(settings)):
            self.assertNotIn("{{", text)
        self.assertEqual(kitlib.normalize(kitlib.parse_simple_yaml(setup.workspace_yaml(settings)))["style"], ["Short."])


if __name__ == "__main__":
    unittest.main(verbosity=1)

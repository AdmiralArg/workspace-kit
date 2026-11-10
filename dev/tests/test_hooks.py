#!/usr/bin/env python3
"""Tests for the hooks and the settings reader. Run: python tests/test_hooks.py"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT / "kit" / "hooks"))
import banned_characters  # noqa: E402
import kitlib  # noqa: E402
import lint_nudge  # noqa: E402

EM_DASH = chr(0x2014)
E_ACUTE = chr(0xE9)
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def settings(**over) -> dict:
    raw = {"work_folder": "projects", "banned_characters": [EM_DASH, "U+00E9"], "banned_in": ["files", "replies"]}
    raw.update(over)
    return kitlib.normalize(raw)


class SettingsReaderTest(unittest.TestCase):
    def test_reads_the_shapes_workspace_yaml_uses(self):
        data = kitlib.parse_simple_yaml(
            "# comment\n"
            "client: Acme Media\n"
            "work_folder: projects   # where the work lives\n"
            'banned_characters: ["' + EM_DASH + '", U+00E9]   # two of them\n'
            "banned_in: [files, replies]\n"
            "lint_every_days: 14\n"
            "style:\n"
            "  - Lead with the result.\n"
            '  - "Short answers: no recap."\n'
            "note: >\n"
            "  folded text\n"
            "  on two lines\n"
            "empty:\n"
            "nested:\n"
            "  inner: yes\n"
        )
        self.assertEqual(data["client"], "Acme Media")
        self.assertEqual(data["work_folder"], "projects")
        self.assertEqual(data["banned_characters"], [EM_DASH, "U+00E9"])
        self.assertEqual(data["banned_in"], ["files", "replies"])
        self.assertEqual(data["lint_every_days"], 14)
        self.assertEqual(data["style"], ["Lead with the result.", "Short answers: no recap."])
        self.assertEqual(data["note"], "folded text on two lines")
        self.assertIsNone(data["empty"])
        self.assertEqual(data["nested"], {"inner": True})

    def test_quoted_values_keep_their_content(self):
        data = kitlib.parse_simple_yaml('a: "x: y"   # note\nb: \'#1\'\nc: ["a, b", "#"]\nd: []\n')
        self.assertEqual(data, {"a": "x: y", "b": "#1", "c": ["a, b", "#"], "d": []})

    def test_refuses_what_it_cannot_read_safely(self):
        for bad in ("a: b: c\n", "a: [1, 2\n", 'a: "open\n', "a:\n\tb: 1\n", "just words\n"):
            with self.assertRaises(ValueError, msg=bad):
                kitlib.parse_simple_yaml(bad)

    def test_normalize_fills_defaults_and_decodes_code_points(self):
        s = kitlib.normalize({})
        self.assertEqual((s["work_folder"], s["inbox"], s["lint_every_days"]), ("projects", "Inbox", 28))
        self.assertEqual((s["banned_characters"], s["banned_in"], s["style"]), ([], ["files"], []))
        s = settings(work_folder="design/", mail={"account": "x"})
        self.assertEqual(s["work_folder"], "design")
        self.assertEqual(s["banned_characters"], [EM_DASH, E_ACUTE])
        self.assertEqual(s["extra"], {"mail": {"account": "x"}})
        with self.assertRaises(ValueError):
            kitlib.normalize({"banned_in": ["files", "everywhere"]})
        with self.assertRaises(ValueError):
            kitlib.normalize({"lint_every_days": "soon"})

    def test_character_names_never_print_the_character(self):
        self.assertEqual(kitlib.character_name(EM_DASH), "EM DASH (U+2014)")
        self.assertEqual(kitlib.character_name(E_ACUTE), "LATIN SMALL LETTER E WITH ACUTE (U+00E9)")
        self.assertEqual(kitlib.character_name("--"), "U+002D + U+002D")


class BannedCharactersTest(unittest.TestCase):
    def decide(self, event: dict, **over):
        return banned_characters.decide(event, settings(**over))

    def write(self, tool: str, tool_input: dict) -> dict:
        return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}

    def test_blocks_new_text_in_every_write_tool(self):
        cases = [
            ("Write", {"file_path": "a.md", "content": "one " + EM_DASH + " two"}),
            ("Edit", {"file_path": "a.md", "old_string": "x", "new_string": "caf" + E_ACUTE}),
            ("MultiEdit", {"file_path": "a.md", "edits": [{"old_string": "a", "new_string": "b"},
                                                         {"old_string": "c", "new_string": "d" + EM_DASH}]}),
            ("NotebookEdit", {"notebook_path": "n.ipynb", "new_source": "x = 1  # " + EM_DASH}),
        ]
        for tool, tool_input in cases:
            code, message = self.decide(self.write(tool, tool_input))
            self.assertEqual(code, 2, tool)
            self.assertIn("(U+", message)
            self.assertNotIn(EM_DASH, message)
            self.assertNotIn(E_ACUTE, message)

    def test_message_names_the_character_and_shows_where(self):
        code, message = self.decide(self.write("Write", {"content": "The plan " + EM_DASH + " in short"}))
        self.assertEqual(code, 2)
        self.assertIn("EM DASH (U+2014)", message)
        self.assertIn("...The plan [HERE] in short...", message)

    def test_allows_clean_text_and_ignores_what_is_already_in_the_file(self):
        self.assertEqual(self.decide(self.write("Write", {"content": "plain - text"}))[0], 0)
        old_has_it = {"file_path": "a.md", "old_string": "caf" + E_ACUTE, "new_string": "cafe"}
        self.assertEqual(self.decide(self.write("Edit", old_has_it))[0], 0)

    def codex_patch(self, *body: str) -> dict:
        """A file edit as Codex sends it: one patch in tool_input.command."""
        patch = "\n".join(["*** Begin Patch", "*** Update File: notes.md", "@@", *body, "*** End Patch"])
        return self.write("apply_patch", {"command": patch})

    def test_a_codex_patch_is_checked_on_the_lines_it_adds_only(self):
        code, message = self.decide(self.codex_patch(" context", "-old line", "+new " + EM_DASH + " line"))
        self.assertEqual(code, 2)
        self.assertIn("EM DASH (U+2014)", message)
        self.assertIn("...new [HERE] line...", message)
        removing = self.codex_patch(" context " + EM_DASH, "-old " + EM_DASH + " line", "+new clean line")
        self.assertEqual(self.decide(removing)[0], 0, "removing a banned character must be allowed")
        new_file = "\n".join(["*** Begin Patch", "*** Add File: a.md", "+caf" + E_ACUTE, "*** End Patch"])
        self.assertEqual(self.decide(self.write("apply_patch", {"command": new_file}))[0], 2)
        self.assertEqual(self.decide(self.write("apply_patch", {"command": 12}))[0], 0)
        self.assertEqual(self.decide(self.write("apply_patch", {}))[0], 0)

    def test_other_tools_and_other_events_pass(self):
        self.assertEqual(self.decide(self.write("Bash", {"command": "echo " + EM_DASH}))[0], 0)
        self.assertEqual(self.decide({"hook_event_name": "SessionStart"})[0], 0)
        self.assertEqual(self.decide(self.write("Write", "not a block"))[0], 0)

    def test_nothing_banned_means_nothing_blocked(self):
        event = self.write("Write", {"content": EM_DASH})
        self.assertEqual(self.decide(event, banned_characters=[])[0], 0)
        self.assertEqual(self.decide(event, banned_in=["replies"])[0], 0)

    def test_replies_are_checked_only_when_asked_and_never_twice_in_a_row(self):
        stop = {"hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "Done " + EM_DASH + " all good"}
        code, message = self.decide(stop)
        self.assertEqual(code, 2)
        self.assertIn("EM DASH (U+2014)", message)
        self.assertEqual(self.decide(stop, banned_in=["files"])[0], 0)
        self.assertEqual(self.decide({**stop, "stop_hook_active": True})[0], 0)
        self.assertEqual(self.decide({**stop, "last_assistant_message": "All good."})[0], 0)
        self.assertEqual(self.decide({"hook_event_name": "Stop"})[0], 0)

    def test_real_payloads_from_the_app(self):
        """Payloads captured from a live session, when they have been recorded."""
        found = sorted(FIXTURES.glob("pretooluse-*.json")) if FIXTURES.is_dir() else []
        if not found:
            self.skipTest("no captured payloads in tests/fixtures")
        for path in found:
            event = json.loads(path.read_text(encoding="utf-8"))
            expected = 2 if "banned" in path.name else 0
            self.assertEqual(self.decide(event)[0], expected, path.name)


class HookProcessTest(unittest.TestCase):
    """The hooks as the app runs them: a process, JSON on stdin, an exit code."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "workspace.yaml").write_text(
            "client: Test\nwork_folder: projects\nbanned_characters: [U+2014]\nbanned_in: [files, replies]\nlint_every_days: 28\n",
            encoding="utf-8")
        (self.root / "projects").mkdir()
        self.env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        self.env.pop("WORKSPACE_KIT_CONFIG", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, script: str, stdin, launcher: bool = False, legacy_encoding: bool = False):
        """Runs a hook the way the app does: raw UTF-8 on stdin, never escaped."""
        cmd = [sys.executable, str(KIT / "kit" / "hooks" / script)]
        env = dict(self.env)
        if launcher:
            shell = shutil.which("sh") or shutil.which("bash")
            if not shell:
                self.skipTest("no sh on this machine")
            cmd = [shell, str(KIT / "kit" / "hooks" / "run.sh"), str(KIT / "kit" / "hooks" / script)]
        if legacy_encoding:
            # What a Windows machine does by default: the old encoding on every stream.
            env.update({"PYTHONUTF8": "0", "PYTHONIOENCODING": "cp1252"})
        if not isinstance(stdin, bytes):
            stdin = (json.dumps(stdin, ensure_ascii=False) if isinstance(stdin, dict) else stdin).encode("utf-8")
        done = subprocess.run(cmd, input=stdin, capture_output=True, env=env, cwd=str(self.root), timeout=60)
        done.stdout = done.stdout.decode("utf-8", errors="replace")
        done.stderr = done.stderr.decode("utf-8", errors="replace")
        return done

    def test_banned_text_exits_2_with_a_message_on_stderr(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"content": "a" + EM_DASH + "b"}}
        done = self.run_script("banned_characters.py", event)
        self.assertEqual(done.returncode, 2)
        self.assertIn("EM DASH (U+2014)", done.stderr)
        self.assertEqual(done.stdout, "")

    def test_blocks_on_a_machine_that_defaults_to_the_old_windows_encoding(self):
        """The bug a live session found: the input is UTF-8 whatever the machine prefers."""
        text = "cafæ 日本 " + EM_DASH + " øl"
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"content": text}}
        done = self.run_script("banned_characters.py", event, legacy_encoding=True)
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertIn("EM DASH (U+2014)", done.stderr)
        self.assertIn("日本 [HERE] øl", done.stderr)

    def test_the_payloads_recorded_from_the_app_through_the_real_process(self):
        for name, expected in (("pretooluse-write-banned.json", 2), ("pretooluse-write-clean.json", 0)):
            raw = (FIXTURES / name).read_bytes()
            for legacy in (False, True):
                done = self.run_script("banned_characters.py", raw, legacy_encoding=legacy)
                self.assertEqual(done.returncode, expected, f"{name} legacy={legacy} {done.stderr}")

    def test_clean_text_and_broken_input_exit_0(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"content": "fine"}}
        self.assertEqual(self.run_script("banned_characters.py", event).returncode, 0)
        self.assertEqual(self.run_script("banned_characters.py", "not json").returncode, 0)
        self.assertEqual(self.run_script("banned_characters.py", "").returncode, 0)
        self.assertEqual(self.run_script("banned_characters.py", bytes([255, 254]) + b" not utf-8").returncode, 0)

    def test_a_broken_workspace_yaml_never_blocks(self):
        (self.root / "workspace.yaml").write_text("this is: not: valid\n", encoding="utf-8")
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"content": EM_DASH}}
        self.assertEqual(self.run_script("banned_characters.py", event).returncode, 0)
        self.assertEqual(self.run_script("lint_nudge.py", "").returncode, 0)

    def test_the_launcher_finds_a_python_and_passes_stdin_and_exit_code(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"content": EM_DASH}}
        done = self.run_script("banned_characters.py", event, launcher=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn("EM DASH", done.stderr)

    def test_lint_reminder_through_the_launcher(self):
        (self.root / "projects" / "log.md").write_text("## [2020-01-01] workspace | lint | old pass\n", encoding="utf-8")
        done = self.run_script("lint_nudge.py", "", launcher=True)
        self.assertEqual(done.returncode, 0)
        self.assertIn("the last pass was 2020-01-01", done.stdout)


class LintNudgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "work").mkdir()
        self.settings = {**settings(work_folder="work"), "root": str(self.root)}
        self.today = date(2026, 11, 10)

    def tearDown(self):
        self.tmp.cleanup()

    def log(self, text: str) -> None:
        (self.root / "work" / "log.md").write_text(text, encoding="utf-8")

    def test_silent_without_a_log(self):
        self.assertEqual(lint_nudge.reminder(self.settings, self.today), "")

    def test_says_so_when_there_has_never_been_a_pass(self):
        self.log("## [2026-11-01] workspace | doc | The word lint in the text does not count | lint |\n")
        self.assertIn("no lint pass has been logged in work/log.md", lint_nudge.reminder(self.settings, self.today))

    def test_reminds_only_when_the_newest_pass_is_too_old(self):
        self.log("## [2026-09-01] workspace | lint | first\n## [2026-10-13] workspace | lint | second\n")
        self.assertEqual(lint_nudge.reminder(self.settings, self.today), "", "28 days is not over 28")
        self.log("## [2026-09-01] workspace | lint | first\n## [2026-10-12] alpha | Lint | second\n")
        text = lint_nudge.reminder(self.settings, self.today)
        self.assertIn("the last pass was 2026-10-12, 29 days ago", text)
        self.assertIn("work/", text)

    def test_the_threshold_comes_from_workspace_yaml(self):
        self.log("## [2026-11-01] workspace | lint | recent\n")
        self.settings["lint_every_days"] = 7
        self.assertIn("9 days ago", lint_nudge.reminder(self.settings, self.today))

    def test_main_never_raises_and_prints_nothing_without_a_workspace(self):
        old = dict(os.environ)
        os.environ.pop("CLAUDE_PROJECT_DIR", None)
        os.environ["WORKSPACE_KIT_CONFIG"] = str(self.root / "missing.yaml")
        out = io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                lint_nudge.main()
        finally:
            os.environ.clear()
            os.environ.update(old)
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=1)

# Plan

Where the kit stands and what comes next. The research behind it is in `docs/research/`.

The principle from the research: writing things down is cheap, what the agent reads every session is scarce. Effort goes into deterministic checks, human approval and deletion, not into capture.

## Built in 0.1.0

- **Installer.** `setup.py` with install, check and remove. Additive, repeatable, and safe in an existing project. It records what it installed, so an update never overwrites a file the user edited.
- **One source of rules.** A marked section in `AGENTS.md`, rendered from `workspace.yaml`. `CLAUDE.md` imports it, with a fallback line in case the import is not loaded.
- **Settings.** `workspace.yaml`, read by the rules, the hooks and the skills. Every key has a reader. Personal defaults in `~/.workspace-kit.yaml`.
- **Hard rules as hooks.** Banned characters are stopped in file writes and, when asked for, in replies. Verified against a live Claude Code session on Windows, where it first failed: Python read the input in the old Windows encoding. The launcher now forces UTF-8 and the hooks decode it themselves.
- **Hook launcher.** `run.sh` finds a Python that actually runs, and needs no executable bit.
- **Lint reminder.** A session start hook that reads the log.
- **Skills.** `workspace-lint`, and the two Smooth Slick sets: concept flow and design flow. All read the work folder from `workspace.yaml`.
- **Checks on the kit itself.** Tests for the installer, the hooks and the settings reader. A build that refuses skills which would fail silently. A leak check for client names.

## Next, in order

1. **A script-only lint.** Dead links, orphans, missing or old dates, stale index, retired terms, and whether numbers and quotes exist in the source a page cites. Weekly, no model. The model pass stays for contradictions.
2. **A retro command.** Corrections go in a queue. Each is shown in a table to approve, edit or skip, and sorted into the cheapest form that holds: hook or lint check, rule, skill, glossary term, decision, or discard. A rule is promoted the second time the mistake happens, and carries the date, the correction it came from, and a condition for when to remove it. Nothing writes rules without approval.
3. **A shared layer.** Optional. Generated from the private layer by one promote step that fails if a page depends on private files. It opens as its own folder, with its own `AGENTS.md`, an index, a statement of what an outside agent may do alone, and who wrote and last reviewed each page. A handover is an export of this layer.
4. **A doctor command.** `setup.py check` already proves the install. The doctor adds what only a session can see: never-used skills as candidates for deletion, and rules that no longer earn their place.
5. **Skill tests.** One should-trigger and one near-miss case per skill, in both languages, with the plugin eval that ships with Claude Code.
6. **A marketplace file,** so the two plugin sets can also be installed with a plugin command.

## Decided

- **Three layers.** Personal defaults (a file in the home folder), the method (this kit), and the client's workspace, which stays with the client.
- **Tone stays prose, hard rules are hooks.** No capital letters or "must" wording in instructions. Few hooks, and only for what has to hold every time.
- **Optional tools stay outside.** A tool that only some workspaces need is its own thing, pulled in when needed and configured by its own block in `workspace.yaml`.
- **Heavy methodology kits are not installed.** Ideas are copied. Superpowers is a per-project choice: on for code, off for documentation and design, where there is no evidence for it.
- **Home.** The kit is its own repository, https://github.com/AdmiralArg/workspace-kit, kept outside any client workspace and outside any synced folder. Apache 2.0.
- **English names** for skills and artifact files. Working and deliverable language are per project.

## Not known from any source

- Whether a correction-to-rule loop improves results at all.
- How well Norwegian trigger phrases work.
- Anything measured on documentation or design work, as opposed to code.

Each promoted rule is a guess to re-check.

## Open

- Not verified live: the reply check. It is tested against the documented input, and it never blocks twice in a row.
- Not verified here: that `CLAUDE.md` importing `AGENTS.md` loads in every Claude surface. The fallback line covers the case where it does not.

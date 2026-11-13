# Plan

Where the kit stands and what comes next. The research behind it is in `dev/docs/research/`.

The principle from the research: writing things down is cheap, what the agent reads every session is scarce. Effort goes into deterministic checks, human approval and deletion, not into capture.

## Built

- **Installer.** `setup.py` with install, check and remove. Additive, repeatable, and safe in an existing project. It records what it installed, so an update never overwrites a file the user edited. Every install rebuilds the index, so an update from an older kit leaves a workspace with one.
- **Three agents, one folder.** Claude Code, Codex and OpenCode are wired by the same install, each in its own way, and can work in the same folder. `agents` in `workspace.yaml` decides which.
- **One source of rules.** A marked section in `AGENTS.md`, rendered from `workspace.yaml`. `CLAUDE.md` imports it, with a fallback line in case the import is not loaded.
- **Settings.** `workspace.yaml`, read by the rules, the hooks and the skills. Every key has a reader. Personal defaults in `~/.workspace-kit.yaml`.
- **Hard rules as hooks.** Banned characters are stopped in file writes and, where the agent allows it, in replies. One implementation in Python, reached three ways: Claude Code's hook settings, Codex's hook file, and a small adapter plugin for OpenCode.
- **Launchers.** `run.sh` and `run.cmd` find a Python that actually runs and force UTF-8. Neither needs an executable bit.
- **Skills in two folders.** `.claude/skills` for Claude Code and `.agents/skills` for Codex and OpenCode. OpenCode reads both and keeps one copy.
- **Git, on the owner's word.** Setup asks whether the folder should be under git. A person at the keyboard is asked directly, an agent has to pass the owner's answer, and with no answer nothing is created. On a yes, a repository is created when there is none, with safe settings for a folder opened from several systems. Every log line names its agent, and the rules ask for one commit per piece of work.
- **A check at every commit.** A pre-commit hook stops a commit that adds a banned character or bytes that are not valid text. It is the one check every path goes through: an agent's file tool, a shell command, or a person. It came from a live run where Codex on Windows wrote through the shell, which the file hook cannot see.
- **Plain characters in what agents copy.** Templates that an agent reproduces, such as the decision format, use plain English characters only. This is a precaution, not a fix for something seen.
- **Lint reminder.** At session start, from the log.
- **The read side.** A section in the rules on how to find things: index, then project, then document, then a text search with the glossary's other names. A header on every document (`description`, `date`, `status`). An index built by `build_index.py` from those headers, with a `--check` that the lint runs: stale index, missing descriptions, documents too large to read whole. The log is searched, never read whole. No embeddings and no packages: the corpus is small enough that an index and a text search do better than a retriever that has to be kept in step.
- **The flows in every folder.** The repository is a Claude Code plugin marketplace for the two flows, and `setup.py skills` puts them in `~/.agents/skills` for Codex and OpenCode, with the same update and remove rules as a workspace.
- **Checks on the kit itself.** Tests for the installer, the hooks and the settings reader. A build that refuses skills which would fail silently. A leak check for client names.

## Verified, and how

| What | How it was verified |
|---|---|
| Claude Code stops a banned character in a write and in an edit | Live, in a running session on Windows |
| Claude Code loads the skills and runs the session start hook | A fresh Claude Code process, read from its debug log |
| OpenCode loads the skills, with one copy of each | Asked OpenCode's own server which skills it sees |
| OpenCode stops a banned character, and the model then rewrites the line | Live, with a real model |
| OpenCode attaches the lint reminder to the session | Read back from the session's instructions |
| Codex shows the model the rules and all the skills | `codex debug prompt-input`, which prints what the model is given |
| Codex's patch format is checked on added lines only | Tests, against the format in Codex's documentation |
| Both launchers pass input, output and exit code through | Tests, in `sh` and in the Windows shell, with a space in the folder name |
| Three harnesses doing real work in one folder | OpenCode started a project, Codex recorded a decision, Claude Code wrote a note. Each followed the rules and named itself in the log |
| The commit check stops a real commit | Tests with real git commits, and live in the test folder |
| An update from 0.3.2 brings the read side into a workspace that already has the kit | A folder set up with 0.3.2 under git, then updated with 0.4.0 on macOS: the index builder, the document template, the new rules and the index arrived, `check` passed, a commit went through the commit check, a second run changed nothing, and `remove` took the index out |

## Found by running it for real

- **Windows reads hook input in its old encoding.** A banned character slipped through until the launchers forced UTF-8 and the hooks decoded their input themselves.
- **Codex's sandbox keeps `.git` read-only.** It cannot commit on its own. It says so and leaves the changes, which the rules now ask for.
- **Codex on Windows may write files through PowerShell.** That skips the file hook, and the lines it added had Windows line endings. The rules now ask for the file tool, and the commit check catches a banned character that still gets through.
- **A correction.** The 0.3.0 commit message says a middle dot was broken when Codex wrote it through PowerShell. That was wrong. The file was correct, and only the console used to inspect it showed the character badly. No agent has been seen to corrupt text.
- **An agent may write its own commit message.** The rule now says the message is the log line, word for word.

## Not verified

- **The read side, in a live session.** The tests pass and an update was run for real, but no agent has yet been watched using the index to find something.
- **Codex running the hooks live.** Codex runs a project's hooks only after the user has approved them in `/hooks`. The hooks follow Codex's documented protocol and pass every test, but no live Codex session has run them.
- **The reply check, live.** It is tested against the documented input and never blocks twice in a row.
- **The `CLAUDE.md` import in every Claude surface.** The fallback line covers the case where it does not load.
- **Agents on macOS or Linux.** The live agent checks were on Windows. The test suite and the 0.3.2 update have run on macOS. The code paths for other systems are the simpler ones.

## Next, in order

1. **The rest of a script-only lint.** The stale index, missing descriptions and oversized documents are done, in `build_index.py --check`. Left: dead links, orphans, missing or old dates, retired terms, and whether numbers and quotes exist in the source a page cites. Weekly, no model. The model pass stays for contradictions.
2. **A retro command.** Corrections go in a queue. Each is shown in a table to approve, edit or skip, and sorted into the cheapest form that holds: hook or lint check, rule, skill, glossary term, decision, or discard. A rule is promoted the second time the mistake happens, and carries the date, the correction it came from, and a condition for when to remove it. Nothing writes rules without approval.
3. **A shared layer.** Optional. Generated from the private layer by one promote step that fails if a page depends on private files. It opens as its own folder, with its own `AGENTS.md`, an index, a statement of what an outside agent may do alone, and who wrote and last reviewed each page. A handover is an export of this layer.
4. **A doctor command.** `setup.py check` already proves the install. The doctor adds what only a session can see: never-used skills as candidates for deletion, and rules that no longer earn their place.
5. **Skill tests.** One should-trigger and one near-miss case per skill, in both languages.
6. **More agents.** Cursor and Copilot read `AGENTS.md` already. Their hooks and skill folders are not wired.

## Decided

- **Three layers.** Personal defaults (a file in the home folder), the method (this kit), and the client's workspace, which stays with the client.
- **Home.** The kit is its own repository, https://github.com/AdmiralArg/workspace-kit, kept outside any client workspace and outside any synced folder. Apache 2.0.
- **Tone stays prose, hard rules are hooks.** No capital letters or "must" wording in instructions. Few hooks, and only for what has to hold every time.
- **One implementation per rule.** A check is written once, in `kit/hooks`. Each agent gets a thin way in, never its own copy of the logic.
- **Optional tools stay outside.** A tool that only some workspaces need is its own thing, pulled in when needed and configured by its own block in `workspace.yaml`.
- **Heavy methodology kits are not installed.** Ideas are copied. Superpowers is a per-project choice: on for code, off for documentation and design, where there is no evidence for it.
- **English names** for skills and artifact files. Working and deliverable language are per project.

## Not known from any source

- Whether a correction-to-rule loop improves results at all.
- How well Norwegian trigger phrases work.
- Anything measured on documentation or design work, as opposed to code.

Each promoted rule is a guess to re-check.

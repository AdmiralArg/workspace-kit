# workspace-kit

A working method for doing documentation, design and product work with an AI agent, packaged so it can be dropped into any project folder. One command wires it up. It is safe in a project that already exists: it adds, it never overwrites, and it can be taken out again.

Built for Claude Code. Other agents that read `AGENTS.md` get the rules, but not the hooks or the skills.

## What you get

| Part | What it does |
|---|---|
| Rules | One marked section in `AGENTS.md`, imported by `CLAUDE.md`, so every agent reads the same rules |
| Settings | `workspace.yaml`: who the work is for, where it lives, languages, banned characters |
| Work folder | One subfolder per project, each with a README, a glossary of terms and a decision log |
| Log | One line per piece of work, in a format a script can read |
| Inbox | A drop zone for unsorted material, with a fixed way of taking it in |
| Hooks | A lint reminder at session start, and a hard stop on characters you have banned |
| Skills | A documentation lint, a Double Diamond concept flow (5 skills) and a design flow from loose idea to review (8 skills) |

## Set it up

**Let your agent do it.** Say this to it, in the project you want set up:

> Set up workspace-kit from https://github.com/AdmiralArg/workspace-kit in this project. Follow the INSTALL.md in that repository.

**Or do it yourself.** Get the kit onto your machine, anywhere outside the project:

```bash
git clone https://github.com/AdmiralArg/workspace-kit.git
```

Then, from inside the kit folder:

```bash
python3 setup.py install --workspace /path/to/your/project --dry-run
```

```bash
python3 setup.py install --workspace /path/to/your/project
```

```bash
python3 setup.py check --workspace /path/to/your/project
```

The first shows what would happen and writes nothing. The second does it. The third confirms everything is in place and that the hooks really run. On Windows, use `python` if `python3` does nothing.

Then start a new session in the project, so the rules, skills and hooks load.

## What it does to your project

| It creates, if missing | It adds to, if present | It never touches |
|---|---|---|
| `workspace.yaml` | `AGENTS.md`: one section between two marker lines | Your own text in `AGENTS.md` and `CLAUDE.md` |
| `<work folder>/log.md` and `context.md` | `CLAUDE.md`: an import of `AGENTS.md` | Skills of yours with the same name as one of the kit's |
| `Inbox/README.md` | `.claude/settings.json`: its own hooks | Other settings and other hooks |
| `.workspace-kit/` with hooks and templates | | Anything else in the project |
| 14 skills under `.claude/skills/` | | |

If a file with the same path already exists and the kit did not write it, the kit leaves it alone and says so.

## Settings

Everything that differs between projects is in `workspace.yaml`. Edit it, then run `install` again so the rules and hooks follow.

```yaml
client: Acme Media
work_folder: projects
working_language: English
deliverable_language: English
banned_characters: [U+2014]
banned_in: [files, replies]
lint_every_days: 28
style: ["Lead with the result."]
```

- `banned_characters` takes the character in quotes or its code point. With `files`, the agent cannot write it into a file. With `replies`, a reply that holds it is sent back once to be rewritten.
- Options on the command line (`--client`, `--work-folder`, `--ban` and the rest, see `python3 setup.py --help`) only count the first time. After that, the file decides.
- Defaults you want in every project can live in `~/.workspace-kit.yaml`. See `examples/personal.yaml`.

## Using it

- **Starting something unclear.** The agent offers `concept-flow` when the problem is unclear, `riff` when there is a loose idea, and `grill-me` when a direction is chosen but untested. It offers once and takes no for an answer.
- **A new project.** A folder under the work folder with `README.md`, `context.md` and `decisions.md`, started from `.workspace-kit/templates/project/`.
- **New material.** Drop it in `Inbox/`. The next session reads it, files it where it belongs and logs it.
- **Keeping it honest.** Say "lint the workspace". The lint finds contradictions, undefined terms, stale claims and broken file references, and proposes fixes. A reminder shows when the last pass is too old.

## Update, check, remove

- **Update.** Get the newer kit and run `install` again. Files you have not edited follow the kit. Files you edited are kept as you left them.
- **Check.** `python3 setup.py check --workspace PATH`. It feeds each hook a sample that must be blocked and one that must pass.
- **Remove.** `python3 setup.py remove --workspace PATH`. It takes out what it put in. Your settings, log, glossary and inbox stay.

## What it needs

- Python 3.9 or newer. No packages.
- Claude Code, for the hooks and skills.
- On Windows: Git for Windows, which Claude Code needs anyway.

## What it does not do yet

No command that turns your corrections into rules, no shared layer for other people's agents, no script-only lint. The plan and the research behind it are in `docs/`.

## Working on the kit

```bash
python3 -m unittest discover -s tests
```

```bash
python3 build.py
```

```bash
python3 leak_check.py --workspace /path/to/a/client/workspace
```

The tests cover the installer, the hooks and the settings reader. The build checks every skill and packs the two plugins into `dist/` for uploading to the Claude desktop app. The leak check fails if the kit mentions a client.

The two skill sets in `plugins/` are also complete Claude Code plugins. Smooth Slick Design is adapted from [julianoczkowski/designer-skills](https://github.com/julianoczkowski/designer-skills), Apache 2.0.

## License

Apache 2.0. See `LICENSE`.

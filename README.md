# workspace-kit

A working method for doing documentation, design and product work with an AI agent, packaged so it can be dropped into any project folder. One command wires it up for Claude Code, Codex and OpenCode at once, so you can point any of them at the same folder. It is safe in a project that already exists: it adds, it never overwrites, and it can be taken out again.

## What you get

| Part | What it does |
|---|---|
| Rules | One marked section in `AGENTS.md`, the file every agent reads. `CLAUDE.md` imports it |
| Settings | `workspace.yaml`: who the work is for, where it lives, languages, banned characters, which agents |
| Work folder | One subfolder per project, each with a README, a glossary of terms and a decision log |
| Log | One line per piece of work, naming the agent that did it, in a format a script can read |
| Git | A repository, so each piece of work is a commit with its log line as the message |
| Inbox | A drop zone for unsorted material, with a fixed way of taking it in |
| Hooks | A lint reminder at session start, and a hard stop on characters you have banned |
| Skills | A documentation lint, a Double Diamond concept flow (5 skills) and a design flow from loose idea to review (8 skills) |

## Which agent gets what

| | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Rules | Yes | Yes | Yes |
| The 14 skills | Yes | Yes | Yes |
| Lint reminder at session start | Yes | Yes | Yes |
| Banned characters stopped in files | Yes | Yes | Yes |
| Banned characters stopped in replies | Yes | Yes | No, OpenCode cannot send a reply back |
| Needs a step from you | No | Approve the hooks once, with `/hooks` | No |

Other agents that read `AGENTS.md`, such as Cursor and Copilot, get the rules and the files. They do not get the hooks, and whether they find the skills depends on the agent.

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

Then start a new session in the project, so the rules, skills and hooks load. The kit folder is only needed again to update, check or remove. You can delete it after setup and fetch it again later.

## What lands in your project

Five things you can see, and five hidden folders.

| You see | What it is |
|---|---|
| `workspace.yaml` | The settings |
| `AGENTS.md` | The rules, with one section between two marker lines that belongs to the kit |
| `CLAUDE.md` | Two lines that send Claude Code to `AGENTS.md` |
| `projects/` | Where the work lives, with `log.md` and `context.md`. An existing `projects/` or `design/` is used as it is |
| `Inbox/` | The drop zone |

| Hidden | What it holds |
|---|---|
| `.workspace-kit/` | The hook scripts, the project templates, and the record of what was installed |
| `.claude/` | Claude Code's copy of the skills, and its hooks |
| `.agents/` | The skills, where Codex and OpenCode look |
| `.codex/` | Codex's hooks |
| `.opencode/` | A small adapter that gives OpenCode the same checks |

It never touches your own text in `AGENTS.md` and `CLAUDE.md`, a skill of yours with the same name as one of the kit's, other settings, other hooks, or anything else in the project. If a file with the same path already exists and the kit did not write it, the kit leaves it alone and says so.

## Settings

Everything that differs between projects is in `workspace.yaml`. Edit it, then run `install` again so the rules and hooks follow.

```yaml
client: Acme Media
work_folder: projects
agents: [claude, codex, opencode]
git: yes
working_language: English
deliverable_language: English
banned_characters: [U+2014]
banned_in: [files, replies]
lint_every_days: 28
style: ["Lead with the result."]
```

- `agents` decides which agents are wired. Take one out and run `install`, and its files are removed.
- `banned_characters` takes the character in quotes or its code point. With `files`, the agent cannot write it into a file. With `replies`, a reply that holds it is sent back once to be rewritten.
- Options on the command line (`--client`, `--work-folder`, `--agents`, `--ban` and the rest, see `python3 setup.py --help`) only count the first time. After that, the file decides. The exception is `--git` and `--no-git`, which work on any run.
- Defaults you want in every project can live in `~/.workspace-kit.yaml`. See `kit/personal-defaults.example.yaml`.

## Git and accountability

Setup asks whether you want the folder under git. If you say yes and there is no repository, it creates one and commits what it installed. From then on the rules tell every agent to end its work with one line in the log, naming itself, and one commit with that line as the message. So the history shows what was done, when, and by which agent.

- When you run setup yourself, it asks. When an agent runs it, the agent asks you and passes your answer as `--git` or `--no-git`. With no answer, nothing is created and setup says so.
- The answer is kept as `git: yes` or `git: no` in `workspace.yaml`. Change your mind by running setup again with the other option.
- Files that were in the folder before setup are not committed for you.
- A folder that is already under git is left as it is. Setup commits nothing there.
- In a folder synced between devices, git works, but use it from one device at a time and let the sync finish before you switch.
- Git needs a name and an email to say who made a commit. Setup tells you if they are missing.

## Using it

- **Starting something unclear.** The agent offers `concept-flow` when the problem is unclear, `riff` when there is a loose idea, and `grill-me` when a direction is chosen but untested. It offers once and takes no for an answer.
- **A new project.** A folder under the work folder with `README.md`, `context.md` and `decisions.md`, started from `.workspace-kit/templates/project/`.
- **New material.** Drop it in `Inbox/`. The next session reads it, files it where it belongs and logs it.
- **Keeping it honest.** Say "lint the workspace". The lint finds contradictions, undefined terms, stale claims and broken file references, and proposes fixes. A reminder shows when the last pass is too old.

## Update, check, remove

- **Update.** Get the newer kit and run `install` again. Files you have not edited follow the kit. Files you edited are kept as you left them.
- **Check.** `python3 setup.py check --workspace PATH`. It feeds each hook a sample that must be blocked and one that must pass, in every form an agent uses.
- **Remove.** `python3 setup.py remove --workspace PATH`. It takes out what it put in. Your settings, log, glossary, inbox and git history stay.

## What it needs

- Python 3.9 or newer. No packages.
- At least one of Claude Code, Codex or OpenCode.
- Git, for the history. Without it everything else still works.
- On Windows: Git for Windows, which Claude Code needs anyway.

## What it does not do yet

No command that turns your corrections into rules, no shared layer for other people's agents, no script-only lint. The plan and the research behind it are in `dev/docs/`.

## In this repository

| Path | What |
|---|---|
| `setup.py` | The installer |
| `INSTALL.md` | The steps an agent follows to set the kit up |
| `kit/` | Everything that gets installed: hooks, templates, skills, the OpenCode adapter |
| `dev/` | For working on the kit itself: tests, the build, the leak check, the plan and the research |

```bash
python3 -m unittest discover -s dev/tests
```

```bash
python3 dev/build.py
```

```bash
python3 dev/leak_check.py --workspace /path/to/a/client/workspace
```

The tests cover the installer, the hooks and the settings reader. The build checks every skill and packs the two skill sets into `dev/dist/` as plugins for the Claude desktop app. The leak check fails if the kit mentions a client.

Smooth Slick Design, one of the two skill sets in `kit/plugins/`, is adapted from [julianoczkowski/designer-skills](https://github.com/julianoczkowski/designer-skills), Apache 2.0.

## License

Apache 2.0. See `LICENSE`.

# workspace-kit

A working method for doing documentation, design and product work with an AI agent, packaged so it can be dropped into any project folder. One command wires it up for Claude Code, Codex and OpenCode at once, so you can point any of them at the same folder. It is safe in a project that already exists: it adds, it never overwrites, and it can be taken out again.

## What you get

| Part | What it does |
|---|---|
| Rules | One marked section in `AGENTS.md`, the file every agent reads. `CLAUDE.md` imports it |
| Settings | `workspace.yaml`: who the work is for, where it lives, languages, banned characters, which agents |
| Work folder | One subfolder per project, each with a README, a glossary of terms and a decision log |
| Index | One line per document, built by a script from the documents themselves. It is where an agent starts when it looks for something |
| Log | One line per piece of work, naming the agent that did it, in a format a script can read |
| Git | A repository, so each piece of work is a commit with its log line as the message |
| Inbox | A drop zone for unsorted material, with a fixed way of taking it in |
| Hooks | A lint reminder at session start, a hard stop on characters you have banned, and a check at every commit |
| Skills | A documentation lint, a Double Diamond concept flow (5 skills) and a design flow from loose idea to review (8 skills) |

## Which agent gets what

| | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Rules | Yes | Yes | Yes |
| The 14 skills | Yes | Yes | Yes |
| Lint reminder at session start | Yes | Yes | Yes |
| Banned characters stopped in files | Yes | Yes | Yes |
| Banned characters stopped in replies | Yes | Yes | No, OpenCode cannot send a reply back |
| Makes its own commits | Yes | Its sandbox protects git, so it asks you to approve the commit or leaves it to you | Yes |
| Needs a step from you | No | Approve the hooks once, with `/hooks` | No |

Whatever an agent's own hook misses is caught when the work is committed. That covers text an agent writes through a shell command instead of its file tool, which Codex on Windows sometimes does.

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
| `projects/` | Where the work lives, with `log.md`, `context.md` and `index.md`. An existing `projects/` or `design/` is used as it is |
| `Inbox/` | The drop zone |

| Hidden | What it holds |
|---|---|
| `.workspace-kit/` | The hook scripts, the index builder, the templates, and the record of what was installed |
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
- **A check at every commit.** With git on, a commit is stopped if a line it adds holds a banned character, or bytes that are not valid text. It looks only at added lines, so old text never stops a commit, and `git commit --no-verify` overrules it. If the repository already has a pre-commit hook of its own, the kit leaves that alone and says so.
- Files that were in the folder before setup are not committed for you.
- A folder that is already under git is left as it is. Setup commits nothing there.
- In a folder synced between devices, git works, but use it from one device at a time and let the sync finish before you switch.
- Git needs a name and an email to say who made a commit. Setup tells you if they are missing.

## Using it

- **Starting something unclear.** The agent offers `concept-flow` when the problem is unclear or you are thinking out loud about it, `riff` when there is a loose idea for something to build, and `grill-me` when a direction is chosen but untested. It offers once and takes no for an answer.
- **A new project.** A folder under the work folder with `README.md`, `context.md` and `decisions.md`, started from `.workspace-kit/templates/project/`.
- **Finding something.** The agent reads `projects/index.md`, narrows to the project and the document, and searches the files for the word and its other names from the glossary. It names the file an answer rests on. There is no search engine and nothing to keep running: the index is a text file, rebuilt with `sh .workspace-kit/hooks/run.sh .workspace-kit/hooks/build_index.py`.
- **A new document.** Three lines at the top say what question it answers, when it was last true, and whether it is current, a snapshot or superseded. The index is built from them.
- **New material.** Drop it in `Inbox/`. The next session reads it, files it where it belongs and logs it.
- **Keeping it honest.** Say "lint the workspace". The lint finds contradictions, undefined terms, stale claims, a stale index, documents with no description, documents too large to read whole and broken file references, and proposes fixes. A reminder shows when the last pass is too old.

## Update

An update is the same `install` command, run again with a newer kit. It reads `workspace.yaml` and the record of what it installed last time, and changes only what the newer kit changes.

**Let your agent do it.** Say this to it, in the project:

> Update workspace-kit in this project from https://github.com/AdmiralArg/workspace-kit. Follow the "Updating" part of INSTALL.md in that repository.

**Or do it yourself.** Get the newer kit. If you still have the folder you cloned, pull it, otherwise clone it again:

```bash
git -C /path/to/workspace-kit pull
```

Then, from inside the kit folder, see which version the project has, see what the update would change, do it, and check it:

```bash
python3 setup.py check --workspace /path/to/your/project
```

```bash
python3 setup.py install --workspace /path/to/your/project --dry-run
```

```bash
python3 setup.py install --workspace /path/to/your/project
```

```bash
python3 setup.py check --workspace /path/to/your/project
```

The first line of `check` fails with `installed 0.3.2, this kit is 0.4.0. Run install to update` when the project is behind. Leave out the setup options: once `workspace.yaml` exists they are ignored, and you change settings by editing the file. Then start a new session in the project, so the new rules, skills and hooks load.

What an update does to each kind of file:

| File | On update |
|---|---|
| Hooks, templates, skills and the OpenCode adapter, untouched since install | Replaced with the newer kit's version |
| The same files, edited by you | Left alone, and listed as "left alone, you edited it". The newer version is not installed |
| Files the newer kit no longer has | Removed, unless you edited them |
| `AGENTS.md` and `CLAUDE.md` | Only the section between the markers is rewritten. Your own text above and below stays |
| `.claude/settings.json`, `.codex/hooks.json` | Only the kit's hooks are changed. Your settings and other hooks stay |
| `workspace.yaml`, the log, the glossary, the inbox, your documents | Never touched |
| `<work folder>/index.md` | Rebuilt from the documents. An `index.md` you wrote yourself is left alone |

To take the kit's version of a file you edited, delete the file and run `install` again.

If the project is under git, the update commits nothing. Add a line to the log, such as `## [2026-11-13] workspace | doc | workspace-kit updated from 0.3.2 to 0.4.0 [Claude Code]`, and commit the changes with that line as the message. Your agent does this for you when it runs the update.

To update several projects at once, run the same command for each:

```bash
for p in ~/work/alpha ~/work/beta; do python3 setup.py install --workspace "$p"; done
```

**From 0.3 to 0.4.** The update adds the index builder, a template for new documents, the "Finding things" rules and the index itself. Documents written before have no header yet, so the index takes each one's description from its first line of text. Say "lint the workspace" to have the agent propose the missing headers.

## The flows in every folder

The concept and design flows are useful outside a workspace too. They can be installed once for your user, so every agent has them in every folder. Nothing is uploaded anywhere: they come from this repository and live on your machine.

**Claude Code** gets them as two plugins, from this repository as a plugin marketplace:

```bash
claude plugin marketplace add AdmiralArg/workspace-kit
```

```bash
claude plugin install smooth-slick-concept@workspace-kit
```

```bash
claude plugin install smooth-slick-design@workspace-kit
```

Their skills are then named `smooth-slick-concept:concept-flow` and so on. To update, run `claude plugin marketplace update workspace-kit`, then `claude plugin update smooth-slick-concept@workspace-kit` and the same for design.

**Codex** reads the same marketplace:

```bash
codex plugin marketplace add AdmiralArg/workspace-kit
```

```bash
codex plugin add smooth-slick-concept@workspace-kit
```

```bash
codex plugin add smooth-slick-design@workspace-kit
```

To update, run `codex plugin marketplace upgrade workspace-kit`.

**OpenCode** has no plugins of this kind, so it gets the skills as files in `~/.config/opencode/skills`, a folder only OpenCode reads. From inside the kit folder:

```bash
python3 setup.py skills
```

That puts the 13 skills of the two flows there. Run it again after pulling a newer kit to update them: skills you have not edited follow the kit, skills you edited are kept, and a skill of the same name that the kit did not write is left alone. `python3 setup.py skills --remove` takes them out. `workspace-lint` is not among them, since it needs a workspace.

Older copies compete with these. If the plugins were uploaded to claude.ai, Claude Code also loads them as `smooth-slick-concept@synced`: turn that off with `claude plugin disable smooth-slick-concept@synced`, and the same for design. In Codex, remove a copy from another marketplace with `codex plugin remove smooth-slick-concept@<marketplace>`.

## Check and remove

- **Check.** `python3 setup.py check --workspace PATH`. It feeds each hook a sample that must be blocked and one that must pass, in every form an agent uses.
- **Remove.** `python3 setup.py remove --workspace PATH`. It takes out what it put in, the index included. Your settings, log, glossary, inbox and git history stay.

## What it needs

- Python 3.9 or newer. No packages.
- At least one of Claude Code, Codex or OpenCode.
- Git, for the history. Without it everything else still works.
- On Windows: Git for Windows, which Claude Code needs anyway.

## What it does not do yet

No command that turns your corrections into rules, no shared layer for other people's agents, and only the first part of a script-only lint (the index check). No search by meaning: finding things is the index plus a text search, which holds up to some hundreds of documents. The plan and the research behind it are in `dev/docs/`.

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

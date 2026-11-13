# Smooth Slick Concept

A Double Diamond concept flow for Claude Cowork. Four phases that take you from a vague situation to a clear, defensible concept recommendation.

## Install

In Claude Code:

```
/plugin install smooth-slick-concept --marketplace AdmiralArg/workspace-kit
```

In Codex:

```
codex plugin marketplace add AdmiralArg/workspace-kit
codex plugin add smooth-slick-concept@workspace-kit
```

For OpenCode, run `python3 setup.py skills` from the workspace-kit folder. It puts the skills in `~/.config/opencode/skills`. A workspace set up with the kit has them already.

## Skills

| Skill | Phase | What it does |
|-------|-------|-------------|
| **concept-flow** | Orchestrator | Runs all four phases in sequence. Start here. |
| **explore** | Diamond 1, diverge | Maps the problem space broadly. |
| **frame** | Diamond 1, converge | Sharpens into a specific problem statement. |
| **ideate** | Diamond 2, diverge | Generates multiple solution directions. |
| **select** | Diamond 2, converge | Evaluates directions and picks a recommendation. |

## How It Works

```
explore -> frame -> ideate -> select -> [hand off to production flow]
```

The first diamond is about the problem: explore opens wide, frame narrows to a specific problem worth solving. The second diamond is about the solution: ideate opens wide again with multiple directions, select narrows to a recommended approach.

Frame and Select have built-in critical challenge. Instead of a separate "stress-test" step, the convergent phases themselves push back on the user's thinking to make sure decisions are defensible.

## Work folder

`<work-folder>` is the folder that holds one subfolder per project. Each skill resolves it the same way: the `work_folder` value in `workspace.yaml` at the project root, then the folder the project's `CLAUDE.md` or `AGENTS.md` names for project work, then an existing `projects/` or `design/` folder. If none of these settle it, the skill asks once and suggests `projects/`.

## Artifacts

Every artifact saves to `<work-folder>/<slug>/<slug>-<type>.md`:

- `<slug>-landscape.md` (explore)
- `<slug>-problem-frame.md` (frame)
- `<slug>-concepts.md` (ideate)
- `<slug>-recommendation.md` (select)

## Bridge to Production

The recommendation artifact ends with a structured "Handoff to Production Flow" section. If you also have the Smooth Slick Design plugin installed, running `design-brief` after the concept flow will pick up the problem frame, chosen direction, and constraints automatically.

## Principles

- **The user is the expert.** The skill is a thinking partner, not a thinking replacement. It asks questions and listens, then takes ownership of writing the artifact.
- **No solutions in Diamond 1.** Explore and Frame stay in the problem space. Solution ideas are parked for Ideate.
- **Breadth before depth.** Ideate pushes for genuinely different directions, not variations on the obvious answer.
- **Challenge is built in.** Frame challenges "is this the right problem?" and Select challenges "is this the right solution?" No separate challenge step needed.

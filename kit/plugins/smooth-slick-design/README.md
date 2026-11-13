# Smooth Slick Design

A design-tool-focused workflow for Claude Cowork. Seven skills plus an orchestrator that take you from a loose idea to a reviewed design, with structured artifacts at every step. Mockup-first, system and technology agnostic, code generation only when explicitly requested.

## Install

In Claude Code:

```
/plugin install smooth-slick-design --marketplace AdmiralArg/workspace-kit
```

For Codex and OpenCode, run `python3 setup.py skills` from the workspace-kit folder. It puts the skills in `~/.agents/skills`. A workspace set up with the kit has them already.

## Skills

| Skill | What it does |
|-------|-------------|
| **design-flow** | Orchestrates all phases in sequence. Start here for a full project. |
| **riff** | Bounces loose concepts and writes a short sketch. The earliest step. |
| **grill-me** | Stress-tests the chosen direction and saves the resulting plan. |
| **design-brief** | Writes a specific brief from concept flow output, sketch, grilled plan, or brand assets. |
| **information-architecture** | Defines flows, surfacing rules, and data presentation. |
| **design-tokens** | Establishes the visual foundation for use in the design tool of choice. |
| **brief-to-tasks** | Designer-led task list. Each task picks its own deliverable form. |
| **design-review** | Critiques what was produced against the brief, IA, tokens, and tasks. |

## Workflow

Run the full sequence with `design-flow`, or invoke individual skills as needed. All artifacts save to `<work-folder>/<slug>/` in your project, with filenames that include the slug so they remain self-identifying when shared.

```
riff -> grill-me -> design-brief -> information-architecture -> design-tokens -> brief-to-tasks -> [design work in your tool] -> design-review
```

Phases 1 through 6 are continuous; the design work happens outside the flow in your tool of choice (Figma, Paper Design, Penpot, Sketch, paper, somewhere else); design-review runs when you are ready to critique what you produced.

## Work folder

`<work-folder>` is the folder that holds one subfolder per project. Each skill resolves it the same way: the `work_folder` value in `workspace.yaml` at the project root, then the folder the project's `CLAUDE.md` or `AGENTS.md` names for project work, then an existing `projects/` or `design/` folder. If none of these settle it, the skill asks once and suggests `projects/`.

## Artifacts

Every artifact saves to `<work-folder>/<slug>/<slug>-<type>.md`:

- `<slug>-sketch.md` (riff)
- `<slug>-grilled-plan.md` (grill-me)
- `<slug>-brief.md` (design-brief)
- `<slug>-ia.md` (information-architecture)
- `<slug>-tokens.md` (design-tokens)
- `<slug>-tasks.md` (brief-to-tasks)
- `<slug>-review.md` plus `screenshots/` (design-review)

## Bridge from Concept Flow

If the Smooth Slick Concept plugin has been used first, `design-brief` automatically picks up the concept recommendation artifact (`<slug>-recommendation.md`) and pre-populates Problem, Solution, Audience, and Out of Scope from it. No need to re-explain the concept decision.

## Principles

- **Mockup-first**: skills produce design-tool deliverables by default. Code is opt-in only when explicitly requested.
- **No codebase scans by default**: the user can opt in if a codebase is in play.
- **Surface-aware**: TV, mobile, desktop, voice, kiosk and other surfaces drive what questions get asked and what tokens get added.
- **Brand-driven when a brand exists**: tokens and visual direction derive from the brand source, not invented in parallel.
- **Workflow-aware**: skills ask where you are designing (Figma, Paper Design, Penpot, Sketch, etc.) and adapt their handoffs.

## Source

Adapted from [julianoczkowski/designer-skills](https://github.com/julianoczkowski/designer-skills), Apache 2.0 license.

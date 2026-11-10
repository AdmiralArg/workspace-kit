---
name: concept-flow
description: >
  Runs the full Double Diamond concept flow in sequence: explore, frame, ideate, select. Use when a session starts undefined (an unclear problem, no named deliverable, a new project without a frame) and offer the flow before anything is built. Also when the user says "run the concept flow", «kjør konseptflyten», "help me think this through end to end", «start konseptløpet», or wants to go from a vague situation to a clear recommendation.
---

# Concept Flow

## Establishing the Work Folder and Slug

Every artifact in this workflow lives at `<work-folder>/<slug>/<slug>-*.md`. Establish both before reading or writing anything.

**Work folder.** The folder that holds one subfolder per project. Resolve it in this order and stop at the first hit:

1. `workspace.yaml` at the project root has a `work_folder` value. Use it.
2. The project's `CLAUDE.md` or `AGENTS.md` names the folder where project work lives. Use that.
3. Exactly one of `projects/` or `design/` exists at the project root. Use it.
4. None of the above. Ask the user once, suggest `projects/`, and offer to save the answer as `work_folder` in `workspace.yaml`.

Say which folder you resolved, in one line, the first time you read or write in it. Everywhere below, `<work-folder>` means the resolved folder.

**Slug.**

1. If the user names the project, derive the slug from it: lowercase, hyphenated, no diacritics. "TV-søk redesign" becomes `tv-sok-redesign`.
2. If the user does not name it, list the existing directories under `<work-folder>/` and ask which project this is, offering to create a new one.
3. If `<work-folder>/` does not exist or is empty, ask for a project name and create `<work-folder>/<slug>/`.

Never guess the work folder or the slug silently. If you cannot establish either, say so and ask. A wrong folder or slug means this skill reads nothing, finds no prior work, and starts from zero without telling the user.

Orchestrate the four-phase Double Diamond concept flow. Each phase must be completed and confirmed before moving to the next. Do not rush. The flow is designed to help the user think better and more precisely.

## The Sequence

1. **Explore** (Diamond 1, diverge) - Map the problem space broadly.
2. **Frame** (Diamond 1, converge) - Sharpen into a specific, defensible problem statement.
3. **Ideate** (Diamond 2, diverge) - Generate multiple solution directions.
4. **Select** (Diamond 2, converge) - Evaluate and converge on a recommendation.

## Before Starting

Present the four phases briefly. Explain that the flow moves through two diamonds: first understanding the problem, then exploring solutions. Each diamond opens wide and then narrows.

Ask which phases to skip. Common skip patterns:
- Skip Explore if the user already has a clear picture of the problem space
- Skip Frame if the user already has a sharp, specific problem statement
- Never skip both Explore and Frame; the concept flow needs a problem to work from

Confirm the project slug before starting. The slug is used in every artifact filename.

## During Each Phase

1. Announce the phase: what it does and what it produces
2. Load and follow the corresponding skill completely. Do not summarize or abbreviate.
3. After completing the phase, confirm the artifact was saved to `<work-folder>/<slug>/`
4. Confirm with the user before proceeding to the next phase
5. Check whether prior outputs affect upcoming work before moving forward

## Mid-Flow Returns

If the user resumes an interrupted flow, scan `<work-folder>/<slug>/` for completed artifacts. Identify the last completed phase and resume from the next incomplete one. Expected artifact filenames:

- Phase 1 (Explore): `<slug>-landscape.md`
- Phase 2 (Frame): `<slug>-problem-frame.md`
- Phase 3 (Ideate): `<slug>-concepts.md`
- Phase 4 (Select): `<slug>-recommendation.md`

## After the Flow

When all four phases are complete, tell the user the concept flow is done and explain the bridge to the production flow:

> "The concept flow is complete. You have a problem landscape, a problem frame, a concept spread, and a recommendation, all saved under `<work-folder>/<slug>/`. When you're ready to move into production design, run design-brief. It will pick up the problem frame, chosen direction, and constraints from the recommendation so you don't start from scratch."

Do not auto-trigger design-brief.

## Activation Examples

- "Run the concept flow"
- "Start the concept flow"
- "Take this from problem to recommendation"
- "Help me think through this end to end"
- "I need to figure out what to build"
- "Run the concept flow"
- "Start the concept flow"
- "Take this from problem to recommendation"
- "Help me think through this end to end"
- "I need to figure out what to build"

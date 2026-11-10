---
name: design-flow
description: >
  Runs the full design workflow in sequence: riff, grill-me, brief, information architecture, tokens, tasks, review. Use when the user says "run the design flow", «kjør designflyten», "start the design process", «ta meg gjennom hele løpet», or wants to go from a loose idea to a reviewed design step by step.
---

# Design Flow

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

Orchestrate the complete design workflow as a guided sequence through seven phases. Do not rush. Each phase must be completed and confirmed before moving to the next.

The flow is designed to be paused and resumed. Phases 1 through 6 produce planning and design-foundation artifacts; phase 7 (review) usually runs after the user has done the actual design work in their tool of choice.

## The Sequence

1. **Riff (optional)** - Shape a loose idea into a sketch. Skip if the user already has a sharp concept.
2. **Grill Me** - Stress-test the chosen direction and resolve open questions.
3. **Design Brief** - Document the project specifically and concretely.
4. **Information Architecture** - Define how the experience flows and behaves.
5. **Design Tokens** - Establish the visual foundation for use in the design tool.
6. **Brief to Tasks** - Plan the design work as an ordered checklist.
7. **Design Review** - Critique what was produced against the brief, IA, tokens, and tasks. Usually runs after the user has done design work outside the flow.

## Before Starting

Check for `<work-folder>/<slug>/<slug>-recommendation.md` first. If it exists, the user has already run the concept flow (`concept-flow`) and the direction is chosen and already stress-tested. Default to skipping phase 1 and phase 2, say why, and confirm. Do not re-litigate a decision the concept flow already made.

Present the full sequence to the user. Ask which phases to skip. Common skip patterns:
- Skip Riff if the user already has a sharp concept
- Skip Grill Me if the user already has clarity and a written plan
- Skip Information Architecture for single components or isolated UI
- Skip Design Tokens if the project already has an established brand or token system
- Always pause before phase 7; review usually comes later

Confirm the project slug before starting. The slug is used in every artifact filename.

## During Each Phase

1. Announce the phase with its expected output and filename
2. Load and follow the corresponding skill completely. Do not summarize or abbreviate.
3. After completing the phase, confirm the artifact was saved to `<work-folder>/<slug>/<slug>-<artifact>.md`
4. Confirm with the user before proceeding
5. Check whether prior outputs affect upcoming work before moving forward

## Mid-Flow Returns

If the user resumes an interrupted flow, scan `<work-folder>/<slug>/` for completed artifacts. Identify the last completed phase and resume from the next incomplete one. Expected artifact filenames:

- Phase 1 (Riff): `<slug>-sketch.md`
- Phase 2 (Grill Me): `<slug>-grilled-plan.md`
- Phase 3 (Design Brief): `<slug>-brief.md`
- Phase 4 (Information Architecture): `<slug>-ia.md`
- Phase 5 (Design Tokens): `<slug>-tokens.md`
- Phase 6 (Brief to Tasks): `<slug>-tasks.md`
- Phase 7 (Design Review): `<slug>-review.md` plus a `screenshots/` directory

## Pause Before Review

Phase 7 is not continuous with phases 1 through 6. After phase 6 completes, the tasks list is ready and the user goes off to do the actual design work in their tool of choice (Figma, Paper Design, Penpot, Sketch, paper, somewhere else). Tell the user this explicitly:

> Phases 1 through 6 are done. The plan and foundation are saved under `<work-folder>/<slug>/`. Go do the design work in your tool. Invoke `design-review` when you are ready to critique what you produced.

Do not auto-trigger phase 7.

## Activation Examples

- "Run the design flow"
- "Start the design process"
- "Walk me through the full workflow"
- "Take this idea from loose concept to reviewed design"
- "Kjør designflyten"
- "Start designprosessen"
- "Ta meg gjennom hele løpet"
- "Ta denne ideen fra løst konsept til ferdig gjennomgått design"

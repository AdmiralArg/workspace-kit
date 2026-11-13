---
name: riff
description: >
  Shapes a loose idea for something to build (a feature, a screen, a product) before a design brief. Use when the user brings such an idea without asking for anything specific, and offer a riff before anything is built. Also on "riff with me", «riff med meg», "I have an idea for a feature", «jeg har en ide til en funksjon», "shape this idea". A problem that is not yet understood belongs to concept-flow instead.
---

# Riff

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

Help the user move a loose concept into something with enough shape to stress-test. The goal is not a polished brief, it is a captured sketch that the rest of the workflow can build on.

## Mode

Be divergent before convergent. Generate options, raise tensions, propose framings. Do not converge prematurely. The user is here to think, not to decide.

## Methodology

1. **Hear the seed**: Ask the user for one sentence on what they are noodling on. Do not demand structure.
2. **Riff with them**: Offer 3 to 5 angles, framings, analogies, or scope cuts and expansions. Each should be short and concrete enough to react to.
3. **Surface tensions**: Name the trade-offs and open questions you can already see. Help the user notice what they have not decided yet.
4. **Capture what stuck**: As the user reacts, track which framings landed and which got rejected, and why.
5. **Write the sketch**: When the conversation has produced a workable shape, save a short sketch to `<work-folder>/<slug>/<slug>-sketch.md`. The filename must include the slug so the file is self-identifying when shared.

## Sketch Structure

Keep it short, four to eight short sections at most:

- **Problem**: One paragraph on what this is trying to solve, in the user's own words where possible
- **Audience**: Who this is for, if known
- **Shape**: The rough form of the solution (page, flow, feature, system) without committing to specifics
- **Constraints**: Anything that is already pinned down (tech, brand, timeline, scope cuts)
- **Open questions**: What still has to be decided
- **Rejected angles**: Brief list of framings that came up and got cut, with one-line reasons (this saves rework later)

## Before Asking Questions

Investigate before interrogating. Scan the codebase, design tokens, existing `<work-folder>/` artifacts, and any prior sketches for shared context. Only ask the user what evidence cannot answer.

## Activation Examples

- "Riff with me on a settings redesign"
- "I have a loose idea for a notifications panel"
- "Help me bounce some concepts for the onboarding flow"
- "Shape this idea before I commit to a brief"
- "Riff with me on a settings redesign"
- "I have a loose idea for a notifications panel"
- "Help me bounce some concepts for the onboarding flow"
- "Shape this idea before I commit to a brief"

## When to Stop

Stop when the user can articulate the problem, the audience, and a rough shape, and when the open questions are listed rather than tangled. The sketch does not have to be complete, it has to be sharable.

## Handoff

After saving the sketch, mention that `grill-me` is the natural next step when the user is ready to pressure-test the chosen direction. Do not invoke it automatically. The user decides when to graduate from sketch to plan.

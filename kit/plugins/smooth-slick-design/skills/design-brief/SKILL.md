---
name: design-brief
description: >
  Writes a specific design brief that builds on prior work (concept recommendation, sketch or grilled plan) and takes in existing brand assets, references and usage context. Use when the user says "create a design brief", «lag en designbrief», "write a brief for", «skriv en brief for», "document the direction", or wants a structured base for the rest of the design work.
---

# Design Brief

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

Produce a specific, well-considered brief that builds on what has already been decided and pulls in everything the user has on hand. The goal is a brief that is concrete enough to design from, not a generic template.

## Inputs to Load First

Before asking any questions, look for and load:

1. **Concept recommendation**: `<work-folder>/<slug>/<slug>-recommendation.md` (output of the Smooth Slick Concept flow's `select` phase). Contains a structured Handoff section with the problem frame, chosen direction, key constraints, and rejected directions. If this exists, it is the strongest starting point: pre-populate Problem, Solution, Audience, and Out of Scope from the handoff section, and do not re-litigate the concept decision.
2. **Concept sketch**: `<work-folder>/<slug>/<slug>-sketch.md` (output of `riff`). Carries the chosen direction, audience, and rejected angles.
3. **Grilled plan**: `<work-folder>/<slug>/<slug>-grilled-plan.md` (output of `grill-me`). Carries decisions reached, tensions resolved, anti-decisions, and open questions.
4. **Reference material the user has provided**: Figma files, Figma libraries, screenshots, exported brand files (brand.zip, design-system.zip), pictures, hand-drawn sketches, written notes, or a Claude Design file. If not obvious from the conversation or attachments, ask the user what they have.
5. **A codebase**: Only scan a codebase if the user explicitly says one is in play. Most users of this skill will not have one. Do not assume.

If a concept recommendation exists, treat it as the primary input. The brief extends and operationalizes the recommendation, it does not revisit the concept decision. If no recommendation exists but both the sketch and the grilled plan exist, treat those as load-bearing context. The brief sharpens and extends them, it does not start over. Do not re-litigate decisions that prior phases already resolved.

## Process

### 1. Confirm Project Identity
Confirm the project name, slug, and one-sentence intent based on the loaded inputs. Use the slug to name the brief file (see Output below).

### 2. Inventory Available Assets
Make a short list of what the user has on hand. Reference the path or URL for each item:
- Brand assets (Figma library URL, brand.zip path, design-system.zip path, Claude Design file, brand guideline doc)
- Reference screenshots, photos, hand sketches
- Existing UI screenshots from related work
- Anti-references (things to actively avoid)

If a brand exists, treat it as authoritative for color, type, spacing, and dark mode. Do not invent a parallel system.

### 3. Pin Down Usage Context
Usage context is load-bearing and shapes everything downstream. This should usually be surfaced already in `riff` or `grill-me`; confirm rather than re-derive. If still unclear, ask:
- Primary surface (TV, desktop, mobile, tablet, kiosk, watch, embedded display, in-vehicle, set-top box)
- Input method (remote, mouse plus keyboard, touch, voice, controller, gesture)
- Viewing distance and conditions (10-foot UI, leaning back, walking past, focused work, bright sunlight, low light)
- Session length and frequency (glance, short task, long focused session, ambient)

A TV remote-driven UI and a touch mobile UI are different products, even with the same content. Treat surface and input as first-class constraints.

### 4. Establish Visual Direction
Two paths:

- **If a brand exists**: Treat the brand as the visual vocabulary. Document where it lives, how to apply it, and what the brand says about dark mode (assume dark mode is part of any modern brand; flag explicitly if missing). Do NOT propose a separate aesthetic philosophy.
- **If no brand exists**: Ask about aesthetic direction, references, and explicit anti-references. Confirm with the user before locking it in.

### 5. Resolve Remaining Decisions
Walk through anything the prior steps did not pin down:
- Accessibility requirements (WCAG level, keyboard, focus management, screen reader, captioning if media is involved)
- Responsive or multi-surface behavior (only if more than one surface is in scope)
- Key interactions and state feedback
- Explicit out-of-scope boundaries
- Loose success metrics (see template)

### 6. Write the Brief
Save the brief using the template below.

## Output

Save to `<work-folder>/<slug>/<slug>-brief.md`. The filename must include the slug so the file is self-identifying when shared or pasted into another conversation. Examples: `tv-search-redesign-brief.md`, `notifications-panel-brief.md`, `epg-grid-v2-brief.md`.

## Brief Template

```markdown
# [Project Name] Design Brief

## Project Identity
- Slug: [slug]
- One-sentence intent: [pulled from sketch and sharpened]
- Status: [exploring | committed | in-build]

## Problem
[User-centered friction in plain language. Pulled from the sketch and sharpened.]

## Solution
[Experience-level description of what is being built. Pulled from the grilled plan.]

## Audience
[Who this is for. Pull from the sketch.]

## Usage Context
- Primary surface: [TV / desktop / mobile / kiosk / etc.]
- Input method: [remote / touch / mouse + keyboard / voice / etc.]
- Viewing conditions: [distance, posture, attention level, lighting]
- Session pattern: [glance, short task, long session, ambient]

## Brand and Visual System
[If brand exists: where it lives, how to apply it, dark mode handling, anything notable.
If no brand exists: aesthetic direction, references, explicit anti-references.]

## Experience Principles
[Up to 3 principles that resolve the core design tensions.]

## Reference Assets
[Bulleted list of every asset informing the design: Figma URLs, brand.zip paths, screenshots, sketches, prior `<work-folder>/` artifacts. Each entry should be a path or URL plus a one-line note on why it matters.]

## Component Inventory
[Required UI elements. Skip this section unless a codebase or component library is in play. When in play, mark each as Exists / Modify / New.]

## Key Interactions
[Critical state changes and user feedback patterns: focus moves, loading, error, empty, success, transitions.]

## Responsive or Multi-Surface Behavior
[How the UI adapts across the surfaces in scope. Skip if only one surface.]

## Accessibility Requirements
[WCAG level, keyboard navigation, focus management, screen reader support, captioning if applicable, remote-friendly focus behavior on TV.]

## Success Metrics (Loose)
[How we'd know this worked. Keep loose; metrics are often set by someone other than the designer or evolve over time. One to three rough indicators are enough. Examples: "users find the show they want without scrolling past 2 rows", "support tickets about settings drop", "task time falls noticeably".]

## Out of Scope
[Explicit exclusions that prevent scope creep.]

## Open Questions
[Carry forward any unresolved questions from the grilled plan that downstream steps should keep visible.]
```

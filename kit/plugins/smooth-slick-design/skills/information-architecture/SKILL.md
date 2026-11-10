---
name: information-architecture
description: >
  Defines how the experience flows and behaves: critical user paths, what is shown when, data presentation and conceptual navigation. System and technology agnostic unless the brief names a surface. Use when the user says "plan the information architecture", «planlegg strukturen», "map the flows", «kartlegg flyten», or wants to settle behavior before visual design.
---

# Information Architecture

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

Define how the experience flows and behaves before visual design begins. The output is primarily a description of how things should work: how users move through the product, when things surface, and how data is shown and indicated.

This skill is technology agnostic by default. If the brief specifies a particular surface (TV, mobile, kiosk, in-vehicle, voice-first, etc.), the questions adapt. Do not assume web or URL conventions unless the brief explicitly says so.

## Inputs to Load First

1. **Design brief**: `<work-folder>/<slug>/<slug>-brief.md`. The Usage Context section drives whether this skill stays generic or adapts to a specific surface.
2. **Sketch and the grilled plan**, if present: useful for confirming flows that were already discussed.
3. **A codebase**: Only inspect if the user explicitly says one is in play and asks you to look at it. Otherwise do not scan. You may ask once whether a codebase is in play, but do not run anything against it without explicit instruction.

## Process

### 1. Locate Inputs and Confirm Context
Find `<work-folder>/<slug>/<slug>-brief.md`. If multiple briefs exist, ask which one this IA is for. If none exists, ask the user for the project goals, audience, and usage context, then proceed.

Read the brief's Usage Context section. Treat it as load-bearing. It tells you whether to stay generic or to ask the surface-specific questions in step 5.

### 2. Map Critical Flows
Flows are the spine of this document. Spend the most time here. Interview the user about:
- The 3 to 7 most important things users do here, in priority order
- For each flow: where it starts, what the user does, what they see along the way, how they know they succeeded
- Where flows branch and what governs the branch
- Failure paths and recovery (what happens when something goes wrong, how the user gets unstuck)

Each flow becomes a section in the output document.

### 3. Define Surfacing and Presentation Rules
Surfacing rules govern when things appear and what gets prioritized. Presentation rules govern how data is rendered. Both apply across the product, not page by page. Ask:

**Surfacing**
- What is always visible, vs revealed on intent, vs hidden behind a deliberate action
- What gets prioritized when space is tight
- What signals "new", "active", "unavailable", "loading", "stale", "important", "personalized"
- What conditions cause an element to appear, disappear, or change

**Presentation**
- How lists and collections are ordered by default
- How data freshness is communicated (timestamps, indicators, badges)
- How counts, statuses, and progress are shown
- How empty, loading, error, and partial-data states are presented
- What gets summarized vs shown in full
- How destructive or irreversible actions are signaled

### 4. Define Conceptual Navigation Model
At the conceptual level, not the URL level:
- The major areas of the product and how they relate to each other
- How users move between areas (persistent nav, contextual nav, returning to a previous place)
- What "home" means in this product and when users land there
- How depth works (do users go deep then back, or stay shallow)

Only translate this into URLs, screen IDs, or routes if the user explicitly wants that.

### 5. Adaptive Surface-Specific Questions
Only ask these when the brief's Usage Context indicates the surface. Do not ask all of them on every project.

- **TV or 10-foot UI**: focus order, remote button mapping, focus visibility, text legibility at distance, what triggers shelf or rail changes, deep-link handling from voice or recommendations
- **Mobile or touch**: gesture model, thumb reach, navigation pattern (tabs, drawer, stack), platform conventions (iOS, Android), keyboard avoidance, swipe affordances
- **Desktop**: keyboard shortcuts, hover states, density, multi-pane vs single-pane behavior, window resizing, drag and drop
- **Voice-first**: turn structure, confirmation strategy, error recovery, fallback to visual
- **Kiosk or shared device**: session reset, idle timeout, accessibility under timed conditions, privacy between sessions
- **In-vehicle or glanceable**: glance budget, hands-busy assumptions, audio confirmation
- **Other surface**: ask the user what conventions the surface imposes and capture them

### 6. Write the IA Document
Save to `<work-folder>/<slug>/<slug>-ia.md`. The filename must include the slug so the file is self-identifying when shared.

## Document Template

```markdown
# [Project Name] Information Architecture

## Scope
[One paragraph on what this IA covers and what is out of scope. Reference the brief.]

## Critical Flows
For each of the top 3 to 7 flows, fill in:

### Flow: [Name]
- **Goal**: [What the user is trying to accomplish]
- **Trigger**: [What starts the flow]
- **Path**: [Step by step, including branches and decision points]
- **Success signal**: [How the user knows it worked]
- **Failure and recovery**: [What happens when it goes wrong, how the user gets unstuck]

## Surfacing Rules
[System-wide rules for when things appear, what gets prioritized, and what signals state change. Bulleted or short paragraphs.]

## Data Presentation Rules
[How lists are ordered, how freshness is shown, how empty / loading / error / partial states are presented, what gets summarized vs detailed, how destructive actions are signaled.]

## Navigation Model
[Conceptual map of major areas and how users move between them. No URLs or routes unless the user explicitly asked for them.]

## Hierarchy and Grouping
[How content and features are grouped and prioritized. Reference the audience and top tasks from the brief.]

## Naming Conventions
[Short glossary of UI terminology used consistently across the product.]

## Surface-Specific Notes
[Only present if a specific surface was relevant. Captures focus order for TV, gesture model for touch, keyboard behavior for desktop, voice turn structure, etc.]

## Open Questions
[Anything that could not be resolved here and needs to surface in tokens, tasks, or implementation.]
```

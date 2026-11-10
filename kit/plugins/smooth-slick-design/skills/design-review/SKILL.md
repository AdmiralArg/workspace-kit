---
name: design-review
description: >
  Runs a structured design critique of the deliverables against the brief, information architecture, tokens and task list. Adapts to the deliverable form: Figma frames, other design tools, written specs or screenshots of built UI. Use when the user says "review the design", «gå gjennom designet», "check it against the brief", «sjekk det mot briefen», or wants a prioritized list of what to fix.
---

# Design Review

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

Run a structured critique comparing what was produced against what the upstream artifacts said should be produced. The review is opinionated and prioritized: every finding is graded Must Fix, Should Fix, or Could Improve.

This skill is design-tool agnostic. It works with Figma frames, Paper Design / Penpot / Sketch files, written specs, or built UI screenshots, depending on what each task said it would produce.

## Inputs to Load First

1. **Design brief**: `<work-folder>/<slug>/<slug>-brief.md`. The spec to review against. Pay close attention to Audience, Usage Context, Brand and Visual System, Experience Principles, and Out of Scope.
2. **Information architecture**: `<work-folder>/<slug>/<slug>-ia.md`. Verifies that critical flows, surfacing rules, and presentation rules were respected.
3. **Tokens**: `<work-folder>/<slug>/<slug>-tokens.md`. Verifies that the visual vocabulary was used and not bypassed.
4. **Tasks**: `<work-folder>/<slug>/<slug>-tasks.md`. The checklist of deliverables. Each task has a `Deliverable` field that tells you what to look for: mockup, spec, or both.
5. **Sketch and the grilled plan**, if present: anti-decisions that must NOT have come back in.
6. **The actual deliverables**: Figma frames, Penpot / Paper Design / Sketch screens, written specs, or built UI screenshots. Ask the user where to find them if not obvious.

## Process

### 1. Confirm Scope of Review
Confirm:
- Which slug this is (one project at a time)
- Which deliverables are in scope (everything in `<slug>-tasks.md`, or a specific subset)
- What state the deliverables are in (in progress, ready for handoff, shipped)

If a tasks file exists, walk it task by task. If not, walk the IA flows instead.

### 2. Gather Visuals
Get visual evidence for each deliverable. Method depends on the workflow:
- **Figma**: ask the user for the file URL or use the Figma MCP if available. Pull the relevant frames.
- **Paper Design, Penpot, Sketch**: ask the user for an export (PNG, PDF) or screenshots of the relevant screens.
- **Built UI**: ask the user for screenshots, or use a browser-automation MCP if one is available and the user has a running build.
- **Spec-only deliverables**: read the spec doc; no visual is needed.

Save any screenshots gathered to `<work-folder>/<slug>/screenshots/` with descriptive filenames that indicate the screen and state. Capture what the brief's Usage Context demands; do not enforce a fixed set of viewports on every project.

- TV: capture at the target resolution with focus visible
- Mobile or touch: capture at typical mobile viewport with touch targets visible
- Desktop: capture at the typical viewport
- Multi-surface projects: capture each surface in scope

### 3. Walk the Tasks
For each task in the tasks file:
- Confirm the task's `Done when` criterion is met
- Confirm the deliverable form matches what the task specified (mockup, spec, or both)
- Note any task that was skipped, partially completed, or replaced by something else

### 4. Run the Review Checklist
Evaluate against the categories below. Skip categories that don't apply to the surface or the deliverable form.

Do not fill in every category for the sake of completeness. Follow what actually matters for this deliverable on this surface. A review that reports evenly across all categories is a review that found nothing. Lead with what would stop handoff, and say plainly when a category is fine.

**Visual Hierarchy**: does the eye move correctly, is priority clear at a glance, are headings and key actions emphasized?

**Consistency**: spacing, color, border radius, shadows, and type styles match across screens. Tokens are used and not bypassed.

**Brand and Aesthetic Fidelity**: matches the brief's Brand and Visual System section. If the brief named anti-references, none of those creep in.

**States and Interactions**: every state required by the IA is present (loading, empty, partial, full, error, success, focused, selected, idle, etc.). Transitions match the IA's surfacing rules.

**Surface Fidelity**: the design respects the brief's Usage Context.
- TV or 10-foot: focus is visible and unambiguous, type is legible at distance, safe-area is honored
- Mobile or touch: hit targets meet the size standard, thumb reach is respected, gestures match platform conventions
- Desktop: keyboard focus, hover, and density are appropriate
- Voice-first: visual fallback exists where required
- Kiosk: idle and timeout visuals exist
- Other surface: the surface's explicit conventions are honored

**Information Architecture Fidelity**: every critical flow in the IA is supported, surfacing rules are respected, data presentation rules are respected.

**Accessibility**: contrast meets WCAG AA, focus indicators are visible, motion respects reduced-motion preferences, touch targets are adequate.

**Typography**: font pairing is consistent, scale hierarchy is clear, line lengths are readable, weights are intentional.

**Dark Mode**: if dark mode is in scope, the dark palette is intentional (not inverted), contrast is maintained, accents remain accessible.

**Anti-Decision Check**: nothing rejected in the grilled plan or marked Out of Scope in the brief has crept in.

**Responsive or Multi-Surface Behavior**: only if more than one surface is in scope.

### 5. Prioritize Refinements
Grade every finding:
- **Must Fix**: accessibility violations, broken or missing states, brand violations, anti-decisions that came back, IA flow gaps
- **Should Fix**: inconsistencies, weak hierarchy, surfacing rules not followed, tokens bypassed
- **Could Improve**: polish, micro-interactions, refinements that would make the work better but are not required

### 6. Save the Review
Save to `<work-folder>/<slug>/<slug>-review.md`. The filename must include the slug.

## Review Document Template

```markdown
# [Project Name] Design Review

## Summary
[Two to three sentence overall assessment.]

## Scope Reviewed
- Tasks reviewed: [list or reference to the tasks file]
- Deliverables seen: [Figma frames, screenshots, spec docs, etc.]
- Surface: [from the brief]

## Visuals Captured
| Screen or State | File | Notes |
|-----------------|------|-------|

## Must Fix
- [ ] [Issue]: [Where it appears: screen, file, spec section]: [Specific fix]

## Should Fix
- [ ] [Issue]: [Where it appears]: [Specific fix]

## Could Improve
- [ ] [Issue]: [Suggestion]

## Anti-Decisions and Out-of-Scope Check
[Confirm that nothing rejected in the grilled plan or marked Out of Scope crept in. Flag anything that did.]

## What Works Well
[Highlight 3 to 5 things done well to anchor the feedback constructively.]

## Open Questions
[Anything that could not be resolved by the review and needs the designer or stakeholder to decide.]
```

## Activation Examples

- "Review the design"
- "Critique this against the brief"
- "Check it against the IA"
- "Run a design review"
- "What should I fix"
- "Review the design"
- "Critique this against the brief"
- "Check it against the IA"
- "Run a design review"
- "What should I fix"

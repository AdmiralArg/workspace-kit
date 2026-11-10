---
name: brief-to-tasks
description: >
  Turns a design brief into an ordered, designer-led task list. Each task says what must be decided and shown, with the deliverable form chosen per task. Use when the user says "break this brief into tasks", «bryt briefen ned i oppgaver», "create a task list", «lag en oppgaveliste», "what do I design first", or wants to turn design decisions into concrete work.
---

# Brief to Tasks

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

Convert a design brief into an ordered task checklist that the designer drives. Each task describes what needs to be decided and what needs to be shown. The deliverable form (mockup in a design tool, written spec, or both) is chosen per task to match the project, not forced into a single mold.

## Inputs to Load First

1. **Design brief**: `<work-folder>/<slug>/<slug>-brief.md`. The spine of the task list.
2. **Information architecture**: `<work-folder>/<slug>/<slug>-ia.md`. Tells you which flows and screens to break down.
3. **Tokens**: `<work-folder>/<slug>/<slug>-tokens.md`. Tells you what visual vocabulary already exists vs what still has to be decided.
4. **Sketch and the grilled plan**, if present: anti-decisions and tensions that must NOT become tasks.
5. **A codebase**: Only inspect if the user explicitly says one is in play and asks you to. Otherwise do not scan.

## Process

### 1. Confirm Project Identity
Read the brief. Confirm the slug, the audience, the usage context, and the success criteria. The task list is grounded in these.

### 2. Decompose the Work
Walk the IA's critical flows and identify what needs to be designed for each:
- The screens or surfaces involved
- The states each screen or surface can be in (loading, empty, partial, full, success, error, focused, selected, idle, etc.)
- Cross-cutting interactions that aren't tied to a single screen (transitions, focus rules, surfacing rules, key data-presentation behaviors)
- Edge cases that need an explicit decision

### 3. Decide Deliverable Form Per Task
For each task, decide the deliverable form. The choice depends on the project, not the skill:
- **Mockup**: a screen or component in the user's design tool, with the relevant states
- **Spec**: a written description, used when the behavior is the point and pixels are secondary (a focus rule, a surfacing rule, a data-presentation rule)
- **Both**: a mockup paired with written annotation or rules, common for handoff to engineering

When in doubt, default to whatever lets the next person (reviewer, dev, stakeholder) work with what you produce. Behaviors lean spec, screens lean mockup, anything going to a developer leans both.

### 4. Sequence Strategically
Order tasks by:
1. **Foundation first**: anything later tasks depend on. If tokens or core patterns are still open, those go before screens.
2. **Highest-traffic flows first**: design the screens users actually see most.
3. **Risk-first for uncertain items**: surface the design decisions that scare you early, while there is time to redo them.
4. **Happy path before edge cases**: complete the main flow of a screen before chasing every state.

### 5. Save Output
Save to `<work-folder>/<slug>/<slug>-tasks.md`. The filename must include the slug.

## Task Format

Each task captures enough that the designer can pick it up cold and know what to produce.

```markdown
- [ ] **[Task name]**
  - *Decides*: [what gets resolved or shown]
  - *Inputs*: [which artifacts feed into this: brief sections, IA flows, tokens]
  - *Deliverable*: [mockup | spec | both]
  - *Done when*: [verifiable criterion: the brief, IA, or tokens it must align with]
```

Keep one level of nesting. Group tasks under headings (Foundation, Screens, Behaviors, Edge Cases, Review) but do not nest tasks under each other.

## Task List Structure

```markdown
# [Project Name] Tasks

## Foundation
- [ ] [Foundation task]
  - *Decides*: ...
  - *Inputs*: ...
  - *Deliverable*: ...
  - *Done when*: ...

## Screens
- [ ] [Screen-level task, including all relevant states]
  - ...

## Behaviors
- [ ] [Cross-cutting behavior task: focus rules, surfacing rules, data-presentation rules]
  - ...

## Edge Cases
- [ ] [Edge case task: unusual states, error recovery flows, empty states with no fallback]
  - ...

## Review
- [ ] Run `design-review` against the brief
```

## Rules

- Every task delivers something decidable or shareable, not just investigation
- No meta-tasks ("set up the project", "audit the codebase"). Drop them.
- Reference tokens, brief sections, and IA flows by name where possible
- A task should be completable in one focused session. If it isn't, split it.
- Anti-decisions from the grilled plan must NOT show up as tasks. They were rejected for a reason.
- Open questions from the brief should either become explicit decision-tasks or be resolved before tasks are written. Never silently ignored.

## Activation Examples

- "Break this brief into tasks"
- "Create the task list from the IA"
- "Plan the design work for this project"
- "What do I design first"
- "What's the order of attack"
- "Break this brief into tasks"
- "Create the task list from the IA"
- "Plan the design work for this project"
- "What do I design first"
- "What's the order of attack"

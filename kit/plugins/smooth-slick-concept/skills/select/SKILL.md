---
name: select
description: >
  Weighs solution directions against the problem frame and converges on one recommendation. Use when the user has several options and is torn between them. Also on "select a direction", «velg retning», "which one should we go with", «hvilken skal vi gå for», "help me choose". Last step of concept-flow.
---

# Select

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

Evaluate the concept directions against the problem frame and converge on a single recommendation. This phase has built-in critical challenge: the skill actively pushes back on the user's preference to make sure the choice is defensible.

## Starting Context

Load these artifacts if they exist:
1. `<work-folder>/<slug>/<slug>-concepts.md` - the directions to evaluate
2. `<work-folder>/<slug>/<slug>-problem-frame.md` - the yardstick for evaluation

Both are important. The concepts tell you what to evaluate; the problem frame tells you what to evaluate against. If either is missing, ask the user to provide the relevant context.

## Mode

Convergent with built-in challenge. The skill helps the user make a defensible choice, not just validate their gut feeling. It asks hard questions and waits for answers. When the choice is clear, it takes ownership of writing the recommendation.

## Process

### 1. Ask for the User's Instinct

Before any structured evaluation, ask: "Which direction are you leaning toward, and why?"

This is important. The user's instinct carries information. But it also needs to be tested.

### 2. Test the Favorite

Whatever the user leans toward, challenge it against the problem frame:

- "Does this actually solve the problem as framed, or does it solve a different, easier problem?"
- "What's the weakest part of this direction? Where does it break?"
- "What assumption does this depend on? What if that assumption is wrong?"
- "Who would push back on this choice, and what would they say?"
- "Is this the right scope? Are we doing too much or too little?"

Do not run through these as a checklist. Follow the thread. The point is to find the weak spots, not to disqualify the direction.

### 3. Test the Runners-Up

Briefly revisit the other directions:

- "Is there anything in Direction X that the favorite doesn't have?"
- "Could we combine elements, or does that create a mess?"
- "What would have to be true for Direction Y to be the better choice?"

The goal is to make sure something valuable isn't being left on the table.

### 4. Evaluate Feasibility and Risk

For the leading direction:

- "What's the cheapest way to test whether this works?"
- "What kills this if we're wrong?"
- "What has to go right for this to succeed?"
- "Are there dependencies or prerequisites we need to be honest about?"

### 5. Lock the Recommendation

When the user can defend the choice and its tradeoffs, write the recommendation. Do not ask the user to write it. Synthesize the conversation and present it for confirmation.

The recommendation must include a structured handoff section that the production design flow (design-brief) can pick up directly.

## Output

Save to `<work-folder>/<slug>/<slug>-recommendation.md`.

## Recommendation Template

```markdown
# [Project Name] Concept Recommendation

## Recommended Direction
[Name of the chosen direction and a one-paragraph description of what it is.]

## Why This Direction
[Why this one over the others. What makes it the strongest fit for the problem frame. Two to three paragraphs.]

## What Was Rejected
For each rejected direction:
- **[Direction Name]**: [One to two sentences on why it was not chosen.]

## Key Risks
[The two to four biggest risks with this direction. For each: what the risk is, what would trigger it, and how it might be mitigated.]

## Cheapest Test
[How to validate this direction with minimum effort before committing fully.]

## Open Questions
[Anything that could not be resolved and should stay visible through the production flow.]

---

## Handoff to Production Flow

This section is structured for the design-brief skill to pick up directly.

### Problem Frame
[Verbatim from the problem frame document, or a tightened version confirmed during Select.]

### Chosen Direction
[The recommended direction restated as a solution description: what is being built, for whom, and why.]

### Key Constraints
[Scope boundaries, technical constraints, audience constraints, timeline constraints. Pulled from the full concept flow.]

### Rejected Directions (Summary)
[One line per rejected direction with the reason. Prevents re-litigation in the brief phase.]
```

## When to Stop

Stop when the user can state which direction they're going with and why, can name the biggest risk, and is satisfied that the other directions were considered fairly. The recommendation does not have to be certain. It has to be the best available choice given what is known.

## Handoff

After saving the recommendation, tell the user the concept flow is complete and that the production flow can pick up from here:

> "The concept recommendation is saved. When you're ready to turn this into a full design brief, run design-brief. It will pick up the problem frame, chosen direction, and constraints from this recommendation so you don't have to re-explain anything."

Do not invoke design-brief automatically.

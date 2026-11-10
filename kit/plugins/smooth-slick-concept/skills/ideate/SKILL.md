---
name: ideate
description: >
  Generates several solution directions for a framed problem. Use when the user says "ideate", «myldre ideer», "what could we do", «hva kan vi gjøre», "come up with options", or wants breadth before committing to one approach. Part of the Smooth Slick Concept flow (Diamond 2, diverge).
---

# Ideate

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

Generate multiple solution directions against a framed problem. The goal is breadth, not depth. Three to five rough directions, each distinct enough to be worth comparing. No winner yet.

## Starting Context

Load `<work-folder>/<slug>/<slug>-problem-frame.md` if it exists. The problem frame is the constraint: every direction must plausibly solve the framed problem. If a direction doesn't address the problem statement, it doesn't belong here.

Also check for `<work-folder>/<slug>/<slug>-landscape.md`. The "Parked Ideas" section from Explore may contain early solution thinking worth revisiting.

If no problem frame exists, ask the user to state the problem they're solving, then proceed. The directions will be looser without a frame, but the skill still works.

## Mode

Divergent. Push for variety. The user's first instinct is usually the obvious solution; help them see alternatives. Weird ideas are welcome here. Bad ideas are useful because they reveal constraints.

## Process

### 1. Start With What the User Already Has

Ask: "Do you have a direction in mind already, or are we starting from scratch?"

If they have one, capture it as Direction 1, then push beyond it. If not, generate a few starting provocations.

### 2. Generate Directions

Aim for three to five meaningfully different directions. Not variations on a theme, but distinct approaches. Use provocations to push breadth:

- "What's the obvious solution? Let's capture that first."
- "What's the opposite approach?"
- "What if we solved only part of the problem? Which part?"
- "What would a competitor do? What would someone with no constraints do?"
- "What if we didn't build anything new? Can this be solved with what exists?"
- "What's the scrappy version that could ship in a week?"

For each direction, the user and the skill collaborate to sketch out:
- The core idea in two to three sentences
- How it addresses the problem frame
- What it trades off (what gets better, what gets worse or harder)
- A rough sense of effort or complexity (light, medium, heavy)

### 3. Keep It Rough

Resist the temptation to refine any single direction. If the user starts going deep on one, note the detail and pull back: "Good, I've captured that. Let's keep moving to make sure we have enough directions on the table before we go deep on any of them."

### 4. Include At Least One Surprise

If all directions feel safe or incremental, add a provocative one. Flag it as such: "This one is deliberately left-field, but it might surface something useful." The point is to stretch the thinking, not necessarily to propose something viable.

### 5. Write the Concept Spread

When three to five directions are on the table, write the artifact. Present all directions side by side with enough detail to compare them, but not so much that it feels like any one is the answer.

## Output

Save to `<work-folder>/<slug>/<slug>-concepts.md`.

## Concept Spread Template

```markdown
# [Project Name] Concept Spread

## Problem Being Solved
[One-sentence reference to the problem frame. Link to the full problem frame doc.]

## Directions

### Direction 1: [Short Name]
**Core idea**: [Two to three sentences.]
**How it addresses the problem**: [One sentence tying back to the problem frame.]
**Tradeoffs**: [What gets better, what gets worse or harder.]
**Effort sense**: [Light / medium / heavy, with a one-line reason.]

### Direction 2: [Short Name]
...

### Direction 3: [Short Name]
...

(repeat for each direction, three to five total)

## Comparison

| Direction | Solves core problem? | Effort | Biggest risk |
|-----------|---------------------|--------|-------------|
| [Name]    | [Yes/Partially/No]  | [L/M/H]| [One line]  |
| ...       | ...                 | ...    | ...         |

## Parked Details
[Any deep-dive thinking that came up during a specific direction but was too detailed for this phase. Captured so it's not lost.]
```

## When to Stop

Stop when the user has three to five directions that feel genuinely different from each other. The spread does not have to be exhaustive. It has to be broad enough that the user is choosing between real alternatives, not just variations on the first thing they thought of.

## Handoff

After saving the concept spread, mention that Select is the natural next step: "There are [N] directions on the table. When you're ready to evaluate and pick one, run select." Do not invoke it automatically.

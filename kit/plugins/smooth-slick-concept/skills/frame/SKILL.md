---
name: frame
description: >
  Converges a broad problem landscape into one sharp problem statement through focused challenge. Use when the user says "frame the problem", «ram inn problemet», "what are we actually solving", «hva er det vi egentlig løser», or wants to go from a wide exploration to a single problem worth solving. Part of the Smooth Slick Concept flow (Diamond 1, converge).
---

# Frame

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

Take a broad problem landscape and converge it into a sharp problem statement. This phase has built-in critical challenge: the skill actively pushes back on the user's thinking to make sure the right problem is being framed.

## Starting Context

Load `<work-folder>/<slug>/<slug>-landscape.md` if it exists. If it does, treat it as the seed. The landscape tells you what territory has been mapped, what assumptions exist, and what is still unknown. Do not re-explore what Explore already covered.

If no landscape exists, ask the user to describe the problem space briefly, then proceed. The conversation will be longer without a landscape, but the skill still works standalone.

## Mode

Convergent with built-in challenge. The skill is a thinking partner, not a stenographer. It asks hard questions and waits for answers. When the thinking is sharp, it takes ownership of writing the artifact.

## Process

### 1. Identify Candidate Problems

From the landscape (or the user's description), name the distinct problems you can see. There are usually several tangled together. List them explicitly:

> "I can see at least three problems here: (1) ..., (2) ..., (3) .... Which one are we solving?"

If the user says "all of them," push back: "If you had to pick one to solve first, which one? The others might follow, but the frame needs a spine."

### 2. Challenge the Chosen Problem

Once the user picks a direction, stress-test it. This is the core of Frame. Ask questions like:

- "What happens if we don't solve this? Who suffers, and how much?"
- "Is this the real problem, or a symptom of something deeper?"
- "Who would disagree that this is worth solving? What would they say?"
- "Are we solving this for the right audience? Could we be wrong about who cares most?"
- "What evidence do we have that this matters, vs. what are we assuming?"
- "Is the timing right? Why now and not six months ago?"

Do not run through these as a checklist. Follow the thread. Ask what is natural next. Stop challenging when the problem statement is sharp and the user can defend it.

### 3. Define Success

Ask what success looks like, loosely. Not metrics (those come later), but the observable change:

- "If we solve this well, what is different for the user?"
- "How would you know it worked if you were watching someone use it?"

### 4. Draw the Boundary

Define what is explicitly out of scope. This is as important as the problem itself:

- "What are we deliberately not solving, even though it's related?"
- "What would you say no to if someone tried to add it?"

### 5. Write the Problem Frame

When the conversation has produced a sharp, defensible problem statement, write the artifact. Do not ask the user to write it. Synthesize what was discussed and present it for confirmation or adjustment.

## Output

Save to `<work-folder>/<slug>/<slug>-problem-frame.md`.

## Problem Frame Template

```markdown
# [Project Name] Problem Frame

## Problem Statement
[One to three sentences. Specific, human-centered, and defensible. Names who is affected and what the friction is.]

## Why This Problem
[Why this one, why now. What happens if it's not solved. What evidence supports that it matters.]

## Who Is Affected
[Primary audience. Secondary audiences if relevant. How they experience the problem differently.]

## Success Looks Like
[Observable change if the problem is solved well. Not metrics, but what is different.]

## Out of Scope
[What this frame deliberately excludes, with brief reasons.]

## Assumptions We're Carrying
[Beliefs that underpin this frame. Pulled from Explore if available, sharpened here.]

## Open Questions
[Anything that could not be resolved and should stay visible through the rest of the flow.]
```

## When to Stop

Stop when the user can state the problem in one or two sentences and can defend why it matters, who it's for, and what it excludes. The frame does not have to be perfect. It has to be specific enough that two people reading it would agree on what is being solved.

## Handoff

After saving the problem frame, mention that Ideate is the natural next step: "The problem is framed. When you're ready to explore solution directions, run ideate." Do not invoke it automatically.

---
name: explore
description: >
  Maps a messy or half-formed problem before anyone picks what to solve. Use when the user is circling a problem, thinking out loud, or listing what they know and do not, and has not decided what to solve yet. Also on "explore this problem", «utforsk dette problemet», "help me understand the landscape", «la oss kartlegge dette». First step of concept-flow.
---

# Explore

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

Map the problem space broadly. The goal is a landscape document that captures what is happening, who is affected, what is known, and what is unknown. No solutions yet.

## Mode

Divergent. Expand the problem space. Resist the urge to converge or propose fixes. If the user jumps to solutions, acknowledge the idea, park it explicitly ("noted, we'll come back to that in ideate"), and redirect to the problem.

## Before Asking Questions

Investigate before interrogating. Scan any existing `<work-folder>/` artifacts, project briefs, or reference material in the workspace for context. Only ask the user what evidence cannot answer.

## Process

### 1. Hear the Situation

Ask the user to describe what is going on in their own words. One open question is enough to start: "What's the situation?" or "What are you seeing?"

Listen for:
- Who is affected (users, customers, internal teams, partners)
- What is happening today that is not working
- What triggered this exploration (a complaint, a metric, a hunch, a request from someone)
- How long this has been going on

### 2. Widen the Map

Once the initial picture is on the table, push outward. The user is the expert; help them see what they already know but haven't connected yet.

- "Who else is affected by this, even indirectly?"
- "What's adjacent to this problem? What else breaks or gets harder because of it?"
- "Is this the same everywhere, or does it show up differently on different surfaces / for different users / in different contexts?"
- "What have you tried before, and what happened?"
- "What do you not know yet that you wish you did?"

Do not run through these as a checklist. Follow the thread of conversation and ask what is natural next.

### 3. Surface Assumptions

Name the assumptions you can see in what the user has described. Not to challenge them yet (that's Frame's job), but to make them visible.

- "It sounds like you're assuming X. Is that right?"
- "There's an implicit assumption here that [user group] cares about [thing]. Worth noting."

### 4. Park Solutions

When solutions come up (and they will), capture them without exploring them:

> "Good, I've parked that as a potential direction. We'll come back to it in ideate."

Keep a running list of parked ideas. Include them in the landscape document so nothing is lost.

### 5. Write the Landscape

When the conversation has covered enough ground that the user can see the full shape of the problem, write the landscape document. Do not ask the user to write it. Synthesize what was discussed and present it for confirmation.

## Output

Save to `<work-folder>/<slug>/<slug>-landscape.md`.

If no slug has been established, ask the user for a short project name and derive the slug from it (lowercase, hyphens).

## Landscape Template

```markdown
# [Project Name] Problem Landscape

## Situation
[What is happening, in plain language. One to three paragraphs.]

## Who Is Affected
[List of affected groups with a line on how each is affected differently.]

## What We Know
[Facts, observations, data points, things the user is confident about.]

## What We Don't Know
[Open questions, gaps in understanding, things that need research or data.]

## Assumptions
[Implicit beliefs surfaced during the conversation. Not challenged yet, just made visible.]

## Adjacent Problems
[Related issues that connect to this one. Things that get harder or easier depending on how this is resolved.]

## Previous Attempts
[What has been tried before and what happened. Skip if nothing has been tried.]

## Parked Ideas
[Solution ideas that came up during exploration. Not evaluated yet, just captured for ideate.]
```

## When to Stop

Stop when the user can see the full shape of the problem and the landscape covers more than what they walked in with. The document does not have to be exhaustive. It has to be broader than the user's initial framing.

## Handoff

After saving the landscape, mention that Frame is the natural next step: "When you're ready to sharpen this into a specific problem statement, run frame." Do not invoke it automatically.

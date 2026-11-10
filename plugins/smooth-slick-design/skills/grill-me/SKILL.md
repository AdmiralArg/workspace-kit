---
name: grill-me
description: >
  Interrogates the user about a plan or design to stress-test the thinking and reach shared understanding. Use when the user says "grill me", «gi meg motstand», "challenge my thinking", «utfordre meg», "stress-test this idea", «stresstest ideen min», or wants to pressure-test a design decision.
---

# Grill Me

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

Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree.

## Starting Context

Check whether a concept sketch already exists for this work. If `<work-folder>/<slug>/<slug>-sketch.md` is present, load it and use it as the seed to stress-test. The sketch tells you what direction the user has already chosen, what framings were rejected, and what open questions remain. Sharpen the sketch, do not start from zero.

If no sketch exists, ask the user for the version of the plan they want challenged, then proceed.

## Methodology

Walk methodically through every aspect of the proposal. Resolve dependencies between decisions one by one before moving forward. Do not move to a new branch until the current one is resolved.

## Before Asking Questions

Prioritize investigation over interrogation. Before asking the user a question, check whether it can be answered by:
- The concept sketch, if one exists at `<work-folder>/<slug>/<slug>-sketch.md`
- Scanning the codebase for existing patterns, components, or constraints (only if a codebase is in play)
- Reading design tokens, theme configs, or style files (only if a codebase is in play)
- Reviewing other existing `<work-folder>/` artifacts

Only ask the user what cannot be determined from evidence.

## For Each Question

- Provide a recommended answer to guide the conversation constructively
- Explain the reasoning behind the recommendation
- Wait for the user's response before moving to the next decision

## When to Stop

Stop when all three are true:

- The user can state the direction in their own words without hedging
- Every decision that blocks downstream work is either resolved, or explicitly listed as open with a reason
- The questions that remain can only be answered by reality (a test, a number, a stakeholder), not by more discussion

Do not keep going just because branches remain. A decision tree has no natural bottom. When the remaining branches no longer change what gets designed next, say so and write the artifact.

Watch for fatigue. Short answers, "whatever you think", or the user asking you to decide all mean stop now. Write up what you have and mark the unresolved branches as open. An exhausted user produces worse answers than an open question does.

## Activation Examples

- "Grill me on this landing page idea"
- "Challenge my approach to this dashboard"
- "Help me think through the settings page structure"
- "I want to stress-test this design"
- "Gi meg motstand på denne landingssiden"
- "Utfordre tilnærmingen min til dette dashbordet"
- "Hjelp meg å tenke gjennom strukturen på innstillingssiden"
- "Stresstest dette designet"

## Output

When the session ends, save the resulting plan to `<work-folder>/<slug>/<slug>-grilled-plan.md`. The filename must include the slug so the file is self-identifying when shared.

Use this structure:

```markdown
# [Project Name] Grilled Plan

## Direction
[The chosen direction in one paragraph, sharper than the sketch.]

## Decisions Resolved
- [Decision]: [What was chosen and the short reason]

## Tensions Found
- [Tension]: [How it was resolved, or that it remains open]

## Open Questions
[Anything that could not be resolved here and needs to surface in the brief.]

## Constraints Confirmed
[Constraints the user re-affirmed during the session: tech, brand, time, scope.]

## Anti-Decisions
[Paths that were explicitly rejected, with a one-line reason. Saves rework later.]
```

## Goal

Transform vague ideas into concrete, well-tested plans through disciplined questioning and evidence-based exploration. The session ends when every branch of the decision tree is resolved, the plan is written, and the designer has a clear, defensible direction.

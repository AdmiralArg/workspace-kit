---
name: workspace-lint
description: >
  Read-only health check of the documentation in the work folder: contradictions, undefined terms, stale claims, files missing from a README, references that do not resolve, banned characters. Proposes fixes and writes nothing until approved. Use when the user says "lint the workspace", «kjør en lint», "check the docs", «er dokumentasjonen konsistent», or asks whether anything has gone stale, contradictory or undocumented.
---

# Workspace lint

A read-only health check of the documentation in the work folder. It finds problems and proposes fixes. It writes nothing until the user approves.

## Scope

Read `workspace.yaml` first. It names the work folder (`work_folder`), the banned characters, and the inbox folder. Everywhere below, `<work-folder>` means that folder.

Read in this order:

1. `<work-folder>/context.md` (shared glossary)
2. every `<work-folder>/<project>/context.md`
3. every `<work-folder>/<project>/decisions.md`
4. every `<work-folder>/<project>/README.md`
5. `<work-folder>/log.md`
6. the remaining `.md` files under `<work-folder>/`

Skip binaries, `.workspace-kit/`, and any folder the workspace rules say to leave alone.

## Checks

Run all eleven. Every finding needs a file path and a proposed fix.

1. **Contradictions.** Two documents claiming different things about the same term, behavior or constraint. Check the shared glossary against project context, context against decisions, and each README against what is actually in the folder.
2. **Undefined terms.** Terms used in two or more documents but defined in no `context.md`. These are glossary candidates.
3. **Orphan definitions.** Glossary terms no longer used anywhere. Either stale, or the work moved and the term did not.
4. **Dormant decision logs.** `decisions.md` files holding nothing but the template. Either the project made no hard calls, or they were never written down. Ask which.
5. **README drift.** Files in a project folder missing from its README, and README entries pointing at files that no longer exist.
6. **Stale claims.** Present-tense claims about how something works, in documents older than three months. Limitations, ownership and integration status go stale fastest. Say which ones can be checked against a live source, and how.
7. **Duplicated facts.** The same fact restated in more than one project. These are candidates for one shared page.
8. **Stale open questions.** Open questions in a `context.md` that are much older than the newest document in the same folder. Either answered and never closed, or quietly dropped.
9. **Superseded decisions.** A decision marked accepted that a later decision or document contradicts. Propose marking the old one as superseded.
10. **Unresolvable file references.** Every backticked path that ends in a file extension must resolve, either as a bare file name in the citing document's own folder or as a path from the workspace root. Skip anything containing `...` or starting with `~`.
11. **Banned characters.** Any character listed under `banned_characters` in `workspace.yaml`, anywhere in the workspace's own documents, quotations included. Report file, line and word, and propose the replacement. Skip this check when the list is empty.

Also report log gaps: documents changed after the newest log line that mentions them.

## Output

Group by what the user has to do, not by check number:

- **Contradictions to resolve** (needs their call)
- **Fills** (missing definitions, README lines, log entries: safe to write once approved)
- **Verify against a live source** (one concrete check per item)
- **Candidates for a shared page**
- **Worth mentioning once** (orphans, dormant logs)

One line per finding. No preamble, no severity scores, no closing summary. Drop any heading whose group is empty.

## Rules

- Propose, never write, until the user approves.
- Only flag claims about what exists. Never flag forward-looking or speculative text.
- Do not invent findings to fill a section. An empty lint pass is a valid result, and worth saying plainly.
- Prefer a live check over a documentation fix when the answer lives in a system the session can reach.
- When the pass finishes, add a `lint` line to `<work-folder>/log.md` with the counts, even when nothing was fixed.

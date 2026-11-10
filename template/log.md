# Log

What was actually done in this workspace, oldest first. The format is fixed so a script can read it:

    grep "^## \[" {{work_folder}}/log.md | tail -10

## Format

`## [YYYY-MM-DD] <project> | <type> | <what happened>`

- **project**: a folder name under `{{work_folder}}/`, or `workspace` for anything that applies across projects
- **type**: `doc` (new or changed document), `decision`, `source` (new source material taken in), `test`, `lint`, `work` (work that changed nothing in the workspace, such as an analysis or a clarification, with the conclusion)
- **what happened**: one line, concrete. File names where they help.

## Rules

- One line per event. No paragraphs, no sub-points.
- Old lines are never edited. If something was wrong, add a new line.
- The log does not replace a task tracker. The tracker holds tasks, the log holds what was done and learned.

## Entries

## [{{today}}] workspace | doc | Workspace set up with workspace-kit {{version}}

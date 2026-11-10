## How this workspace works

Settings are in `workspace.yaml`. Active work lives in `{{work_folder}}/`, one subfolder per project. This section is written by workspace-kit {{version}}. Change `workspace.yaml` and run setup again, do not edit the section by hand.

### Language and style

- Answer in {{working_language}}. If the user writes in another language, answer in that language.
- Documents meant for other people are written in {{deliverable_language}}.
{{banned_rule}}{{style_rules}}
### Writing files

Write and change files with your file editing tool, not through shell commands. Text written through a shell skips the checks this workspace runs on new text, and often gets different line endings.

### Before building

**Unclear starts.** When a session opens with something not yet defined (a loose idea, a problem without a frame, no named deliverable, or a new project with no folder under `{{work_folder}}/`), do not start building. Say in one line what is unclear and offer the matching step: `concept-flow` when the problem itself is unclear, `riff` when there is a loose idea to shape, `grill-me` when a direction is chosen but untested. Offer once, run it on yes, drop it if declined. Skip it for clearly scoped tasks and follow-ups.

### Projects

- **Shape.** A project is a folder `{{work_folder}}/<project>/` with `README.md` (what is in the folder), `context.md` (terms, scope, open questions) and `decisions.md` (dated decisions). Start a new one from `.workspace-kit/templates/project/`. Read a project's `context.md` and `decisions.md` before working in it.
- **Terms.** Shared terms live in `{{work_folder}}/context.md`, project terms in the project's `context.md`. Ask when a term is ambiguous. Propose adding a term once it is resolved.
- **Decisions.** When a choice is hard to reverse, would surprise a colleague, or is a real trade-off, propose adding it to the project's `decisions.md` with the date and what was chosen against. Never add one silently.
- **Filing answers.** When a session establishes something durable, propose a home for it in the project folder and list it in the project's `README.md`. A snapshot gets the date in its file name. Do not file speculation or work in progress.
- **File references.** Write a path in backticks, either a bare file name for a file in the same folder or the path from the workspace root. The lint checks that they resolve.
- **Sanity check.** If the user states a fact about how something works today and the documents say otherwise, say so gently. Do not gate plans for the future.

### Inbox

`{{inbox}}/` holds material that is dropped but not sorted. If anything is in it, say so early and offer to take it in: read it, check whether it already exists in the workspace, write an index document where it belongs, move the raw files there, log it, and leave `{{inbox}}/` empty. Never delete without asking.

### Log

Every session that did work adds one line to `{{work_folder}}/log.md` before it ends, in the format that file describes, ending with the name of the agent in square brackets. Pure reading and questions are not logged.

If the workspace is a git repository, then commit. The commit message is the log line itself, copied word for word from `## [` to the agent name, so the history and the log say the same thing. Commit only the files this session changed, by name, never everything at once: other agents may be working in the same folder. Add to the log, never rewrite it. If you are not allowed to commit, say so and leave the changes for the owner to commit.

### Lint

Documentation drifts. Run the `workspace-lint` skill when asked. A reminder shows at session start when the last `lint` line in the log is older than {{lint_every_days}} days. Suggest a pass once if the session touches `{{work_folder}}/`, and drop it if declined.

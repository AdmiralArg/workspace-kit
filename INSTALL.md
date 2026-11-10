# Install guide for an agent

You are setting up workspace-kit in the user's project. Follow the steps in order. The installer is the only thing that writes kit files. Do not create, edit or move them by hand. This guide is the same whichever agent you are.

## Steps

1. **Find the project.** It is the folder the user is working in, unless they named another. Call it PROJECT.

2. **Get the kit onto the machine.** If you are reading this file from a folder on disk, that folder is the kit. Otherwise clone it. Put it outside PROJECT, for example in a temporary folder. Call the folder KIT.

   ```bash
   git clone https://github.com/AdmiralArg/workspace-kit.git
   ```

3. **Find a Python that runs.** Try these in order and use the first that prints version 3.9 or newer. Call it PY.

   ```bash
   python3 --version
   ```

   ```bash
   python --version
   ```

   ```bash
   py --version
   ```

4. **Show the plan.** This writes nothing. Show the user the output.

   ```bash
   PY KIT/setup.py install --workspace PROJECT --dry-run
   ```

5. **Ask once, only if `workspace.yaml` is in the list of files to be created.** Ask in one message, and offer the default for each:
   - Who the work is for. Default: the folder name.
   - Where project folders live. Default: an existing `projects/` or `design/`, else `projects`.
   - Which agents will work in the folder: Claude Code, Codex, OpenCode. Default: all three.
   - The language to answer in, and the language of documents meant for others. Default: English for both.
   - Characters that must never be written, and whether in files, replies or both. Default: none.

   If the user says to use the defaults, go on without those options.

   **Always ask about git, and never answer for the user**, unless the dry run shows the folder is already under git: "Do you want this folder under git, so every piece of work becomes a commit that shows what was done, when, and by which agent?" This question has no default.

6. **Install.** Add only the options the user answered, and `--git` or `--no-git` from their answer about git.

   ```bash
   PY KIT/setup.py install --workspace PROJECT --git --client "NAME" --work-folder NAME --agents claude,codex,opencode --working-language NAME --deliverable-language NAME --ban U+2014 --ban-in files,replies
   ```

   If you leave out both `--git` and `--no-git`, no repository is created and the installer tells you to go and ask.

7. **Check.** Every line must start with `ok` or `note`. If one says `FAIL`, show it to the user and stop.

   ```bash
   PY KIT/setup.py check --workspace PROJECT
   ```

8. **Report.** Tell the user:
   - what was created, and what was left alone and why
   - every line the installer printed that starts with `Note:`
   - that they must start a new session in PROJECT before the rules, skills and hooks take effect
   - if Codex is among the agents: that Codex runs the hooks only after they approve them, by opening `/hooks` in Codex once

## Rules

- Never edit, move or delete the user's existing files to make room. The installer leaves them alone and says which.
- If the installer prints "Stopped, nothing was changed", show the message and stop. Do not work around it.
- The installer makes one commit when it creates a git repository. Do not commit anything else unless the user asks.
- Do not install into the kit folder itself.

## Later

- **After editing `workspace.yaml`:** run step 6 without options, then step 7.
- **Updating:** get the newer kit, then run step 6 without options, then step 7.
- **Removing:**

  ```bash
  PY KIT/setup.py remove --workspace PROJECT
  ```

# Install guide for an agent

You are setting up workspace-kit in the user's project. Follow the steps in order. The installer is the only thing that writes kit files. Do not create, edit or move them by hand.

## Steps

1. **Find the project.** It is the folder the user is working in, unless they named another. Call it PROJECT.

2. **Get the kit onto the machine.** If you are reading this file from a folder on disk, that folder is the kit. Otherwise clone it. Put it outside PROJECT, for example next to it. Call the folder KIT.

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
   - The language to answer in, and the language of documents meant for others. Default: English for both.
   - Characters that must never be written, and whether in files, replies or both. Default: none.

   If the user says to use the defaults, go on without options.

6. **Install.** Add only the options the user answered.

   ```bash
   PY KIT/setup.py install --workspace PROJECT --client "NAME" --work-folder NAME --working-language NAME --deliverable-language NAME --ban U+2014 --ban-in files,replies
   ```

7. **Check.** Every line must start with `ok`. If one says `FAIL`, show it to the user and stop.

   ```bash
   PY KIT/setup.py check --workspace PROJECT
   ```

8. **Report.** Tell the user what was created, what was left alone and why, and that they must start a new session in PROJECT before the rules, skills and hooks take effect.

## Rules

- Never edit, move or delete the user's existing files to make room. The installer leaves them alone and says which.
- If the installer prints "Stopped, nothing was changed", show the message and stop. Do not work around it.
- Do not commit anything unless the user asks.
- Do not install into the kit folder itself.

## Later

- **After editing `workspace.yaml`:** run step 6 without options, then step 7.
- **Updating:** get the newer kit, then run step 6 without options, then step 7.
- **Removing:**

  ```bash
  PY KIT/setup.py remove --workspace PROJECT
  ```

// workspace-kit adapter for OpenCode. Installed by workspace-kit: do not edit, run setup again instead.
//
// OpenCode has no command hooks, so this small plugin hands its tool calls to the
// same checks the other agents use, in .workspace-kit/hooks. There is one
// implementation of every rule, and this file only translates.
//
//   - Before a file is written, edited or patched, the new text is checked for
//     characters that workspace.yaml bans. A hit stops the call and tells the model why.
//   - On the first prompt of a session, the lint reminder is attached to the
//     session's instructions when a documentation lint pass is overdue.
//
// Any failure in here lets the tool call through: the adapter must never be the
// reason a session cannot work.
import { Plugin } from "@opencode/plugin"
import { spawnSync } from "node:child_process"
import { existsSync } from "node:fs"
import { dirname, join, resolve } from "node:path"

const ENV = { ...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" }
let python // undefined: not looked for yet. null: none found.

// On Windows `python3` is often a shortcut to the Store that runs nothing, so each
// candidate is tried before it is used.
function findPython() {
  if (python !== undefined) return python
  python = null
  for (const candidate of ["python3", "python", "py"]) {
    const probe = spawnSync(candidate, ["-c", "import sys"], { env: ENV, windowsHide: true })
    if (!probe.error && probe.status === 0) {
      python = candidate
      break
    }
  }
  return python
}

// The nearest folder at or above `start` that holds the kit's hooks.
function findRoot(start) {
  let dir = resolve(start)
  for (;;) {
    if (existsSync(join(dir, ".workspace-kit", "hooks"))) return dir
    const parent = dirname(dir)
    if (parent === dir) return null
    dir = parent
  }
}

function runHook(root, script, event) {
  const py = findPython()
  if (!py) return { status: 0, stdout: "", stderr: "" }
  const done = spawnSync(py, [join(root, ".workspace-kit", "hooks", script)], {
    input: JSON.stringify(event),
    cwd: root,
    encoding: "utf-8",
    windowsHide: true,
    timeout: 30000,
    env: { ...ENV, WORKSPACE_KIT_ROOT: root },
  })
  return { status: done.status ?? 0, stdout: done.stdout ?? "", stderr: done.stderr ?? "" }
}

// Only the lines a patch adds, so text that is being removed is never checked.
function addedLines(patch) {
  return patch
    .split("\n")
    .filter((line) => line.startsWith("+") && !line.startsWith("+++"))
    .map((line) => line.slice(1))
    .join("\n")
}

// The text a tool is about to put into a file, or null when the tool writes nothing.
function newText(tool, input) {
  if (!input || typeof input !== "object") return null
  if (tool === "write") return typeof input.content === "string" ? input.content : null
  if (tool === "edit") return typeof input.newString === "string" ? input.newString : null
  if (tool === "patch") {
    const patches = Object.values(input).filter((value) => typeof value === "string")
    return patches.length ? patches.map(addedLines).join("\n") : null
  }
  return null
}

export default Plugin.define({
  id: "workspace-kit",
  async setup(ctx) {
    const root = findRoot(ctx.location.directory)
    if (!root) return

    await ctx.tool.hook("execute.before", (event) => {
      let blocked = null
      try {
        const text = newText(event.tool, event.input)
        if (text === null) return
        const result = runHook(root, "banned_characters.py", {
          hook_event_name: "PreToolUse",
          tool_name: "Write",
          tool_input: { content: text },
        })
        if (result.status === 2) blocked = result.stderr.trim() || "Blocked by workspace.yaml."
      } catch {
        return
      }
      if (blocked) throw new Error(blocked)
    })

    const reminded = new Set()
    await ctx.session.hook("prompt", async (event) => {
      try {
        const sessionID = event.sessionID
        if (!sessionID || reminded.has(sessionID)) return
        reminded.add(sessionID)
        const text = runHook(root, "lint_nudge.py", { hook_event_name: "SessionStart", source: "startup" }).stdout.trim()
        if (text) await ctx.session.instructions.entry.put({ sessionID, key: "workspace-kit-lint", value: text })
      } catch {
        // A reminder is never worth failing a prompt for.
      }
    })
  },
})

---
name: design-tokens
description: >
  Establishes the visual foundation (color, spacing, typography, motion, surface-specific values) for use in a design tool. Mockup-focused, production code only on request. Use when the user says "generate design tokens", «lag designtokens», "set up the design system", «sett opp designsystemet», or wants to lock the visual vocabulary before designing screens.
---

# Design Tokens

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

Establish the visual foundation that screens will be designed from: color, spacing, typography, layout values, and motion. The output is for use in a design tool (Figma, Paper Design, Penpot, Sketch, or similar), not for code.

This skill produces mockup-ready tokens by default. Only generate code-ready tokens (CSS variables, Tailwind config, JSON, etc.) when the user explicitly asks for that depth.

## Inputs to Load First

1. **Design brief**: `<work-folder>/<slug>/<slug>-brief.md`. The Brand and Visual System section tells you whether tokens should be derived from an existing brand or invented from scratch. The Usage Context section tells you what surface-specific values matter.
2. **Sketch and the grilled plan**, if present: useful for tensions about visual direction that were already debated.
3. **No codebase scan.** This skill does not generate code by default. If the user explicitly asks for code-ready tokens, ask once whether a codebase exists and what conventions to follow. Do not scan unprompted.

## Process

### 1. Confirm Workflow
Before generating tokens, ask the user two short questions. The answers determine output format and handoffs.

1. **Where are you designing this?**
   - Figma, Paper Design, Penpot, Sketch, paper or whiteboard, somewhere else, or undecided.
   - This decides which MCP or sibling skill to hand off to at the end.

2. **What depth do you need?**
   - **Mockup (default)**: just enough tokens to design screens that feel cohesive. Color, type, spacing, radii, maybe shadows. No motion or state-level tokens unless the user wants them.
   - **Component-ready**: a fuller set suitable for building components that could later be connected to code (Figma Code Connect, design-system handoff). Includes semantic naming, focus, hover, and state values.
   - **Code-ready**: tokens that also produce a developer-consumable spec. Only when the user explicitly asks.

Default to mockup unless the user picks otherwise. Do not over-deliver.

### 2. Use the Brand if One Exists
If the brief's Brand and Visual System section names a brand source (Figma library URL, brand.zip, design-system.zip, brand guideline doc, Claude Design file), tokens should be derived from the brand, not invented:
- Pull color, type, spacing, radii, and motion from the brand source
- Note which values are missing from the brand and need filling (dark mode is the most common gap)
- Do not propose a parallel system

If no brand exists, proceed to interview the user.

### 3. Define Tokens (if no brand)
Walk through the categories below in order. Propose values and explain the reasoning before locking each in. Anchor decisions to the aesthetic direction in the brief, the audience, and the usage context.

### 4. Apply Surface-Specific Adjustments
The brief's Usage Context determines what extra tokens are needed:
- **TV or 10-foot UI**: larger base type sizes, generous spacing, strong focus styles, palette tuned for backlit displays viewed at distance, safe-area insets
- **Mobile or touch**: minimum hit-target sizing reflected in spacing scale, thumb-friendly densities
- **Desktop**: tighter density acceptable, hover plus keyboard focus styles needed
- **Voice-first**: visual fallback only, minimal token set
- **Kiosk**: high-contrast palette for varied lighting, larger type, idle and timeout visuals
- **Glanceable or in-vehicle**: very high contrast, oversized type, minimal palette, motion suppressed

### 5. Output
Save a token specification to `<work-folder>/<slug>/<slug>-tokens.md`. The filename must include the slug. The spec should be readable enough that the user can copy values into their design tool by hand if needed.

Then hand off based on workflow:
- **Figma**: offer to push the tokens as Figma variables. The `figma-generate-library` skill is the right next step.
- **Paper Design, Penpot, Sketch, paper, other**: the markdown spec is the deliverable. The user copies values into their tool.
- **Code-ready (only when asked)**: also output `<slug>-tokens.json` (or the format the user specified) alongside the markdown.

## Token Categories

Use semantic naming. Tokens describe role (background, text, accent, hover) rather than appearance (gray-100, blue-500).

### Color
- Backgrounds: `bg`, `bg-subtle`, `bg-raised`
- Text: `text`, `text-muted`, `text-inverted`
- Borders: `border`, `border-strong`
- Status: `success`, `warning`, `error`, `info`
- Accents: `accent`, `accent-hover`, `accent-subtle`
- Focus (especially TV and keyboard-driven): `focus-ring`, `focus-fill`

Always include light and dark variants. Treat dark mode as a baseline expectation, not a feature.

### Spacing
Base unit follows the aesthetic and the surface:
- Compact (dense, information-rich, desktop-heavy): 4 unit base
- Balanced (most products): 8 unit base
- Spacious (calm, generous, TV at distance): 8 or 12 unit base, larger steps

Provide a scale with named steps (xs, sm, md, lg, xl, 2xl, etc.) rather than raw numbers in screen specs.

### Typography
- Font families: display, body, monospace (only if needed)
- Size ramp with named steps
- Weights: at least light, regular, medium, bold
- Line heights: tight, normal, relaxed
- Letter spacing where relevant
- Adjust the ramp for surface: TV needs larger base sizes; mobile and desktop differ in display-size steps

### Layout
- Border radius: none, sm, md, lg, full
- Shadows or elevation: light and dark variants
- Content widths or container values, only if relevant to the surface

### Motion
Only include if the surface uses motion meaningfully and the user picked component-ready or code-ready depth:
- Durations: fast, normal, slow
- Easing: in, out, in-out, optionally a spring
- Always honor reduced motion: define the reduced-motion fallback for any meaningful animation

### Surface-Specific Tokens
Add only what the surface demands:
- TV: focus glow size, focus animation duration, safe-area inset
- Touch: minimum hit target
- Desktop: hover transition, focus outline
- Kiosk: idle dim level, timeout countdown style

## Dark Mode Rules

- Treat dark mode as a baseline. Do not invert light values.
- Reduce contrast slightly. Pure white on pure black is harsh.
- Adjust elevation visuals for dark contexts (lighter, more diffuse).
- Maintain WCAG AA contrast ratios for all text and background combinations.
- Keep accent colors accessible in both modes.
- If the user is in a tool that supports modes natively (Figma variables with modes, Penpot themes), produce tokens with both modes attached.

## Handoffs

- **Figma users**: hand off to `figma-generate-library` to push the tokens as Figma variables. Mention that as the next step but do not invoke it automatically.
- **Paper Design, Penpot, Sketch, paper, other tool users**: the markdown spec is the deliverable.
- **Code-ready (only when explicitly asked)**: also output the requested code-format file alongside the markdown.

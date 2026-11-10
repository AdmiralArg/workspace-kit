# Gate every rule: how the kit should change

**The kit's architecture holds up. Its upkeep design needs a harder gate.** The best 2025-2026 systems agree on one pattern: capture is cheap, so promotion into always-on instructions must be human-approved, evidence-gated and reversible, and anything that must hold every time belongs in a hook or script, not prose. The only controlled study of context files found they "do not generally improve task success" and raise cost by over 20 percent ([arXiv 2602.11988](https://arxiv.org/abs/2602.11988)). No study tests a self-updating rule loop at all, so every promoted rule is a hypothesis. The planned `/retro` and `/doctor` are the right shape. Four changes matter most: enforce the hard rules as hooks, split lint into a weekly deterministic script and an LLM pass, make Superpowers opt-in per project type, and generate the shared layer from the private one instead of editing both. Research date: 10 November 2026.

## Design review: what holds, what bends

| Decision in README | Verdict | Evidence |
|---|---|---|
| Three layers (personal, method plugin, client workspace) | Holds | Same split in Fulkerson's vault (work skills shared, personal private) ([post](https://aaronfulkerson.com/2026/04/12/karpathys-pattern-for-an-llm-wiki-in-production/)) and Claude Code's own scopes ([docs](https://code.claude.com/docs/en/memory)). |
| Hard rules (no acute e, no em-dash, lead with result) "every project" | Change | Instructions are "context, not enforced configuration" ([docs](https://code.claude.com/docs/en/memory)). A plugin cannot ship CLAUDE.md ([reference](https://code.claude.com/docs/en/plugins-reference)). Character bans need hooks. |
| `workspace.yaml` per project | Holds, add three details | CE and OpenSpec use the same shape, with a committed base, a local override, a template version line and a fail-closed path setting ([CE config](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/configuration.md), [OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/main/docs/customization.md)). |
| Shared layer optional, fixed page shape, index, no links into private | Holds, tighten | One author per layer avoids conflicts ([Exbrain](https://github.com/chaenmasahiro0425/exbrain)). Add generation, provenance and lint (below). |
| Handover is an export of the shared layer | Holds, add owner | The pattern assumes one curator; the maintainer role itself changes hands ([Falconer](https://falconer.com/guides/enterprise-llm-wiki-karpathy/), [gist](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw)). |
| Unclear starts get offered the concept flow | Holds, keep it an offer | Pressure wording over-triggers; Superpowers' "annoying" brainstorming was its most-commented open issue ([#2377](https://github.com/obra/superpowers/issues/2377), [#2530](https://github.com/obra/superpowers/issues/2530)). Skills alone go uninvoked in 56 percent of cases ([Vercel](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)), so keep the rule in both CLAUDE.md and descriptions. |
| Superpowers on by default, routed by CLAUDE.md | Change | One benchmark: +2.4 points at about 1.1x cost on code tasks ([Surge HQ](https://surgehq.ai/blog/benchmarking-coding-agent-harnesses)). No evidence for docs or design work. Routing by prose is advisory, and plugin skills cannot be edited in place. |
| `/retro` fortnightly, `/doctor` monthly, one log-driven nudge | Holds, change content | Queue then human review is the pattern that works ([claude-reflect](https://github.com/BayramAnnakov/claude-reflect)). Deterministic checks pay off weekly ([Tuszynski](https://www.mpt.solutions/karpathys-llm-wiki-works-heres-what-broke-when-i-ran-it-at-real-scale/)). The nudge has no published precedent. |
| Generated `AGENTS.md` | Flip direction | Claude Code reads AGENTS.md only when no CLAUDE.md exists; the documented bridge is `@AGENTS.md` inside CLAUDE.md, and symlinks are risky on Windows ([docs](https://code.claude.com/docs/en/memory)). |

## Self-improvement works when promotion is gated

The strongest implementations differ in size but share three controls.

- **A worth-it gate.** CE's `ce-compound` writes a learning only if it is non-obvious, durable and material, with the test "if the learning document disappeared, would a future engineer... still be likely to repeat the mistake?" ([guide](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/ce-compound.md)). Anthropic's triggers are the same: wrong twice, same correction typed again, same playbook pasted a third time ([docs](https://code.claude.com/docs/en/features-overview)).
- **A cheapest-form ladder.** Test or lint rule, then a standards line, then a learning doc, never a doc first ([guide](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/ce-compound.md)). Hashimoto: each AGENTS.md line traces to an observed bad behavior, or becomes a script ([post](https://mitchellh.com/writing/my-ai-adoption-journey)).
- **Human approval before write, and pruning.** claude-reflect queues corrections and shows an Apply / Edit / Skip table ([README](https://github.com/BayramAnnakov/claude-reflect)). Fully automatic writers show false positives (closures queued as 0.85-confidence rules, [#43](https://github.com/BayramAnnakov/claude-reflect/issues/43)). Cursor removed its Memories UI within about a year ([forum](https://forum.cursor.com/t/are-my-memories-gone/144057)). CE added a worth-audit that deletes learnings recoverable from the code ([worth-audit](https://github.com/EveryInc/compound-engineering-plugin/blob/main/skills/ce-compound/references/refresh/worth-audit.md)).

Superpowers adds a check worth copying: run a no-guidance control first, because "if the control doesn't exhibit the failure, there is nothing to fix" ([writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)). Models improve, so rules rot; Anthropic's `/doctor prompt-audit` exists to find "instructions written for older models" ([docs](https://code.claude.com/docs/en/memory)).

## Enforcement belongs in hooks and scripts

Anthropic: "If something has to happen every time, make it a hook, a deny rule, or a managed setting"; use `command` hooks, since `prompt` and `agent` hooks are not deterministic; keep the set small ("forty" is a smell) ([best practices](https://code.claude.com/docs/en/best-practices)). Skills are a weak carrier for global rules: they trigger probabilistically, descriptions are dropped silently when the listing budget overflows ([issue #64606](https://github.com/anthropics/claude-code/issues/64606)), and only the first 5,000 tokens of a skill survive compaction ([skills docs](https://code.claude.com/docs/en/skills)). A confidentiality rule in CLAUDE.md was ignored in a real case ([#41852](https://github.com/anthropics/claude-code/issues/41852)).

For this kit that means a small hook set: the character ban (PreToolUse on Write/Edit, plus a Stop check, which is capped at eight consecutive blocks), commit and log format, protected folders, and a confidentiality scan. Use `onFailure: "block"` so a crashing hook does not fail silently. Hook matchers are case-sensitive and a misspelled one matches nothing without warning ([debug docs](https://code.claude.com/docs/en/debug-your-config.md)), so `/doctor` must pipe a known-bad sample through each hook. The banned-character design itself is my inference from the documented mechanics; no source describes it.

## The shared layer needs generation, provenance and drift checks

Karpathy's wiki pattern (raw sources, LLM-owned wiki, schema file; operations ingest, query, lint) is what the workspace already mirrors, down to the `## [date] type | title` log header ([gist](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw)). Missing relative to the better implementations:

- **Deterministic lint, no LLM.** Orphans, dead links, stale index, missing frontmatter, a retired-terms list, run weekly. Tuszynski's wiki drifted because dated entries were appended while reference text still described retired systems; his drift linter caught nine stale files after one migration ([post](https://www.mpt.solutions/karpathys-llm-wiki-works-heres-what-broke-when-i-ran-it-at-real-scale/)). hve-core silently skips files with missing dates, so count a missing date as a failure ([docs](https://microsoft.github.io/hve-core/docs/contributing/documentation-maintenance)).
- **Grounding check.** `check_evidence.py` greps every number, date and quote in a page against the raw file it cites ([SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)). The workspace's "paths resolve" lint is half of this.
- **Provenance and expiry in frontmatter.** Human-written, LLM-written or LLM-written and reviewed ([Fulkerson](https://aaronfulkerson.com/2026/04/12/karpathys-pattern-for-an-llm-wiki-in-production/)); a review date; CE's optional `retire_when` ([guide](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/ce-compound.md)).
- **Status instead of silent rewrite.** Accepted, proposed, superseded with `Supersedes` and `Superseded-On`, and a stop-and-flag rule when work conflicts with an accepted decision. An agent kept an obsolete abstraction because an ADR still called it mandatory ([O'Reilly Radar](https://oreilly.com/radar/coding-agents-love-decision-records/)).
- **An Authority section** for outside agents: what they do alone, flag, or leave to the human ([pm-copilot-starter](https://github.com/albertcollell-qurrent/pm-copilot-starter)).
- **Plain folder, not imports.** Imports from outside the working directory trigger an approval dialog as untrusted ([docs](https://code.claude.com/docs/en/memory)), so the shared layer must work when opened as the working directory, with its own AGENTS.md and an `index.md` of one-line descriptions.

## Packaging: simple beats clever

Use one private repo that is both marketplace and plugin, with the plugin at a relative path, so project settings suffice on any machine; an external-source plugin is not fetched from project settings alone ([org docs](https://code.claude.com/docs/en/plugins/org.md)). Omit `version` or bump it every release, never set it and push unbumped ([host docs](https://code.claude.com/docs/en/plugins/host-marketplace.md)). Third-party marketplaces do not auto-update by default, and private HTTPS updates fail quietly without `gh auth setup-git` ([loading](https://code.claude.com/docs/en/plugins/loading.md), [host docs](https://code.claude.com/docs/en/plugins/host-marketplace.md)). Names starting `claude-` or `anthropic-` fail validation ([reference](https://code.claude.com/docs/en/plugins-reference)), which bears on the open repo-name question. Kits that write generated files into projects break most on upgrade (CE stale snapshot, Spec Kit two-step upgrade, BMAD v6 to v7) ([CE upgrading](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/install/upgrading.md), [Spec Kit](https://github.com/github/spec-kit/blob/main/docs/upgrade.md)); keep logic in the plugin and one small versioned config in the workspace.

## What to adopt

| Item | Evidence |
|---|---|
| `/retro` as queue, classify, approval table: lint or hook, rule, skill, glossary term, decision, or discard | claude-reflect table; CE ladder; Anthropic trigger table (above) |
| Promotion gate: second occurrence, non-derivable, durable; log date, origin correction and `retire_when` on each rule | CE gate and worth-audit; Hashimoto; Anthropic "start minimal, add on observed failures" ([post](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) |
| No-guidance control before promoting a correction | Superpowers writing-skills |
| Hooks for the hard rules, with hook scripts in the plugin and per-client banned strings in the workspace | Anthropic best practices; Superpowers "mechanical constraints... automate it" |
| Weekly deterministic lint script plus the existing LLM pass for contradictions | Tuszynski; Exbrain weekly shell-only lint; hve-core |
| Grounding check, retired-terms list, provenance frontmatter, generated index | Astro-Han skill; Fulkerson; Karpathy gist |
| `workspace.yaml` with `config.local.yaml` override, template version line, idempotent `/new-client` that preserves edits | CE `/ce-setup`, OpenSpec config |
| `claude plugin validate --strict` on every edit; one should-trigger and one near-miss case per skill in `claude plugin eval`, with `--model` and `--judge-model` pinned; treat delta near zero as a pruning candidate | [plugin evals docs](https://code.claude.com/docs/en/plugin-evals.md) |
| `/doctor` that wraps `claude doctor`, `/skill-doctor`, `/doctor prompt-audit`, then adds kit checks: hooks fire, plugin and template version drift, dead references, last `/retro` date | Debug and skills docs; hook failure modes above |
| AGENTS.md as canonical, CLAUDE.md as `@AGENTS.md` plus Claude-only notes | Claude Code memory docs |
| Norwegian and English trigger phrases in descriptions, key use case first, negatives early, under about 500 characters | Truncation drops the tail ([anthropics/skills #881](https://github.com/anthropics/skills/issues/881)); 1,536-character cap ([skills docs](https://code.claude.com/docs/en/skills)) |
| `SUPERPOWERS_DISABLE_TELEMETRY` in the template | [Superpowers README](https://github.com/obra/superpowers) |

## What to change

| Change | Evidence |
|---|---|
| Move hard rules from "rules in CLAUDE.md" to hooks; keep tone and response shape as prose | Anthropic best practices; issue #41852 |
| Make Superpowers a per-project choice: on for code projects, off or name-only for docs and design. Keep its `brainstorming` and `writing-plans` from competing with Smooth Slick by giving each skill a "use when" boundary | No docs/design evidence; near-duplicate descriptions can confuse selection (my inference); Surge; issues #2377, #2530 |
| Split lint: weekly deterministic script (SessionStart or pre-commit), LLM pass monthly | Tuszynski; hve-core |
| Trigger `/retro` on event or date, whichever comes first (for example 5 queued corrections or 14 days) rather than date alone | Anthropic "second time" triggers; my inference |
| Generate the shared layer by an explicit promote step from the private layer, with a check that no page depends on private-only files; never edit both | Exbrain single author per layer; Karpathy raw-versus-wiki split |
| Add to the shared layer: "how this is maintained" page, "known gaps and open questions" page, named owner for weekly lint | No handover standard exists (my inference); "Disagreements & open questions" practice ([v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)) |
| Add a deterministic leak check: a per-client denylist kept in the client workspace scans the plugin repo and template before commit. Review auto-memory in `/retro` and promote only generic lessons | No off-the-shelf tool found; auto memory is machine-local and drifts client facts (docs); my inference |
| Keep always-loaded text small: workspace CLAUDE.md well under 200 lines, shorter bootstrap, factual phrasing in hook output | Anthropic docs; hook `additionalContext` capped at 10,000 characters ([hooks reference](https://code.claude.com/docs/en/hooks.md)) |
| Reserve auto memory for personal notes; versioned files hold anything portable across machines | Memory docs: machine-local, unversioned, invisible to subagents |
| Single-repo marketplace, relative plugin path, no `version` pin while iterating; test hooks under Git Bash and PowerShell | Plugin docs; Superpowers 7.0.x Windows fixes ([release notes](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md)) |

## What to avoid

| Avoid | Evidence |
|---|---|
| Automatic writes into CLAUDE.md or rules (instinct stores, auto-promotion, confidence scores) | False positives in claude-reflect issues; small models "silently corrupt" wikis; confidence scores called "false precision" ([v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)); no calibration published |
| LLM-generated overviews, architecture summaries and `/init` output as context | ETH study: overviews not helpful, cost over 20 percent higher; Anthropic: "mostly removing lines" |
| Pressure and emphasis wording (`EXTREMELY_IMPORTANT`, "you MUST", all caps) in the bootstrap | Anthropic: emphasis "mostly makes Claude over-apply"; Superpowers #2377 |
| Hooks for mere preferences; growing the hook set past a handful | Anthropic "forty" warning |
| Global rules carried only by skills | Vercel 56 percent never invoked; listing-budget truncation; compaction drops older skills |
| Heavy methodology scaffolding per project (CE, BMAD, Spec Kit) | CE 8x cost with no clear gain ([Surge](https://surgehq.ai/blog/benchmarking-coding-agent-harnesses)); Spec Kit "overkill" ([Fowler site](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)); Agent OS v3 dropped its own scaffolding ([changelog](https://github.com/buildermethods/agent-os/blob/main/CHANGELOG.md)) |
| Running two methodology plugins that both own brainstorm and plan entrypoints, or a plugin that writes `docs/plans` into a docs workspace | Competing bootstraps and duplicate folders; untested, so treat as a risk (my inference) |
| Symlinked AGENTS.md on Windows; rule generators (rulesync, ruler) unless commands and MCP must sync to other tools | Git checks out symlinks as text files without `core.symlinks`; rulesync majors 18 to 21 in three days (secondary) |
| Time-decay that hides superseded decisions | Superseded decisions still explain current choices; use explicit supersession with git as audit trail (v2 gist comments) |
| Ranking tools by stars (ECC 300k, gstack 141k) | Growth not verified as organic; no evaluation of either |
| Third-party tooling for kit health | Community doctor and eval repos have 0 to 4 stars; official commands displaced them |

## What the research could not establish

- Whether any correction-to-rule loop (reflect, compound, instincts) improves outcomes. Evidence is stars, testimonials and vendor claims; the ETH study tested static files.
- Anything about non-code workspaces. No benchmark covers docs, design or glossary work, including for Superpowers.
- Skill trigger rates in Norwegian, or with Opus-class models and many skills. Spence's numbers are Sonnet 4.5 and Haiku 4.5, and he notes newer tests differ ([post](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals)).
- Any published example of a log-driven nudge hook, or of hook-based banned-character enforcement. Both are the owner's own designs, supported by documented mechanics only.
- How to hand an LLM-maintained knowledge base to a successor, how third-party agents should be permitted to write to it, and whether outside agents read an AGENTS.md placed in a subfolder.
- ETH figures beyond the abstract (the small gains and losses come from secondary summaries; full text not read). Cherny's own statements and Claude Code's "auto dream" were reported second-hand or unofficially.
- Whether project-scoped plugin trust behaves identically in the Claude desktop app, and whether any tool exists for scanning a reusable layer for client-confidential strings.

## Conclusion

The research reframes the kit's job. The 2025 idea was "write everything down so the agent learns"; the 2026 evidence says the scarce resource is the always-loaded instruction budget, and the winning systems spend effort on deletion, deterministic checks and human gates rather than on capture. The kit's differentiator is therefore not a smarter learning loop but a cheap, honest upkeep loop: hooks for what must hold, a lint script that runs without a model, a `/retro` that asks "does the model still make this mistake?", and a shared layer a stranger's agent can use without the author's context. Build those four before the nudge hook and `/new-client`, and test each skill with a handful of natural-phrasing cases in both languages.

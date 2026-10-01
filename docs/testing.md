# Local acceptance checklist

Use fictional information. Keep generated files under ignored `tmp/`, `output/`, or a separate personal directory. The owner wants to test before any public release.

## Automated local checks

Run `python -m unittest discover -s tests -v`. The suite covers:

- Five unique recommendations, deterministic order and sensible preference scenarios.
- All 13 method paths and complete/draft state validation.
- Switching: confirmation, first selection, same-method selection, clearing state, fourth-switch choice, deferred switches, resume count.
- Navigation and transcript-based CLI execution.
- Resuming partial sessions and refusing to overwrite an existing session on start.
- Malformed and oversized input; literal markup in Markdown answers.
- Markdown export for all methods, long answers, Unicode, source inclusion and no extra output formats.
- Packaging from an explicit allowlist; no session or export leakage.
- Distinct layouts for all 13 methods, with every supplied answer mapped exactly once.
- Explicit table rows, missing cells, literal pipes, HTML escaping, and old unstructured notes.
- Blank future logs, partial/complete Harada map structure, and packaged standalone export.
- Numbered method choice, colour only in an interactive terminal (or with FORCE_COLOR), and NO_COLOR respected.
- Table answers asked one question at a time; Harada actions collected area by area.
- Plans saved as `Ganbaru_<method>_plan.md` with `_2`, `_3` for repeats, the full path shown, and no program commands, JSON or "resume" wording in user-facing output.
- Saved plans offered when the program starts again; the Ganbaru analysis rendered when present.

## Human walkthroughs

1. **Guided beginner:** fictional early-career user, limited time, preferences clarity/action. Confirm five options have descriptions, reasons, limitations and working source links. Select SMART and complete the plan.
2. **Discovery:** start with no profile, browse all 13, select Ikigai. Confirm it is identified as an adaptation and does not assume that purpose must generate income.
3. **Workload:** choose overload/action and explore GTD. Confirm it guides capture, clarification, organization, reflection and engagement.
4. **Uncertain process:** choose uncertainty/learning and use Kata. Distinguish current condition, target condition, prediction and experiment.
5. **Organizational goal:** choose organization/team and use Hoshin. Confirm stakeholder discussions are proposed, not falsely recorded as agreements.
6. **Harada:** work through eight supporting areas, a partial or full action map, routines and reflection. Do not fill 64 cells with invented commitments.
7. **Switching:** enter recognizable fictional answers, switch three times, and inspect the JSON. Old worksheet/plan answers must be absent, profile retained. Fourth switch: test pause, discovery, cancel and continue. Resume must retain the count.
8. **Review and edit:** revise a plan after approval and check that it returns to draft. Empty required answers block approval but can be exported as draft.
9. **AI coaching (most important):** install the skill in your AI assistant and plan a fictional goal. Check that it asks one warm question at a time, follows up on vague answers, gives a short analysis in your own words before suggesting five numbered methods, never asks you to type table syntax, shows table rows for you to confirm, writes a Ganbaru analysis you can edit, never shows commands or JSON, and ends with the full path of `Ganbaru_<method>_plan.md`.
9. **Privacy:** inspect JSON and exported files. Interview background should not appear in Markdown unless the user put it into a plan answer. Verify no requests or telemetry originate from the CLI.
10. **Markdown:** generate the 13-format gallery with `python tools/create_examples.py`. Open the plans in an editor. Compare method-specific layouts, check headings, complete long answers, Unicode, table columns, source links and draft/reviewed status. Confirm future logs are blank, Harada's sample map is partial, and Hoshin does not imply stakeholder agreement. Normal export creates only a `.md` file.
11. **Portable prompt:** in a fresh chat without tools, verify that the agent admits it cannot automatically save locally and offers copyable Markdown/session JSON instead.

## Platform review record

Documentation is checked; live product tests below remain for the owner before release.

| Platform | Native discovery | Guided flow | Discovery | Fourth switch | Local Markdown | Notes |
|---|---|---|---|---|---|---|
| Claude Code / Claude UI | Pending | Pending | Pending | Pending | Pending | Separate local and cloud surfaces |
| Codex | Pending | Pending | Pending | Pending | Pending | Test a fresh local task |
| Qoder | Pending | Pending | Pending | Pending | Pending | Record IDE/CLI version |
| Grok Build / Grok chat | Pending | Pending | Pending | Pending | Pending | Prompt fallback in normal chat |
| Cursor | Pending | Pending | Pending | Pending | Pending | |
| GitHub Copilot | Pending | Pending | Pending | Pending | Pending | Record IDE/CLI surface |
| Gemini CLI | Pending | Pending | Pending | Pending | Pending | |
| Windsurf / Devin Desktop | Pending | Pending | Pending | Pending | Pending | Record actual installed name/version |
| Cline | Pending | Pending | Pending | Pending | Pending | |
| OpenCode | Pending | Pending | Pending | Pending | Pending | Record local/hosted model |

## Release gate

Owner approves the behavior and sample Markdown, resolves the priority-platform tests, chooses a GitHub account/repository, and authorizes publishing. Before release, inspect the exact Git diff and package contents for personal data, update version/date, and preserve method attribution. No GitHub action is part of this local build.

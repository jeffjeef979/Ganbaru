# Platform compatibility

Research checked: 2026-10-01. This is a practical selection of 10 major or relevant AI-agent platforms, **not a measured global top-10 market-share ranking**. The first four are the requested priorities. Support below is verified against official documentation, not tested in ten signed-in product sessions. Versions, organizational policies and available execution tools may change behavior.

Copy the **whole** `skills/ganbaru` folder, not just SKILL.md. The resulting path must end in `ganbaru/SKILL.md`, with `scripts` and `references` alongside it. Do not copy personal sessions into an installation directory.

| Platform | Documented integration | Project installation directory | Important boundary |
|---|---|---|---|
| 1. Claude / Claude Code | Native skills in Claude Code; Claude UI supports custom skill ZIPs subject to account/admin availability | `.claude/skills/ganbaru/` | Claude web/Cowork artifacts may be cloud-hosted. Use Code with local files or the CLI for local storage. |
| 2. OpenAI Codex | Native SKILL.md discovery in local repositories and user directories | `.agents/skills/ganbaru/` | Use a local workspace for local output; cloud agent execution is a different storage boundary. |
| 3. Qoder | IDE skill import and native CLI skill folders; QoderWork also documents skills | Use IDE's Upload Skill for the ZIP, or CLI user path `~/.qoder/skills/ganbaru/` | QoderWork uses its own `~/.qoderwork/skills/`; verify which product surface you are using. |
| 4. Grok Build / Grok | Grok Build documents native skill folders and user-invocable slash commands | `.grok/skills/ganbaru/` | This does not establish identical native skill loading in normal Grok chat. Use the single-file prompt there, with local CLI export if execution is unavailable. |
| 5. Cursor | Native agent skills | `.cursor/skills/ganbaru/` | File access and Python execution still depend on the environment and permissions. |
| 6. GitHub Copilot | Agent skills in CLI, app and supported IDE/agent surfaces | `.github/skills/ganbaru/` | Prefer a local interactive surface for interviews. A cloud coding task is not a local-only session. |
| 7. Gemini CLI | Native agent skills and local skill linking | `.gemini/skills/ganbaru/` | Gemini's consumer chat is a separate surface; do not equate CLI support with Gems/native skill import. |
| 8. Windsurf / Devin Desktop (Cascade) | Official Windsurf skills URL now redirects to Devin Desktop documentation | `.devin/skills/ganbaru/`; legacy `.windsurf/skills/ganbaru/` is documented as read | Match the installed product/version; this entry covers the Cascade lineage, not an additional eleventh platform. |
| 9. Cline | Native skills in workspace or global directories | `.cline/skills/ganbaru/` | Confirm skills are enabled and that your agent has local file execution. |
| 10. OpenCode | Native skills with scripts and reference resources | `.opencode/skills/ganbaru/` | A local model configuration can differ from a hosted-model configuration; check provider processing separately. |

## Official documentation

- Claude Code: https://code.claude.com/docs/en/skills
- Claude UI: https://support.claude.com/en/articles/12512180-use-skills-in-claude
- Codex local skill discovery: https://learn.chatgpt.com/docs/build-skills (the former https://developers.openai.com/codex/skills/ redirects here)
- Qoder IDE: https://docs.qoder.com/qoder/skills
- Qoder CLI: https://docs.qoder.com/cli/Skills
- QoderWork: https://docs.qoder.com/qoderwork/skills
- Grok Build: https://docs.x.ai/build/features/skills-plugins-marketplaces
- Grok chat files/features: https://docs.x.ai/grok/faq
- Cursor: https://prod.cursor.com/docs/skills
- Copilot: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- Gemini CLI: https://geminicli.com/docs/cli/using-agent-skills/
- Windsurf/Cascade redirect: https://docs.windsurf.com/windsurf/cascade/skills
- Devin Desktop current page: https://docs.devin.ai/desktop/cascade/skills
- Cline: https://docs.cline.bot/customization/skills
- OpenCode: https://opencode.ai/docs/skills/

## Installation and trial

1. Build the package with `python tools/build.py` from the repository root.
2. For native folder installs, copy `skills/ganbaru` to the appropriate location in the table. For Claude's UI or Qoder's import UI, use `dist/ganbaru.zip` when available in your account.
3. Refresh skills or restart the agent as its documentation directs. In Gemini CLI, `/skills reload` is documented. In Codex, select or mention `$ganbaru`; in Claude Code use `/ganbaru`. Grok Build documents `/<skill-name>` for user-invocable skills. Else ask naturally to use Ganbaru.
4. For plain chat, load `dist/ganbaru-prompt.md`. It includes the interview, state contract and catalogue. This is a prompt fallback, not native tool support. It cannot by itself run Python, guarantee persistence, or save a file on the user's device.
5. Test with a fictional profile. Verify that the agent asks one question at a time, gives five explained recommendations, honors switches, and labels cultural adaptations.
6. For local Markdown creation, the host needs local file-write access. The optional CLI exporter needs only Python 3.10+ with its standard library. Without local file tools, show the Markdown in chat for the user to save. Do not silently use a cloud sandbox when the user requires local-only files.

The ZIP contains only the portable skill, license, dependency list and resources. It does not install dependencies automatically or modify global AI settings. Do not auto-install it into every platform during review.

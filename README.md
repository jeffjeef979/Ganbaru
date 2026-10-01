# Ganbaru 頑張る

Goal-planning coach for AI assistants. One skill, 13 planning methods, and a short analysis of your situation. It turns a vague goal into a plan you can act on.

> **Quick start:** Upload `dist/ganbaru.zip` to Claude (or copy `skills/ganbaru` into your AI tool's skills folder), then say **"Use Ganbaru to help me plan a goal."**

## What does Ganbaru mean?

**頑張る** (*ganbaru*, pronounced *gahn-bah-roo*) is a Japanese verb meaning **to persevere, to keep going, to do your very best**, especially when things are hard. It is written with 頑 (*gan*, firm or stubborn) and 張る (*haru*, to stretch or hold out). You hear it every day in Japan as encouragement: **頑張って!** (*ganbatte!*) means "you can do it, give it your best!"

It's not about being perfect. It's about showing up again tomorrow. That's what a good plan should help you do.

## Why Ganbaru?

Most goals fail between "I want to" and "I did." Ask an AI for help and you usually get the same generic advice: make it SMART, break it into steps, stay motivated. That advice ignores your actual life: how much time you really have, what has tripped you up before, and whether a numbers-driven framework even suits what you care about.

Ganbaru makes your AI assistant act like a coach instead of a template:

- **It asks before it advises.** Eight warm, open questions about your life, strengths, motivation, time and past obstacles, one at a time.
- **It analyses what you say.** It points out themes, tensions (such as a big goal against little free time) and your biggest risk, in your own words.
- **It offers a choice of methods, not one formula.** You get five methods suited to you out of 13 from around the world, from OKRs to Ikigai to the Harada Method, each with its trade-offs explained.
- **It gives each method its own shape.** A WOOP plan looks like a WOOP card. An OKR plan has a scorecard. A Harada plan has an action map.
- **It never makes things up.** No invented deadlines, numbers or commitments. Empty means empty, and drafts are labelled as drafts.

## What's Included

### The skill: `ganbaru`

One Agent Skill (`skills/ganbaru/SKILL.md`) that works with any AI assistant that supports skills. It guides the AI through:

1. **Guided or Discovery mode.** Answer a few questions and get suggestions, or browse all 13 methods yourself.
2. **Interview and analysis.** Eight open questions, then a short read on your situation.
3. **Five numbered suggestions.** Why each fits you, and one limitation to keep in mind.
4. **Method-led planning.** The chosen method's steps, one question at a time, with brief coaching after each answer.
5. **Execution plan.** Goal, milestones, weekly actions, support, obstacles and responses, first step, review rhythm.
6. **Ganbaru analysis.** A short, editable assessment of your plan's fit, strengths and main risk.
7. **Your plan file.** Saved as `Ganbaru_<method>_plan.md` on your computer.

### 13 Methodologies

| Method | What it does |
|---|---|
| SMART Goals | Shapes your goal so it is specific, measurable, achievable, relevant and time-bound. |
| OKRs | One meaningful objective with a few measurable key results, kept separate from the tasks that drive them. |
| Kaizen | Improves something you already do through small changes, keeping what works. |
| Getting Things Done (GTD) | Captures everything on your mind, clarifies next actions, and keeps your lists trustworthy. |
| GROW | A coaching conversation through Goal, Reality, Options and Will (your way forward). |
| Ikigai-informed reflection | Explores what gives your life meaning and joy, then tests a direction with a small experiment. |
| WOOP | Wish, Outcome, Obstacle, Plan: names your main inner obstacle and sets an if-then response. |
| Unity of Knowing and Acting | Closes the gap between what you believe and what you do, through small daily practice. |
| Wu Wei | Reduces forced effort and finds the action that fits your current conditions. |
| Karma Yoga | Focuses on doing meaningful work well, without tying your worth to the result. |
| Harada Method | Links a big goal to self-analysis, eight supporting areas, concrete actions and daily routines. |
| Toyota Improvement Kata | Moves you toward a target step by step through small experiments and learning. |
| Hoshin Kanri | Aligns a long-term direction with this year's objective and concrete actions with owners. |

Ikigai, Unity of Knowing and Acting, Wu Wei and Karma Yoga are Ganbaru's own practical adaptations of philosophical traditions, clearly labelled as such. No method is endorsed by, or affiliated with, its originators.

### Offline mode (no AI needed)

A small Python program (`skills/ganbaru/scripts/ganbaru.py`) runs the same planning flow in a terminal: colour-coded, numbered choices, nothing to install, no internet. AI assistants also use it behind the scenes to rank methods and write the plan file. It asks the questions but does not analyse your answers; that is what the AI version is for.

## Usage Examples

```text
Use Ganbaru to help me plan a goal.
Use Ganbaru in discovery mode. I want to compare the methods first.
I want to get back into running but I keep quitting after two weeks. Can Ganbaru help?
Let's carry on with my Ganbaru plan.
Turn my Ganbaru plan into a PDF.
```

## Installation

Ganbaru is not just a terminal tool. It runs inside the AI apps you already use, on desktop, web or in your code editor. Pick whichever option suits you.

### Option 1: Claude app (desktop or web), recommended

1. Download `dist/ganbaru.zip` from this repository.
2. In Claude, go to **Settings → Capabilities**, make sure code execution is on, then under **Skills** choose **Upload skill** and select the ZIP. (In some versions this is under **Customize → Skills**.)
3. Start a new chat: *"Use Ganbaru to help me plan a goal."*

### Option 2: AI coding tools and agents

Copy the whole `skills/ganbaru` folder (not just `SKILL.md`) into your tool's skills folder, then restart or reload skills.

| Tool | Skills folder |
|---|---|
| Claude Code | `.claude/skills/ganbaru/` |
| OpenAI Codex | `.agents/skills/ganbaru/` |
| Cursor | `.cursor/skills/ganbaru/` |
| GitHub Copilot | `.github/skills/ganbaru/` |
| Gemini CLI | `.gemini/skills/ganbaru/` |
| Cline | `.cline/skills/ganbaru/` |
| OpenCode | `.opencode/skills/ganbaru/` |
| Windsurf / Devin Desktop | `.devin/skills/ganbaru/` |
| Qoder | Upload `dist/ganbaru.zip`, or `~/.qoder/skills/ganbaru/` |
| Grok Build | `.grok/skills/ganbaru/` |

Then ask your assistant to use Ganbaru (in Claude Code you can type `/ganbaru`). Details and official docs for each tool: [docs/platforms.md](docs/platforms.md).

### Option 3: Any AI chat (ChatGPT, Gemini, Grok and others)

If your chat app doesn't support skills, open `dist/ganbaru-prompt.md`, copy everything, and paste it as your first message. The AI will coach you the same way and give you the plan as Markdown to save.

### Option 4: Offline in a terminal

Needs Python 3.10 or later; nothing else to install.

```powershell
# Windows (from the repository folder)
.\start.ps1
```

```sh
# macOS / Linux
python3 skills/ganbaru/scripts/ganbaru.py start
```

Choose a method by its number, press Enter to skip any question, and type `/help` for commands (`/back`, `/switch`, `/pause` and more). Your plan is saved to `Documents/Ganbaru/` and the full path is shown at the end. If you stop part-way, run it again and pick your saved plan.

## Your Privacy

- **Everything is saved on your own computer.** Plans are saved as `Ganbaru_<method>_plan.md` files, in `Documents/Ganbaru/` by default. Progress is kept in a hidden `.ganbaru` folder. Nothing is uploaded anywhere by Ganbaru.
- **Ganbaru does not collect any information.** No accounts, no tracking, no analytics, no servers. The skill never asks for your name, employer, age, financial or medical details, and you can skip any question.
- **Your answers go to the AI you choose.** When you use Ganbaru inside Claude, ChatGPT, Cursor or another assistant, that AI model processes your conversation under that provider's own privacy terms. Ganbaru cannot change that.
- **Want nothing to leave your computer?** Use offline mode (Option 4). It runs entirely on your machine with no AI and no internet.
- Saved files are plain text, not encrypted. If your Documents folder syncs to a cloud service, your plans sync with it.

## Repository Layout

| Path | What it is |
|---|---|
| `skills/ganbaru/` | The skill: instructions, method catalogue, output layouts and helper scripts |
| `dist/ganbaru.zip` | Ready-to-upload skill package |
| `dist/ganbaru-prompt.md` | Single-file version for chat apps without skill support |
| `start.ps1` | Windows launcher for offline mode |
| `docs/` | Platform guide and testing checklist |
| `tests/` | Automated tests (fictional data only) |
| `tools/` | Builds the ZIP and example plans |

## Building and Testing

```sh
python -m unittest discover -s tests -v   # run the test suite
python tools/build.py                      # rebuild dist/ganbaru.zip and the prompt file
python tools/create_examples.py            # generate example plans for all 13 methods in output/
```

Uses Python's standard library only. See [docs/testing.md](docs/testing.md) for the manual checklist.

## License

Open source under the [MIT License](LICENSE): free to use, change and share, including commercially. Method names, trademarks and the source materials they come from belong to their respective owners. Ganbaru's exercises are original adaptations; no official worksheets are included, and no certification or endorsement is implied.

---

Created by **Jeff Zhu**.

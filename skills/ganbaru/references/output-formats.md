# Methodology-specific outputs

The selected methodology determines the main output structure. Do not prepend a generic ten-section plan and append a worksheet. The 13 layout definitions in `output-templates.json` are the source of truth for both Python output and tool-free AI conversations. Read only the selected entry. Map each saved answer to its specified section; never drop details to shorten the output.

The common ending contains the **Ganbaru analysis** (only when the AI coach wrote one and the user approved it), **My next action**, **My review date**, and attribution/context. Plans are saved as `Ganbaru_<method-id>_plan.md`. Execution details belong within each method's structure. Philosophical formats remain original Ganbaru practical adaptations. Harada and Hoshin are Markdown representations, not replicas of official graphic worksheets.

| Method | Output |
|---|---|
| SMART | S/M/A/R/T canvas plus final goal statement and follow-through checklist |
| OKRs | Objective, key-result scorecard, initiatives, ownership and future check-in log |
| Kaizen | Plan/Do/Check/Act table, execution commitments and future improvement log |
| GTD | Capture inbox, project outcome, organization system, next-action checklist and review |
| GROW | Goal, Reality, Options, Will/way-forward sections |
| Ikigai | Meaning, themes, chosen direction, experiment and reflection journal |
| WOOP | Wish, Outcome, Obstacle and Plan card, then supporting commitments |
| Knowing and Acting | Understanding, conduct gap, practice and reflection cycle |
| Wu Wei | Excessive striving, conditions, simplification, appropriate action and reassessment |
| Karma Yoga | Responsibility, agency, committed action and non-attachment reflection |
| Harada | Central goal, self-analysis, eight-area table, area/action map, routines and journal |
| Toyota Kata | Challenge, current/target conditions, obstacle, experiment table and learning log |
| Hoshin Kanri | Strategy alignment table, catchball, deployment matrix and review log |

## Table entry without inference

Users never type table syntax. The offline program asks one question per column, one row at a time (press Enter on the first question to finish a list); Harada actions are collected area by area. In an AI assistant, gather the details conversationally or from prose, show the resulting rows as a table, and save them only after the user confirms.

Internally, the session schema remains version 1 and method answers are strings. Each table row is stored as one line with cells separated by ` | `, a literal pipe stored as `\|` and a backslash as `\\`. This is a storage detail for programs and AI assistants only; never show it to the user or ask them to type it. During output, the renderer turns these lines into a JSON-serializable document model with `columns` and `rows`.

| Method / answer | Row columns, in order |
|---|---|
| OKR `results` | Key result \| Baseline \| Target \| Due date |
| OKR `initiatives` | Initiative \| Related key result \| Owner |
| Harada `eight_areas` | Area number \| Supporting area |
| Harada `actions_64` | Area number \| Action number \| Concrete action |
| Kata `experiment` | Test \| Prediction \| Observation to collect \| Check date |
| Hoshin `deployment` | Initiative \| Owner \| Measure \| Due date \| Dependency |

If a line has the wrong number of columns, preserve it under **Original notes - not assigned to columns**. The program never parses prose. An AI assistant may propose rows from what the user said, but saves them only after the user confirms; never silently truncate a row or fill a cell by assumption. Keep valid rows and unstructured notes when an answer contains both. `Not specified` identifies missing data, not a commitment.

For Harada, use area numbers 1-8 and action numbers 1-8. Check references and duplicates during the conversation. If the map is partial or contains prose notes, label it partial/unverified; the presence of text is not proof of 64 distinct actions. Never invent actions merely to fill the map. A 9x9 graphic can be added later with a PDF renderer.

Future check-in, experiment, improvement and journal logs are explicitly blank templates. Never write predicted results into actual-observation columns or imply an experiment already happened.

## Data handling

All supplied text is escaped when rendered as Markdown: literal HTML is shown as text, embedded images do not load, pipes cannot create new table columns, and newlines are retained. Checklists use one item per input line and retain an explicit user `[x]` marker; otherwise they start unchecked. The original wording remains in session JSON. Source links come from the maintained catalogue.

Export is read-only with respect to the session. Editing a Markdown file does not change saved JSON. Refine through the session, then export again; earlier exports are kept.

## Future PDF boundary

`ganbaru.build_document(state)` validates the session and returns a plain dictionary of sections, tables, checklists, log templates and metadata. `output_renderer.render_markdown(document)` is one renderer for that model. A later deterministic PDF implementation can share it, with graphical mappings for Harada and Hoshin. No PDF dependency or PDF export is added in this version.

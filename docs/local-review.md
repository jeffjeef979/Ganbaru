# Local review results

Checked on 2026-10-01 with Python 3.10 (Linux). Earlier rows were first checked on Windows with Python 3.12.

| Check | Result |
|---|---|
| Automated behavioral suite | 44 tests passed after the Ganbaru usability update (numbered choices, colour, guided table entry, plan naming, AI analysis field) |
| Guided CLI transcript | Completed interview, selected SMART, approved plan, generated only Markdown |
| Discovery CLI transcript | Selected WOOP without interview, edited with back, paused and resumed |
| Switching | Confirmation and clearing verified; fourth-switch pause/discovery/continue tested; count persists |
| All 13 methods | Validated completed synthetic states and generated Markdown with method worksheets and source links |
| Distinct layouts | Each method has its own structure; every answer mapped exactly once, without mutating source JSON |
| Tables and compatibility | Explicit row parsing, missing cells, mixed prose/rows and escaped pipes verified; old version-1 sessions retained |
| Future logs and Harada map | No invented observations; partial/complete map structure and duplicate actions checked |
| Installed ZIP | Extracted package exports a Hoshin matrix using standard-library Python |
| Long answers and Unicode | Complete long answers, accents, Chinese text and emoji preserved in UTF-8 exports |
| Private interview omission | Background marker absent from Markdown |
| Package boundary | ZIP contents match source allowlist; no personal sessions or PDFs |
| Standard skill validator | Frontmatter checked after the rename: kebab-case name, description without angle brackets, under 1024 characters |
| Export dependencies | Export command passes with Python site packages disabled; standard library only |
| Repeated exports | Plans named `Ganbaru_<method>_plan.md`; repeats get `_2`, `_3`, so earlier plans are kept; revised answers return to draft |
| Remote publishing | Not performed |
| Live product compatibility | Documentation checked; signed-in platform walkthroughs pending |

Run the test suite from README.md to repeat local checks. The current sample is a fictional WOOP plan at `output/markdown/ganbaru-demo.md`; its synthetic session is `output/demo.session.json`. These generated files are ignored and excluded from the skill package. Earlier PDF exports, if present, are historical files; the current code does not create PDFs.

The current gallery at `output/methodologies/index.md` contains all 13 fictional Markdown layouts and their local source JSON. Regenerate with `python tools/create_examples.py`. The normalized document model is ready for a later renderer; PDF generation remains intentionally unimplemented.

The CLI checks structure, not the truth or feasibility of free-text answers. A user can type vague text into required fields; the human review and conversational skill should refine it. The matching weights are explicit editorial choices and have not been empirically validated.

The two priority privacy cases remain distinct: offline CLI input never leaves through this application; hosted AI chat input is processed by that platform even when file outputs are local. The skill's instructions disclose this rather than promise impossible offline behavior across hosted services.

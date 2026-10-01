import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ganbaru" / "scripts" / "ganbaru.py"
spec = importlib.util.spec_from_file_location("planner", SCRIPT)
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)
build_spec = importlib.util.spec_from_file_location("build", ROOT / "tools" / "build.py")
builder = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(builder)


def complete(mid="smart"):
    state = gp.new_state()
    gp.switch_method(state, mid)
    state["profile"] = {"experience": "PRIVATE-INTERVIEW-ONLY"}
    state["method_answers"] = {s["key"]: "Fictional practice answer: work on a small writing project each week." for s in gp.BY_ID[mid]["steps"]}
    state["plan"] = {
        "goal": "Publish three fictional portfolio articles by 20 December 2026.",
        "why": "Build confidence explaining technical ideas clearly.",
        "success": "Baseline: no drafts. Target: three reviewed articles by 20 December 2026.",
        "milestones": "Outline by 15 October; first draft by 1 November; second by 20 November; third by 10 December.",
        "actions": "Write Tuesday and Thursday, 19:00-19:45, at my desk. Keep Sunday free.",
        "support": "A fictional peer reviewer and publicly available examples.",
        "obstacles": "If tired after work, outline one paragraph before deciding whether to continue.",
        "first_action": "Choose three topics on 3 October 2026 at 10:00.",
        "review": "First review 11 October 2026; then every Sunday for 15 minutes.",
        "adjustment": "If two writing sessions are missed, reduce the next article's scope.",
    }
    state["reviewed"] = True
    return state


class Recommendations(unittest.TestCase):
    def test_exactly_five_unique_reproducible(self):
        for tags in ([], ["purpose"], ["team", "structure"], list(gp.TAGS)):
            results = gp.recommend(tags)
            self.assertEqual(len(results), 5)
            self.assertEqual(len({r["id"] for r in results}), 5)
            self.assertEqual(results, gp.recommend(tags))
            self.assertTrue(all(r["reason"] for r in results))

    def test_fit_scenarios(self):
        for tags, expected in [(["clarity"], "smart"), (["organization", "team"], "hoshin-kanri"),
                               (["uncertainty", "learning"], "toyota-kata"), (["overload"], "gtd"),
                               (["purpose"], "ikigai"), (["gentle"], "kaizen"),
                               (["structure", "learning", "habits"], "harada")]:
            with self.subTest(tags=tags):
                self.assertEqual(gp.recommend(tags)[0]["id"], expected)

    def test_unknown_tag_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            gp.recommend(["secret-personality-type"])

    def test_no_tags_includes_a_reflective_option(self):
        results = gp.recommend([])
        self.assertEqual(len({r["id"] for r in results}), 5)
        self.assertTrue(any("practical adaptation" in gp.BY_ID[r["id"]]["kind"] for r in results))

    def test_workflow_doc_lists_only_supported_tags(self):
        text = (ROOT / "skills" / "ganbaru" / "references" / "workflow.md").read_text(encoding="utf-8")
        question = next(line for line in text.splitlines() if line.startswith("8. Planning preference"))
        import re
        self.assertEqual(set(re.findall(r"`([a-z-]+)`", question)), set(gp.TAGS))

    def test_catalogue_integrity(self):
        self.assertEqual(len(gp.METHODS), 13)
        for method in gp.METHODS:
            self.assertTrue(method["source"].startswith("https://"))
            keys = [step["key"] for step in method["steps"]]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertFalse(set(method["weights"]) - gp.TAGS.keys())
        self.assertEqual([s["key"] for s in gp.BY_ID["woop"]["steps"]], ["wish", "outcome", "obstacle", "plan"])
        self.assertIn("catchball", [s["key"] for s in gp.BY_ID["hoshin-kanri"]["steps"]])
        self.assertIn("actions_64", [s["key"] for s in gp.BY_ID["harada"]["steps"]])


class StateTransitions(unittest.TestCase):
    def test_selection_and_same_method_do_not_count(self):
        state = gp.new_state()
        gp.switch_method(state, "smart")
        gp.set_answer(state, "method_answers", "specific", "Keep this")
        before = copy.deepcopy(state)
        self.assertEqual(gp.switch_method(state, "smart"), "unchanged")
        self.assertEqual(state, before)
        self.assertEqual(state["switch_count"], 0)

    def test_switch_confirmation_and_reset(self):
        state = complete()
        before = copy.deepcopy(state)
        self.assertEqual(gp.switch_method(state, "woop"), "confirm")
        self.assertEqual(state, before)
        self.assertEqual(gp.switch_method(state, "woop", confirmed=True), "switched")
        self.assertEqual(state["profile"], before["profile"])
        self.assertEqual(state["method_answers"], {})
        self.assertEqual(state["plan"], {})
        self.assertFalse(state["reviewed"])

    def test_fourth_switch_break_and_resume(self):
        state = complete()
        for method in ["woop", "gtd", "grow"]:
            self.assertEqual(gp.switch_method(state, method, confirmed=True), "switched")
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "saved.session.json"
            gp.save_state(state, file)
            state = gp.load_state(file)
        before = copy.deepcopy(state)
        self.assertEqual(gp.switch_method(state, "harada", confirmed=True), "breather")
        self.assertEqual(state, before)
        for choice, result in [("pause", "paused"), ("discovery", "discovery")]:
            self.assertEqual(gp.switch_method(state, "harada", confirmed=True, break_choice=choice), result)
            self.assertEqual(state, before)
        self.assertEqual(gp.switch_method(state, "harada", confirmed=True, break_choice="continue"), "switched")
        self.assertEqual(state["switch_count"], 4)
        self.assertEqual(gp.switch_method(state, "smart", confirmed=True), "breather")

    def test_approval_invalidated_by_edits(self):
        state = complete()
        gp.set_answer(state, "plan", "goal", "A revised goal")
        self.assertFalse(state["reviewed"])

    def test_incomplete_cannot_be_final(self):
        state = complete()
        state["plan"]["first_action"] = ""
        with self.assertRaises(ValueError):
            gp.validate(state)
        state["reviewed"] = False
        self.assertIn("DRAFT", gp.markdown(state))
        self.assertIn("plan.first_action", gp.missing_fields(state))

    def test_wrong_method_answers_rejected(self):
        state = complete()
        state["method_answers"]["wish"] = "An obsolete method's answer"
        with self.assertRaises(ValueError):
            gp.validate(state)

    def test_large_and_control_character_input_rejected(self):
        state = complete()
        for bad in ["X" * 20001, "\x1b[31mInjected", "DEL\x7f", "C1\x9b31m", {"nested": "object"}]:
            with self.subTest(bad_type=type(bad)):
                state["plan"]["goal"] = bad
                with self.assertRaises(ValueError):
                    gp.validate(state)

    def test_plaintext_atomic_roundtrip(self):
        state = complete()
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "test.session.json"
            gp.save_state(state, file)
            self.assertEqual(gp.load_state(file), state)
            gp.switch_method(state, "woop", confirmed=True)
            gp.save_state(state, file)
            self.assertNotIn("Fictional practice answer", file.read_text())
            self.assertEqual(len(list(Path(folder).iterdir())), 1)


class CLISessions(unittest.TestCase):
    def cli(self, args, transcript=""):
        return subprocess.run([sys.executable, str(SCRIPT)] + args, input=transcript,
                              text=True, encoding="utf-8", capture_output=True, timeout=30)

    def test_guided_full_run(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guided.session.json"
            profile = ["Early career", "Two years of study", "Write articles", "Share knowledge", "12 weeks", "Two hours per week", "Procrastination", "clarity,action"]
            transcript = profile + ["smart"] + ["Synthetic worksheet response"] * 5 + ["Synthetic specific commitment"] * 10 + ["approve"]
            result = self.cli(["start", "--mode", "guided", "--file", str(path)], "\n".join(transcript) + "\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("YOUR FIVE SUGGESTED METHODS", result.stdout)
            self.assertIn("YOUR PLAN IS SAVED", result.stdout)
            plan = path.parent / "Ganbaru_smart_plan.md"
            self.assertIn(str(plan), result.stdout)
            self.assertTrue(plan.is_file())
            self.assertTrue(gp.load_state(path)["reviewed"])
            # User-facing text must not show program commands, JSON or a 'resume' instruction.
            for leaked in ("python", ".py", "resume", "{", "Traceback"):
                self.assertNotIn(leaked, result.stdout)
            self.assertNotIn("\x1b[", result.stdout)  # No colour codes when output is not a terminal.

    def test_discovery_pause_resume_and_back(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "discovery.session.json"
            result = self.cli(["start", "--mode", "discovery", "--file", str(path)],
                              "woop\nOriginal wish\n/back\nRevised wish\n/pause\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            state = gp.load_state(path)
            self.assertEqual(state["profile"], {})
            self.assertEqual(state["method_answers"]["wish"], "Revised wish")
            resumed = self.cli(["resume", "--file", str(path)], "Desired outcome\n/pause\n")
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(gp.load_state(path)["method_answers"]["outcome"], "Desired outcome")

    def test_repeated_all_does_not_exhaust_stack(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "all.session.json"
            result = self.cli(["start", "--mode", "discovery", "--file", str(path)],
                              "all\n" * 1100 + "woop\n/pause\n")
            self.assertEqual(result.returncode, 0, result.stderr[-500:])
            self.assertEqual(gp.load_state(path)["method_id"], "woop")

    def test_methods_are_chosen_by_number(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "number.session.json"
            result = self.cli(["start", "--mode", "discovery", "--file", str(path)], "13\n/pause\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(" 13  Hoshin Kanri", result.stdout)
            self.assertEqual(gp.load_state(path)["method_id"], gp.METHODS[12]["id"])
            path2 = Path(folder) / "suggested.session.json"
            result = self.cli(["start", "--mode", "guided", "--file", str(path2)], "\n" * 7 + "8\n2\n/pause\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(gp.load_state(path2)["method_id"], gp.recommend(["team"])[1]["id"])

    def test_table_answers_are_asked_one_question_at_a_time(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "table.session.json"
            transcript = "okr\nObjective\nArticles | published\n0\n3\nDecember\nBad\x1b[31m\nReviews\n0\n3\nDecember\n\n/pause\n"
            result = self.cli(["start", "--mode", "discovery", "--file", str(path)], transcript)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("/rows", result.stdout)
            self.assertNotIn("\\|", result.stdout)
            saved = gp.load_state(path)["method_answers"]["results"]
            self.assertEqual(saved, "Articles \\| published | 0 | 3 | December\nReviews | 0 | 3 | December")
            self.assertIn("| Reviews | 0 | 3 | December |", gp.markdown(gp.load_state(path)))

    def test_harada_actions_are_collected_per_area(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "harada.session.json"
            state = gp.new_state("discovery")
            gp.switch_method(state, "harada")
            state["method_answers"].update(purpose="Goal", self_analysis="Notes",
                                           eight_areas="1 | Fitness\n2 | Writing")
            gp.save_state(state, path)
            result = self.cli(["resume", "--file", str(path)], "Run twice a week\nStretch daily\n\nWrite 200 words\n\n/pause\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(gp.load_state(path)["method_answers"]["actions_64"],
                             "1 | 1 | Run twice a week\n1 | 2 | Stretch daily\n2 | 1 | Write 200 words")

    def test_saved_plans_are_offered_when_starting_again(self):
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, HOME=folder, USERPROFILE=folder)
            home = Path(folder) / ".ganbaru"
            state = complete()
            state["reviewed"] = False
            gp.save_state(state, home / "abc.session.json")
            result = subprocess.run([sys.executable, str(SCRIPT), "start"], input="1\n7\n", env=env,
                                    text=True, encoding="utf-8", capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WELCOME BACK", result.stdout)
            self.assertIn("SMART Goals", result.stdout)
            self.assertIn("Your progress is saved", result.stdout)
            self.assertNotIn("abc.session.json", result.stdout)

    def test_colour_only_when_requested_or_interactive(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "catalogue"], text=True, encoding="utf-8",
                                capture_output=True, timeout=30, env=dict(os.environ, FORCE_COLOR="1", NO_COLOR=""))
        self.assertIn("\x1b[", result.stdout)
        plain = subprocess.run([sys.executable, str(SCRIPT), "catalogue"], text=True, encoding="utf-8",
                               capture_output=True, timeout=30, env=dict(os.environ, NO_COLOR="1"))
        self.assertNotIn("\x1b[", plain.stdout)
        self.assertIn(" 1  SMART Goals", plain.stdout)

    def test_eof_saves_and_existing_file_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "partial.session.json"
            result = self.cli(["start", "--mode", "guided", "--file", str(path)], "Life transition\n")
            self.assertEqual(result.returncode, 0)
            saved = path.read_bytes()
            result = self.cli(["start", "--mode", "guided", "--file", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(path.read_bytes(), saved)

    def test_fourth_switch_cli_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "switch.session.json"
            state = complete()
            state["switch_count"] = 3
            gp.save_state(state, path)
            # Resume skips unanswered interview by using discovery mode.
            state["mode"] = "discovery"
            gp.save_state(state, path)
            result = self.cli(["resume", "--file", str(path)], "switch\nwoop\nyes\npause\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("short breather", result.stdout)
            self.assertEqual(gp.load_state(path)["method_id"], "smart")
            self.assertEqual(gp.load_state(path)["switch_count"], 3)

    def test_eof_during_switch_preserves_session(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "interrupted.session.json"
            state = complete()
            state["mode"] = "discovery"
            gp.save_state(state, path)
            result = self.cli(["resume", "--file", str(path)], "switch\nwoop\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Your progress is saved", result.stdout)
            self.assertEqual(gp.load_state(path), state)


class MarkdownAndPackaging(unittest.TestCase):
    def test_every_method_markdown_and_privacy(self):
        with tempfile.TemporaryDirectory() as folder:
            for method in gp.METHODS:
                with self.subTest(method=method["id"]):
                    state = complete(method["id"])
                    file = gp.export_markdown(state, folder)
                    text = file.read_text(encoding="utf-8")
                    self.assertEqual(file.suffix, ".md")
                    self.assertIn("REVIEWED PLAN", text)
                    self.assertIn("Choose three topics", text)
                    self.assertTrue(text.startswith("# " + gp.TEMPLATES[method["id"]]["title"]))
                    self.assertIn(method["source"], text)
                    self.assertNotIn("## Your execution plan", text)
                    self.assertNotIn("PRIVATE-INTERVIEW-ONLY", text)
            self.assertEqual(len(list(Path(folder).iterdir())), 13)

    def test_long_answers_literal_markup_and_unicode(self):
        state = complete()
        state["plan"]["goal"] = "Café <b>literal</b> & learning — 学习 🎯"
        state["plan"]["milestones"] = ("Long milestone with realistic detail. " * 350) + " END-OF-LONG-ANSWER"
        with tempfile.TemporaryDirectory() as folder:
            file = gp.export_markdown(state, folder)
            text = file.read_text(encoding="utf-8")
            self.assertIn("Café &lt;b&gt;literal&lt;/b&gt; &amp; learning — 学习 🎯", text)
            self.assertIn(state["plan"]["milestones"], text)
            self.assertIn("END-OF-LONG-ANSWER", text)

    def test_repeated_exports_preserve_previous_files(self):
        with tempfile.TemporaryDirectory() as folder:
            state = complete()
            first = gp.export_markdown(state, folder)
            original = first.read_bytes()
            gp.set_answer(state, "plan", "goal", "Revised goal")
            second = gp.export_markdown(state, folder)
            self.assertEqual(first.name, "Ganbaru_smart_plan.md")
            self.assertEqual(second.name, "Ganbaru_smart_plan_2.md")
            self.assertEqual(first.read_bytes(), original)
            self.assertIn("DRAFT - NOT YET APPROVED", second.read_text(encoding="utf-8"))

    def test_analysis_is_rendered_and_old_sessions_still_load(self):
        state = complete()
        state["analysis"] = "Your weekly time budget fits the milestones; the main risk is evening fatigue."
        text = gp.markdown(state)
        self.assertIn("## Ganbaru analysis", text)
        self.assertIn("evening fatigue", text)
        state["analysis"] = "- Fit is good\n- Risk: <b>fatigue</b>\nSummary line"
        text = gp.markdown(state)
        self.assertIn("- Fit is good\n- Risk: &lt;b&gt;fatigue&lt;/b&gt;\n\nSummary line", text)
        self.assertNotIn("## Ganbaru analysis", gp.markdown(complete()))
        old = complete()
        del old["analysis"]
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "old.session.json"
            file.write_text(json.dumps(old), encoding="utf-8")
            self.assertEqual(gp.load_state(file)["analysis"], "")
        switched = complete()
        switched["analysis"] = "Old method notes"
        gp.switch_method(switched, "woop", confirmed=True)
        self.assertEqual(switched["analysis"], "")

    def test_invalid_export_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "not-created"
            with self.assertRaises(ValueError):
                gp.export_markdown(gp.new_state(), destination)
            self.assertFalse(destination.exists())

    def test_export_command_runs_without_site_packages(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder) / "plan.session.json"
            gp.save_state(complete(), session)
            output = Path(folder) / "exports"
            result = subprocess.run([sys.executable, "-S", str(SCRIPT), "export", "--file", str(session), "--out", str(output)],
                                    text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Plan saved:", result.stdout)
            self.assertEqual([p.name for p in output.iterdir()], ["Ganbaru_smart_plan.md"])

    def test_distribution_contains_only_source_allowlist(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, prompt = builder.build(folder)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                expected = {"ganbaru/" + n for n in builder.FILES} | {"ganbaru/LICENSE", "ganbaru/requirements.txt"}
                self.assertEqual(set(names), expected)
                self.assertFalse(any("session" in n or n.endswith(".pdf") for n in names))
            content = prompt.read_text(encoding="utf-8")
            for method in gp.METHODS:
                self.assertIn(method["source"], content)
            self.assertNotIn("PRIVATE-INTERVIEW-ONLY", content)


class MethodLayouts(unittest.TestCase):
    def test_every_answer_is_mapped_once_without_mutation(self):
        for method in gp.METHODS:
            with self.subTest(method=method["id"]):
                state = complete(method["id"])
                markers = []
                for group in ("method_answers", "plan"):
                    for i, key in enumerate(state[group]):
                        marker = f"Unique{group.replace('_', '')}{i}Value"
                        state[group][key] = marker
                        markers.append(marker)
                before = copy.deepcopy(state)
                text = gp.markdown(state)
                for marker in markers:
                    self.assertEqual(text.count(marker), 1, marker)
                self.assertEqual(state, before)
                document = gp.build_document(state)
                self.assertEqual(json.loads(json.dumps(document)), document)
                self.assertEqual(text, gp.renderer.render_markdown(document))

    def test_all_thirteen_distinct_layouts(self):
        expected = {
            "smart": "## S - Specific", "okr": "## Key results",
            "kaizen": "## Plan - Do - Check - Act", "gtd": "## Capture inbox",
            "grow": "## W - Will / way forward", "ikigai": "## What makes life worthwhile",
            "woop": "## P - Plan", "knowing-acting": "## Understanding worth living",
            "wu-wei": "## Read the conditions", "karma-yoga": "## Meaningful responsibility",
            "harada": "## Open Window 64-inspired action map",
            "toyota-kata": "## Current and target conditions", "hoshin-kanri": "## Deployment matrix",
        }
        self.assertEqual(set(gp.TEMPLATES), set(gp.BY_ID))
        for mid, heading in expected.items():
            output = gp.markdown(complete(mid))
            self.assertIn(heading, output)
            self.assertIn("## My next action", output)
            self.assertIn("## My review date", output)

    def test_scorecard_rows_and_unknown_cells(self):
        state = complete("okr")
        state["method_answers"]["results"] = "Published articles | 0 | 3 | 20 December 2026\nPeer reviews | 0 |  |"
        text = gp.markdown(state)
        self.assertIn("| Key result | Baseline | Target | Due date |", text)
        self.assertIn("| Published articles | 0 | 3 | 20 December 2026 |", text)
        self.assertIn("| Peer reviews | 0 | Not specified | Not specified |", text)

    def test_old_prose_and_malformed_rows_are_preserved(self):
        state = complete("okr")
        raw = "Improve quality without a numeric target\nValid | 0 | 3 | Friday\nToo | many | columns | in | this row"
        state["method_answers"]["results"] = raw
        block = next(b for b in gp.build_document(state)["blocks"] if b.get("source") == "method_answers.results")
        self.assertEqual(block["rows"], [["Valid", "0", "3", "Friday"]])
        self.assertEqual(block["unstructured"], [raw.splitlines()[0], raw.splitlines()[2]])
        self.assertIn("Original notes - not assigned to columns", gp.markdown(state))

    def test_table_escaping_and_no_embedded_html_or_images(self):
        state = complete("okr")
        state["method_answers"]["results"] = r"A \| B | 0 | 1 | Friday"
        state["plan"]["goal"] = "![track](https://example.invalid/image)\n<script>alert(1)</script>\n# Fake heading"
        state["method_answers"]["alignment"] = "First line\nSecond | line"
        text = gp.markdown(state)
        self.assertIn(r"| A \| B | 0 | 1 | Friday |", text)
        self.assertNotIn("![track]", text)
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)
        self.assertNotIn("\n# Fake heading", text)
        self.assertIn("First line  \nSecond \\| line", text)
        self.assertEqual(gp.renderer.cell("A | B\nC"), "A \\| B<br>C")

    def test_user_text_cannot_create_setext_headings(self):
        state = complete()
        state["plan"]["goal"] = "Looks like a title\n===\nAnd another\n---"
        text = gp.markdown(state)
        self.assertIn("\\===", text)
        self.assertIn("\\---", text)
        self.assertNotIn("\n===", text)

    def test_harada_template_missing_blocks_raises_clear_error(self):
        method = gp.BY_ID["harada"]
        template = copy.deepcopy(gp.TEMPLATES["harada"])
        template["blocks"] = [b for b in template["blocks"] if b.get("source") != "method_answers.actions_64"]
        with self.assertRaisesRegex(ValueError, "Harada template"):
            gp.renderer.build_document(complete("harada"), method, template)

    def test_blank_logs_do_not_invent_observations(self):
        for mid in ("okr", "kaizen", "toyota-kata", "harada", "hoshin-kanri"):
            logs = [b for b in gp.build_document(complete(mid))["blocks"] if b["type"] == "log"]
            self.assertTrue(logs)
            self.assertTrue(all(b["rows"] == [] for b in logs))
            self.assertIn("Blank template for future observations", gp.markdown(complete(mid)))

    def test_harada_map_completeness_checks(self):
        state = complete("harada")
        self.assertIn("Partial / unverified", gp.markdown(state))
        state["method_answers"]["eight_areas"] = "\n".join(f"{i} | Area {i}" for i in range(1, 9))
        state["method_answers"]["actions_64"] = "\n".join(f"{a} | {i} | Action {a}-{i}" for a in range(1, 9) for i in range(1, 9))
        self.assertIn("Structurally complete - 8/8 named areas and 64/64", gp.markdown(state))
        state["method_answers"]["actions_64"] += "\n1 | 1 | Duplicate action"
        self.assertIn("Partial / unverified", gp.markdown(state))
        self.assertIn("Duplicate action", gp.markdown(state))

    def test_empty_drafts_and_checklist_state(self):
        for method in gp.METHODS:
            state = gp.new_state()
            gp.switch_method(state, method["id"])
            self.assertIn("DRAFT", gp.markdown(state))
            self.assertIn("Not specified", gp.markdown(state))
        state = complete("gtd")
        state["plan"]["actions"] = "- [x] Completed action\n- [ ] Pending action\nAnother action"
        text = gp.markdown(state)
        self.assertIn("- [x] Completed action", text)
        self.assertIn("- [ ] Pending action", text)
        self.assertIn("- [ ] Another action", text)

    def test_cli_multiline_rows_survive_resume_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "okr.session.json"
            state = gp.new_state("discovery")
            gp.switch_method(state, "okr")
            state["method_answers"]["objective"] = "Publish a useful portfolio"
            gp.save_state(state, path)
            transcript = "Articles\n0\n3\nDecember\nReviews\n0\n3\nDecember\n\n/pause\n"
            result = subprocess.run([sys.executable, str(SCRIPT), "resume", "--file", str(path)],
                                    input=transcript, text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = gp.load_state(path)
            self.assertEqual(saved["method_answers"]["results"].count("\n"), 1)
            self.assertIn("| Reviews | 0 | 3 | December |", gp.markdown(saved))

    def test_packaged_exporter_is_self_contained(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            archive, _ = builder.build(folder / "dist")
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(folder / "installed")
            script = folder / "installed/ganbaru/scripts/ganbaru.py"
            session = folder / "test.session.json"
            gp.save_state(complete("hoshin-kanri"), session)
            result = subprocess.run([sys.executable, "-S", str(script), "export", "--file", str(session)],
                                    text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = (folder / "Ganbaru_hoshin-kanri_plan.md").read_text(encoding="utf-8")
            self.assertIn("## Deployment matrix", output)


if __name__ == "__main__":
    unittest.main()

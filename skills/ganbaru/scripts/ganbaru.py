#!/usr/bin/env python3
"""Ganbaru offline mode: guided goal-planning interview, transparent matching, local state and Markdown export.

Inside an AI assistant, SKILL.md makes the assistant the coach and uses this file only as a helper
for ranking, checking and exporting. Run on its own, it is a self-contained offline planner.
"""
from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import textwrap
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parents[1]
METHODS = json.loads((ROOT / "references" / "methodologies.json").read_text(encoding="utf-8"))
BY_ID = {m["id"]: m for m in METHODS}
TEMPLATES = json.loads((ROOT / "references" / "output-templates.json").read_text(encoding="utf-8"))
_renderer_spec = importlib.util.spec_from_file_location("ganbaru_renderer", Path(__file__).with_name("output_renderer.py"))
renderer = importlib.util.module_from_spec(_renderer_spec)
_renderer_spec.loader.exec_module(renderer)
UNSPECIFIED = renderer.UNSPECIFIED

TAGS = {
    "clarity": "clear targets", "purpose": "meaning and direction",
    "action": "starting and following through", "habits": "consistent routines",
    "overload": "too many commitments", "coaching": "guided reflection",
    "uncertainty": "an unclear route", "team": "team alignment",
    "organization": "organizational strategy", "gentle": "manageable effort",
    "reflection": "learning about yourself", "structure": "detailed planning",
    "outcome-stress": "less attachment to results", "learning": "learning through practice",
}
TAG_LIST = list(TAGS)
PROFILE = [
    ("life_stage", "Let's start with you. What's happening in your life at the moment? Any big changes, or people and responsibilities you're looking after?"),
    ("experience", "What are you already good at? Think of work, study, caring for others or hobbies that could help you here."),
    ("desired_change", "If the next year went really well, what would be different for you? It's fine if you're not sure yet."),
    ("motivation", "Why does that matter to you? Is there anything you don't want to sacrifice along the way?"),
    ("timeframe", "When would you like to see progress? Are there any dates you can't move?"),
    ("capacity", "Realistically, how much time and energy can you give this each week? Is there anyone or anything that could help?"),
    ("obstacles", "When you've tried something like this before, what usually got in the way?"),
    ("preference", "What kind of help would be most useful right now? Type up to five numbers from the list, separated by commas."),
]
PLAN = [
    ("goal", "Main goal", "Now let's pull it together. In one sentence, what is the main goal you want to commit to?"),
    ("why", "Why this matters", "Why does this goal matter to you personally?"),
    ("success", "Evidence of success", "How will you know you've succeeded? Where are you starting from, and by when do you want to get there? Words are fine if numbers don't fit."),
    ("milestones", "Milestones", "What are a few checkpoints along the way, and roughly when should you reach each one?"),
    ("actions", "Action rhythm", "What will you actually do each week? Include when, where and how much time you can give it."),
    ("support", "Resources and support", "Who or what could help you: people, tools, money, information? 'Nothing needed' is a fine answer."),
    ("obstacles", "Obstacles and responses", "What's most likely to get in your way, and what will you do when it happens?"),
    ("first_action", "First action", "What's the very first small step you'll take, and when?"),
    ("review", "Review rhythm", "When will you first sit down to check how it's going, and how often after that?"),
    ("adjustment", "Adjustment rule", "What would tell you it's time to change the plan, and what would you change first?"),
]
MAX_TEXT = 20000
MAX_FILE = 2_000_000
COMMANDS = {"/quit", "/pause", "/back", "/switch", "/discover", "/profile", "/help"}
HELP = ("/back  go back to the previous question\n/profile  change your background answers\n"
        "/switch  choose a different method\n/discover  browse all 13 methods\n"
        "/pause  save your progress and stop (/quit does the same)")


# ---------------------------------------------------------------- terminal styling

COLOUR = False
STYLES = {"bold": "1", "dim": "2", "red": "91", "green": "92", "yellow": "93", "blue": "94",
          "magenta": "95", "cyan": "96"}
ACCENTS = ["cyan", "magenta", "yellow", "green", "blue"]


def _windows_ansi():
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(mode.value & 0x0004) or bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:
        return False


def colour_supported():
    """Colour only for an interactive terminal; NO_COLOR is respected and FORCE_COLOR overrides."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
        return False
    return _windows_ansi() if os.name == "nt" else True


def paint(text, *styles):
    if not COLOUR or not styles or not text:
        return text
    return "\x1b[" + ";".join(STYLES[s] for s in styles) + "m" + text + "\x1b[0m"


def width():
    return max(40, min(96, shutil.get_terminal_size((88, 24)).columns - 2))


def wrap(text, indent=""):
    lines = []
    for line in str(text).splitlines() or [""]:
        lines.append(textwrap.fill(line, width(), initial_indent=indent, subsequent_indent=indent,
                                   break_long_words=False, break_on_hyphens=False) if line.strip() else "")
    return "\n".join(lines)


def say(text="", *styles, indent=""):
    print(paint(wrap(text, indent), *styles) if text else "")


def heading(title, subtitle=None):
    print()
    print(paint("=" * min(width(), 60), "dim"))
    print(paint(title.upper(), "bold", "cyan"))
    if subtitle:
        say(subtitle, "dim")
    print(paint("=" * min(width(), 60), "dim"))


# ---------------------------------------------------------------- session state

def has_control(text, allowed="\n\r\t"):
    """True for C0/C1 control characters and DEL, which can manipulate terminals."""
    return any(unicodedata.category(c) == "Cc" and c not in allowed for c in text)


def new_state(mode="guided"):
    return {"schema_version": 1, "mode": mode, "profile": {}, "tags": [],
            "method_id": None, "method_answers": {}, "plan": {}, "analysis": "",
            "switch_count": 0, "reviewed": False}


def parse_tags(value):
    result = list(dict.fromkeys(t.strip().lower() for t in value.split(",") if t.strip()))
    unknown = set(result) - TAGS.keys()
    if unknown:
        raise ValueError("Unknown preference tags: " + ", ".join(sorted(unknown)))
    return result


def parse_tag_choice(value):
    """Accept numbers from the on-screen list, tag names, or a mix, separated by commas or spaces."""
    chosen = []
    for part in value.replace(",", " ").split():
        if part.isdigit() and 1 <= int(part) <= len(TAG_LIST):
            chosen.append(TAG_LIST[int(part) - 1])
        elif part.lower() in TAGS:
            chosen.append(part.lower())
        else:
            raise ValueError(f"'{part}' isn't on the list. Use numbers from 1 to {len(TAG_LIST)}.")
    return list(dict.fromkeys(chosen))


def validate(state):
    expected = set(new_state())
    if isinstance(state, dict) and set(state) == expected - {"analysis"}:
        state["analysis"] = ""  # Sessions saved before the analysis field existed remain valid.
    if not isinstance(state, dict) or set(state) != expected:
        raise ValueError("Session fields must match schema version 1; see references/workflow.md.")
    if type(state["schema_version"]) is not int or state["schema_version"] != 1:
        raise ValueError("Unsupported session schema version.")
    if state["mode"] not in ("guided", "discovery"):
        raise ValueError("Invalid mode.")
    mid = state["method_id"]
    if mid is not None and (not isinstance(mid, str) or mid not in BY_ID):
        raise ValueError("Unknown methodology.")
    if type(state["switch_count"]) is not int or state["switch_count"] < 0:
        raise ValueError("Invalid switch count.")
    if type(state["reviewed"]) is not bool:
        raise ValueError("Reviewed must be boolean.")
    tags = state["tags"]
    if not isinstance(tags, list) or any(not isinstance(t, str) or t not in TAGS for t in tags):
        raise ValueError("Invalid preference tags.")
    if len(tags) != len(set(tags)):
        raise ValueError("Preference tags must be unique.")
    allowed = {
        "profile": {k for k, _ in PROFILE},
        "method_answers": {s["key"] for s in BY_ID[mid]["steps"]} if mid else set(),
        "plan": {k for k, _, _ in PLAN} if mid else set(),
    }
    texts = [state["analysis"]]
    for group, keys in allowed.items():
        values = state[group]
        if not isinstance(values, dict) or set(values) - keys:
            raise ValueError(f"Invalid fields in {group}.")
        texts += list(values.values())
    for value in texts:
        if not isinstance(value, str) or len(value) > MAX_TEXT:
            raise ValueError(f"Answers must be text of at most {MAX_TEXT} characters.")
        if has_control(value):
            raise ValueError("Answers cannot contain terminal control characters.")
    if state["reviewed"] and missing_fields(state):
        raise ValueError("An incomplete plan cannot be marked reviewed.")
    return state


def missing_fields(state):
    mid = state["method_id"]
    if not mid:
        return ["method_id"]
    required = [("method_answers", s["key"]) for s in BY_ID[mid]["steps"]]
    required += [("plan", k) for k, _, _ in PLAN]
    return [f"{group}.{key}" for group, key in required if not state[group].get(key, "").strip()]


def field_title(state, name):
    group, key = name.split(".", 1)
    if group == "method_answers":
        return next(s["title"] for s in BY_ID[state["method_id"]]["steps"] if s["key"] == key)
    return next(title for k, title, _ in PLAN if k == key)


def save_state(state, path):
    validate(state)
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ganbaru-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def load_state(path):
    path = Path(path).expanduser()
    if path.stat().st_size > MAX_FILE:
        raise ValueError("Session exceeds the 2 MB size limit.")
    return validate(json.loads(path.read_text(encoding="utf-8")))


def recommend(tags):
    tags = parse_tags(",".join(tags))
    ranked = []
    for index, method in enumerate(METHODS):
        matches = [t for t in tags if method["weights"].get(t, 0) > 0]
        score = method["base"] + sum(method["weights"].get(t, 0) for t in tags)
        reason = ("Matches your wish for " + ", ".join(TAGS[t] for t in matches) + "."
                  if matches else "A tentative alternative; it doesn't directly match the help you picked.")
        ranked.append({"id": method["id"], "score": score, "reason": reason, "order": index})
    ranked.sort(key=lambda item: (-item["score"], item["order"]))
    top = ranked[:5]
    if not tags:
        # Without preferences, base scores alone would always hide the reflective adaptations.
        # Keep one in the tentative five so the starting set spans different kinds of approach.
        reflective = [r for r in ranked if "practical adaptation" in BY_ID[r["id"]]["kind"]]
        if reflective and not any(r in top for r in reflective):
            top[-1] = dict(reflective[0], reason="A tentative reflective alternative, included so the "
                           "starting options are not only target-setting frameworks.")
    return top


def switch_method(state, method_id, *, confirmed=False, break_choice=None):
    """Return switched/unchanged/confirm/breather/paused/discovery; no mutation on deferral."""
    validate(state)
    if method_id not in BY_ID:
        raise ValueError("Unknown methodology.")
    if state["method_id"] == method_id:
        return "unchanged"
    if state["method_id"] is not None:
        if not confirmed:
            return "confirm"
        if state["switch_count"] >= 3:
            if break_choice is None:
                return "breather"
            if break_choice in ("pause", "discovery"):
                return "paused" if break_choice == "pause" else "discovery"
            if break_choice != "continue":
                raise ValueError("Choose pause, discovery or continue.")
        state["switch_count"] += 1
    state.update(method_id=method_id, method_answers={}, plan={}, analysis="", reviewed=False)
    return "switched"


def set_answer(state, group, key, value):
    candidate = json.loads(json.dumps(state))
    candidate[group][key] = value
    candidate["reviewed"] = False
    validate(candidate)
    state.update(candidate)


def build_document(state):
    """Normalize saved answers into method-specific blocks, reusable by future renderers."""
    validate(state)
    if not state["method_id"]:
        raise ValueError("Choose a methodology before exporting.")
    method = BY_ID[state["method_id"]]
    return renderer.build_document(state, method, TEMPLATES[method["id"]])


def markdown(state):
    return renderer.render_markdown(build_document(state))


def records_spec(method_id, source):
    for block in TEMPLATES[method_id]["blocks"]:
        if block["type"] == "records" and block["source"] == source:
            return block
    return None


def record_columns(method_id, source):
    spec = records_spec(method_id, source)
    return spec["columns"] if spec else None


def encode_row(cells):
    """Internal storage format for table rows; users never type this."""
    return " | ".join(c.replace("\\", "\\\\").replace("|", "\\|") for c in cells)


def plan_filename(method_id):
    return f"Ganbaru_{method_id}_plan"


def export_markdown(state, out):
    """Write Ganbaru_<method>_plan.md, adding _2, _3... rather than overwriting an earlier plan."""
    content = markdown(state)  # Validate before creating output directories or files.
    out = Path(out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    stem = plan_filename(state["method_id"])
    for number in range(1, 10000):
        path = out / (f"{stem}.md" if number == 1 else f"{stem}_{number}.md")
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(content)
            return path
        except FileExistsError:
            continue
    raise OSError("Too many plans with the same name in " + str(out))


def home_dir():
    return Path.home() / ".ganbaru"


def default_plans_dir():
    documents = Path.home() / "Documents"
    return (documents if documents.is_dir() else Path.home()) / "Ganbaru"


def plans_dir_for(session_path):
    session_path = Path(session_path).expanduser().resolve()
    return default_plans_dir() if session_path.parent == home_dir().resolve() else session_path.parent


# ---------------------------------------------------------------- interactive offline mode

class Control(Exception):
    def __init__(self, command):
        self.command = command


def ask(question, *, hint=None, commands=True):
    print()
    say(question, "bold")
    if hint:
        say(hint, "dim")
    value = input(paint("> ", "cyan")).strip()
    if commands and value.startswith("/"):
        if value.lower() in COMMANDS:
            raise Control(value.lower())
        say("I don't recognise that command. Type /help to see the options.", "red")
        return ask(question, hint=hint, commands=commands)
    if len(value) > MAX_TEXT or has_control(value):
        say(f"Please use ordinary text, at most {MAX_TEXT} characters.", "red")
        return ask(question, hint=hint, commands=commands)
    return value


def card(number, method, reason=None, accent="cyan"):
    print()
    print(paint(f" {number:>2}  {method['name']} ", "bold", accent) + paint(f"  {method['kind']}  |  {method['origin']}", "dim"))
    say(method["description"], indent="     ")
    if reason:
        say("Why it may suit you: " + reason, "green", indent="     ")
    say("Keep in mind: " + method["limitation"], "yellow", indent="     ")
    say("Learn more: " + method["source"], "blue", indent="     ")


def show_methods(state, discovery):
    if discovery:
        heading("All 13 methods", "Browsing doesn't change anything you've written.")
        options = [m["id"] for m in METHODS]
        for i, method in enumerate(METHODS, 1):
            card(i, method, accent=ACCENTS[(i - 1) % len(ACCENTS)])
    else:
        heading("Your five suggested methods", "Matched to the help you asked for. A simple guide, not a test.")
        if not state["tags"]:
            say("You didn't pick any preferences, so these are general starting points.", "dim")
        ranked = recommend(state["tags"])
        options = [item["id"] for item in ranked]
        for i, item in enumerate(ranked, 1):
            card(i, BY_ID[item["id"]], item["reason"], ACCENTS[(i - 1) % len(ACCENTS)])
    return options


def choose_method(state, *, discovery=False):
    options = show_methods(state, discovery)
    first_choice = state["method_id"] is None
    while True:
        hint = "Type A to see all 13 methods." + ("" if first_choice else " Press Enter to keep your current method.")
        value = ask("Which method would you like to use? Type its number.", hint=hint)
        low = value.lower()
        if low in ("", "cancel"):
            if first_choice:
                continue
            return False
        if low in ("a", "all"):
            discovery = True  # Re-list in place; never recurse, so repeated 'all' is harmless.
            options = show_methods(state, discovery)
            continue
        if value.isdigit() and 1 <= int(value) <= len(options):
            chosen = options[int(value) - 1]
            break
        if low in BY_ID:
            chosen = low
            break
        say(f"Please type a number from 1 to {len(options)}.", "red")
    result = switch_method(state, chosen)
    if result == "confirm":
        say("Switching keeps your background answers but clears what you've written for the current method. "
            "Plans you've already saved are not touched.", "yellow")
        confirmation = ask(f"Switch to {BY_ID[chosen]['name']}? Type Y to switch, or press Enter to stay.")
        if confirmation.lower() not in ("y", "yes"):
            return False
        result = switch_method(state, chosen, confirmed=True)
    if result == "breather":
        say("You've explored several directions. A short breather may help you choose what fits.", "yellow")
        choices = {"1": "pause", "2": "discovery", "3": "continue"}
        while True:
            decision = ask("What would you like to do?",
                           hint="1  Take a break (your progress is saved)\n2  Compare all methods first\n3  Go ahead with this switch").lower()
            decision = choices.get(decision, decision)
            if decision in choices.values():
                break
            say("Please type 1, 2 or 3.", "red")
        result = switch_method(state, chosen, confirmed=True, break_choice=decision)
        if result == "paused":
            raise Control("/pause")
        if result == "discovery":
            choose_method(state, discovery=True)
    return result == "switched"


def interview(state, path, *, edit=False):
    if not edit:
        heading("About you", "Eight short questions. Every one is optional: press Enter to skip.")
    for key, question in PROFILE:
        current = state["profile"].get(key)
        if current is not None and not edit:
            continue
        hint = None
        if key == "preference":
            print()
            for i, tag in enumerate(TAG_LIST, 1):
                print(paint(f"  {i:>2}", "bold", ACCENTS[(i - 1) % len(ACCENTS)]) + f"  {TAGS[tag].capitalize()}")
        if edit and current:
            hint = f"Current answer: {current}\nPress Enter to keep it."
        while True:
            answer = ask(question, hint=hint)
            if edit and not answer and current is not None:
                break
            if key == "preference":
                try:
                    tags = parse_tag_choice(answer)
                    if len(tags) > 5:
                        raise ValueError("Please choose up to five, so the suggestions stay focused.")
                except ValueError as exc:
                    say(str(exc), "red")
                    continue
                state["tags"] = tags
                answer = ", ".join(TAGS[t] for t in tags)
            set_answer(state, "profile", key, answer)
            save_state(state, path)
            break


def format_rows(raw, columns):
    rows, notes = renderer.records(raw.strip() or UNSPECIFIED, columns)
    lines = []
    for i, row in enumerate(rows, 1):
        parts = [f"{c}: {v}" for c, v in zip(columns, row) if v != UNSPECIFIED]
        lines.append(f"{i}. " + "  |  ".join(parts))
    lines += ["Note: " + n for n in notes]
    return lines


def ask_records(state, spec, current):
    """Collect table rows one question at a time; the user never types separators."""
    columns, asks = spec["columns"], spec["ask"]
    lines = current.splitlines() if current.strip() else []
    if lines:
        say("Here's what you have so far:", "dim")
        for line in format_rows(current, columns):
            say(line, indent="   ")
        options = "Press Enter to keep these, R to start again" + ("." if spec.get("per_area") else ", or A to add more.")
        choice = ask("Would you like to change this list?", hint=options).lower()
        if choice in ("r", "redo"):
            lines = []
        elif choice in ("a", "add") and not spec.get("per_area"):
            pass
        else:
            return current
    if spec.get("per_area"):
        return ask_per_area(state, spec, lines)
    limit = spec.get("max_rows")
    while limit is None or len(lines) < limit:
        number = len(lines) + 1
        print()
        print(paint(f"  {spec['item']} {number}" + (f" of {limit}" if limit else ""), "bold", "magenta"))
        cells, asked = [], False
        for question in asks:
            if question is None:
                cells.append(str(number))
                continue
            hint = "Press Enter to finish this list." if not asked and lines else None
            value = ask(question, hint=hint)
            if not asked and not value:
                return "\n".join(lines)
            asked = True
            cells.append(value)
        lines.append(encode_row(cells))
    return "\n".join(lines)


def ask_per_area(state, spec, lines):
    areas, _ = renderer.records(state["method_answers"].get("eight_areas", "").strip() or UNSPECIFIED,
                                ["Area number", "Supporting area"])
    areas = [a for a in areas if a[1] != UNSPECIFIED]
    if not areas:
        say("You haven't named any supporting areas yet, so there's nothing to fill in here. "
            "Use 'change an answer' at the review to add them, then come back to this step.", "yellow")
        return "\n".join(lines)
    for area_number, area_name in areas:
        print()
        print(paint(f"  Area {area_number}: {area_name}", "bold", "magenta"))
        for action_number in range(1, 9):
            value = ask(f"Action {action_number} of 8 for '{area_name}': what's one concrete thing you could do?",
                        hint="Press Enter to move to the next area." if action_number > 1 else "Press Enter to skip this area.")
            if not value:
                break
            lines.append(encode_row([area_number, str(action_number), value]))
    return "\n".join(lines)


def all_fields(method):
    fields = [("method_answers", s["key"], s["title"], s["prompt"]) for s in method["steps"]]
    fields += [("plan", k, title, question) for k, title, question in PLAN]
    return fields


def show_review(state):
    method = BY_ID[state["method_id"]]
    heading(f"Your {method['name']} plan", "Approved" if state["reviewed"] else "Draft: not approved yet")
    for i, (group, key, title, _) in enumerate(all_fields(method)):
        raw = state[group].get(key, "")
        print()
        print(paint(title, "bold", ACCENTS[i % len(ACCENTS)]))
        columns = record_columns(method["id"], f"{group}.{key}")
        if not raw.strip():
            say("Not answered yet", "dim", indent="   ")
        elif columns:
            for line in format_rows(raw, columns):
                say(line, indent="   ")
        else:
            say(raw, indent="   ")


REVIEW_MENU = [("approve", "Approve and save my plan"), ("edit", "Change an answer"),
               ("export-draft", "Save it as a draft for now"), ("switch", "Try a different method"),
               ("discover", "Browse all 13 methods"), ("profile", "Update my background answers"),
               ("pause", "Pause and come back later")]


def finish(state, path):
    plan = export_markdown(state, plans_dir_for(path))
    print()
    print(paint("=" * min(width(), 60), "green"))
    print(paint("YOUR PLAN IS SAVED" if state["reviewed"] else "YOUR DRAFT IS SAVED", "bold", "green"))
    print(paint("=" * min(width(), 60), "green"))
    say("File:", "dim")
    say(str(plan), "bold")
    say("It's a Markdown (.md) file. Open it in any Markdown viewer, or in a text editor such as Notepad.", "dim")
    print()
    say("Your first step:  " + (state["plan"].get("first_action") or "Not specified"))
    say("Your review date: " + (state["plan"].get("review") or "Not specified"))
    print()
    say("To change this plan later, run Ganbaru again and pick it from your saved plans.", "dim")


def paused(path):
    print()
    say("Your progress is saved.", "green")
    if Path(path).resolve().parent == home_dir().resolve():
        say("Run Ganbaru again any time and pick this plan to carry on where you left off.", "dim")
    else:
        say(f"Progress file: {path}", "dim")


def run_session(state, path):
    heading("Ganbaru  |  turn a goal into a plan you can act on")
    say("You're using Ganbaru's offline mode. It asks the questions and builds your plan, but it doesn't "
        "analyse your answers. For personal coaching and analysis, use Ganbaru inside your AI assistant.", "yellow")
    print()
    say("Privacy: nothing leaves this computer. Your answers are saved as plain text on this computer only.", "dim")
    say("Press Enter to skip any question. Type /help at any time to see the commands.", "dim")
    save_state(state, path)
    history = []
    force = None
    while True:
        try:
            if state["mode"] == "guided" and len(state["profile"]) < len(PROFILE):
                interview(state, path)
            if not state["method_id"]:
                choose_method(state, discovery=state["mode"] == "discovery")
                save_state(state, path)
                if not state["method_id"]:
                    continue
            method = BY_ID[state["method_id"]]
            fields = all_fields(method)
            todo = force or next((f for f in fields if f[1] not in state[f[0]]), None)
            force = None
            if todo:
                group, key, title, question = todo
                force = todo
                position = fields.index(todo) + 1
                print()
                print(paint(f"{method['name']}  |  step {position} of {len(fields)}  |  {title}", "bold", "magenta"))
                spec = records_spec(method["id"], f"{group}.{key}")
                current = state[group].get(key)
                if spec:
                    say(question)
                    answer = ask_records(state, spec, current or "")
                else:
                    hint = f"Current answer: {current}\nPress Enter to keep it." if current else None
                    answer = ask(question, hint=hint)
                    if not answer and current:
                        answer = current
                set_answer(state, group, key, answer)
                force = None
                history.append(todo)
                save_state(state, path)
                continue
            show_review(state)
            missing = missing_fields(state)
            if missing:
                print()
                say("Still empty: " + ", ".join(field_title(state, m) for m in missing), "yellow")
            menu = "\n".join(f"{i}  {label}" for i, (_, label) in enumerate(REVIEW_MENU, 1))
            value = ask("What would you like to do next? Type a number.", hint=menu).lower()
            if value.isdigit() and 1 <= int(value) <= len(REVIEW_MENU):
                value = REVIEW_MENU[int(value) - 1][0]
            if value == "edit":
                listing = "\n".join(f"{i}  {title}" for i, (_, _, title, _) in enumerate(fields, 1))
                choice = ask("Which answer would you like to change? Type its number.", hint=listing)
                if choice.isdigit() and 1 <= int(choice) <= len(fields):
                    force = fields[int(choice) - 1]
                else:
                    say("That number isn't on the list.", "red")
            elif value in {"switch", "discover", "profile", "pause"}:
                raise Control("/" + value)
            elif value in {"approve", "export-draft"}:
                if value == "approve" and missing:
                    say("A few answers are still empty. Fill them in (option 2), or save a draft (option 3).", "yellow")
                    continue
                state["reviewed"] = value == "approve"
                save_state(state, path)
                finish(state, path)
                return
            else:
                say("Please type a number from the list.", "red")
        except Control as navigation:
            command = navigation.command
            if command in {"/quit", "/pause"}:
                save_state(state, path)
                paused(path)
                return
            if command == "/help":
                print()
                say(HELP, "dim")
            elif command == "/back":
                if history:
                    force = history.pop()
                else:
                    say("There's no earlier answer to go back to yet. Use /profile to change your background answers.", "yellow")
            elif command in {"/switch", "/discover", "/profile"}:
                try:
                    if command == "/profile":
                        interview(state, path, edit=True)
                    else:
                        previous = state["method_id"]
                        choose_method(state, discovery=command == "/discover")
                        if previous != state["method_id"]:
                            history, force = [], None
                    save_state(state, path)
                except Control as inner:
                    if inner.command in {"/quit", "/pause"}:
                        save_state(state, path)
                        paused(path)
                        return
                    say("Back to your plan. Commands work again at the next question.", "dim")
                except (EOFError, KeyboardInterrupt):
                    save_state(state, path)
                    print()
                    paused(path)
                    return
        except (EOFError, KeyboardInterrupt):
            save_state(state, path)
            print()
            paused(path)
            return


def saved_sessions():
    items = []
    folder = home_dir()
    if not folder.is_dir():
        return items
    for file in folder.glob("*.session.json"):
        try:
            items.append((file.stat().st_mtime, file, load_state(file)))
        except (OSError, ValueError):
            continue
    return sorted(items, key=lambda item: item[0], reverse=True)[:9]


def session_label(state, modified):
    name = BY_ID[state["method_id"]]["name"] if state["method_id"] else "Method not chosen yet"
    topic = state["plan"].get("goal") or state["profile"].get("desired_change") or ""
    topic = (topic[:50] + "...") if len(topic) > 50 else topic
    status = "approved" if state["reviewed"] else "in progress"
    when = datetime.fromtimestamp(modified).strftime("%d %b %Y, %H:%M")
    return f"{name}" + (f"  '{topic}'" if topic else "") + f"  ({status}, {when})"


def pick_saved_session():
    sessions = saved_sessions()
    if not sessions:
        return None
    heading("Welcome back", "You have saved plans on this computer.")
    for i, (modified, _, state) in enumerate(sessions, 1):
        print(paint(f"  {i}", "bold", ACCENTS[(i - 1) % len(ACCENTS)]) + "  " + session_label(state, modified))
    print(paint("  N", "bold") + "  Start a new plan")
    while True:
        value = ask("Which would you like? Type a number, or N for a new plan.", commands=False).lower()
        if value in ("", "n", "new"):
            return None
        if value.isdigit() and 1 <= int(value) <= len(sessions):
            return sessions[int(value) - 1][1]
        say("Please type one of the numbers shown, or N.", "red")


def main(argv=None):
    global COLOUR
    COLOUR = colour_supported()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalogue", help="Browse all 13 methods without saving anything")
    rec = sub.add_parser("recommend", help="Get five transparent preference-based suggestions")
    rec.add_argument("--tags", default="")
    rec.add_argument("--json", action="store_true")
    start = sub.add_parser("start", help="Start planning (or carry on with a saved plan)")
    start.add_argument("--mode", choices=["guided", "discovery"])
    start.add_argument("--file", type=Path)
    for name, text in (("resume", "Continue a saved session file"), ("check", "Validate a session file (for AI assistants)"),
                       ("export", "Write the Markdown plan for a session file")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--file", type=Path, required=True)
        if name == "export":
            p.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "catalogue":
            for i, method in enumerate(METHODS, 1):
                card(i, method, accent=ACCENTS[(i - 1) % len(ACCENTS)])
        elif args.command == "recommend":
            ranking = recommend(parse_tags(args.tags))
            if args.json:
                print(json.dumps(ranking, indent=2))
            else:
                say("A simple guide, not a scientific assessment. No personal data is sent anywhere.", "dim")
                for i, item in enumerate(ranking, 1):
                    card(i, BY_ID[item["id"]], item["reason"], ACCENTS[(i - 1) % len(ACCENTS)])
        elif args.command == "start":
            if not args.file and not args.mode:
                existing = pick_saved_session()
                if existing:
                    run_session(load_state(existing), existing.resolve())
                    return 0
            mode = args.mode
            choices = {"1": "guided", "2": "discovery"}
            while mode not in ("guided", "discovery"):
                heading("Welcome to Ganbaru", "Turn a goal into a plan you can act on.")
                mode = ask("How would you like to start? Type 1 or 2.", commands=False,
                           hint="1  Guided: I'll ask a few questions and suggest five methods\n"
                                "2  Discovery: browse all 13 methods and pick one yourself").lower()
                mode = choices.get(mode, mode)
            path = args.file or home_dir() / f"{uuid.uuid4().hex}.session.json"
            path = path.expanduser().resolve()
            if path.exists():
                raise ValueError("That session already exists. Choose another filename, or run Ganbaru without --file to pick it.")
            run_session(new_state(mode), path)
        else:
            state = load_state(args.file)
            if args.command == "resume":
                run_session(state, args.file.expanduser().resolve())
            elif args.command == "check":
                print(json.dumps({"valid": True, "missing": missing_fields(state), "reviewed": state["reviewed"]}, indent=2))
            else:
                out = args.out or plans_dir_for(args.file)
                plan = export_markdown(state, out)
                print(f"Plan saved: {plan}")
    except (ValueError, OSError, RuntimeError) as exc:
        print(paint(f"Ganbaru: {exc}", "red"), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Nothing was saved yet.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

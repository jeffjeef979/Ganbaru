"""Deterministic, format-neutral document model and methodology-led Markdown renderer.

Only the source session is persisted. A future PDF renderer can consume the same
document dictionary without asking an AI to recreate or reinterpret user answers.
"""
from __future__ import annotations

from html import escape
import re

UNSPECIFIED = "Not specified"


def value(state, source):
    group, key = source.split(".", 1)
    return state[group].get(key, "").strip() or UNSPECIFIED


def split_record(line):
    """Split explicit pipe-delimited input. Backslash escapes pipes or backslashes."""
    cells, current = [], []
    i = 0
    while i < len(line):
        char = line[i]
        if char == "\\" and i + 1 < len(line) and line[i + 1] in "|\\":
            current.append(line[i + 1])
            i += 2
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    cells.append("".join(current).strip())
    return cells


def records(raw, columns):
    """Never infer dates/owners from prose or drop lines with an unexpected shape."""
    rows, unstructured = [], []
    if raw == UNSPECIFIED:
        return [], []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = split_record(line)
        if len(parts) == len(columns):
            rows.append([part or UNSPECIFIED for part in parts])
        else:
            unstructured.append(line)
    return rows, unstructured


def build_document(state, method, template):
    """Return JSON-serializable blocks; this function never changes the session."""
    blocks = []
    for spec in template["blocks"]:
        kind = spec["type"]
        block = {"type": kind, "title": spec["title"]}
        if "note" in spec:
            block["note"] = spec["note"]
        if kind == "section":
            block["fields"] = [{"label": label, "text": value(state, source)} for label, source in spec["fields"]]
        elif kind == "table":
            block["columns"] = spec["columns"]
            block["rows"] = [[label, value(state, source)] for label, source in spec["rows"]]
        elif kind == "records":
            block["columns"] = spec["columns"]
            block["rows"], block["unstructured"] = records(value(state, spec["source"]), spec["columns"])
            block["source"] = spec["source"]
        elif kind == "checklist":
            raw = value(state, spec["source"])
            block["items"] = []
            if raw != UNSPECIFIED:
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    item = re.sub(r"^\s*[-*+]\s+", "", line).strip()
                    mark = re.match(r"^\[([ xX])\]\s+(.*)$", item)
                    block["items"].append({"checked": bool(mark and mark[1].lower() == "x"),
                                           "text": mark[2] if mark else item})
        elif kind == "log":
            block["columns"] = spec["columns"]
            block["rows"] = []
        else:
            raise ValueError(f"Unknown template block type: {kind}")
        blocks.append(block)
    if method["id"] == "harada":
        areas = next((b for b in blocks if b.get("source") == "method_answers.eight_areas"), None)
        actions = next((b for b in blocks if b.get("source") == "method_answers.actions_64"), None)
        if areas is None or actions is None:
            raise ValueError("The Harada template must contain records blocks for "
                             "method_answers.eight_areas and method_answers.actions_64.")
        numbers = {str(i) for i in range(1, 9)}
        area_ids = [r[0] for r in areas["rows"] if r[0] in numbers and r[1] != UNSPECIFIED]
        pairs = [(r[0], r[1]) for r in actions["rows"]
                 if r[0] in area_ids and r[1] in numbers and r[2] != UNSPECIFIED]
        complete = (len(area_ids) == len(set(area_ids)) == len(areas["rows"]) == 8
                    and len(pairs) == len(set(pairs)) == len(actions["rows"]) == 64
                    and not areas["unstructured"] and not actions["unstructured"])
        label = "Structurally complete" if complete else "Partial / unverified"
        actions["note"] = actions.get("note", "") + (f" Map status: {label} - {len(set(area_ids))}/8 named areas and "
                            f"{len(set(pairs))}/64 distinct linked actions. Counts check structure, not quality or feasibility.")
    return {
        "document_version": 1,
        "method_id": method["id"],
        "title": template["title"],
        "status": "REVIEWED PLAN" if state["reviewed"] else "DRAFT - NOT YET APPROVED",
        "method_name": method["name"], "kind": method["kind"],
        "description": method["description"], "limitation": method["limitation"],
        "source": method["source"], "blocks": blocks,
        "analysis": str(state.get("analysis", "")).strip(),
        "next_action": value(state, "plan.first_action"),
        "review": value(state, "plan.review"),
    }


def inline(text):
    """Render user text literally; disallow embedded HTML, images or injected tables."""
    text = escape(str(text), quote=False)
    text = re.sub(r"([\\`*_\[\]|~])", r"\\\1", text)
    # Leading '=' is escaped too: a line of '===' under text would otherwise become a heading.
    text = re.sub(r"^(\s*)([#+\-=])", r"\1\\\2", text)
    return re.sub(r"^(\s*\d+)([.)])", r"\1\\\2", text)


def paragraph(text):
    # Markdown hard breaks retain the user's line structure without interpreting it.
    return "  \n".join(inline(line) for line in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"))


def cell(text):
    return inline(text).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def table(columns, rows):
    lines = ["| " + " | ".join(cell(c) for c in columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        if len(row) != len(columns):
            raise ValueError("A document table row does not match its columns.")
        lines.append("| " + " | ".join(cell(c) for c in row) + " |")
    return lines + [""]


def analysis_markdown(text):
    """Keep the coach's bullet points as a real list; everything else stays escaped literal text."""
    out, previous_bullet = [], None
    for line in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not line.strip():
            continue
        bullet = re.match(r"^\s*[-*\u2022]\s+(.*)$", line)
        if previous_bullet is not None and previous_bullet != bool(bullet):
            out.append("")
        out.append("- " + inline(bullet[1]) if bullet else inline(line) + "  ")
        previous_bullet = bool(bullet)
    return "\n".join(out).rstrip()


def render_markdown(document):
    lines = ["# " + document["title"], "", document["status"], "",
             "Method: " + document["method_name"], "", "Type: " + document["kind"], "",
             document["description"], ""]
    for block in document["blocks"]:
        lines += ["## " + block["title"], ""]
        if block.get("note"):
            lines += [block["note"], ""]
        kind = block["type"]
        if kind == "section":
            for field in block["fields"]:
                lines += ["### " + field["label"], "", paragraph(field["text"]), ""]
        elif kind in ("table", "records"):
            rows = block["rows"] or [[UNSPECIFIED] * len(block["columns"])]
            lines += table(block["columns"], rows)
            if kind == "records" and block["unstructured"]:
                lines += ["**Original notes - not assigned to columns**", "",
                          "These notes are preserved below. Owners, measures and dates have not been inferred.", "",
                          paragraph("\n".join(block["unstructured"])), ""]
        elif kind == "checklist":
            if block["items"]:
                lines += [f"- [{'x' if item['checked'] else ' '}] " + inline(item["text"]) for item in block["items"]]
                lines += [""]
            else:
                lines += [UNSPECIFIED, ""]
        elif kind == "log":
            lines += ["Blank template for future observations; no results are recorded here.", ""]
            lines += table(block["columns"], [[""] * len(block["columns"])])
    if document.get("analysis"):
        lines += ["## Ganbaru analysis", "",
                  "Prepared with your AI coach and reviewed by you. It is guidance, not a prediction.", "",
                  analysis_markdown(document["analysis"]), ""]
    lines += ["## My next action", "", paragraph(document["next_action"]), "",
              "## My review date", "", paragraph(document["review"]), "",
              "## Method context", "", document["limitation"], "",
              f"[Method explanation and source]({document['source']})", "",
              "Original Ganbaru exercises; no affiliation or certification implied.", "",
              "Private interview background is omitted from exports by default.", ""]
    return "\n".join(lines)

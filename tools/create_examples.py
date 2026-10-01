"""Generate a local gallery of 13 method-specific plans using fictional answers only."""
from pathlib import Path
from create_demo import gp, demo_state

ROOT = Path(__file__).resolve().parents[1]
ANSWERS = {
    "smart": [
        "Publish three short technical articles; a full course is outside scope.",
        "Start with zero completed articles; finish three reviewed and published articles.",
        "Use two 45-minute writing blocks per week and a peer reviewer.",
        "Clear writing supports the kind of work I want to do next.",
        "Publish by 20 December 2026; review the first draft on 1 November.",
    ],
    "okr": [
        "Build a small, useful portfolio of technical explanations.",
        "Published articles | 0 | 3 | 20 December 2026\nArticles reviewed by a peer | 0 | 3 | 15 December 2026",
        "Draft a weekly outline | Published articles | Me\nAsk a peer to review each draft | Articles reviewed by a peer | Me",
        "I own delivery. Peer availability is a dependency, not an agreed commitment yet.",
        "Check article progress each Sunday; revise scope if drafting repeatedly slips.",
    ],
    "kaizen": [
        "Writing sessions currently start with 20 minutes searching for references.",
        "Prepare three references before the session and keep other tabs closed.",
        "Try the change for two sessions, recording time until the first paragraph.",
        "Keep it if drafting starts sooner without reducing accuracy; otherwise adjust the preparation step.",
        "Reflect after the second session and choose one new friction point.",
    ],
    "gtd": [
        "Choose topics; collect examples; ask about review availability; finish old notes.",
        "Done means three published articles. The next action is listing five possible topics.",
        "Keep next actions in a local note, fixed writing blocks on the calendar, and reviewer replies in a waiting-for list.",
        "Review the project and waiting-for list on Sunday for 15 minutes.",
        "At my desk on Saturday morning, list five topics before researching them.",
    ],
    "grow": [
        "Leave with a feasible plan to publish three articles.",
        "I know the subject but currently have no complete drafts and limited weekday energy.",
        "Write short explainers; collaborate with a peer; or begin with one annotated example.",
        "Choose short explainers. Outline the first on 3 October and review progress weekly.",
    ],
    "ikigai": [
        "I enjoy helping someone understand an idea that previously felt confusing.",
        "Curiosity, clarity and contribution recur across those experiences.",
        "Make space for a small weekly writing practice without turning every interest into paid work.",
        "Write one short explanation and ask a willing reader what helped them.",
        "Reflect after sharing it: did this activity feel meaningful, and what would I like to try next?",
    ],
    "woop": [
        "Publish three useful articles by 20 December 2026.",
        "Feel confident explaining an idea and have work I am happy to share.",
        "When a paragraph feels imperfect, I avoid it by researching more.",
        "If I open another reference to avoid drafting, then I will write one rough paragraph first.",
    ],
    "knowing-acting": [
        "Helpful communication should respect the reader's time and understanding.",
        "I say clarity matters but sometimes leave unexplained terms in my drafts.",
        "Revise one paragraph for a new reader, then ask what remains unclear.",
        "Compare my intention with the reader's experience and revise my next explanation.",
    ],
    "wu-wei": [
        "Trying to write late every night leaves me tired; regular work and rest still need attention.",
        "I think more clearly in short early-evening sessions with prepared notes.",
        "Remove the demand to produce a long article; explain one useful idea at a time.",
        "Draft one short section at the next planned session and reassess the rhythm on Sunday.",
    ],
    "karma-yoga": [
        "Explain technical ideas accurately and with care for the reader.",
        "I can choose preparation, writing and revision; I cannot guarantee recognition or readership.",
        "Keep two manageable writing sessions each week and verify factual claims.",
        "Use feedback to improve the work, without treating audience size as a verdict on my worth.",
    ],
    "harada": [
        "Publish three articles by 20 December 2026, developing my communication and helping readers.",
        "Strength: technical experience. Development need: concise explanations. Obstacle: perfectionism.",
        "1 | Topic knowledge\n2 | Reader understanding\n3 | Outlining\n4 | Drafting\n5 | Examples\n6 | Review\n7 | Publishing\n8 | Sustainable routine",
        "1 | 1 | Verify each central claim\n2 | 1 | State the intended reader\n3 | 1 | Outline three main points\n4 | 1 | Draft for 25 minutes\n5 | 1 | Add one worked example\n6 | 1 | Ask for peer feedback\n7 | 1 | Check the published page\n8 | 1 | Protect two weekly writing blocks",
        "Write during the scheduled blocks\nRecord one lesson after each session\nReview the action map on Sunday",
        "After each writing session, note the action completed, a lesson and the next adjustment. This example action map is intentionally partial.",
    ],
    "toyota-kata": [
        "Make a reliable process for publishing clear technical articles.",
        "Sessions start with unbounded research and often finish without a drafted section.",
        "By 18 October, start each session with a prepared outline and finish one rough section.",
        "The first obstacle is not knowing whether enough research has been done to start drafting.",
        "Prepare an outline and three references | Begin drafting within 10 minutes | Time to first paragraph and a completed rough section | 11 October 2026",
        "Compare expectation with observation after two sessions, then choose the next experiment.",
    ],
    "hoshin-kanri": [
        "Solo adaptation: develop a dependable technical communication practice.",
        "Move from collecting ideas to regularly finishing and publishing useful explanations.",
        "Publish three reviewed articles during the current planning cycle.",
        "Ask a potential reviewer about available time and scope. No agreement is assumed in this example.",
        "Outline three articles | Me | Three outlines ready | 15 October 2026 | Topic selection\nArrange review | Me | Review availability confirmed | 20 October 2026 | Reviewer response",
        "Review execution each Sunday and revisit the overall direction at the end of the cycle.",
    ],
}


def create_examples():
    out = ROOT / "output" / "methodologies"
    out.mkdir(parents=True, exist_ok=True)
    index = ["# Ganbaru format gallery", "", "Thirteen fictional drafts for comparing output formats. These are examples, not real user commitments. All are generated deterministically from local session JSON.", "",
             "| Method | Markdown example | Source JSON |", "|---|---|---|"]
    for method in gp.METHODS:
        mid = method["id"]
        state = demo_state()
        state["method_id"] = mid
        state["reviewed"] = False
        state["plan"]["obstacles"] = (
            "Perfectionism: write one rough paragraph before gathering more references.\n"
            "Low energy: outline for five minutes and reschedule remaining work.\n"
            "Delayed feedback: continue the next article while waiting and revise dates if necessary."
        )
        answers = ANSWERS[mid]
        if len(answers) != len(method["steps"]):
            raise ValueError(f"Example answer count mismatch: {mid}")
        state["method_answers"] = {step["key"]: answer for step, answer in zip(method["steps"], answers)}
        gp.save_state(state, out / f"{mid}.session.json")
        (out / f"{mid}.md").write_text(gp.markdown(state), encoding="utf-8")
        index.append(f"| {method['name']} | [View plan]({mid}.md) | [Session]({mid}.session.json) |")
    (out / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(out / "index.md")


if __name__ == "__main__":
    create_examples()

"""Generate one fictional review plan. No actual user information is used."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("planner", ROOT / "skills/ganbaru/scripts/ganbaru.py")
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)


def demo_state():
    state = gp.new_state()
    state["profile"] = {"life_stage": "Fictional early-career professional", "experience": "Two years in a technical role"}
    state["tags"] = ["clarity", "action"]
    gp.switch_method(state, "woop")
    state["method_answers"] = {
        "wish": "Publish three useful portfolio articles by 20 December 2026, while keeping evenings manageable.",
        "outcome": "I feel more confident explaining ideas and have three concrete examples of my work to share.",
        "obstacle": "When a draft feels imperfect, I keep researching instead of writing the next paragraph.",
        "plan": "If I notice myself opening another reference to avoid drafting, then I will write one rough paragraph before browsing again.",
    }
    state["plan"] = {
        "goal": "Publish three reviewed portfolio articles by 20 December 2026.",
        "why": "Practice clear technical communication and create a small body of work I am proud of. This is a fictional demonstration, not a real user's plan.",
        "success": "Starting point: no completed drafts. Success: three articles, each reviewed by a peer and revised at least once, published by 20 December 2026.",
        "milestones": "15 October: choose topics and outline all three articles.\n1 November: finish article one.\n20 November: finish article two.\n10 December: finish article three.\n20 December: complete review and publication.",
        "actions": "Tuesday and Thursday, 19:00-19:45: write at my desk with reference tabs closed. Sunday, 17:00-17:15: check progress and schedule the next two writing sessions. Weekly budget: 1 hour 45 minutes.",
        "support": "Use public technical references and a fictional peer reviewer. Ask about review availability before depending on a particular turnaround time.",
        "obstacles": "Perfectionism: use the WOOP response below.\nLow energy: write a five-minute outline and reschedule the remaining work.\nDelayed feedback: continue the next article while waiting; avoid promising publication dates to others until review is confirmed.",
        "first_action": "On 3 October 2026 at 10:00, list five article ideas and select three within 20 minutes.",
        "review": "First review: 11 October 2026 at 17:00. Repeat every Sunday for 15 minutes. Check drafts completed, whether writing sessions happened, and whether the workload still fits.",
        "adjustment": "If two planned sessions are missed in a week, reduce the next article's scope before adding more hours. If the plan repeatedly crowds out rest, revise the target date or article count.",
    }
    state["analysis"] = (
        "- Fit: 1 hour 45 minutes a week matches three short articles over about eleven weeks, with a little slack.\n"
        "- Strength: the if-then plan targets the exact moment perfectionism shows up (opening another reference).\n"
        "- Main risk: peer review timing is outside your control; keep writing the next article while you wait.\n"
        "- Still vague: what 'useful' means for each article. Consider naming one reader question each one answers.\n"
        "Fictional example of the analysis an AI coach writes and the user approves.")
    state["reviewed"] = True
    return state


def create_demo():
    state = demo_state()
    out = ROOT / "output" / "markdown"
    out.mkdir(parents=True, exist_ok=True)
    gp.save_state(state, ROOT / "output" / "demo.session.json")
    (out / "ganbaru-demo.md").write_text(gp.markdown(state), encoding="utf-8")
    print(out / "ganbaru-demo.md")


if __name__ == "__main__":
    create_demo()

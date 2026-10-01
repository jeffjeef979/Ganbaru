# Conversation and local state contract

## Interview (eight topics, one at a time)

These are friendly starting points. In an AI assistant, adapt the wording to the conversation, skip what the user has already told you, and follow up on vague answers. The offline program asks them as written.

1. Life stage: "Let's start with you. What's happening in your life at the moment? Any big changes, or people and responsibilities you're looking after?" Broad descriptions are enough; never ask for exact age.
2. Experience: "What are you already good at? Think of work, study, caring for others or hobbies that could help you here."
3. Desired change: "If the next year went really well, what would be different for you? It's fine if you're not sure yet."
4. Motivation: "Why does that matter to you? Is there anything you don't want to sacrifice along the way?"
5. Timeframe: "When would you like to see progress? Are there any dates you can't move?"
6. Capacity: "Realistically, how much time and energy can you give this each week? Is there anyone or anything that could help?"
7. Obstacles: "When you've tried something like this before, what usually got in the way?"
8. Planning preference: What kind of help fits? Offer the supported tags below in plain words: clear targets (`clarity`), meaning and direction (`purpose`), starting and following through (`action`), consistent routines (`habits`), too many commitments (`overload`), guided reflection (`coaching`), an unclear route (`uncertainty`), team alignment (`team`), organizational strategy (`organization`), manageable effort (`gentle`), learning about yourself (`reflection`), detailed planning (`structure`), less attachment to results (`outcome-stress`), or learning through practice (`learning`).

All profile answers are optional. Do not request sensitive background to improve a score. In the offline program, the eighth question is a numbered list the user picks from. In an AI assistant, propose tags from the whole interview, explain them in plain words, and ask the user to confirm. Free-text context shapes coaching, not hidden profiling.

Supported tags: `clarity`, `purpose`, `action`, `habits`, `overload`, `coaching`, `uncertainty`, `team`, `organization`, `gentle`, `reflection`, `structure`, `outcome-stress`, `learning`.

Scores start from each method's small editorial base and add its catalogue weights for selected tags. Tie-break by catalogue order. A ranking is a starting point, not a validity test. Explain matched tags and catalogue limitations; do not display scores as probabilities. Unknown tags are rejected. Recommending 5 does not restrict the available 13.

## Final execution fields

These fields remain common in saved JSON, but are distributed within the selected methodology's layout at export. See `output-formats.md` and `output-templates.json` for the mapping. Existing version-1 sessions remain compatible; no answer migration or AI rewriting is required.

- `goal`: One main outcome, bounded enough to act on.
- `why`: The user's motivation.
- `success`: Baseline, desired evidence/measure, and target date where appropriate.
- `milestones`: Intermediate results with dates; one per line if convenient.
- `actions`: Repeated actions, when/where, and realistic time budget.
- `support`: Resources, dependencies, or people who can help; no private contact details needed.
- `obstacles`: Likely obstacles and responses.
- `first_action`: The next concrete action and when it will happen.
- `review`: First review date and review cadence.
- `adjustment`: What evidence will trigger a change of plan?

Use qualitative evidence where numeric targets would distort the goal. Never turn spiritual liberation, moral growth, or joy into arbitrary numerical scores. Ask users for missing dates; do not silently invent deadlines. Mark uncertain commitments as draft.

## State schema (version 1)

The Python helper validates fields and bounds. This JSON shape is the contract; method answer keys must exactly match the selected method's `steps[].key` from `methodologies.json`.

```json
{
  "schema_version": 1,
  "mode": "guided",
  "profile": {},
  "tags": [],
  "method_id": null,
  "method_answers": {},
  "plan": {},
  "analysis": "",
  "switch_count": 0,
  "reviewed": false
}
```

Profile keys: `life_stage`, `experience`, `desired_change`, `motivation`, `timeframe`, `capacity`, `obstacles`, `preference`. Values are strings. `mode` is `guided` or `discovery`. `method_id` is a catalogue ID or null. `method_answers` and `plan` map valid keys to strings. `tags` is a unique list of valid tags. `analysis` is the user-approved Ganbaru analysis written by the AI coach (plain text, may be empty; the offline program leaves it empty). Sessions saved without this field are still valid. `switch_count` is a non-negative integer. `reviewed` is boolean and can only be true when every required method and plan answer is nonblank. Skipped profile fields do not block a final plan.

Changing any method answer or plan field resets `reviewed` to false. A confirmed switch to a different method clears both dictionaries, the analysis and approval, retains profile/tags, and increments the count. Switching to the same method does nothing. The break prompt is required when the next committed switch count exceeds three. Resuming does not reset the count.

Local JSON is plaintext, not encrypted. Save only the active state; no answer history or backups are created by the application. Atomic replacement prevents partial JSON writes, but does not securely erase filesystem history. Local sync folders, OS backups, terminal scrollback, and AI chat retention are outside the skill's control.

## Host without execution

Use the self-contained `dist/ganbaru-prompt.md` from the source distribution, or load this skill, the workflow, methodology catalogue, and output-format references manually. Keep active state in the conversation only if the user accepts the provider's processing boundary. Provide a copyable session JSON and Markdown plan; clearly say local saving requires the user to download/save it. The local CLI can validate and export that JSON later. Never promise automatic local saving in a host without local file access. Provide the Markdown directly so the user can save it themselves.

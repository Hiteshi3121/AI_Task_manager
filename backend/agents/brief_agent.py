"""
Brief agent: the ONLY part of the daily brief that calls the LLM.
Counting tasks and finding overdue items is plain SQL/Python (see
brief_service.py) — only deciding what's worth surfacing and how to
phrase it goes through the model. This keeps numbers always accurate
and keeps the LLM call small and cheap.
"""

from services.llm_client import call_llm_json


def _build_prompt(
    open_tasks: list[dict],
    overdue_candidates: list[dict],
    calendar_events: list[dict] | None = None,
) -> str:
    task_lines = "\n".join(
        f'- [{t["priority"].upper()}] {t["title"]} (bucket: {t["bucket_id"]}, due: {t["due"]})'
        for t in open_tasks
    ) or "(no open tasks)"

    candidate_lines = "\n".join(
        f'- {c["name"]} — linked task: {c["title"]} (priority: {c["priority"]}, due: {c["due"]})'
        for c in overdue_candidates
    ) or "(none)"

    urgent_count = sum(
        1 for t in open_tasks if t["priority"] == "high" or t["due"] == "today"
    )
    total_open = len(open_tasks)
    bullet_target = min(max(8, urgent_count), 12)

    # Calendar section — only included when Google Calendar is connected
    if calendar_events:
        event_lines = "\n".join(
            f'- {e["title"]} ({e["start"]}{"–" + e["end"] if not e["all_day"] else ", all day"})'
            for e in calendar_events
        )
        calendar_section = f"""
Today's calendar events:
{event_lines}

Calendar guidance:
- If a calendar event overlaps with a high-priority task, flag the conflict (e.g. "You have a meeting at 3 PM but still need to review the pitch deck first")
- If there's a clear gap in the calendar with no meetings, suggest using it for focused work on the top open task
- Mention specific event names when flagging conflicts, not generic "meeting" labels
"""
    else:
        calendar_section = ""

    return f"""You are an AI chief of staff writing a short daily brief for a founder named Ishita.

Open tasks right now:
{task_lines}

People/students with pending follow-ups:
{candidate_lines}
{calendar_section}
Return ONLY a JSON object with exactly these keys:
{{
  "what_matters_today": [
    {{"text": "short bullet sentence", "priority": "high" | "medium" | "low"}}
  ],
  "who_to_check_on": [{{"name": "...", "reason": "one short phrase, under 8 words"}}]
}}

Rules:
- aim for {bullet_target} bullets in what_matters_today, but there are only {total_open} open tasks total right now — never invent a task that isn't listed above; if there aren't enough real tasks to reach {bullet_target}, write one bullet per real open task and stop there
- order bullets by priority: all high first, then medium, then low
- each bullet's "priority" field must match the priority of the task it's describing (high/medium/low) — for general nudges not tied to one task (e.g. a quiet bucket), use "low"
- mention high-priority and today-due items first, with the most concrete, specific phrasing
- if a bucket has had no recent activity, you may note that as a gentle nudge, but only after every real open task is covered
- who_to_check_on should only include people from the candidates list above, rephrased naturally
- be concrete, not generic — refer to actual task titles
- keep it warm but brief, no fluff

Return ONLY the JSON object."""


def generate_brief_narrative(
    open_tasks: list[dict],
    overdue_candidates: list[dict],
    calendar_events: list[dict] | None = None,
) -> dict:
    """
    Returns {"what_matters_today": [...], "who_to_check_on": [...]}.
    Raises json.JSONDecodeError on a malformed model response —
    the caller (brief_service) should catch this and fall back gracefully.
    """
    prompt = _build_prompt(open_tasks, overdue_candidates, calendar_events)
    return call_llm_json(prompt)

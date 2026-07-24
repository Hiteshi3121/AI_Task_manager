"""
Classifier agent: takes raw task text typed by Ishita and returns a
structured ClassifiedTask — which bucket, which sub-bucket (Udukku only),
which person or student it's tied to (if any), priority, and due timing.

This is intentionally a plain function, not a framework agent. See the
project README for why: at two agents total with no inter-agent routing,
a framework like LangGraph or CrewAI would add ceremony without adding
capability.
"""

from datetime import date
from services.llm_client import call_llm_json
from models.schemas import ClassifiedTask

BUCKETS = {
    "udukku": "Udukku — the core team and company operations",
    "ascend_social": "Ascend Now — Social Media (Hiya runs this with Ishita)",
    "ascend_classes": "Ascend Now — Entrepreneurship Classes (Ishita's students)",
    "music": "My Music — Ishita's own music career",
    "social_brand": "My Social Media — Ishita's personal brand",
    "fitness": "Fitness — Hyrox Prep — training, diet, hair, skin",
    "personal": "Personal / Errands — generic life admin and errands with no clear tie to the other five buckets (e.g. groceries, appointments, chores, bills)",
}

SUB_BUCKETS = {
    "music_room": "Udukku's Music Room project",
    "marketing": "Udukku marketing and content",
    "operations": "Udukku day-to-day operations",
    "partnerships": "Udukku partnerships and outreach",
    "content": "Udukku general content work",
}

PEOPLE = [
    "Evita", "Meezan", "Heeral", "Evani", "Hiya",
    "Sagarika", "Dhanya Sree", "Tanvi",
]


def _build_prompt(raw_text: str, known_students: list[str]) -> str:
    bucket_list = "\n".join(f'- "{k}": {v}' for k, v in BUCKETS.items())
    sub_bucket_list = "\n".join(f'- "{k}": {v}' for k, v in SUB_BUCKETS.items())
    people_list = ", ".join(PEOPLE)
    students_list = ", ".join(known_students) if known_students else "(none yet)"

    today_str = date.today().isoformat()  # e.g. "2026-07-02"

    return f"""You are a task classification agent for a founder named Ishita.
Classify the task below and return ONLY a JSON object, no markdown, no explanation.

Today's date is {today_str}.

Buckets (pick exactly one id):
{bucket_list}

Sub-buckets (ONLY use these if bucket_id is "udukku", otherwise set to null):
{sub_bucket_list}

Known Udukku team members: {people_list}
Known students (Ascend Now Entrepreneurship Classes): {students_list}

Task: "{raw_text}"

Return a JSON object with exactly these keys:
{{
  "title": "if the raw task is under 15 words, keep it as-is but fix spelling and grammar; otherwise write a 15-20 word clean action-oriented summary",
  "bucket_id": one of the bucket ids above,
  "sub_bucket_id": one of the sub-bucket ids above, or null if bucket_id is not "udukku",
  "person_name": the matching team member's exact name if the task mentions one of them, else null,
  "student_name": the matching student's exact name if the task mentions one of them, else null,
  "priority": "high" | "medium" | "low",
  "due": "today" | "this week" | "upcoming" | "no deadline"  (exactly one of these four strings, never any other word),
  "calendar_event": null or an object with these fields if the task explicitly mentions a meeting/call/session at a specific time:
    {{
      "summary": "short event title (e.g. 'Pitch Deck Prep with Hiya')",
      "start_iso": "ISO 8601 datetime in IST offset, e.g. 2026-07-02T19:30:00+05:30",
      "end_iso": "ISO 8601 datetime in IST offset — assume 1 hour duration if not specified"
    }}
}}

Rules:
- priority is high if urgent, has a near deadline, or uses words like ASAP/urgent/critical
- due: infer from words like today, tomorrow, Friday, this week, next month
- person_name and student_name are mutually exclusive — a task is about a team member OR a student, not both
- Only set person_name/student_name if the task text actually names them or clearly refers to them
- calendar_event: only set this if the task explicitly mentions scheduling a meeting, call, session, or event at a specific time — never infer a time that isn't mentioned; if no time is given, set calendar_event to null
- For calendar_event dates: "today" means {today_str}; resolve relative days (tomorrow, Friday) against today's date

Return ONLY the JSON object."""


def classify_task(raw_text: str, known_students: list[str] = None) -> dict:
    """
    Classifies raw task text into a structured shape.
    known_students should be the current list of student names from the
    database, so the model can match mentions to existing roster entries
    instead of guessing — the caller (task_service) is responsible for
    resolving person_name/student_name into actual foreign key IDs.
    """
    prompt = _build_prompt(raw_text, known_students or [])
    result = call_llm_json(prompt)
    return result


if __name__ == "__main__":
    # Manual test — run directly: python agents/classifier_agent.py
    examples = [
        "Follow up with Tanvi about music room attendance tomorrow",
        "Review Meezan's carousel draft before Friday",
        "Block 2 hours for songwriting this weekend",
        "Log today's Hyrox training session",
    ]
    for ex in examples:
        print(f"\nInput: {ex}")
        print(classify_task(ex))

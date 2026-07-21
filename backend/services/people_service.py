"""
People service: powers the "People" tab. There's no new table here —
every Udukku team member already lives in `people`, and every task that
names one of them already gets `person_id` set by the classifier (see
classifier_agent.py). This just groups existing tasks by the person
they're linked to, so a person "shows up" the moment a task mentions
them and never needs a separate add step.
"""

from db.connection import get_connection


def list_people_with_tasks() -> list[dict]:
    """
    Returns every person who has at least one task ever linked to them,
    each with their tasks newest-first. `title` is the short classifier
    summary (already 4-8 words, e.g. "Review Prompt Logic") used as the
    clickable label; `raw_text` is the original sentence Ishita typed,
    shown when that label is clicked.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select p.id as person_id, p.name, p.role,
                       t.id as task_id, t.title, t.raw_text, t.priority,
                       t.due, t.done, t.created_at
                from people p
                join tasks t on t.person_id = p.id
                order by p.name, t.created_at desc
                """
            )
            rows = cur.fetchall()

    people: dict[int, dict] = {}
    for row in rows:
        pid = row["person_id"]
        if pid not in people:
            people[pid] = {"id": pid, "name": row["name"], "role": row["role"], "tasks": []}
        people[pid]["tasks"].append(
            {
                "id": row["task_id"],
                "title": row["title"],
                "raw_text": row["raw_text"],
                "priority": row["priority"],
                "due": row["due"],
                "done": row["done"],
                "created_at": row["created_at"],
            }
        )

    return list(people.values())

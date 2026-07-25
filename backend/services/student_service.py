"""
Student service: manages the Ascend Now student roster.
This is deliberately separate from task_service — a student is a
standing record (always visible, even with zero open tasks), not a
task. See README for the reasoning.
"""

from db.connection import get_connection


def list_students(status: str | None = None) -> list[dict]:
    query = "select * from students"
    params = []
    if status:
        query += " where status = %s"
        params.append(status)
    query += " order by name"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def create_student(name: str, current_project: str | None, status: str, next_follow_up: str | None) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into students (name, current_project, status, next_follow_up)
                values (%s, %s, %s, %s)
                returning *
                """,
                (name, current_project, status, next_follow_up),
            )
            conn.commit()
            return cur.fetchone()


def update_student(student_id: int, updates: dict) -> dict | None:
    if not updates:
        return None
    set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
    set_clause += ", last_updated = now()"
    params = list(updates.values()) + [student_id]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"update students set {set_clause} where id = %s returning *",
                params,
            )
            conn.commit()
            return cur.fetchone()


def delete_student(student_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("delete from students where id = %s", (student_id,))
            conn.commit()


def get_tasks_for_student(student_id: int) -> list[dict]:
    """Any specific to-dos tied to this student, separate from their standing project status."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select * from tasks where student_id = %s order by created_at desc",
                (student_id,),
            )
            return cur.fetchall()

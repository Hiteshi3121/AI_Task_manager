from db.connection import get_connection


def list_people_with_tasks() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select p.id as person_id, p.name, p.role,
                       t.id as task_id, t.title, t.raw_text, t.priority,
                       t.due, t.done, t.created_at
                from people p
                left join tasks t on t.person_id = p.id
                order by p.name, t.created_at desc
                """
            )
            rows = cur.fetchall()

    people: dict[int, dict] = {}
    for row in rows:
        pid = row["person_id"]
        if pid not in people:
            people[pid] = {"id": pid, "name": row["name"], "role": row["role"] or '', "tasks": []}
        if row["task_id"]:
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


def create_person(name: str, role: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into people (name, role) values (%s, %s) returning id, name, role",
                (name, role or None)
            )
            row = cur.fetchone()
            conn.commit()
    return {"id": row["id"], "name": row["name"], "role": row["role"] or '', "tasks": []}


def update_person(person_id: int, name: str | None, role: str | None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select id, name, role from people where id = %s", (person_id,))
            row = cur.fetchone()
            if not row:
                return None
            new_name = name if name is not None else row["name"]
            new_role = role if role is not None else (row["role"] or '')
            cur.execute(
                "update people set name = %s, role = %s where id = %s returning id, name, role",
                (new_name, new_role or None, person_id)
            )
            updated = cur.fetchone()
            conn.commit()
    return {"id": updated["id"], "name": updated["name"], "role": updated["role"] or '', "tasks": []}


def delete_person(person_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("update tasks set person_id = null where person_id = %s", (person_id,))
            cur.execute("delete from people where id = %s", (person_id,))
            deleted = cur.rowcount
            conn.commit()
    return deleted > 0

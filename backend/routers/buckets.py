from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import get_connection

router = APIRouter()


class BucketCreate(BaseModel):
    id: str
    name: str


@router.get("/custom")
def list_custom():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select id, name from buckets where sort_order > 100 order by sort_order"
            )
            return [dict(r) for r in cur.fetchall()]


@router.post("/")
def create_bucket(body: BucketCreate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """insert into buckets (id, name, sort_order)
                   values (%s, %s,
                     (select coalesce(max(sort_order), 100) + 1 from buckets where sort_order > 100))
                   on conflict (id) do nothing""",
                (body.id, body.name),
            )
            conn.commit()
    return {"ok": True, "id": body.id}


@router.delete("/{bucket_id}")
def delete_bucket(bucket_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select sort_order from buckets where id = %s", (bucket_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Bucket not found")
            if row["sort_order"] <= 100:
                raise HTTPException(status_code=400, detail="Cannot delete a default bucket")
            cur.execute("update tasks set bucket_id = 'personal' where bucket_id = %s", (bucket_id,))
            cur.execute("delete from buckets where id = %s", (bucket_id,))
            conn.commit()
    return {"ok": True}

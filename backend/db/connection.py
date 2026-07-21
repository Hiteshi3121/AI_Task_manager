"""
Single place that knows how to talk to Postgres.
Every other file imports get_connection() from here — nobody else
should import psycopg directly. This is what makes it easy to swap
drivers or add pooling later without touching business logic.
"""

import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
    )


def get_connection():
    """
    Returns a new psycopg connection with dict-style rows,
    so query results come back as {"column_name": value} instead of tuples.
    Use with a `with` block so it always closes:

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select * from tasks")
                rows = cur.fetchall()
    """
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def test_connection():
    """Quick sanity check — run this file directly to confirm the DB is reachable."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) as count from buckets")
            result = cur.fetchone()
            print(f"Connected. Found {result['count']} buckets in the database.")


if __name__ == "__main__":
    test_connection()

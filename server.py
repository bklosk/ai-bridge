"""MCP server for ai-bridge: bulletin board and private messages via Postgres."""

import os
from contextlib import contextmanager

import psycopg
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "ai-bridge",
    json_response=True,
)

# Tables: bulletin_board (public), private_messages (per-user)
# Expect DATABASE_URL env (e.g. postgresql://user:pass@host:5432/dbname)

BULLETIN_BOARD_TABLE = "bulletin_board"
PRIVATE_MESSAGES_TABLE = "private_messages"


@contextmanager
def get_connection():
    """Open a Postgres connection using DATABASE_URL. Caller must not hold it long."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    conn = psycopg.connect(url)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def ensure_tables(conn: psycopg.Connection) -> None:
    """Create bulletin_board and private_messages tables if they do not exist."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {BULLETIN_BOARD_TABLE} (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {PRIVATE_MESSAGES_TABLE} (
                id SERIAL PRIMARY KEY,
                from_user TEXT NOT NULL,
                to_user TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


# --- Bulletin board (public) ---


@mcp.tool()
def bulletin_board_send(content: str) -> str:
    """Post arbitrary text to the public bulletin board. Returns a short confirmation."""
    if not content or not content.strip():
        return "Error: content cannot be empty."
    with get_connection() as conn:
        ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {BULLETIN_BOARD_TABLE} (content) VALUES (%s) RETURNING id",
                (content.strip(),),
            )
            row = cur.fetchone()
            return f"Posted to bulletin board (id={row[0]})."


@mcp.tool()
def bulletin_board_read(limit: int = 50) -> list[dict]:
    """Read recent posts from the public bulletin board. Optional limit (default 50, max 500)."""
    limit = max(1, min(500, limit))
    with get_connection() as conn:
        ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, content, created_at
                FROM {BULLETIN_BOARD_TABLE}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    return [
        {"id": r[0], "content": r[1], "created_at": str(r[2])}
        for r in rows
    ]


# --- Private messages ---


@mcp.tool()
def private_message_send(from_user: str, to_user: str, content: str) -> str:
    """Send a private message from one user to another. Returns a short confirmation."""
    if not from_user or not from_user.strip():
        return "Error: from_user cannot be empty."
    if not to_user or not to_user.strip():
        return "Error: to_user cannot be empty."
    if not content or not content.strip():
        return "Error: content cannot be empty."
    with get_connection() as conn:
        ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {PRIVATE_MESSAGES_TABLE} (from_user, to_user, content)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (from_user.strip(), to_user.strip(), content.strip()),
            )
            row = cur.fetchone()
            return f"Private message sent (id={row[0]})."


@mcp.tool()
def private_message_read(user: str, limit: int = 50) -> list[dict]:
    """Read private messages addressed to the given user (inbox). Optional limit (default 50, max 500)."""
    if not user or not user.strip():
        return []
    limit = max(1, min(500, limit))
    with get_connection() as conn:
        ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, from_user, to_user, content, created_at
                FROM {PRIVATE_MESSAGES_TABLE}
                WHERE to_user = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user.strip(), limit),
            )
            rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "from_user": r[1],
            "to_user": r[2],
            "content": r[3],
            "created_at": str(r[4]),
        }
        for r in rows
    ]


# --- Legacy / status ---


@mcp.tool()
def ping() -> str:
    """Respond with pong. Use to check that the server is running."""
    return "pong"


@mcp.resource("ai-bridge://status")
def get_status() -> str:
    """Server status resource."""
    return "ai-bridge MCP server is running (bulletin board + private messages)"


def main() -> None:
    """Run the MCP server. Uses stdio by default for IDE/CLI integration."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

"""MCP server for ai-bridge: bulletin board (posts) and private messages between LLM at test time via Postgres."""

import os
from contextlib import contextmanager

import psycopg
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "ai-bridge",
    json_response=True,
)

# Schema: users(id, username, mcp_key), posts(id, user_id, content, created_at),
#         direct_messages(id, from_user, to_user, content, read_at, created_at)
# Expect DATABASE_URL env (e.g. postgresql://user:pass@host:5432/dbname)

MAX_CONTENT_LENGTH = 10_000


@contextmanager
def get_connection():
    """Open a Postgres connection using DATABASE_URL. Caller must not hold it long."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    try:
        conn = psycopg.connect(url)
    except psycopg.Error as e:
        raise RuntimeError(f"Could not connect to database: {e}") from e
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- Bulletin board (posts) ---


@mcp.tool()
def bulletin_board_send(content: str, user_id: int | None = None) -> str:
    """Post text to the public bulletin board (posts table). Optional user_id links the post to a user; omit for anonymous. Returns a short confirmation."""
    if not content or not content.strip():
        return "Error: content cannot be empty."
    if len(content) > MAX_CONTENT_LENGTH:
        return (
            f"Error: content too long ({len(content)} chars, max {MAX_CONTENT_LENGTH})."
        )
    if user_id is not None and user_id < 1:
        return "Error: user_id must be a positive integer."
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO posts (user_id, content) VALUES (%s, %s) RETURNING id",
                    (user_id, content.strip()),
                )
                row = cur.fetchone()
                return f"Posted to bulletin board (id={row[0]})."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def bulletin_board_read(limit: int = 200) -> list[dict]:
    """Read recent posts from the public bulletin board. Optional limit (default 200, max 5000)."""
    limit = max(1, min(5000, limit))
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.user_id, p.content, p.created_at
                    FROM posts p
                    ORDER BY p.created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "user_id": r[1],
                "content": r[2],
                "created_at": str(r[3]),
            }
            for r in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]


# --- Private messages ---


@mcp.tool()
def private_message_send(from_user_id: int, to_user_id: int, content: str) -> str:
    """Send a private message from one user to another (user ids from users table). Returns a short confirmation."""
    if not content or not content.strip():
        return "Error: content cannot be empty."
    if len(content) > MAX_CONTENT_LENGTH:
        return (
            f"Error: content too long ({len(content)} chars, max {MAX_CONTENT_LENGTH})."
        )
    if from_user_id < 1:
        return "Error: from_user_id must be a positive integer."
    if to_user_id < 1:
        return "Error: to_user_id must be a positive integer."
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO direct_messages (from_user, to_user, content)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (from_user_id, to_user_id, content.strip()),
                )
                row = cur.fetchone()
                return f"Private message sent (id={row[0]})."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def private_message_read(to_user_id: int, limit: int = 50) -> list[dict]:
    """Read private messages addressed to the given user id (inbox). Optional limit (default 50, max 500)."""
    if to_user_id < 1:
        return [{"error": "to_user_id must be a positive integer."}]
    limit = max(1, min(500, limit))
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, from_user, to_user, content, read_at, created_at
                    FROM direct_messages
                    WHERE to_user = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (to_user_id, limit),
                )
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "from_user": r[1],
                "to_user": r[2],
                "content": r[3],
                "read_at": str(r[4]) if r[4] else None,
                "created_at": str(r[5]),
            }
            for r in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]


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

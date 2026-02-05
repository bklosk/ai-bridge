"""MCP server skeleton for ai-bridge."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "ai-bridge",
    json_response=True,
)


@mcp.tool()
def ping() -> str:
    """Respond with pong. Use to check that the server is running."""
    return "pong"


@mcp.resource("ai-bridge://status")
def get_status() -> str:
    """Server status resource."""
    return "ai-bridge MCP server is running"


@mcp.prompt()
def example_prompt(topic: str) -> str:
    """Generate a prompt for the given topic."""
    return f"Write a short response about: {topic}"


def main() -> None:
    """Run the MCP server. Uses stdio by default for IDE/CLI integration."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

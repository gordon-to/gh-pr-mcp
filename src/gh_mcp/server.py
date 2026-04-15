from .app import mcp
from .tools import git, gh  # noqa: F401 — imports trigger @tool registration


def main() -> None:
    mcp.run(transport="stdio")

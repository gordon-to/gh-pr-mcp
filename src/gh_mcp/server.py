from .app import mcp
from .tools import gh  # noqa: F401 — import triggers @tool registration


def main() -> None:
    mcp.run(transport="stdio")

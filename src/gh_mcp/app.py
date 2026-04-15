import functools
from mcp.server.fastmcp import FastMCP
from .run import CommandError

mcp = FastMCP(
    "gh-mcp",
    instructions=(
        "Tools for all git and GitHub CLI operations. "
        "Read-only tools (git_status, git_diff, git_log, git_branch_list, "
        "gh_pr_list, gh_issue_list, gh_run_list, gh_repo_view, gh_release_list) "
        "are always safe. "
        "Write tools that affect remotes or are destructive will ask for confirmation."
    ),
)


def tool(prefix_or_fn=None, *, name=None):
    """register a function as an MCP tool with CommandError wrapping.

    returns the original function unchanged so it can be called directly in tests.
    the MCP-registered wrapper catches CommandError and returns it as a string.

    usage:
        @tool("git")       # registers as "git_<fn.__name__>"
        @tool("gh")        # registers as "gh_<fn.__name__>"
        @tool              # registers using fn.__name__ directly
        @tool(name="x")    # registers with explicit name
    """
    if callable(prefix_or_fn):
        fn = prefix_or_fn
        return _register(fn, name or fn.__name__)
    prefix = prefix_or_fn

    def decorator(fn):
        tool_name = f"{prefix}_{fn.__name__}" if prefix else (name or fn.__name__)
        return _register(fn, tool_name)

    return decorator


def _register(fn, tool_name: str):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except CommandError as e:
            return f"error: {e}"

    wrapper.__name__ = tool_name
    wrapper.__qualname__ = tool_name
    mcp.tool(name=tool_name)(wrapper)
    return fn

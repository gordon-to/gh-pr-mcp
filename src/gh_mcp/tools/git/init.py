from ...app import tool
from ...run import _validate_ref, format_result, run


@tool("git")
def init(path: str, initial_branch: str = "main") -> str:
    """initialize a new git repository (git init)."""
    _validate_ref(initial_branch, "initial_branch")
    return format_result(
        run(["git", "init", "-b", initial_branch, path]),
        "git init",
    )

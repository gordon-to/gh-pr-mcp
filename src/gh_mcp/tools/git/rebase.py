from ...app import tool
from ...run import CommandError, _validate_ref, format_result, run


@tool("git")
def rebase(repo_path: str, onto: str, interactive: bool = False) -> str:
    """rebase current branch onto another (git rebase).

    interactive mode is not supported over stdio — use rebase_abort/continue instead.
    """
    if interactive:
        raise CommandError("interactive rebase is not supported in MCP mode; use non-interactive rebase")
    args = ["git", "rebase", _validate_ref(onto, "onto")]
    return format_result(run(args, cwd=repo_path), f"git rebase {onto}")


@tool("git")
def rebase_abort(repo_path: str = ".") -> str:
    """abort an in-progress rebase (git rebase --abort)."""
    return format_result(run(["git", "rebase", "--abort"], cwd=repo_path), "git rebase --abort")


@tool("git")
def rebase_continue(repo_path: str = ".") -> str:
    """continue a rebase after resolving conflicts (git rebase --continue)."""
    return format_result(run(["git", "rebase", "--continue"], cwd=repo_path), "git rebase --continue")

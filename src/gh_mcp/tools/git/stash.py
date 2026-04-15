from ...app import tool
from ...run import format_result, run, run_ok


@tool("git")
def stash_list(repo_path: str = ".") -> str:
    """list stash entries (git stash list)."""
    return format_result(run_ok(["git", "stash", "list"], cwd=repo_path), "git stash list")


@tool("git")
def stash_push(repo_path: str = ".", message: str = "", include_untracked: bool = True) -> str:
    """stash current changes (git stash push)."""
    args = ["git", "stash", "push"]
    if include_untracked:
        args.append("-u")
    if message:
        args.extend(["-m", message])
    return format_result(run(args, cwd=repo_path), "git stash push")


@tool("git")
def stash_pop(repo_path: str = ".", index: int = 0) -> str:
    """apply and drop a stash entry (git stash pop)."""
    args = ["git", "stash", "pop", f"stash@{{{index}}}"]
    return format_result(run(args, cwd=repo_path), "git stash pop")

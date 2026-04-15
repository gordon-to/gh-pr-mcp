from ...run import format_result, run_ok


def status(repo_path: str = ".") -> str:
    """show working tree status (git status)."""
    return format_result(run_ok(["git", "status"], cwd=repo_path), "git status")

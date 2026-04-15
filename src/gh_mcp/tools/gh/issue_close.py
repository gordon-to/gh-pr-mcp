from ...app import tool
from ...run import format_result, run
from ._api import _repo_args


@tool("gh")
def issue_close(issue: str | int, reason: str = "", repo: str = "", repo_path: str = ".") -> str:
    """close an issue (gh issue close).

    reason: 'completed', 'not planned', or '' (default).
    """
    args = ["gh", "issue", "close", str(issue)] + _repo_args(repo)
    if reason:
        args += ["--reason", reason]
    return format_result(run(args, cwd=repo_path), f"gh issue close {issue}")

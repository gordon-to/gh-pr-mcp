from ...app import tool
from ...run import CommandError, format_result, run
from ._api import _repo_args


@tool("gh")
def issue_comment(issue: str | int, body: str, repo: str = "", repo_path: str = ".") -> str:
    """add a comment to an issue (gh issue comment)."""
    if not body.strip():
        raise CommandError("comment body must not be empty")
    args = ["gh", "issue", "comment", str(issue), "--body", body] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh issue comment {issue}")

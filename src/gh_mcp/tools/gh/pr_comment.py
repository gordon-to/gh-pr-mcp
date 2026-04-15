from ...app import tool
from ...run import CommandError, format_result, run
from ._api import _repo_args


@tool("gh")
def pr_comment(pr: str | int, body: str, repo: str = "", repo_path: str = ".") -> str:
    """add a comment to a pull request (gh pr comment)."""
    if not body.strip():
        raise CommandError("comment body must not be empty")
    args = ["gh", "pr", "comment", str(pr), "--body", body] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh pr comment {pr}")

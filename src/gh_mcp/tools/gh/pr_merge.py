from ...run import CommandError, format_result, run
from ._api import _repo_args


def pr_merge(
    pr: str | int,
    method: str = "merge",
    delete_branch: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """merge a pull request (gh pr merge) — WRITES TO REMOTE.

    method: 'merge', 'squash', or 'rebase'.
    delete_branch: delete head branch after merge (default True).
    """
    if method not in ("merge", "squash", "rebase"):
        raise CommandError(f"method must be 'merge', 'squash', or 'rebase', got {method!r}")
    args = ["gh", "pr", "merge", str(pr), f"--{method}"] + _repo_args(repo)
    if delete_branch:
        args.append("--delete-branch")
    return format_result(run(args, cwd=repo_path), f"gh pr merge {pr}")


def pr_close(pr: str | int, comment: str = "", repo: str = "", repo_path: str = ".") -> str:
    """close a pull request without merging (gh pr close)."""
    args = ["gh", "pr", "close", str(pr)] + _repo_args(repo)
    if comment:
        args += ["--comment", comment]
    return format_result(run(args, cwd=repo_path), f"gh pr close {pr}")

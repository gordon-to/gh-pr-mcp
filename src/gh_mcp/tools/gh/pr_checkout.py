from ...app import tool
from ...run import format_result, run
from ._api import _repo_args


@tool("gh")
def pr_checkout(pr: str | int, repo: str = "", repo_path: str = ".") -> str:
    """check out a PR's branch locally (gh pr checkout)."""
    args = ["gh", "pr", "checkout", str(pr)] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh pr checkout {pr}")

from ...run import format_result, run
from ._api import _repo_args


def run_rerun(run_id: str | int, failed_only: bool = True, repo: str = "", repo_path: str = ".") -> str:
    """rerun a workflow run (gh run rerun). gh:write."""
    args = ["gh", "run", "rerun", str(run_id)] + _repo_args(repo)
    if failed_only:
        args.append("--failed")
    return format_result(run(args, cwd=repo_path), f"gh run rerun {run_id}")


def run_cancel(run_id: str | int, repo: str = "", repo_path: str = ".") -> str:
    """cancel an in-progress workflow run (gh run cancel). gh:write."""
    args = ["gh", "run", "cancel", str(run_id)] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh run cancel {run_id}")

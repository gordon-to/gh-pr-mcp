from ...app import tool
from ...run import _validate_ref, format_result, run


@tool("git")
def pull(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    rebase: bool = False,
) -> str:
    """pull commits from remote (git pull). git:remote-read — safe to always-allow."""
    args = ["git", "pull", _validate_ref(remote, "remote")]
    if branch:
        args.append(_validate_ref(branch, "branch"))
    if rebase:
        args.append("--rebase")
    return format_result(run(args, cwd=repo_path), "git pull")

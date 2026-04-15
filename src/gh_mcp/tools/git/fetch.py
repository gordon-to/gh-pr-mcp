from ...app import tool
from ...run import _validate_ref, format_result, run


@tool("git")
def fetch(repo_path: str = ".", remote: str = "origin", prune: bool = True) -> str:
    """fetch from remote without merging (git fetch). git:remote-read — safe to always-allow."""
    args = ["git", "fetch", _validate_ref(remote, "remote")]
    if prune:
        args.append("--prune")
    return format_result(run(args, cwd=repo_path), "git fetch")

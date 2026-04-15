from ...app import tool
from ...run import _validate_ref, format_result, run


@tool("git")
def push(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    set_upstream: bool = False,
    tags: bool = False,
) -> str:
    """push commits to remote (git push). git:remote-write — ask before running.

    branch: local branch to push (default: current branch).
    set_upstream: set tracking (-u flag).
    tags: push all tags.
    """
    args = ["git", "push", _validate_ref(remote, "remote")]
    if branch:
        args.append(_validate_ref(branch, "branch"))
    if set_upstream:
        args.append("-u")
    if tags:
        args.append("--tags")
    return format_result(run(args, cwd=repo_path), "git push")


@tool("git")
def push_force(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    with_lease: bool = True,
) -> str:
    """force-push to remote — rewrites remote history. git:remote-destructive — ask/block.

    with_lease: use --force-with-lease (safer, refuses if remote has diverged — default True).
    """
    args = ["git", "push", _validate_ref(remote, "remote")]
    if branch:
        args.append(_validate_ref(branch, "branch"))
    args.append("--force-with-lease" if with_lease else "--force")
    return format_result(run(args, cwd=repo_path), "git push --force")

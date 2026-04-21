from ...app import tool
from ...run import CommandError, _validate_ref, format_result, run


@tool("git")
def rebase(
    repo_path: str,
    onto: str,
    upstream: str | None = None,
    branch: str | None = None,
    interactive: bool = False,
) -> str:
    """rebase current branch onto another (git rebase).

    onto: target ref. when upstream is None, this is the upstream argument
        (plain `git rebase <onto>`); when upstream is set, it becomes the
        --onto newbase (`git rebase --onto <onto> <upstream> [<branch>]`).
    upstream: if set, switches to three-point rebase mode. commits reachable
        from HEAD (or branch) but not from upstream are replayed onto onto.
    branch: optional branch to check out before rebasing. only meaningful
        with upstream.
    interactive mode is not supported over stdio — use rebase_abort/continue instead.
    """
    if interactive:
        raise CommandError("interactive rebase is not supported in MCP mode; use non-interactive rebase")
    if branch is not None and upstream is None:
        raise CommandError("branch requires upstream to be set (three-point rebase)")

    args = ["git", "rebase"]
    if upstream is not None:
        args += ["--onto", _validate_ref(onto, "onto"), _validate_ref(upstream, "upstream")]
        if branch is not None:
            args.append(_validate_ref(branch, "branch"))
        label = f"git rebase --onto {onto} {upstream}" + (f" {branch}" if branch else "")
    else:
        args.append(_validate_ref(onto, "onto"))
        label = f"git rebase {onto}"
    return format_result(run(args, cwd=repo_path), label)


@tool("git")
def rebase_abort(repo_path: str = ".") -> str:
    """abort an in-progress rebase (git rebase --abort)."""
    return format_result(run(["git", "rebase", "--abort"], cwd=repo_path), "git rebase --abort")


@tool("git")
def rebase_continue(repo_path: str = ".") -> str:
    """continue a rebase after resolving conflicts (git rebase --continue)."""
    return format_result(run(["git", "rebase", "--continue"], cwd=repo_path), "git rebase --continue")

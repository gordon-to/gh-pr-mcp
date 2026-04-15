from ...run import _validate_path, _validate_ref, format_result, run, run_ok


def worktree_list(repo_path: str = ".") -> str:
    """list worktrees (git worktree list)."""
    return format_result(run_ok(["git", "worktree", "list", "--porcelain"], cwd=repo_path), "git worktree list")


def worktree_add(repo_path: str, path: str, branch: str, create_branch: bool = True) -> str:
    """add a new worktree (git worktree add)."""
    _validate_path(path)
    _validate_ref(branch, "branch")
    args = ["git", "worktree", "add"]
    if create_branch:
        args.extend(["-b", branch])
    args.extend([path, branch if not create_branch else "HEAD"])
    return format_result(run(args, cwd=repo_path), "git worktree add")


def worktree_remove(repo_path: str, path: str, force: bool = False) -> str:
    """remove a worktree (git worktree remove)."""
    args = ["git", "worktree", "remove"]
    if force:
        args.append("--force")
    args.append(_validate_path(path))
    return format_result(run(args, cwd=repo_path), "git worktree remove")

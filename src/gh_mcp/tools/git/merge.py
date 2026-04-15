from ...run import _validate_ref, format_result, run


def merge(repo_path: str, branch: str, no_ff: bool = False, squash: bool = False) -> str:
    """merge a branch into current HEAD (git merge). git:integrate."""
    args = ["git", "merge", _validate_ref(branch, "branch")]
    if no_ff:
        args.append("--no-ff")
    if squash:
        args.append("--squash")
    return format_result(run(args, cwd=repo_path), f"git merge {branch}")

from ...run import CommandError, format_result, run


def clean(repo_path: str, directories: bool = False, force: bool = True, dry_run: bool = False) -> str:
    """remove untracked files — DESTRUCTIVE (git clean).

    dry_run: show what would be removed without deleting.
    CAUTION: permanently deletes untracked files.
    """
    args = ["git", "clean"]
    if dry_run:
        args.append("-n")
    elif force:
        args.append("-f")
    else:
        raise CommandError("clean requires force=True or dry_run=True")
    if directories:
        args.append("-d")
    return format_result(run(args, cwd=repo_path), "git clean")

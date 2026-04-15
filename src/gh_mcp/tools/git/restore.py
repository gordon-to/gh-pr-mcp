from ...run import CommandError, _validate_path, format_result, run


def restore(repo_path: str, paths: list[str], staged: bool = False) -> str:
    """discard changes to files — DESTRUCTIVE (git restore).

    staged: restore staged changes back to working tree.
    CAUTION: discards uncommitted changes permanently.
    """
    if not paths:
        raise CommandError("paths must not be empty")
    args = ["git", "restore"]
    if staged:
        args.append("--staged")
    args.extend(["--"] + [_validate_path(p) for p in paths])
    return format_result(run(args, cwd=repo_path), "git restore")

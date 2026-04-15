from ...run import CommandError, format_result, run


def commit(repo_path: str, message: str, allow_empty: bool = False) -> str:
    """create a commit (git commit).

    message: commit message.
    allow_empty: allow commits with no changes staged.
    """
    if not message.strip():
        raise CommandError("commit message must not be empty")
    args = ["git", "commit", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    return format_result(run(args, cwd=repo_path), "git commit")

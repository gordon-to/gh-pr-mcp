from ...app import tool
from ...run import CommandError, _validate_path, format_result, run, run_ok


@tool("git")
def add(repo_path: str, paths: list[str]) -> str:
    """stage files (git add).

    paths: list of files/directories to stage. Use ['.'] for all changes.
    """
    if not paths:
        raise CommandError("paths must not be empty")
    validated = [_validate_path(p) for p in paths]
    run(["git", "add", "--"] + validated, cwd=repo_path)
    return format_result(
        run_ok(["git", "status", "--short", "--"] + validated, cwd=repo_path),
        "git status",
    )

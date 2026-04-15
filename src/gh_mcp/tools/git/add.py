from ...app import tool
from ...run import CommandError, _validate_path, run
from .status import status


@tool("git")
def add(repo_path: str, paths: list[str]) -> str:
    """stage files (git add).

    paths: list of files/directories to stage. Use ['.'] for all changes.
    """
    if not paths:
        raise CommandError("paths must not be empty")
    validated = [_validate_path(p) for p in paths]
    args = ["git", "add", "--"] + validated
    run(args, cwd=repo_path)
    return status(repo_path)

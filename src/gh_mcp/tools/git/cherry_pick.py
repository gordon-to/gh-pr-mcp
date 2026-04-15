from ...app import tool
from ...run import CommandError, _validate_ref, format_result, run


@tool("git")
def cherry_pick(repo_path: str, commits: list[str]) -> str:
    """apply commits onto current HEAD (git cherry-pick)."""
    if not commits:
        raise CommandError("commits list must not be empty")
    validated = [_validate_ref(c, "commit") for c in commits]
    return format_result(run(["git", "cherry-pick"] + validated, cwd=repo_path), "git cherry-pick")

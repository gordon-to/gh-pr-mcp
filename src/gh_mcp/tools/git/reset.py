from ...app import tool
from ...run import CommandError, _validate_ref, format_result, run


@tool("git")
def reset(repo_path: str, ref: str = "HEAD", mode: str = "mixed") -> str:
    """reset HEAD to a ref. mode='hard' discards all uncommitted changes. git:local-destructive.

    mode: 'soft' (keep staged), 'mixed' (unstage, keep files), 'hard' (discard all).
    """
    if mode not in ("soft", "mixed", "hard"):
        raise CommandError(f"mode must be 'soft', 'mixed', or 'hard', got {mode!r}")
    return format_result(
        run(["git", "reset", f"--{mode}", _validate_ref(ref)], cwd=repo_path),
        f"git reset --{mode} {ref}",
    )

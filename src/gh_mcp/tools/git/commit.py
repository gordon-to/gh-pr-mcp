from ...app import tool
from ...run import CommandError, format_result, run


@tool("git")
def commit(
    repo_path: str,
    message: str,
    allow_empty: bool = False,
    amend: bool = False,
) -> str:
    """create a commit (git commit).

    message: commit message. with amend=True this replaces HEAD's message.
    allow_empty: allow commits with no changes staged.
    amend: replace HEAD instead of creating a new commit (git commit --amend).
        staged changes are folded into HEAD. works with nothing staged too —
        e.g. for rewording HEAD's message.
    """
    if not message.strip():
        raise CommandError("commit message must not be empty")
    args = ["git", "commit", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    if amend:
        args.append("--amend")
    label = "git commit --amend" if amend else "git commit"
    return format_result(run(args, cwd=repo_path), label)

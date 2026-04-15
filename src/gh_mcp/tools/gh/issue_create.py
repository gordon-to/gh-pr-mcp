from ...app import tool
from ...run import CommandError, format_result, run
from ._api import _repo_args


@tool("gh")
def issue_create(
    title: str,
    body: str = "",
    label: list[str] | None = None,
    assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """create a new issue (gh issue create)."""
    if not title.strip():
        raise CommandError("issue title must not be empty")
    args = ["gh", "issue", "create", "--title", title] + _repo_args(repo)
    args += ["--body", body or ""]
    for lbl in (label or []):
        args += ["--label", lbl]
    for a in (assignee or []):
        args += ["--assignee", a]
    return format_result(run(args, cwd=repo_path), "gh issue create")

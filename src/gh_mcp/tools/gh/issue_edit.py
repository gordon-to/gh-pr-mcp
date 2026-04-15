from ...run import format_result, run
from ._api import _repo_args


def issue_edit(
    issue: str | int,
    title: str = "",
    body: str = "",
    add_label: list[str] | None = None,
    remove_label: list[str] | None = None,
    add_assignee: list[str] | None = None,
    remove_assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """edit an issue's metadata (gh issue edit)."""
    args = ["gh", "issue", "edit", str(issue)] + _repo_args(repo)
    if title:
        args += ["--title", title]
    if body:
        args += ["--body", body]
    for lbl in (add_label or []):
        args += ["--add-label", lbl]
    for lbl in (remove_label or []):
        args += ["--remove-label", lbl]
    for a in (add_assignee or []):
        args += ["--add-assignee", a]
    for a in (remove_assignee or []):
        args += ["--remove-assignee", a]
    return format_result(run(args, cwd=repo_path), f"gh issue edit {issue}")

from ...app import tool
from ...run import _validate_ref, format_result, run
from ._api import _repo_args


@tool("gh")
def pr_edit(
    pr: str | int,
    title: str = "",
    body: str = "",
    base: str = "",
    add_label: list[str] | None = None,
    remove_label: list[str] | None = None,
    add_reviewer: list[str] | None = None,
    remove_reviewer: list[str] | None = None,
    add_assignee: list[str] | None = None,
    remove_assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """edit a pull request's metadata (gh pr edit).

    use body to replace the PR description. omit fields to leave unchanged.
    """
    args = ["gh", "pr", "edit", str(pr)] + _repo_args(repo)
    if title:
        args += ["--title", title]
    if body:
        args += ["--body", body]
    if base:
        args += ["--base", _validate_ref(base, "base")]
    for lbl in (add_label or []):
        args += ["--add-label", lbl]
    for lbl in (remove_label or []):
        args += ["--remove-label", lbl]
    for r in (add_reviewer or []):
        args += ["--add-reviewer", r]
    for r in (remove_reviewer or []):
        args += ["--remove-reviewer", r]
    for a in (add_assignee or []):
        args += ["--add-assignee", a]
    for a in (remove_assignee or []):
        args += ["--remove-assignee", a]
    return format_result(run(args, cwd=repo_path), f"gh pr edit {pr}")

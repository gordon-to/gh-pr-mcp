from ...app import tool
from ...run import _validate_ref, format_result, run
from ._api import _repo_args


@tool("gh")
def pr_create(
    repo_path: str = ".",
    repo: str = "",
    title: str = "",
    body: str = "",
    base: str = "main",
    draft: bool = False,
    reviewer: list[str] | None = None,
    label: list[str] | None = None,
) -> str:
    """create a pull request (gh pr create).

    title and body default to the commit message if omitted.
    reviewer: list of GitHub usernames to request review from.
    """
    args = ["gh", "pr", "create", "--base", _validate_ref(base, "base")]
    args += _repo_args(repo)
    if title:
        args += ["--title", title]
    else:
        args.append("--fill")
    if body:
        args += ["--body", body]
    elif not title:
        pass  # --fill covers body too
    else:
        args += ["--body", ""]
    if draft:
        args.append("--draft")
    for r in (reviewer or []):
        args += ["--reviewer", r]
    for lbl in (label or []):
        args += ["--label", lbl]
    return format_result(run(args, cwd=repo_path), "gh pr create")

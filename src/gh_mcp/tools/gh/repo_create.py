from ...app import tool
from ...run import CommandError, format_result, run


@tool("gh")
def repo_create(
    name: str,
    private: bool = True,
    description: str = "",
    clone: bool = False,
) -> str:
    """create a new GitHub repository (gh repo create)."""
    if not name.strip():
        raise CommandError("repo name must not be empty")
    args = ["gh", "repo", "create", name]
    args.append("--private" if private else "--public")
    if description:
        args += ["--description", description]
    if clone:
        args.append("--clone")
    return format_result(run(args), "gh repo create")

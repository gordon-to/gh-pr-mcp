from ...app import tool
from ...run import _validate_ref, format_result, run, run_ok


@tool("git")
def branch_list(repo_path: str = ".", all_branches: bool = False) -> str:
    """list branches (git branch -v[a])."""
    args = ["git", "branch", "-v"]
    if all_branches:
        args.append("-a")
    return format_result(run_ok(args, cwd=repo_path), "git branch")


@tool("git")
def branch_create(repo_path: str, name: str, start_point: str = "", checkout: bool = True) -> str:
    """create a branch (git switch -c / git branch).

    name: new branch name.
    start_point: base ref (default: current HEAD).
    checkout: switch to new branch immediately (default True).
    """
    _validate_ref(name, "branch name")
    if checkout:
        args = ["git", "switch", "-c", name]
    else:
        args = ["git", "branch", name]
    if start_point:
        args.append(_validate_ref(start_point, "start_point"))
    return format_result(run(args, cwd=repo_path), f"git branch create {name}")


@tool("git")
def branch_delete(repo_path: str, name: str, force: bool = False, remote: str = "") -> str:
    """delete a branch (git branch -d / git push --delete).

    force: use -D to delete unmerged branches.
    remote: if given, delete the remote-tracking branch too.
    """
    _validate_ref(name, "branch name")
    flag = "-D" if force else "-d"
    out = run(["git", "branch", flag, name], cwd=repo_path)
    if remote:
        _validate_ref(remote, "remote")
        out += "\n" + run(["git", "push", remote, "--delete", name], cwd=repo_path)
    return format_result(out, f"git branch delete {name}")


@tool("git")
def checkout(repo_path: str, ref: str) -> str:
    """switch to a branch or commit (git switch / git checkout).

    ref: branch name or commit hash to check out.
    """
    return format_result(
        run(["git", "switch", _validate_ref(ref)], cwd=repo_path),
        f"git switch {ref}",
    )

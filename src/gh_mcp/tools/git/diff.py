from ...run import _validate_path, _validate_ref, format_result, run_ok


def diff(
    repo_path: str = ".",
    staged: bool = False,
    path: str = "",
    commit: str = "",
) -> str:
    """show changes between working tree, index, or commits (git diff).

    staged=True shows only staged changes.
    commit shows diff against that ref (e.g. 'HEAD~1', 'main').
    path restricts to a file or directory.
    """
    args = ["git", "diff"]
    if staged:
        args.append("--staged")
    if commit:
        args.append(_validate_ref(commit, "commit"))
    args.append("--")
    if path:
        args.append(_validate_path(path))
    return format_result(run_ok(args, cwd=repo_path), "git diff")

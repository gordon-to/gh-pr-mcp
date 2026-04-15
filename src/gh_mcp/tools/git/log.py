from ...run import _validate_path, _validate_ref, format_result, run_ok


def log(
    repo_path: str = ".",
    n: int = 20,
    branch: str = "",
    oneline: bool = True,
    path: str = "",
) -> str:
    """show commit history (git log).

    n: max number of commits (default 20).
    branch: show history of a specific branch.
    oneline: compact one-line format (default True).
    path: restrict to commits touching this file/dir.
    """
    args = ["git", "log", f"-{n}"]
    if oneline:
        args.append("--oneline")
    else:
        args.extend(["--format=%H %an %ar%n  %s"])
    if branch:
        args.append(_validate_ref(branch, "branch"))
    if path:
        args.extend(["--", _validate_path(path)])
    return format_result(run_ok(args, cwd=repo_path), "git log")


def show(repo_path: str = ".", ref: str = "HEAD", path: str = "") -> str:
    """show details of a commit (git show)."""
    args = ["git", "show", _validate_ref(ref)]
    if path:
        args.extend(["--", _validate_path(path)])
    return format_result(run_ok(args, cwd=repo_path), f"git show {ref}")


def blame(repo_path: str, path: str, ref: str = "HEAD") -> str:
    """show line-by-line authorship (git blame)."""
    args = ["git", "blame", _validate_ref(ref), "--", _validate_path(path)]
    return format_result(run_ok(args, cwd=repo_path), f"git blame {path}")

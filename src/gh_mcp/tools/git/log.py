from ...app import tool
from ...run import _validate_path, _validate_ref, format_result, run_ok


@tool("git")
def log(
    repo_path: str = ".",
    n: int = 20,
    branch: str = "",
    base: str = "",
    oneline: bool = True,
    graph: bool = False,
    path: str = "",
) -> str:
    """show commit history (git log).

    n: max number of commits (default 20).
    branch: show history of a specific branch or commit.
    base: if set, show range base..branch (or base..HEAD). use to see
          only the commits on a feature branch, e.g. base="main".
    oneline: compact one-line format (default True).
    graph: show branch/merge graph (--graph).
    path: restrict to commits touching this file/dir.
    """
    args = ["git", "log", f"-{n}"]
    if oneline:
        args.append("--oneline")
    else:
        args.extend(["--format=%H %an %ar%n  %s"])
    if graph:
        args.append("--graph")
    if base:
        validated_base = _validate_ref(base, "base")
        end = _validate_ref(branch, "branch") if branch else "HEAD"
        args.append(f"{validated_base}..{end}")
    elif branch:
        args.append(_validate_ref(branch, "branch"))
    if path:
        args.extend(["--", _validate_path(path)])
    return format_result(run_ok(args, cwd=repo_path), "git log")


@tool("git")
def show(repo_path: str = ".", ref: str = "HEAD", path: str = "") -> str:
    """show details of a commit (git show)."""
    args = ["git", "show", _validate_ref(ref)]
    if path:
        args.extend(["--", _validate_path(path)])
    return format_result(run_ok(args, cwd=repo_path), f"git show {ref}")


@tool("git")
def blame(repo_path: str, path: str, ref: str = "HEAD") -> str:
    """show line-by-line authorship (git blame)."""
    args = ["git", "blame", _validate_ref(ref), "--", _validate_path(path)]
    return format_result(run_ok(args, cwd=repo_path), f"git blame {path}")

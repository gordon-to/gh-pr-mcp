from ...app import tool
from ...run import CommandError, _validate_ref, format_result, run, run_ok


@tool("git")
def remote_list(repo_path: str = ".") -> str:
    """list remotes (git remote -v)."""
    return format_result(run_ok(["git", "remote", "-v"], cwd=repo_path), "git remote -v")


@tool("git")
def remote_add(repo_path: str, name: str, url: str) -> str:
    """add a remote (git remote add)."""
    if any(c in url for c in '\x00|;&`$(){}[]<>\\! \t\n'):
        raise CommandError(f"invalid remote URL: {url!r}")
    _validate_ref(name, "remote name")
    return format_result(run(["git", "remote", "add", name, url], cwd=repo_path), "git remote add")

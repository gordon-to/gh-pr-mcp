from ...app import tool
from ...run import _validate_ref, format_result, run, run_ok


@tool("git")
def tag_list(repo_path: str = ".", pattern: str = "") -> str:
    """list tags (git tag -l)."""
    args = ["git", "tag", "-l", "--sort=-version:refname"]
    if pattern:
        args.append(_validate_ref(pattern, "pattern"))
    return format_result(run_ok(args, cwd=repo_path), "git tag -l")


@tool("git")
def tag_create(repo_path: str, name: str, ref: str = "HEAD", message: str = "") -> str:
    """create a tag (git tag)."""
    _validate_ref(name, "tag name")
    args = ["git", "tag"]
    if message:
        args.extend(["-a", name, "-m", message])
    else:
        args.append(name)
    args.append(_validate_ref(ref))
    return format_result(run(args, cwd=repo_path), f"git tag {name}")

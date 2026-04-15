from ...run import CommandError, _validate_path, _validate_ref, format_result, run


def clone(url: str, destination: str = "", branch: str = "", depth: int = 0) -> str:
    """clone a remote repository (git clone). git:remote-read."""
    if any(c in url for c in '\x00|;&`$(){}[]<>\\! \t\n'):
        raise CommandError(f"invalid clone URL: {url!r}")
    args = ["git", "clone", url]
    if destination:
        args.append(_validate_path(destination))
    if branch:
        args.extend(["-b", _validate_ref(branch, "branch")])
    if depth > 0:
        args.extend(["--depth", str(depth)])
    return format_result(run(args), "git clone")

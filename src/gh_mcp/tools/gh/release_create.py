from ...run import _validate_ref, format_result, run
from ._api import _repo_args


def release_create(
    tag: str,
    title: str = "",
    notes: str = "",
    draft: bool = False,
    prerelease: bool = False,
    generate_notes: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """create a release (gh release create) — WRITES TO REMOTE."""
    _validate_ref(tag, "tag")
    args = ["gh", "release", "create", tag] + _repo_args(repo)
    if title:
        args += ["--title", title]
    if notes:
        args += ["--notes", notes]
    elif generate_notes:
        args.append("--generate-notes")
    if draft:
        args.append("--draft")
    if prerelease:
        args.append("--prerelease")
    return format_result(run(args, cwd=repo_path), f"gh release create {tag}")

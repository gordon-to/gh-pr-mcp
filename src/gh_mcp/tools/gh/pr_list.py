import json

from ...app import tool
from ...run import _validate_ref, format_result, run_ok
from ._api import _repo_args


@tool("gh")
def pr_list(
    repo: str = "",
    state: str = "open",
    author: str = "",
    base: str = "",
    label: str = "",
    limit: int = 30,
    repo_path: str = "",
) -> str:
    """list pull requests (gh pr list).

    state: 'open', 'closed', 'merged', or 'all'.
    repo_path: optional local checkout to resolve the repo from. Defaults to the current project directory (where Claude Code is running), so you rarely need to set it. Set it only to target a different checkout.
    """
    args = [
        "gh",
        "pr",
        "list",
        "--state",
        state,
        "--limit",
        str(limit),
        "--json",
        "number,title,author,state,headRefName,updatedAt,isDraft,mergeable,mergeStateStatus",
    ]
    args += _repo_args(repo)
    if author:
        args += ["--author", author]
    if base:
        args += ["--base", _validate_ref(base, "base")]
    if label:
        args += ["--label", label]
    raw = run_ok(args, cwd=repo_path)
    try:
        prs = json.loads(raw)
        if not prs:
            return "no pull requests found"
        lines = []
        for pr in prs:
            draft = " [DRAFT]" if pr.get("isDraft") else ""
            mergeable = pr.get("mergeable") or "UNKNOWN"
            merge_state = pr.get("mergeStateStatus") or "UNKNOWN"
            lines.append(
                f"#{pr['number']} {pr['title']}{draft}\n"
                f"  branch: {pr['headRefName']}  author: {pr['author']['login']}  updated: {pr['updatedAt'][:10]}\n"
                f"  mergeable: {mergeable}  state: {merge_state}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh pr list")

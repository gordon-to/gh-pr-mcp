import json

from ...run import format_result, run_ok
from ._api import _repo_args


def repo_view(repo: str = "") -> str:
    """view repository info (gh repo view)."""
    args = ["gh", "repo", "view", "--json",
            "name,description,defaultBranchRef,isPrivate,stargazerCount,forkCount,openIssues,url"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        d = json.loads(raw)
        lines = [
            f"{d['name']}  {'[private]' if d['isPrivate'] else '[public]'}",
            f"url: {d['url']}",
            f"default branch: {d['defaultBranchRef']['name']}",
            f"stars: {d['stargazerCount']}  forks: {d['forkCount']}  open issues: {len(d.get('openIssues', []))}",
        ]
        if d.get("description"):
            lines.append(f"description: {d['description']}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh repo view")

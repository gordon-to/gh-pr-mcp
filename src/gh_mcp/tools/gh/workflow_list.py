import json

from ...run import format_result, run_ok
from ._api import _repo_args


def workflow_list(repo: str = "", repo_path: str = ".") -> str:
    """list available workflows in the repository (gh workflow list). gh:read."""
    args = ["gh", "workflow", "list", "--json", "id,name,state,path"] + _repo_args(repo)
    raw = run_ok(args, cwd=repo_path)
    try:
        workflows = json.loads(raw)
        if not workflows:
            return "no workflows found"
        lines = []
        for w in workflows:
            lines.append(f"{w['name']}  [{w['state']}]\n  id: {w['id']}  path: {w['path']}")
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh workflow list")

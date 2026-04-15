import json

from ...app import tool
from ...run import _validate_ref, format_result, run_ok
from ._api import _repo_args


@tool("gh")
def run_list(
    repo: str = "",
    workflow: str = "",
    branch: str = "",
    status: str = "",
    limit: int = 20,
    repo_path: str = ".",
) -> str:
    """list workflow runs (gh run list)."""
    args = ["gh", "run", "list", "--limit", str(limit), "--json",
            "databaseId,name,status,conclusion,headBranch,event,startedAt"]
    args += _repo_args(repo)
    if workflow:
        args += ["--workflow", workflow]
    if branch:
        args += ["--branch", _validate_ref(branch, "branch")]
    if status:
        args += ["--status", status]
    raw = run_ok(args, cwd=repo_path)
    try:
        runs = json.loads(raw)
        if not runs:
            return "no workflow runs found"
        lines = []
        for r in runs:
            conclusion = r.get("conclusion") or r.get("status", "")
            lines.append(
                f"#{r['databaseId']} {r['name']}  [{conclusion}]\n"
                f"  branch: {r['headBranch']}  event: {r['event']}  started: {r.get('startedAt', '')[:16]}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh run list")

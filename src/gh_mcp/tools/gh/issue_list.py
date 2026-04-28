import json

from ...app import tool
from ...run import format_result, run_ok
from ._api import _repo_args


@tool("gh")
def issue_list(
    repo: str = "",
    state: str = "open",
    assignee: str = "",
    label: str = "",
    limit: int = 30,
    repo_path: str = ".",
) -> str:
    """list issues (gh issue list)."""
    args = ["gh", "issue", "list", "--state", state, "--limit", str(limit),
            "--json", "number,title,author,state,labels,assignees,updatedAt"]
    args += _repo_args(repo)
    if assignee:
        args += ["--assignee", assignee]
    if label:
        args += ["--label", label]
    raw = run_ok(args, cwd=repo_path)
    try:
        issues = json.loads(raw)
        if not issues:
            return "no issues found"
        lines = []
        for issue in issues:
            labels = ", ".join(lbl["name"] for lbl in issue.get("labels", []))
            label_str = f"  labels: {labels}" if labels else ""
            lines.append(
                f"#{issue['number']} {issue['title']}\n"
                f"  author: {issue['author']['login']}  updated: {issue['updatedAt'][:10]}{label_str}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh issue list")

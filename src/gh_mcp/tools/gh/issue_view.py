import json

from ...app import tool
from ...run import format_result, run_ok
from ._api import _repo_args


@tool("gh")
def issue_view(issue: str | int, repo: str = "") -> str:
    """view issue details and comments (gh issue view)."""
    args = ["gh", "issue", "view", str(issue), "--json",
            "number,title,author,state,body,labels,assignees,comments"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        d = json.loads(raw)
        lines = [
            f"Issue #{d['number']}: {d['title']}",
            f"state: {d['state']}  author: {d['author']['login']}",
        ]
        if d.get("labels"):
            lines.append("labels: " + ", ".join(lbl["name"] for lbl in d["labels"]))
        if d.get("body"):
            lines.append(f"\n{d['body']}")
        if d.get("comments"):
            lines.append("\n--- comments ---")
            for c in d["comments"]:
                lines.append(f"\n{c['author']['login']}:\n{c['body'][:500]}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh issue view {issue}")

import json

from ...app import tool
from ...run import CommandError, format_result, run_ok
from ._api import _api_repo, _gh_api_get, _repo_args


@tool("gh")
def pr_view(pr: str | int, repo: str = "") -> str:
    """view pull request details including description and comments (gh pr view).

    pr: PR number or branch name.
    """
    args = ["gh", "pr", "view", str(pr), "--json",
            "number,title,author,state,body,baseRefName,headRefName,reviews,comments,isDraft,mergeable,statusCheckRollup"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        d = json.loads(raw)
        lines = [
            f"PR #{d['number']}: {d['title']}",
            f"state: {d['state']}  base: {d['baseRefName']} ← {d['headRefName']}  author: {d['author']['login']}",
        ]
        if d.get("isDraft"):
            lines.append("DRAFT")
        if d.get("body"):
            lines.append(f"\n{d['body']}")
        if d.get("reviews"):
            lines.append("\n--- reviews ---")
            for r in d["reviews"]:
                lines.append(f"  {r['author']['login']}: {r['state']}")
        if d.get("comments"):
            lines.append("\n--- comments ---")
            for c in d["comments"]:
                lines.append(f"  {c['author']['login']}: {c['body'][:200]}")
        if d.get("statusCheckRollup"):
            lines.append("\n--- checks ---")
            for check in d["statusCheckRollup"]:
                name = check.get("name") or check.get("context", "")
                conclusion = check.get("conclusion") or check.get("state", "")
                lines.append(f"  {name}: {conclusion}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh pr view {pr}")


@tool("gh")
def pr_diff(pr: str | int, repo: str = "") -> str:
    """show the diff for a pull request (gh pr diff)."""
    args = ["gh", "pr", "diff", str(pr)] + _repo_args(repo)
    return format_result(run_ok(args), f"gh pr diff {pr}")


@tool("gh")
def pr_checks(pr: str | int, repo: str = "") -> str:
    """show CI check status for a pull request (gh pr checks)."""
    args = ["gh", "pr", "checks", str(pr)] + _repo_args(repo)
    return format_result(run_ok(args), f"gh pr checks {pr}")


def _classify_author(user: dict) -> dict:
    return {
        "login": user.get("login", ""),
        "type": "bot" if user.get("type") == "Bot" else "human",
    }


@tool("gh")
def pr_review_threads(
    pr: str | int,
    repo: str = "",
    kind: str = "",
) -> str:
    """fetch inline review comment threads on a PR, structured for agent use.

    Returns JSON with a 'threads' list and a 'summary'. Each thread:
      thread_id  — pass directly to gh_pr_reply_comment to reply
      file, line — where the comment was placed in the diff
      outdated   — true when the commented line no longer exists in the current diff
      author     — {login, type} where type is 'human' or 'bot'
      body       — root comment text
      replies    — [{id, author, body}] in chronological order

    kind: filter results — 'bot', 'human', 'outdated', 'active'. Empty returns all.

    typical workflow:
      1. pr_review_threads(pr="5", kind="human")  → see what needs addressing
      2. pr_reply_comment(pr="5", comment_id=<thread_id>, body="fixed in abc123")
    """
    if kind and kind not in ("bot", "human", "outdated", "active"):
        raise CommandError(f"unknown kind {kind!r}: use 'bot', 'human', 'outdated', or 'active'")

    endpoint = f"repos/{_api_repo(repo)}/pulls/{pr}/comments?per_page=100"
    comments: list[dict] = json.loads(_gh_api_get(endpoint))

    roots: dict[int, dict] = {}
    children: dict[int, list[dict]] = {}
    for c in comments:
        cid = c["id"]
        parent = c.get("in_reply_to_id")
        if parent is None:
            roots[cid] = c
            children.setdefault(cid, [])
        else:
            children.setdefault(parent, []).append(c)

    threads = []
    for cid, root in roots.items():
        # position is null when the line the comment was on is no longer in the diff
        outdated = root.get("position") is None
        threads.append({
            "thread_id": cid,
            "file": root.get("path", ""),
            "line": root.get("line") or root.get("original_line"),
            "outdated": outdated,
            "author": _classify_author(root.get("user", {})),
            "body": root.get("body", ""),
            "replies": [
                {
                    "id": r["id"],
                    "author": _classify_author(r.get("user", {})),
                    "body": r.get("body", ""),
                }
                for r in children.get(cid, [])
            ],
        })

    if kind == "bot":
        threads = [t for t in threads if t["author"]["type"] == "bot"]
    elif kind == "human":
        threads = [t for t in threads if t["author"]["type"] == "human"]
    elif kind == "outdated":
        threads = [t for t in threads if t["outdated"]]
    elif kind == "active":
        threads = [t for t in threads if not t["outdated"]]

    summary = {
        "total": len(threads),
        "active": sum(1 for t in threads if not t["outdated"]),
        "outdated": sum(1 for t in threads if t["outdated"]),
        "human": sum(1 for t in threads if t["author"]["type"] == "human"),
        "bot": sum(1 for t in threads if t["author"]["type"] == "bot"),
    }

    return json.dumps({"threads": threads, "summary": summary}, indent=2)

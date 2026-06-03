import json
import subprocess

from ...app import tool
from ...run import CommandError, format_result, resolve_cwd, run_ok
from ._api import _api_repo, _gh_api_get, _gh_api_graphql, _repo_args


@tool("gh")
def pr_view(pr: str | int, repo: str = "", repo_path: str = "") -> str:
    """view pull request details including description and comments (gh pr view).

    pr: PR number or branch name.
    repo_path: optional local checkout to resolve the repo from. Defaults to the current project directory (where Claude Code is running), so you rarely need to set it. Set it only to target a different checkout.
    """
    args = [
        "gh",
        "pr",
        "view",
        str(pr),
        "--json",
        "number,title,author,state,body,baseRefName,headRefName,reviews,comments,isDraft,mergeable,statusCheckRollup",
    ]
    args += _repo_args(repo)
    raw = run_ok(args, cwd=repo_path)
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
def pr_checks(pr: str | int, repo: str = "", repo_path: str = "") -> str:
    """show CI check status for a pull request (gh pr checks)."""
    args = ["gh", "pr", "checks", str(pr)] + _repo_args(repo)
    return format_result(run_ok(args, cwd=repo_path), f"gh pr checks {pr}")


def _classify_author(user: dict) -> dict:
    return {
        "login": user.get("login", ""),
        "type": "bot" if user.get("type") == "Bot" else "human",
    }


_THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) { nodes { databaseId } }
        }
      }
    }
  }
}
"""


def _resolve_owner_name(repo: str, cwd: str = ".") -> tuple[str, str]:
    """return (owner, name). if repo is empty, query the current remote."""
    if repo:
        if "/" not in repo:
            raise CommandError(f"repo must be 'owner/name', got {repo!r}")
        owner, name = repo.split("/", 1)
        return owner, name
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name"],
        capture_output=True,
        text=True,
        cwd=resolve_cwd(cwd),
    )
    if result.returncode != 0:
        raise CommandError(
            f"gh repo view failed: {(result.stderr or result.stdout).strip()}"
        )
    try:
        d = json.loads(result.stdout)
        return d["owner"]["login"], d["name"]
    except (json.JSONDecodeError, KeyError) as e:
        raise CommandError(f"could not parse gh repo view output: {e}") from e


def _fetch_thread_meta(pr: int, repo: str, cwd: str = ".") -> dict[int, dict]:
    """map root-comment databaseId -> {resolve_id, resolved}."""
    owner, name = _resolve_owner_name(repo, cwd=cwd)
    data = _gh_api_graphql(
        _THREADS_QUERY, {"owner": owner, "name": name, "number": pr}, cwd=cwd
    )
    threads = (
        ((data.get("repository") or {}).get("pullRequest") or {}).get("reviewThreads")
        or {}
    ).get("nodes") or []
    out: dict[int, dict] = {}
    for t in threads:
        comments = ((t.get("comments") or {}).get("nodes")) or []
        if not comments:
            continue
        db_id = comments[0].get("databaseId")
        if db_id is None:
            continue
        out[int(db_id)] = {
            "resolve_id": t.get("id", ""),
            "resolved": bool(t.get("isResolved")),
        }
    return out


@tool("gh")
def pr_review_threads(
    pr: str | int,
    repo: str = "",
    kind: str = "",
    repo_path: str = "",
) -> str:
    """fetch inline review comment threads on a PR, structured for agent use.

    Returns JSON with a 'threads' list and a 'summary'. Each thread:
      thread_id  — numeric comment id; pass to gh_pr_reply_comment to reply
      resolve_id — GraphQL node id; pass to gh_pr_resolve_thread / gh_pr_unresolve_thread
      resolved   — true if the thread has been marked resolved on GitHub
      file, line — where the comment was placed in the diff
      outdated   — true when the commented line no longer exists in the current diff
      author     — {login, type} where type is 'human' or 'bot'
      body       — root comment text
      replies    — [{id, author, body}] in chronological order

    kind: filter results — 'bot', 'human', 'outdated', 'active', 'resolved', 'unresolved'.
          Empty returns all.
    repo_path: optional local checkout to resolve the repo from. Defaults to the current project directory (where Claude Code is running), so you rarely need to set it. Set it only to target a different checkout.

    typical workflow:
      1. pr_review_threads(pr="5", kind="unresolved")  → see what still needs addressing
      2. pr_reply_comment(pr="5", comment_id=<thread_id>, body="fixed in abc123")
      3. pr_resolve_thread(thread_id=<resolve_id>)
    """
    if kind and kind not in (
        "bot",
        "human",
        "outdated",
        "active",
        "resolved",
        "unresolved",
    ):
        raise CommandError(
            f"unknown kind {kind!r}: use 'bot', 'human', 'outdated', 'active', 'resolved', or 'unresolved'"
        )

    endpoint = f"repos/{_api_repo(repo)}/pulls/{pr}/comments?per_page=100"
    comments: list[dict] = json.loads(_gh_api_get(endpoint, cwd=repo_path))
    thread_meta = _fetch_thread_meta(int(pr), repo, cwd=repo_path)

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
        meta = thread_meta.get(cid, {})
        threads.append(
            {
                "thread_id": cid,
                "resolve_id": meta.get("resolve_id", ""),
                "resolved": meta.get("resolved", False),
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
            }
        )

    if kind == "bot":
        threads = [t for t in threads if t["author"]["type"] == "bot"]
    elif kind == "human":
        threads = [t for t in threads if t["author"]["type"] == "human"]
    elif kind == "outdated":
        threads = [t for t in threads if t["outdated"]]
    elif kind == "active":
        threads = [t for t in threads if not t["outdated"]]
    elif kind == "resolved":
        threads = [t for t in threads if t["resolved"]]
    elif kind == "unresolved":
        threads = [t for t in threads if not t["resolved"]]

    summary = {
        "total": len(threads),
        "active": sum(1 for t in threads if not t["outdated"]),
        "outdated": sum(1 for t in threads if t["outdated"]),
        "resolved": sum(1 for t in threads if t["resolved"]),
        "unresolved": sum(1 for t in threads if not t["resolved"]),
        "human": sum(1 for t in threads if t["author"]["type"] == "human"),
        "bot": sum(1 for t in threads if t["author"]["type"] == "bot"),
    }

    return json.dumps({"threads": threads, "summary": summary}, indent=2)

import json

from ...run import format_result, run_ok
from ._api import _api_repo, _gh_api_get, _repo_args


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


def pr_diff(pr: str | int, repo: str = "") -> str:
    """show the diff for a pull request (gh pr diff)."""
    args = ["gh", "pr", "diff", str(pr)] + _repo_args(repo)
    return format_result(run_ok(args), f"gh pr diff {pr}")


def pr_checks(pr: str | int, repo: str = "") -> str:
    """show CI check status for a pull request (gh pr checks)."""
    args = ["gh", "pr", "checks", str(pr)] + _repo_args(repo)
    return format_result(run_ok(args), f"gh pr checks {pr}")


def pr_review_threads(pr: str | int, repo: str = "") -> str:
    """list inline review comment threads on a PR — file, line, diff context, and replies.

    uses gh api directly since 'gh pr view' omits inline/line-level comments.
    returns threads grouped by root comment, showing path, line, diff_hunk, and all replies.
    """
    endpoint = f"repos/{_api_repo(repo)}/pulls/{pr}/comments?per_page=100"
    raw = _gh_api_get(endpoint, paginate=True)
    try:
        comments = json.loads(raw)
        if not comments:
            return "no inline review comments"

        # group into threads: root comments + their replies
        roots: dict[int, dict] = {}
        replies: dict[int, list[dict]] = {}
        for c in comments:
            parent_id = c.get("in_reply_to_id")
            if parent_id:
                replies.setdefault(parent_id, []).append(c)
            else:
                roots[c["id"]] = c

        lines = []
        for cid, c in roots.items():
            hunk = c.get("diff_hunk", "").strip()
            lines.append(
                f"Thread #{cid} — {c['path']}:{c.get('line') or c.get('original_line', '?')} "
                f"({c.get('side', 'RIGHT')})"
            )
            if hunk:
                lines.append(f"  diff: {hunk.splitlines()[-1] if hunk.splitlines() else hunk}")
            lines.append(f"  {c['user']['login']}: {c['body']}")
            for r in replies.get(cid, []):
                lines.append(f"    ↳ {r['user']['login']} (#{r['id']}): {r['body']}")
            lines.append("")
        return "\n".join(lines).strip()
    except (json.JSONDecodeError, KeyError) as e:
        return format_result(raw, f"gh api pr/{pr}/comments (parse error: {e})")

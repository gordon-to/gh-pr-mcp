import json

from ...app import tool
from ...run import CommandError, format_result, run
from ._api import _api_repo, _gh_api_post, _repo_args


@tool("gh")
def pr_review(
    pr: str | int,
    event: str,
    body: str = "",
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """submit a review on a pull request (gh pr review).

    event: 'approve', 'request-changes', or 'comment'.
    body: review comment body (required for 'request-changes' and 'comment').
    """
    if event not in ("approve", "request-changes", "comment"):
        raise CommandError(f"event must be 'approve', 'request-changes', or 'comment', got {event!r}")
    args = ["gh", "pr", "review", str(pr), f"--{event}"] + _repo_args(repo)
    if body:
        args += ["--body", body]
    return format_result(run(args, cwd=repo_path), f"gh pr review {pr}")


@tool("gh")
def pr_add_review(
    pr: str | int,
    event: str,
    body: str = "",
    inline_comments: list[dict] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """submit a PR review with optional inline comments via the GitHub API.

    event: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'.
    body: top-level review body.
    inline_comments: list of dicts, each with:
        path (str)     — relative file path
        line (int)     — line number in the new file
        body (str)     — comment text
        side (str)     — 'RIGHT' (default) or 'LEFT'

    use this instead of pr_review when you need to attach comments to
    specific lines of the diff.
    """
    event_upper = event.upper()
    if event_upper not in ("APPROVE", "REQUEST_CHANGES", "COMMENT"):
        raise CommandError(f"event must be APPROVE, REQUEST_CHANGES, or COMMENT, got {event!r}")
    payload: dict = {"event": event_upper, "body": body, "comments": []}
    for c in (inline_comments or []):
        if not isinstance(c, dict) or "path" not in c or "line" not in c or "body" not in c:
            raise CommandError("each inline_comment needs 'path', 'line', and 'body' keys")
        payload["comments"].append({
            "path": c["path"],
            "line": int(c["line"]),
            "body": c["body"],
            "side": c.get("side", "RIGHT"),
        })
    endpoint = f"repos/{_api_repo(repo)}/pulls/{pr}/reviews"
    raw = _gh_api_post(endpoint, payload, cwd=repo_path)
    try:
        d = json.loads(raw)
        return f"review #{d['id']} submitted: {d['state']} by {d['user']['login']}"
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh api POST pr/{pr}/reviews")


@tool("gh")
def pr_reply_comment(
    pr: str | int,
    comment_id: int,
    body: str,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """reply to an existing inline review comment thread.

    comment_id: the id of the root comment to reply to (from pr_review_threads).
    body: your reply text.
    """
    if not body.strip():
        raise CommandError("reply body must not be empty")
    endpoint = f"repos/{_api_repo(repo)}/pulls/{pr}/comments"
    payload = {"body": body, "in_reply_to": comment_id}
    raw = _gh_api_post(endpoint, payload, cwd=repo_path)
    try:
        d = json.loads(raw)
        return f"comment #{d['id']} posted by {d['user']['login']}: {d['body'][:100]}"
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh api POST pr/{pr}/comments (reply)")

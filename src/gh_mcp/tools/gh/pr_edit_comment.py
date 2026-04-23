import json

from ...app import tool
from ...run import CommandError, format_result
from ._api import _api_repo, _gh_api_patch


@tool("gh")
def pr_edit_comment(
    comment_id: int,
    body: str,
    repo: str = "",
) -> str:
    """edit an existing pull request review comment (inline or reply).

    comment_id: the id of the comment to edit (from pr_review_threads).
    body: the new comment body.
    repo: optional 'owner/repo' override.
    """
    if not body.strip():
        raise CommandError("comment body must not be empty")
    endpoint = f"repos/{_api_repo(repo)}/pulls/comments/{comment_id}"
    raw = _gh_api_patch(endpoint, {"body": body})
    try:
        d = json.loads(raw)
        return f"comment #{d['id']} updated by {d['user']['login']}: {d['body'][:120]}"
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh api PATCH pulls/comments/{comment_id}")

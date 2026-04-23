from ...app import tool
from ._api import _api_repo, _gh_api_delete


@tool("gh")
def pr_delete_comment(
    comment_id: int,
    repo: str = "",
) -> str:
    """delete an existing pull request review comment (inline or reply).

    comment_id: the id of the comment to delete (from pr_review_threads).
    repo: optional 'owner/repo' override.
    """
    endpoint = f"repos/{_api_repo(repo)}/pulls/comments/{comment_id}"
    _gh_api_delete(endpoint)
    return f"comment #{comment_id} deleted"

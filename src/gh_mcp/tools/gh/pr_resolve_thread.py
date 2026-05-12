from ...app import tool
from ...run import CommandError
from ._api import _gh_api_graphql


_RESOLVE = """
mutation($id: ID!) {
  resolveReviewThread(input: {threadId: $id}) {
    thread { id isResolved }
  }
}
"""

_UNRESOLVE = """
mutation($id: ID!) {
  unresolveReviewThread(input: {threadId: $id}) {
    thread { id isResolved }
  }
}
"""


def _validate_thread_id(thread_id: str) -> str:
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise CommandError(
            "thread_id must be a non-empty string (GraphQL node id from pr_review_threads.resolve_id)"
        )
    return thread_id


@tool("gh")
def pr_resolve_thread(thread_id: str) -> str:
    """mark a PR review thread as resolved.

    thread_id: GraphQL node id from pr_review_threads (the 'resolve_id' field).
    """
    _validate_thread_id(thread_id)
    data = _gh_api_graphql(_RESOLVE, {"id": thread_id})
    t = (data.get("resolveReviewThread") or {}).get("thread") or {}
    resolved = t.get("isResolved")
    return f"thread {t.get('id', thread_id)} resolved={resolved}"


@tool("gh")
def pr_unresolve_thread(thread_id: str) -> str:
    """mark a PR review thread as unresolved.

    thread_id: GraphQL node id from pr_review_threads (the 'resolve_id' field).
    """
    _validate_thread_id(thread_id)
    data = _gh_api_graphql(_UNRESOLVE, {"id": thread_id})
    t = (data.get("unresolveReviewThread") or {}).get("thread") or {}
    resolved = t.get("isResolved")
    return f"thread {t.get('id', thread_id)} resolved={resolved}"

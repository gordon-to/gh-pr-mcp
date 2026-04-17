import json
import subprocess

from ...run import CommandError


def _repo_args(repo: str) -> list[str]:
    """return ['-R', repo] if repo is given."""
    if repo:
        return ["-R", repo]
    return []


def _api_repo(repo: str) -> str:
    """repo path component for gh api URLs.

    if repo is 'owner/repo' use it literally; otherwise use gh's {owner}/{repo}
    placeholder which resolves from the current git remote.
    """
    return repo if repo else "{owner}/{repo}"


def _gh_api_get(endpoint: str, paginate: bool = False) -> str:
    """GET from the GitHub REST API via gh api."""
    args = ["gh", "api", "--method", "GET"]
    if paginate:
        args.append("--paginate")
    args.append(endpoint)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise CommandError(f"gh api GET failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def _gh_api_post(endpoint: str, payload: dict) -> str:
    """POST JSON to the GitHub REST API via gh api --input."""
    args = ["gh", "api", "--method", "POST", endpoint, "--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CommandError(f"gh api POST failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def _gh_api_graphql(query: str, variables: dict | None = None) -> dict:
    """run a GraphQL query/mutation via gh api graphql. returns the 'data' object."""
    payload = {"query": query, "variables": variables or {}}
    args = ["gh", "api", "graphql", "--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CommandError(f"gh api graphql failed: {(result.stderr or result.stdout).strip()}")
    try:
        body = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise CommandError(f"gh api graphql returned non-JSON: {e}") from e
    if errors := body.get("errors"):
        msgs = "; ".join(e.get("message", str(e)) for e in errors)
        raise CommandError(f"graphql errors: {msgs}")
    data = body.get("data")
    if data is None:
        raise CommandError("graphql response missing 'data'")
    return data

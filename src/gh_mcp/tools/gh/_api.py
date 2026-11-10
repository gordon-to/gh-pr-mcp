import json
import os
import re
import subprocess

from ...run import CommandError, resolve_cwd

# gh's own preference order when picking which remote identifies a checkout.
_REMOTE_PREFERENCE = ("upstream", "github", "origin")

_HOST_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")


def _split_repo(repo: str) -> tuple[str, str]:
    """split a repo spec into (host, 'owner/name').

    host is '' unless the spec uses the three-part 'host/owner/name' form that
    gh's -R flag also accepts.
    """
    parts = repo.split("/")
    if len(parts) == 3:
        return parts[0], f"{parts[1]}/{parts[2]}"
    return "", repo


def _url_host(url: str) -> str:
    """hostname of a git remote url (https, ssh, or scp-style)."""
    if "://" in url:
        netloc = url.split("://", 1)[1].split("/", 1)[0]
    elif ":" in url:
        netloc = url.split(":", 1)[0]
    else:
        return ""
    host = netloc.rsplit("@", 1)[-1].split(":", 1)[0].lower()
    return host if _HOST_PATTERN.match(host) else ""


def _remote_host(cwd: str = ".") -> str:
    """github hostname backing a checkout's remotes, '' if undeterminable."""
    if host := os.environ.get("GH_HOST"):
        return host
    result = subprocess.run(
        ["git", "remote", "-v"], capture_output=True, text=True, cwd=resolve_cwd(cwd)
    )
    if result.returncode != 0:
        return ""
    hosts: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        name, url = fields[0], fields[1]
        if (host := _url_host(url)) and name not in hosts:
            hosts[name] = host
    for name in _REMOTE_PREFERENCE:
        if name in hosts:
            return hosts[name]
    return next(iter(hosts.values()), "")


def _host_args(repo: str = "", cwd: str = ".") -> list[str]:
    """['--hostname', host] for gh api calls.

    unlike `gh pr`/`gh run`, `gh api` never infers the host from the current
    checkout — it targets github.com unless told otherwise, so every enterprise
    repo 404s without this.
    """
    host, _ = _split_repo(repo)
    host = host or _remote_host(cwd)
    return ["--hostname", host] if host else []


def _repo_args(repo: str, cwd: str = ".") -> list[str]:
    """return ['-R', repo] if repo is given, qualified with the checkout's host."""
    if not repo:
        return []
    host, owner_name = _split_repo(repo)
    host = host or _remote_host(cwd)
    return ["-R", f"{host}/{owner_name}" if host else owner_name]


def _api_repo(repo: str) -> str:
    """repo path component for gh api URLs.

    if repo names a repository use it literally (dropping any host prefix, which
    travels via --hostname instead); otherwise use gh's {owner}/{repo}
    placeholder which resolves from the current git remote.
    """
    owner_name = _split_repo(repo)[1]
    if owner_name and "/" not in owner_name:
        raise CommandError(
            f"repo must be 'owner/name' or 'host/owner/name', got {repo!r}"
        )
    return owner_name or "{owner}/{repo}"


def _gh_api_get(
    endpoint: str, paginate: bool = False, cwd: str = ".", repo: str = ""
) -> str:
    """GET from the GitHub REST API via gh api."""
    args = ["gh", "api", *_host_args(repo, cwd), "--method", "GET"]
    if paginate:
        args.append("--paginate")
    args.append(endpoint)
    result = subprocess.run(args, capture_output=True, text=True, cwd=resolve_cwd(cwd))
    if result.returncode != 0:
        raise CommandError(
            f"gh api GET failed: {(result.stderr or result.stdout).strip()}"
        )
    return result.stdout


def _gh_api_post(endpoint: str, payload: dict, cwd: str = ".", repo: str = "") -> str:
    """POST JSON to the GitHub REST API via gh api --input."""
    args = [
        "gh",
        "api",
        *_host_args(repo, cwd),
        "--method",
        "POST",
        endpoint,
        "--input",
        "-",
    ]
    result = subprocess.run(
        args,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=resolve_cwd(cwd),
    )
    if result.returncode != 0:
        raise CommandError(
            f"gh api POST failed: {(result.stderr or result.stdout).strip()}"
        )
    return result.stdout


def _gh_api_patch(endpoint: str, payload: dict, cwd: str = ".", repo: str = "") -> str:
    """PATCH JSON to the GitHub REST API via gh api --input."""
    args = [
        "gh",
        "api",
        *_host_args(repo, cwd),
        "--method",
        "PATCH",
        endpoint,
        "--input",
        "-",
    ]
    result = subprocess.run(
        args,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=resolve_cwd(cwd),
    )
    if result.returncode != 0:
        raise CommandError(
            f"gh api PATCH failed: {(result.stderr or result.stdout).strip()}"
        )
    return result.stdout


def _gh_api_delete(endpoint: str, cwd: str = ".", repo: str = "") -> None:
    """DELETE via the GitHub REST API via gh api."""
    args = ["gh", "api", *_host_args(repo, cwd), "--method", "DELETE", endpoint]
    result = subprocess.run(args, capture_output=True, text=True, cwd=resolve_cwd(cwd))
    if result.returncode != 0:
        raise CommandError(
            f"gh api DELETE failed: {(result.stderr or result.stdout).strip()}"
        )


def _gh_api_graphql(
    query: str, variables: dict | None = None, cwd: str = ".", repo: str = ""
) -> dict:
    """run a GraphQL query/mutation via gh api graphql. returns the 'data' object."""
    payload = {"query": query, "variables": variables or {}}
    args = ["gh", "api", *_host_args(repo, cwd), "graphql", "--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=resolve_cwd(cwd),
    )
    if result.returncode != 0:
        raise CommandError(
            f"gh api graphql failed: {(result.stderr or result.stdout).strip()}"
        )
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

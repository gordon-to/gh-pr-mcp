import json

from ...run import format_result, run_ok
from ._api import _repo_args


def release_list(repo: str = "", limit: int = 20) -> str:
    """list releases (gh release list)."""
    args = ["gh", "release", "list", "--limit", str(limit), "--json",
            "tagName,name,isDraft,isPrerelease,publishedAt"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        releases = json.loads(raw)
        if not releases:
            return "no releases found"
        lines = []
        for r in releases:
            flags = []
            if r.get("isDraft"):
                flags.append("draft")
            if r.get("isPrerelease"):
                flags.append("pre-release")
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            lines.append(
                f"{r['tagName']}  {r.get('name', '')}{flag_str}\n"
                f"  published: {r.get('publishedAt', '')[:10]}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh release list")


def release_view(tag: str, repo: str = "") -> str:
    """view release details (gh release view)."""
    args = ["gh", "release", "view", tag, "--json",
            "tagName,name,isDraft,isPrerelease,body,publishedAt,author,assets"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        d = json.loads(raw)
        lines = [
            f"Release: {d['tagName']}  {d.get('name', '')}",
            f"published: {d.get('publishedAt', '')[:10]}  author: {d['author']['login']}",
        ]
        if d.get("body"):
            lines.append(f"\n{d['body']}")
        if d.get("assets"):
            lines.append(f"\nassets: {', '.join(a['name'] for a in d['assets'])}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh release view {tag}")

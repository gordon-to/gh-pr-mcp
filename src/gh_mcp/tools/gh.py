"""gh (GitHub CLI) tools — all gh_* MCP tool implementations.

permission levels:
  always-allow: gh_pr_list, gh_pr_view, gh_pr_diff, gh_pr_checks,
                gh_issue_list, gh_issue_view,
                gh_run_list, gh_run_view,
                gh_repo_view, gh_release_list, gh_release_view
  ask:          gh_pr_create, gh_pr_comment, gh_pr_review, gh_pr_checkout,
                gh_issue_create, gh_issue_comment, gh_issue_close, gh_issue_edit,
                gh_run_rerun
  ask:          gh_pr_merge, gh_pr_close, gh_repo_create,
                gh_release_create
"""

import json

from ..run import CommandError, _validate_ref, format_result, run, run_ok


def _repo_args(repo: str) -> list[str]:
    """return ['-R', repo] if repo is given."""
    if repo:
        return ["-R", repo]
    return []


# ---------------------------------------------------------------------------
# PR — read
# ---------------------------------------------------------------------------

def pr_list(
    repo: str = "",
    state: str = "open",
    author: str = "",
    base: str = "",
    label: str = "",
    limit: int = 30,
) -> str:
    """list pull requests (gh pr list).

    state: 'open', 'closed', 'merged', or 'all'.
    """
    args = ["gh", "pr", "list", "--state", state, "--limit", str(limit), "--json",
            "number,title,author,state,headRefName,updatedAt,isDraft"]
    args += _repo_args(repo)
    if author:
        args += ["--author", author]
    if base:
        args += ["--base", _validate_ref(base, "base")]
    if label:
        args += ["--label", label]
    raw = run_ok(args)
    try:
        prs = json.loads(raw)
        if not prs:
            return "no pull requests found"
        lines = []
        for pr in prs:
            draft = " [DRAFT]" if pr.get("isDraft") else ""
            lines.append(
                f"#{pr['number']} {pr['title']}{draft}\n"
                f"  branch: {pr['headRefName']}  author: {pr['author']['login']}  updated: {pr['updatedAt'][:10]}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh pr list")


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


# ---------------------------------------------------------------------------
# PR — write
# ---------------------------------------------------------------------------

def pr_create(
    repo_path: str = ".",
    repo: str = "",
    title: str = "",
    body: str = "",
    base: str = "main",
    draft: bool = False,
    reviewer: list[str] | None = None,
    label: list[str] | None = None,
) -> str:
    """create a pull request (gh pr create).

    title and body default to the commit message if omitted.
    reviewer: list of GitHub usernames to request review from.
    """
    args = ["gh", "pr", "create", "--base", _validate_ref(base, "base")]
    args += _repo_args(repo)
    if title:
        args += ["--title", title]
    else:
        args.append("--fill")
    if body:
        args += ["--body", body]
    elif not title:
        pass  # --fill covers body too
    else:
        args += ["--body", ""]
    if draft:
        args.append("--draft")
    for r in (reviewer or []):
        args += ["--reviewer", r]
    for lbl in (label or []):
        args += ["--label", lbl]
    return format_result(run(args, cwd=repo_path), "gh pr create")


def pr_comment(pr: str | int, body: str, repo: str = "", repo_path: str = ".") -> str:
    """add a comment to a pull request (gh pr comment)."""
    if not body.strip():
        raise CommandError("comment body must not be empty")
    args = ["gh", "pr", "comment", str(pr), "--body", body] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh pr comment {pr}")


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


def pr_checkout(pr: str | int, repo: str = "", repo_path: str = ".") -> str:
    """check out a PR's branch locally (gh pr checkout)."""
    args = ["gh", "pr", "checkout", str(pr)] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh pr checkout {pr}")


def pr_merge(
    pr: str | int,
    method: str = "merge",
    delete_branch: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """merge a pull request (gh pr merge) — WRITES TO REMOTE.

    method: 'merge', 'squash', or 'rebase'.
    delete_branch: delete head branch after merge (default True).
    """
    if method not in ("merge", "squash", "rebase"):
        raise CommandError(f"method must be 'merge', 'squash', or 'rebase', got {method!r}")
    args = ["gh", "pr", "merge", str(pr), f"--{method}"] + _repo_args(repo)
    if delete_branch:
        args.append("--delete-branch")
    return format_result(run(args, cwd=repo_path), f"gh pr merge {pr}")


def pr_close(pr: str | int, comment: str = "", repo: str = "", repo_path: str = ".") -> str:
    """close a pull request without merging (gh pr close)."""
    args = ["gh", "pr", "close", str(pr)] + _repo_args(repo)
    if comment:
        args += ["--comment", comment]
    return format_result(run(args, cwd=repo_path), f"gh pr close {pr}")


# ---------------------------------------------------------------------------
# Issues — read
# ---------------------------------------------------------------------------

def issue_list(
    repo: str = "",
    state: str = "open",
    assignee: str = "",
    label: str = "",
    limit: int = 30,
) -> str:
    """list issues (gh issue list)."""
    args = ["gh", "issue", "list", "--state", state, "--limit", str(limit),
            "--json", "number,title,author,state,labels,assignees,updatedAt"]
    args += _repo_args(repo)
    if assignee:
        args += ["--assignee", assignee]
    if label:
        args += ["--label", label]
    raw = run_ok(args)
    try:
        issues = json.loads(raw)
        if not issues:
            return "no issues found"
        lines = []
        for issue in issues:
            labels = ", ".join(lbl["name"] for lbl in issue.get("labels", []))
            label_str = f"  labels: {labels}" if labels else ""
            lines.append(
                f"#{issue['number']} {issue['title']}\n"
                f"  author: {issue['author']['login']}  updated: {issue['updatedAt'][:10]}{label_str}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh issue list")


def issue_view(issue: str | int, repo: str = "") -> str:
    """view issue details and comments (gh issue view)."""
    args = ["gh", "issue", "view", str(issue), "--json",
            "number,title,author,state,body,labels,assignees,comments"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        d = json.loads(raw)
        lines = [
            f"Issue #{d['number']}: {d['title']}",
            f"state: {d['state']}  author: {d['author']['login']}",
        ]
        if d.get("labels"):
            lines.append("labels: " + ", ".join(lbl["name"] for lbl in d["labels"]))
        if d.get("body"):
            lines.append(f"\n{d['body']}")
        if d.get("comments"):
            lines.append("\n--- comments ---")
            for c in d["comments"]:
                lines.append(f"\n{c['author']['login']}:\n{c['body'][:500]}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh issue view {issue}")


# ---------------------------------------------------------------------------
# Issues — write
# ---------------------------------------------------------------------------

def issue_create(
    title: str,
    body: str = "",
    label: list[str] | None = None,
    assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """create a new issue (gh issue create)."""
    if not title.strip():
        raise CommandError("issue title must not be empty")
    args = ["gh", "issue", "create", "--title", title] + _repo_args(repo)
    args += ["--body", body or ""]
    for lbl in (label or []):
        args += ["--label", lbl]
    for a in (assignee or []):
        args += ["--assignee", a]
    return format_result(run(args, cwd=repo_path), "gh issue create")


def issue_comment(issue: str | int, body: str, repo: str = "", repo_path: str = ".") -> str:
    """add a comment to an issue (gh issue comment)."""
    if not body.strip():
        raise CommandError("comment body must not be empty")
    args = ["gh", "issue", "comment", str(issue), "--body", body] + _repo_args(repo)
    return format_result(run(args, cwd=repo_path), f"gh issue comment {issue}")


def issue_close(issue: str | int, reason: str = "", repo: str = "", repo_path: str = ".") -> str:
    """close an issue (gh issue close).

    reason: 'completed', 'not planned', or '' (default).
    """
    args = ["gh", "issue", "close", str(issue)] + _repo_args(repo)
    if reason:
        args += ["--reason", reason]
    return format_result(run(args, cwd=repo_path), f"gh issue close {issue}")


def issue_edit(
    issue: str | int,
    title: str = "",
    body: str = "",
    add_label: list[str] | None = None,
    remove_label: list[str] | None = None,
    add_assignee: list[str] | None = None,
    remove_assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """edit an issue's metadata (gh issue edit)."""
    args = ["gh", "issue", "edit", str(issue)] + _repo_args(repo)
    if title:
        args += ["--title", title]
    if body:
        args += ["--body", body]
    for lbl in (add_label or []):
        args += ["--add-label", lbl]
    for lbl in (remove_label or []):
        args += ["--remove-label", lbl]
    for a in (add_assignee or []):
        args += ["--add-assignee", a]
    for a in (remove_assignee or []):
        args += ["--remove-assignee", a]
    return format_result(run(args, cwd=repo_path), f"gh issue edit {issue}")


# ---------------------------------------------------------------------------
# Repo
# ---------------------------------------------------------------------------

def repo_view(repo: str = "") -> str:
    """view repository info (gh repo view)."""
    args = ["gh", "repo", "view", "--json",
            "name,description,defaultBranchRef,isPrivate,stargazerCount,forkCount,openIssues,url"]
    args += _repo_args(repo)
    raw = run_ok(args)
    try:
        d = json.loads(raw)
        lines = [
            f"{d['name']}  {'[private]' if d['isPrivate'] else '[public]'}",
            f"url: {d['url']}",
            f"default branch: {d['defaultBranchRef']['name']}",
            f"stars: {d['stargazerCount']}  forks: {d['forkCount']}  open issues: {len(d.get('openIssues', []))}",
        ]
        if d.get("description"):
            lines.append(f"description: {d['description']}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh repo view")


def repo_create(
    name: str,
    private: bool = True,
    description: str = "",
    clone: bool = False,
) -> str:
    """create a new GitHub repository (gh repo create)."""
    if not name.strip():
        raise CommandError("repo name must not be empty")
    args = ["gh", "repo", "create", name]
    args.append("--private" if private else "--public")
    if description:
        args += ["--description", description]
    if clone:
        args.append("--clone")
    return format_result(run(args), "gh repo create")


# ---------------------------------------------------------------------------
# CI Runs
# ---------------------------------------------------------------------------

def run_list(
    repo: str = "",
    workflow: str = "",
    branch: str = "",
    status: str = "",
    limit: int = 20,
    repo_path: str = ".",
) -> str:
    """list workflow runs (gh run list)."""
    args = ["gh", "run", "list", "--limit", str(limit), "--json",
            "databaseId,name,status,conclusion,headBranch,event,startedAt"]
    args += _repo_args(repo)
    if workflow:
        args += ["--workflow", workflow]
    if branch:
        args += ["--branch", _validate_ref(branch, "branch")]
    if status:
        args += ["--status", status]
    raw = run_ok(args, cwd=repo_path)
    try:
        runs = json.loads(raw)
        if not runs:
            return "no workflow runs found"
        lines = []
        for r in runs:
            conclusion = r.get("conclusion") or r.get("status", "")
            lines.append(
                f"#{r['databaseId']} {r['name']}  [{conclusion}]\n"
                f"  branch: {r['headBranch']}  event: {r['event']}  started: {r.get('startedAt', '')[:16]}"
            )
        return "\n\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, "gh run list")


def run_view(run_id: str | int, repo: str = "", log: bool = False, repo_path: str = ".") -> str:
    """view a workflow run's details or logs (gh run view)."""
    args = ["gh", "run", "view", str(run_id)] + _repo_args(repo)
    if log:
        args.append("--log")
    else:
        args.append("--json")
        args.append("databaseId,name,status,conclusion,headBranch,event,jobs,startedAt,updatedAt")
    raw = run_ok(args, cwd=repo_path)
    if log:
        return format_result(raw, f"gh run view {run_id} --log")
    try:
        d = json.loads(raw)
        lines = [
            f"Run #{d['databaseId']}: {d['name']}",
            f"status: {d['status']}  conclusion: {d.get('conclusion', 'pending')}",
            f"branch: {d['headBranch']}  event: {d['event']}",
        ]
        if d.get("jobs"):
            lines.append("\njobs:")
            for job in d["jobs"]:
                lines.append(f"  {job['name']}: {job.get('conclusion') or job.get('status')}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh run view {run_id}")


def run_rerun(run_id: str | int, failed_only: bool = True, repo: str = "", repo_path: str = ".") -> str:
    """rerun a workflow run (gh run rerun)."""
    args = ["gh", "run", "rerun", str(run_id)] + _repo_args(repo)
    if failed_only:
        args.append("--failed")
    return format_result(run(args, cwd=repo_path), f"gh run rerun {run_id}")


# ---------------------------------------------------------------------------
# Releases
# ---------------------------------------------------------------------------

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


def release_create(
    tag: str,
    title: str = "",
    notes: str = "",
    draft: bool = False,
    prerelease: bool = False,
    generate_notes: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """create a release (gh release create) — WRITES TO REMOTE."""
    _validate_ref(tag, "tag")
    args = ["gh", "release", "create", tag] + _repo_args(repo)
    if title:
        args += ["--title", title]
    if notes:
        args += ["--notes", notes]
    elif generate_notes:
        args.append("--generate-notes")
    if draft:
        args.append("--draft")
    if prerelease:
        args.append("--prerelease")
    return format_result(run(args, cwd=repo_path), f"gh release create {tag}")

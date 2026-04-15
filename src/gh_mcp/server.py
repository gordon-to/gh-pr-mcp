"""gh-mcp: MCP server exposing git and gh as structured tools."""

from mcp.server.fastmcp import FastMCP

from .tools import gh, git
from .run import CommandError

mcp = FastMCP(
    "gh-mcp",
    instructions=(
        "Tools for all git and GitHub CLI operations. "
        "Read-only tools (git_status, git_diff, git_log, git_branch_list, "
        "gh_pr_list, gh_issue_list, gh_run_list, gh_repo_view, gh_release_list) "
        "are always safe. "
        "Write tools that affect remotes or are destructive will ask for confirmation."
    ),
)


def _wrap(fn, *args, **kwargs) -> str:
    try:
        return fn(*args, **kwargs)
    except CommandError as e:
        return f"error: {e}"


# ===========================================================================
# Git: read-only
# ===========================================================================

@mcp.tool()
def git_status(repo_path: str = ".") -> str:
    """show working tree status. always safe."""
    return _wrap(git.status, repo_path)


@mcp.tool()
def git_diff(
    repo_path: str = ".",
    staged: bool = False,
    path: str = "",
    commit: str = "",
) -> str:
    """show uncommitted changes. staged=True shows staged changes. always safe."""
    return _wrap(git.diff, repo_path, staged=staged, path=path, commit=commit)


@mcp.tool()
def git_log(
    repo_path: str = ".",
    n: int = 20,
    branch: str = "",
    oneline: bool = True,
    path: str = "",
) -> str:
    """show commit history. always safe."""
    return _wrap(git.log, repo_path, n=n, branch=branch, oneline=oneline, path=path)


@mcp.tool()
def git_show(repo_path: str = ".", ref: str = "HEAD", path: str = "") -> str:
    """show details of a commit. always safe."""
    return _wrap(git.show, repo_path, ref=ref, path=path)


@mcp.tool()
def git_blame(repo_path: str, path: str, ref: str = "HEAD") -> str:
    """show line-by-line authorship of a file. always safe."""
    return _wrap(git.blame, repo_path, path=path, ref=ref)


@mcp.tool()
def git_branch_list(repo_path: str = ".", all_branches: bool = False) -> str:
    """list branches. all_branches=True includes remote-tracking branches. always safe."""
    return _wrap(git.branch_list, repo_path, all_branches=all_branches)


@mcp.tool()
def git_remote_list(repo_path: str = ".") -> str:
    """list remotes and their URLs. always safe."""
    return _wrap(git.remote_list, repo_path)


@mcp.tool()
def git_stash_list(repo_path: str = ".") -> str:
    """list stash entries. always safe."""
    return _wrap(git.stash_list, repo_path)


@mcp.tool()
def git_worktree_list(repo_path: str = ".") -> str:
    """list all worktrees for this repository. always safe."""
    return _wrap(git.worktree_list, repo_path)


@mcp.tool()
def git_tag_list(repo_path: str = ".", pattern: str = "") -> str:
    """list tags, newest first. always safe."""
    return _wrap(git.tag_list, repo_path, pattern=pattern)


# ===========================================================================
# Git: local writes (no network, reversible)
# ===========================================================================

@mcp.tool()
def git_add(repo_path: str, paths: list[str]) -> str:
    """stage files for commit. paths=['.'] stages everything. safe local operation."""
    return _wrap(git.add, repo_path, paths)


@mcp.tool()
def git_commit(repo_path: str, message: str, allow_empty: bool = False) -> str:
    """create a commit from staged changes. safe local operation."""
    return _wrap(git.commit, repo_path, message=message, allow_empty=allow_empty)


@mcp.tool()
def git_branch_create(
    repo_path: str,
    name: str,
    start_point: str = "",
    checkout: bool = True,
) -> str:
    """create a new branch. checkout=True (default) switches to it immediately. safe local operation."""
    return _wrap(git.branch_create, repo_path, name=name, start_point=start_point, checkout=checkout)


@mcp.tool()
def git_checkout(repo_path: str, ref: str) -> str:
    """switch to a branch or detach at a commit. safe local operation."""
    return _wrap(git.checkout, repo_path, ref=ref)


@mcp.tool()
def git_stash_push(
    repo_path: str = ".",
    message: str = "",
    include_untracked: bool = True,
) -> str:
    """stash current changes. safe local operation."""
    return _wrap(git.stash_push, repo_path, message=message, include_untracked=include_untracked)


@mcp.tool()
def git_stash_pop(repo_path: str = ".", index: int = 0) -> str:
    """apply and drop a stash entry. safe local operation."""
    return _wrap(git.stash_pop, repo_path, index=index)


@mcp.tool()
def git_init(path: str, initial_branch: str = "main") -> str:
    """initialize a new git repository. safe local operation."""
    return _wrap(git.init, path, initial_branch=initial_branch)


# ===========================================================================
# Git: remote-read — always-allow or ask (network, read-only local effect)
# ===========================================================================

@mcp.tool()
def git_fetch(repo_path: str = ".", remote: str = "origin", prune: bool = True) -> str:
    """fetch from remote without merging. git:remote-read — safe to always-allow."""
    return _wrap(git.fetch, repo_path, remote=remote, prune=prune)


@mcp.tool()
def git_pull(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    rebase: bool = False,
) -> str:
    """pull and integrate remote commits. git:remote-read — safe to always-allow."""
    return _wrap(git.pull, repo_path, remote=remote, branch=branch, rebase=rebase)


@mcp.tool()
def git_clone(url: str, destination: str = "", branch: str = "", depth: int = 0) -> str:
    """clone a remote repository. git:remote-read."""
    return _wrap(git.clone, url, destination=destination, branch=branch, depth=depth)


# ===========================================================================
# Git: remote-write — ask (writes to remote)
# ===========================================================================

@mcp.tool()
def git_push(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    set_upstream: bool = False,
    tags: bool = False,
) -> str:
    """push commits to remote. git:remote-write — ask before running."""
    return _wrap(git.push, repo_path, remote=remote, branch=branch, set_upstream=set_upstream, tags=tags)


@mcp.tool()
def git_remote_add(repo_path: str, name: str, url: str) -> str:
    """add a remote. git:remote-write — ask before running."""
    return _wrap(git.remote_add, repo_path, name=name, url=url)


@mcp.tool()
def git_tag_create(
    repo_path: str,
    name: str,
    ref: str = "HEAD",
    message: str = "",
) -> str:
    """create a tag (annotated if message given). git:remote-write — ask before running."""
    return _wrap(git.tag_create, repo_path, name=name, ref=ref, message=message)


# ===========================================================================
# Git: remote-destructive — ask/block (rewrites remote history)
# ===========================================================================

@mcp.tool()
def git_push_force(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    with_lease: bool = True,
) -> str:
    """force-push — rewrites remote history. git:remote-destructive — ask/block."""
    return _wrap(git.push_force, repo_path, remote=remote, branch=branch, with_lease=with_lease)


# ===========================================================================
# Git: integrate — ask (rewrites local history / topology)
# ===========================================================================

@mcp.tool()
def git_merge(
    repo_path: str,
    branch: str,
    no_ff: bool = False,
    squash: bool = False,
) -> str:
    """merge a branch into current HEAD. git:integrate — ask before running."""
    return _wrap(git.merge, repo_path, branch=branch, no_ff=no_ff, squash=squash)


@mcp.tool()
def git_rebase(repo_path: str, onto: str) -> str:
    """rebase current branch onto another ref. git:integrate — ask before running."""
    return _wrap(git.rebase, repo_path, onto=onto)


@mcp.tool()
def git_rebase_abort(repo_path: str = ".") -> str:
    """abort an in-progress rebase. git:integrate — ask before running."""
    return _wrap(git.rebase_abort, repo_path)


@mcp.tool()
def git_rebase_continue(repo_path: str = ".") -> str:
    """continue a rebase after resolving conflicts. git:integrate — ask before running."""
    return _wrap(git.rebase_continue, repo_path)


@mcp.tool()
def git_cherry_pick(repo_path: str, commits: list[str]) -> str:
    """apply specific commits onto current HEAD. git:integrate — ask before running."""
    return _wrap(git.cherry_pick, repo_path, commits=commits)


@mcp.tool()
def git_worktree_add(
    repo_path: str,
    path: str,
    branch: str,
    create_branch: bool = True,
) -> str:
    """add a new worktree. create_branch=True creates a new branch at HEAD. git:integrate — ask before running."""
    return _wrap(git.worktree_add, repo_path, path=path, branch=branch, create_branch=create_branch)


@mcp.tool()
def git_worktree_remove(repo_path: str, path: str, force: bool = False) -> str:
    """remove a worktree. force=True removes even with uncommitted changes. git:integrate — ask before running."""
    return _wrap(git.worktree_remove, repo_path, path=path, force=force)


# ===========================================================================
# Git: local-destructive — ask (discards local work, no network)
# ===========================================================================

@mcp.tool()
def git_reset(repo_path: str, ref: str = "HEAD", mode: str = "mixed") -> str:
    """reset HEAD. mode='hard' discards all uncommitted changes. git:local-destructive — ask before running."""
    return _wrap(git.reset, repo_path, ref=ref, mode=mode)


@mcp.tool()
def git_restore(repo_path: str, paths: list[str], staged: bool = False) -> str:
    """discard changes to files. staged=True unstages. git:local-destructive — ask before running."""
    return _wrap(git.restore, repo_path, paths=paths, staged=staged)


@mcp.tool()
def git_clean(
    repo_path: str,
    directories: bool = False,
    force: bool = True,
    dry_run: bool = False,
) -> str:
    """remove untracked files. dry_run=True previews without deleting. git:local-destructive — ask before running."""
    return _wrap(git.clean, repo_path, directories=directories, force=force, dry_run=dry_run)


@mcp.tool()
def git_branch_delete(
    repo_path: str,
    name: str,
    force: bool = False,
    remote: str = "",
) -> str:
    """delete a local branch. force=True deletes unmerged. git:local-destructive — ask before running."""
    return _wrap(git.branch_delete, repo_path, name=name, force=force, remote=remote)


# ===========================================================================
# GitHub: PR read
# ===========================================================================

@mcp.tool()
def gh_pr_list(
    repo: str = "",
    state: str = "open",
    author: str = "",
    base: str = "",
    label: str = "",
    limit: int = 30,
) -> str:
    """list pull requests. always safe."""
    return _wrap(gh.pr_list, repo=repo, state=state, author=author, base=base, label=label, limit=limit)


@mcp.tool()
def gh_pr_view(pr: str, repo: str = "") -> str:
    """view PR details, description, reviews, and comments. always safe."""
    return _wrap(gh.pr_view, pr=pr, repo=repo)


@mcp.tool()
def gh_pr_diff(pr: str, repo: str = "") -> str:
    """show the full diff for a PR. always safe."""
    return _wrap(gh.pr_diff, pr=pr, repo=repo)


@mcp.tool()
def gh_pr_checks(pr: str, repo: str = "") -> str:
    """show CI check status for a PR. gh:read — always safe."""
    return _wrap(gh.pr_checks, pr=pr, repo=repo)


@mcp.tool()
def gh_pr_review_threads(pr: str, repo: str = "") -> str:
    """list inline review comment threads with file, line, diff context and replies. gh:read — always safe."""
    return _wrap(gh.pr_review_threads, pr=pr, repo=repo)


# ===========================================================================
# GitHub: PR write
# ===========================================================================

@mcp.tool()
def gh_pr_create(
    repo_path: str = ".",
    repo: str = "",
    title: str = "",
    body: str = "",
    base: str = "main",
    draft: bool = False,
    reviewer: list[str] | None = None,
    label: list[str] | None = None,
) -> str:
    """create a pull request. ask before running."""
    return _wrap(gh.pr_create, repo_path=repo_path, repo=repo, title=title, body=body,
                 base=base, draft=draft, reviewer=reviewer, label=label)


@mcp.tool()
def gh_pr_comment(pr: str, body: str, repo: str = "", repo_path: str = ".") -> str:
    """add a comment to a PR. ask before running."""
    return _wrap(gh.pr_comment, pr=pr, body=body, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_pr_review(
    pr: str,
    event: str,
    body: str = "",
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """submit a simple PR review (approve/request-changes/comment). ask before running."""
    return _wrap(gh.pr_review, pr=pr, event=event, body=body, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_pr_add_review(
    pr: str,
    event: str,
    body: str = "",
    inline_comments: list[dict] | None = None,
    repo: str = "",
) -> str:
    """submit a PR review with inline line-level comments via GitHub API. ask before running.

    event: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'.
    inline_comments: list of {path, line, body, side?} dicts for line-level feedback.
    use this when you need to attach comments to specific lines of the diff.
    """
    return _wrap(gh.pr_add_review, pr=pr, event=event, body=body,
                 inline_comments=inline_comments, repo=repo)


@mcp.tool()
def gh_pr_reply_comment(pr: str, comment_id: int, body: str, repo: str = "") -> str:
    """reply to an inline review comment thread. ask before running.

    comment_id: from gh_pr_review_threads output.
    """
    return _wrap(gh.pr_reply_comment, pr=pr, comment_id=comment_id, body=body, repo=repo)


@mcp.tool()
def gh_pr_checkout(pr: str, repo: str = "", repo_path: str = ".") -> str:
    """check out a PR's branch locally. ask before running."""
    return _wrap(gh.pr_checkout, pr=pr, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_pr_merge(
    pr: str,
    method: str = "merge",
    delete_branch: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """merge a PR. method: 'merge', 'squash', 'rebase'. WRITES TO REMOTE. ask before running."""
    return _wrap(gh.pr_merge, pr=pr, method=method, delete_branch=delete_branch, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_pr_close(pr: str, comment: str = "", repo: str = "", repo_path: str = ".") -> str:
    """close a PR without merging. ask before running."""
    return _wrap(gh.pr_close, pr=pr, comment=comment, repo=repo, repo_path=repo_path)


# ===========================================================================
# GitHub: Issues read
# ===========================================================================

@mcp.tool()
def gh_issue_list(
    repo: str = "",
    state: str = "open",
    assignee: str = "",
    label: str = "",
    limit: int = 30,
) -> str:
    """list issues. always safe."""
    return _wrap(gh.issue_list, repo=repo, state=state, assignee=assignee, label=label, limit=limit)


@mcp.tool()
def gh_issue_view(issue: str, repo: str = "") -> str:
    """view issue details and comments. always safe."""
    return _wrap(gh.issue_view, issue=issue, repo=repo)


# ===========================================================================
# GitHub: Issues write
# ===========================================================================

@mcp.tool()
def gh_issue_create(
    title: str,
    body: str = "",
    label: list[str] | None = None,
    assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """create a new issue. ask before running."""
    return _wrap(gh.issue_create, title=title, body=body, label=label, assignee=assignee,
                 repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_issue_comment(issue: str, body: str, repo: str = "", repo_path: str = ".") -> str:
    """add a comment to an issue. ask before running."""
    return _wrap(gh.issue_comment, issue=issue, body=body, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_issue_close(
    issue: str,
    reason: str = "",
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """close an issue. reason: 'completed' or 'not planned'. ask before running."""
    return _wrap(gh.issue_close, issue=issue, reason=reason, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_issue_edit(
    issue: str,
    title: str = "",
    body: str = "",
    add_label: list[str] | None = None,
    remove_label: list[str] | None = None,
    add_assignee: list[str] | None = None,
    remove_assignee: list[str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """edit issue metadata (title, body, labels, assignees). ask before running."""
    return _wrap(gh.issue_edit, issue=issue, title=title, body=body,
                 add_label=add_label, remove_label=remove_label,
                 add_assignee=add_assignee, remove_assignee=remove_assignee,
                 repo=repo, repo_path=repo_path)


# ===========================================================================
# GitHub: Repo
# ===========================================================================

@mcp.tool()
def gh_repo_view(repo: str = "") -> str:
    """view repository info (name, stars, default branch, etc.). always safe."""
    return _wrap(gh.repo_view, repo=repo)


@mcp.tool()
def gh_repo_create(
    name: str,
    private: bool = True,
    description: str = "",
    clone: bool = False,
) -> str:
    """create a new GitHub repository. ask before running."""
    return _wrap(gh.repo_create, name=name, private=private, description=description, clone=clone)


# ===========================================================================
# GitHub: CI Runs
# ===========================================================================

@mcp.tool()
def gh_run_list(
    repo: str = "",
    workflow: str = "",
    branch: str = "",
    status: str = "",
    limit: int = 20,
    repo_path: str = ".",
) -> str:
    """list workflow runs. always safe."""
    return _wrap(gh.run_list, repo=repo, workflow=workflow, branch=branch, status=status,
                 limit=limit, repo_path=repo_path)


@mcp.tool()
def gh_run_view(run_id: str, repo: str = "", log: bool = False, repo_path: str = ".") -> str:
    """view a workflow run's overall status and jobs. log=True fetches raw step logs. gh:read — always safe."""
    return _wrap(gh.run_view, run_id=run_id, repo=repo, log=log, repo_path=repo_path)


@mcp.tool()
def gh_run_job_view(
    run_id: str,
    job_name: str = "",
    repo: str = "",
    log: bool = False,
    repo_path: str = ".",
) -> str:
    """view details or step logs for a specific job within a run. gh:read — always safe.

    job_name: partial name match (from gh_run_view output). log=True fetches step-by-step logs.
    """
    return _wrap(gh.run_job_view, run_id=run_id, job_name=job_name, repo=repo, log=log, repo_path=repo_path)


@mcp.tool()
def gh_run_rerun(
    run_id: str,
    failed_only: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """rerun a workflow run. failed_only=True reruns only failed jobs. gh:write — ask before running."""
    return _wrap(gh.run_rerun, run_id=run_id, failed_only=failed_only, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_run_cancel(run_id: str, repo: str = "", repo_path: str = ".") -> str:
    """cancel an in-progress workflow run. gh:write — ask before running."""
    return _wrap(gh.run_cancel, run_id=run_id, repo=repo, repo_path=repo_path)


# ===========================================================================
# GitHub: Workflows
# ===========================================================================

@mcp.tool()
def gh_workflow_list(repo: str = "", repo_path: str = ".") -> str:
    """list all workflows in the repository with their state and file path. gh:read — always safe."""
    return _wrap(gh.workflow_list, repo=repo, repo_path=repo_path)


@mcp.tool()
def gh_workflow_run(
    workflow: str,
    ref: str = "",
    inputs: dict[str, str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """trigger a workflow_dispatch event to run a workflow. gh:write — ask before running.

    workflow: filename, name, or id (e.g. 'ci.yml').
    ref: branch/tag to run on (default: repo default branch).
    inputs: workflow input key=value pairs.
    """
    return _wrap(gh.workflow_run, workflow=workflow, ref=ref, inputs=inputs,
                 repo=repo, repo_path=repo_path)


# ===========================================================================
# GitHub: Releases
# ===========================================================================

@mcp.tool()
def gh_release_list(repo: str = "", limit: int = 20) -> str:
    """list releases. always safe."""
    return _wrap(gh.release_list, repo=repo, limit=limit)


@mcp.tool()
def gh_release_view(tag: str, repo: str = "") -> str:
    """view release details and notes. always safe."""
    return _wrap(gh.release_view, tag=tag, repo=repo)


@mcp.tool()
def gh_release_create(
    tag: str,
    title: str = "",
    notes: str = "",
    draft: bool = False,
    prerelease: bool = False,
    generate_notes: bool = True,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """create a release. generate_notes=True auto-generates from commits. ask before running."""
    return _wrap(gh.release_create, tag=tag, title=title, notes=notes, draft=draft,
                 prerelease=prerelease, generate_notes=generate_notes, repo=repo, repo_path=repo_path)


def main() -> None:
    mcp.run(transport="stdio")

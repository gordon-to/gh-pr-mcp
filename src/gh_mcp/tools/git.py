"""git tools — all git_* MCP tool implementations.

permission levels (for Claude Code settings):
  always-allow: git_status, git_diff, git_log, git_show, git_blame,
                git_branch_list, git_remote_list, git_stash_list,
                git_worktree_list, git_tag_list
  always-allow: git_add, git_commit, git_branch_create, git_checkout,
                git_stash_push, git_stash_pop, git_init
  ask:          git_push, git_pull, git_fetch, git_clone, git_merge,
                git_rebase, git_cherry_pick, git_worktree_add,
                git_worktree_remove, git_remote_add, git_tag_create
  ask:          git_reset, git_restore, git_clean, git_branch_delete,
                git_push_force
"""

from ..run import CommandError, _validate_path, _validate_ref, format_result, run, run_ok


# ---------------------------------------------------------------------------
# read-only — always safe to allow
# ---------------------------------------------------------------------------

def status(repo_path: str = ".") -> str:
    """show working tree status (git status)."""
    return format_result(run_ok(["git", "status"], cwd=repo_path), "git status")


def diff(
    repo_path: str = ".",
    staged: bool = False,
    path: str = "",
    commit: str = "",
) -> str:
    """show changes between working tree, index, or commits (git diff).

    staged=True shows only staged changes.
    commit shows diff against that ref (e.g. 'HEAD~1', 'main').
    path restricts to a file or directory.
    """
    args = ["git", "diff"]
    if staged:
        args.append("--staged")
    if commit:
        args.append(_validate_ref(commit, "commit"))
    args.append("--")
    if path:
        args.append(_validate_path(path))
    return format_result(run_ok(args, cwd=repo_path), "git diff")


def log(
    repo_path: str = ".",
    n: int = 20,
    branch: str = "",
    oneline: bool = True,
    path: str = "",
) -> str:
    """show commit history (git log).

    n: max number of commits (default 20).
    branch: show history of a specific branch.
    oneline: compact one-line format (default True).
    path: restrict to commits touching this file/dir.
    """
    args = ["git", "log", f"-{n}"]
    if oneline:
        args.append("--oneline")
    else:
        args.extend(["--format=%H %an %ar%n  %s"])
    if branch:
        args.append(_validate_ref(branch, "branch"))
    if path:
        args.extend(["--", _validate_path(path)])
    return format_result(run_ok(args, cwd=repo_path), "git log")


def show(repo_path: str = ".", ref: str = "HEAD", path: str = "") -> str:
    """show details of a commit (git show)."""
    args = ["git", "show", _validate_ref(ref)]
    if path:
        args.extend(["--", _validate_path(path)])
    return format_result(run_ok(args, cwd=repo_path), f"git show {ref}")


def blame(repo_path: str, path: str, ref: str = "HEAD") -> str:
    """show line-by-line authorship (git blame)."""
    args = ["git", "blame", _validate_ref(ref), "--", _validate_path(path)]
    return format_result(run_ok(args, cwd=repo_path), f"git blame {path}")


def branch_list(repo_path: str = ".", all_branches: bool = False) -> str:
    """list branches (git branch -v[a])."""
    args = ["git", "branch", "-v"]
    if all_branches:
        args.append("-a")
    return format_result(run_ok(args, cwd=repo_path), "git branch")


def remote_list(repo_path: str = ".") -> str:
    """list remotes (git remote -v)."""
    return format_result(run_ok(["git", "remote", "-v"], cwd=repo_path), "git remote -v")


def stash_list(repo_path: str = ".") -> str:
    """list stash entries (git stash list)."""
    return format_result(run_ok(["git", "stash", "list"], cwd=repo_path), "git stash list")


def worktree_list(repo_path: str = ".") -> str:
    """list worktrees (git worktree list)."""
    return format_result(run_ok(["git", "worktree", "list", "--porcelain"], cwd=repo_path), "git worktree list")


def tag_list(repo_path: str = ".", pattern: str = "") -> str:
    """list tags (git tag -l)."""
    args = ["git", "tag", "-l", "--sort=-version:refname"]
    if pattern:
        args.append(_validate_ref(pattern, "pattern"))
    return format_result(run_ok(args, cwd=repo_path), "git tag -l")


# ---------------------------------------------------------------------------
# local writes — safe to always-allow (reversible, no network)
# ---------------------------------------------------------------------------

def add(repo_path: str, paths: list[str]) -> str:
    """stage files (git add).

    paths: list of files/directories to stage. Use ['.'] for all changes.
    """
    if not paths:
        raise CommandError("paths must not be empty")
    validated = [_validate_path(p) for p in paths]
    args = ["git", "add", "--"] + validated
    run(args, cwd=repo_path)
    return status(repo_path)


def commit(repo_path: str, message: str, allow_empty: bool = False) -> str:
    """create a commit (git commit).

    message: commit message.
    allow_empty: allow commits with no changes staged.
    """
    if not message.strip():
        raise CommandError("commit message must not be empty")
    args = ["git", "commit", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    return format_result(run(args, cwd=repo_path), "git commit")


def branch_create(repo_path: str, name: str, start_point: str = "", checkout: bool = True) -> str:
    """create a branch (git switch -c / git branch).

    name: new branch name.
    start_point: base ref (default: current HEAD).
    checkout: switch to new branch immediately (default True).
    """
    _validate_ref(name, "branch name")
    if checkout:
        args = ["git", "switch", "-c", name]
    else:
        args = ["git", "branch", name]
    if start_point:
        args.append(_validate_ref(start_point, "start_point"))
    return format_result(run(args, cwd=repo_path), f"git branch create {name}")


def checkout(repo_path: str, ref: str) -> str:
    """switch to a branch or commit (git switch / git checkout).

    ref: branch name or commit hash to check out.
    """
    return format_result(
        run(["git", "switch", _validate_ref(ref)], cwd=repo_path),
        f"git switch {ref}",
    )


def stash_push(repo_path: str = ".", message: str = "", include_untracked: bool = True) -> str:
    """stash current changes (git stash push)."""
    args = ["git", "stash", "push"]
    if include_untracked:
        args.append("-u")
    if message:
        args.extend(["-m", message])
    return format_result(run(args, cwd=repo_path), "git stash push")


def stash_pop(repo_path: str = ".", index: int = 0) -> str:
    """apply and drop a stash entry (git stash pop)."""
    args = ["git", "stash", "pop", f"stash@{{{index}}}"]
    return format_result(run(args, cwd=repo_path), "git stash pop")


def init(path: str, initial_branch: str = "main") -> str:
    """initialize a new git repository (git init)."""
    _validate_ref(initial_branch, "initial_branch")
    return format_result(
        run(["git", "init", "-b", initial_branch, path]),
        "git init",
    )


# ---------------------------------------------------------------------------
# remote / network — ask before running
# ---------------------------------------------------------------------------

def push(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    set_upstream: bool = False,
    tags: bool = False,
) -> str:
    """push commits to remote (git push).

    Requires network access and writes to the remote.
    branch: local branch to push (default: current branch).
    set_upstream: set tracking (-u flag).
    tags: push all tags.
    """
    args = ["git", "push", _validate_ref(remote, "remote")]
    if branch:
        args.append(_validate_ref(branch, "branch"))
    if set_upstream:
        args.append("-u")
    if tags:
        args.append("--tags")
    return format_result(run(args, cwd=repo_path), "git push")


def push_force(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    with_lease: bool = True,
) -> str:
    """force-push to remote — DESTRUCTIVE (git push --force[-with-lease]).

    with_lease: use --force-with-lease (safer, default True).
    Only use when you know remote history will be rewritten.
    """
    args = ["git", "push", _validate_ref(remote, "remote")]
    if branch:
        args.append(_validate_ref(branch, "branch"))
    args.append("--force-with-lease" if with_lease else "--force")
    return format_result(run(args, cwd=repo_path), "git push --force")


def pull(
    repo_path: str = ".",
    remote: str = "origin",
    branch: str = "",
    rebase: bool = False,
) -> str:
    """pull commits from remote (git pull)."""
    args = ["git", "pull", _validate_ref(remote, "remote")]
    if branch:
        args.append(_validate_ref(branch, "branch"))
    if rebase:
        args.append("--rebase")
    return format_result(run(args, cwd=repo_path), "git pull")


def fetch(repo_path: str = ".", remote: str = "origin", prune: bool = True) -> str:
    """fetch from remote without merging (git fetch)."""
    args = ["git", "fetch", _validate_ref(remote, "remote")]
    if prune:
        args.append("--prune")
    return format_result(run(args, cwd=repo_path), "git fetch")


def clone(url: str, destination: str = "", branch: str = "", depth: int = 0) -> str:
    """clone a remote repository (git clone)."""
    if any(c in url for c in '\x00|;&`$(){}[]<>\\! \t\n'):
        raise CommandError(f"invalid clone URL: {url!r}")
    args = ["git", "clone", url]
    if destination:
        args.append(_validate_path(destination))
    if branch:
        args.extend(["-b", _validate_ref(branch, "branch")])
    if depth > 0:
        args.extend(["--depth", str(depth)])
    return format_result(run(args), "git clone")


def merge(repo_path: str, branch: str, no_ff: bool = False, squash: bool = False) -> str:
    """merge a branch into current HEAD (git merge)."""
    args = ["git", "merge", _validate_ref(branch, "branch")]
    if no_ff:
        args.append("--no-ff")
    if squash:
        args.append("--squash")
    return format_result(run(args, cwd=repo_path), f"git merge {branch}")


def rebase(repo_path: str, onto: str, interactive: bool = False) -> str:
    """rebase current branch onto another (git rebase).

    interactive mode is not supported over stdio — use rebase_abort/continue instead.
    """
    if interactive:
        raise CommandError("interactive rebase is not supported in MCP mode; use non-interactive rebase")
    args = ["git", "rebase", _validate_ref(onto, "onto")]
    return format_result(run(args, cwd=repo_path), f"git rebase {onto}")


def rebase_abort(repo_path: str = ".") -> str:
    """abort an in-progress rebase (git rebase --abort)."""
    return format_result(run(["git", "rebase", "--abort"], cwd=repo_path), "git rebase --abort")


def rebase_continue(repo_path: str = ".") -> str:
    """continue a rebase after resolving conflicts (git rebase --continue)."""
    return format_result(run(["git", "rebase", "--continue"], cwd=repo_path), "git rebase --continue")


def cherry_pick(repo_path: str, commits: list[str]) -> str:
    """apply commits onto current HEAD (git cherry-pick)."""
    if not commits:
        raise CommandError("commits list must not be empty")
    validated = [_validate_ref(c, "commit") for c in commits]
    return format_result(run(["git", "cherry-pick"] + validated, cwd=repo_path), "git cherry-pick")


def remote_add(repo_path: str, name: str, url: str) -> str:
    """add a remote (git remote add)."""
    if any(c in url for c in '\x00|;&`$(){}[]<>\\! \t\n'):
        raise CommandError(f"invalid remote URL: {url!r}")
    _validate_ref(name, "remote name")
    return format_result(run(["git", "remote", "add", name, url], cwd=repo_path), "git remote add")


def tag_create(repo_path: str, name: str, ref: str = "HEAD", message: str = "") -> str:
    """create a tag (git tag)."""
    _validate_ref(name, "tag name")
    args = ["git", "tag"]
    if message:
        args.extend(["-a", name, "-m", message])
    else:
        args.append(name)
    args.append(_validate_ref(ref))
    return format_result(run(args, cwd=repo_path), f"git tag {name}")


def worktree_add(repo_path: str, path: str, branch: str, create_branch: bool = True) -> str:
    """add a new worktree (git worktree add)."""
    _validate_path(path)
    _validate_ref(branch, "branch")
    args = ["git", "worktree", "add"]
    if create_branch:
        args.extend(["-b", branch])
    args.extend([path, branch if not create_branch else "HEAD"])
    return format_result(run(args, cwd=repo_path), "git worktree add")


def worktree_remove(repo_path: str, path: str, force: bool = False) -> str:
    """remove a worktree (git worktree remove)."""
    args = ["git", "worktree", "remove"]
    if force:
        args.append("--force")
    args.append(_validate_path(path))
    return format_result(run(args, cwd=repo_path), "git worktree remove")


# ---------------------------------------------------------------------------
# destructive — ask before running
# ---------------------------------------------------------------------------

def reset(repo_path: str, ref: str = "HEAD", mode: str = "mixed") -> str:
    """reset HEAD to a ref — can discard commits (git reset).

    mode: 'soft' (keep staged), 'mixed' (unstage, keep files), 'hard' (discard all).
    CAUTION: hard mode permanently discards uncommitted changes.
    """
    if mode not in ("soft", "mixed", "hard"):
        raise CommandError(f"mode must be 'soft', 'mixed', or 'hard', got {mode!r}")
    return format_result(
        run(["git", "reset", f"--{mode}", _validate_ref(ref)], cwd=repo_path),
        f"git reset --{mode} {ref}",
    )


def restore(repo_path: str, paths: list[str], staged: bool = False) -> str:
    """discard changes to files — DESTRUCTIVE (git restore).

    staged: restore staged changes back to working tree.
    CAUTION: discards uncommitted changes permanently.
    """
    if not paths:
        raise CommandError("paths must not be empty")
    args = ["git", "restore"]
    if staged:
        args.append("--staged")
    args.extend(["--"] + [_validate_path(p) for p in paths])
    return format_result(run(args, cwd=repo_path), "git restore")


def clean(repo_path: str, directories: bool = False, force: bool = True, dry_run: bool = False) -> str:
    """remove untracked files — DESTRUCTIVE (git clean).

    dry_run: show what would be removed without deleting.
    CAUTION: permanently deletes untracked files.
    """
    args = ["git", "clean"]
    if dry_run:
        args.append("-n")
    elif force:
        args.append("-f")
    else:
        raise CommandError("clean requires force=True or dry_run=True")
    if directories:
        args.append("-d")
    return format_result(run(args, cwd=repo_path), "git clean")


def branch_delete(repo_path: str, name: str, force: bool = False, remote: str = "") -> str:
    """delete a branch (git branch -d / git push --delete).

    force: use -D to delete unmerged branches.
    remote: if given, delete the remote-tracking branch too.
    """
    _validate_ref(name, "branch name")
    flag = "-D" if force else "-d"
    out = run(["git", "branch", flag, name], cwd=repo_path)
    if remote:
        _validate_ref(remote, "remote")
        out += "\n" + run(["git", "push", remote, "--delete", name], cwd=repo_path)
    return format_result(out, f"git branch delete {name}")

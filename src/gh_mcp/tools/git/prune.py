from ...app import tool
from ...run import _validate_ref, format_result, run, run_ok


@tool("git")
def prune(
    repo_path: str,
    remote: str = "origin",
    remote_refs: bool = True,
    gone_branches: bool = True,
    worktrees: bool = True,
    dry_run: bool = False,
) -> str:
    """clean up local-only state: stale remote-tracking refs, merged branches, and worktree admin entries.

    does NOT touch the remote — no pushes, no deletes on the server. each
    cleanup step is gated by a flag. the steps (in order):

    1. remote_refs: `git remote prune <remote>`
       removes local remote-tracking refs (e.g. `refs/remotes/origin/foo`)
       whose upstream no longer exists on the remote. same effect as
       `git fetch --prune` but without contacting the remote.

    2. gone_branches: delete local branches whose upstream is gone.
       identifies branches via `git for-each-ref` with `%(upstream:track) == [gone]`
       — i.e. their tracking branch was deleted (typically by a merged PR).
       uses `git branch -D` (force) so squash-merged branches, which git
       doesn't see as reachable from HEAD, are still removed. the current
       branch is always skipped.

    3. worktrees: `git worktree prune`
       removes metadata in `.git/worktrees/` for worktree directories that
       were deleted manually (outside `git worktree remove`).

    dry_run: if True, report what would happen without making changes. the
        remote-ref and worktree steps use their native `--dry-run` flags;
        gone-branch deletion is simulated.
    """
    _validate_ref(remote, "remote")
    lines: list[str] = []
    header = "[dry-run] " if dry_run else ""

    if remote_refs:
        args = ["git", "remote", "prune", remote]
        if dry_run:
            args.append("--dry-run")
        out = run_ok(args, cwd=repo_path)
        lines.append(f"{header}remote prune {remote}:")
        lines.append(out or "  (nothing to prune)")

    if gone_branches:
        current = run_ok(["git", "symbolic-ref", "--short", "HEAD"], cwd=repo_path)
        refs_out = run(
            [
                "git",
                "for-each-ref",
                "--format=%(refname:short) %(upstream:track)",
                "refs/heads/",
            ],
            cwd=repo_path,
        )
        gone = []
        for line in refs_out.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1].strip() == "[gone]":
                name = parts[0]
                if name != current:
                    gone.append(name)

        lines.append(f"{header}delete gone branches:")
        if not gone:
            lines.append("  (none)")
        else:
            for name in gone:
                if dry_run:
                    lines.append(f"  would delete {name}")
                else:
                    out = run(["git", "branch", "-D", name], cwd=repo_path)
                    lines.append(f"  {out}")

    if worktrees:
        args = ["git", "worktree", "prune", "-v"]
        if dry_run:
            args.append("--dry-run")
        out = run_ok(args, cwd=repo_path)
        lines.append(f"{header}worktree prune:")
        lines.append(out or "  (nothing to prune)")

    return format_result("\n".join(lines), "git prune")

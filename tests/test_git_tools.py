"""tests for git tools."""

import subprocess
from pathlib import Path

import pytest

from gh_mcp.tools.git import (
    add,
    blame,
    branch_create,
    branch_delete,
    branch_list,
    checkout,
    clean,
    commit,
    diff,
    fetch,
    log,
    merge,
    merge_base,
    prune,
    pull,
    push,
    rebase,
    rebase_abort,
    rebase_continue,
    remote_add,
    remote_list,
    reset,
    restore,
    show,
    stash_list,
    stash_pop,
    stash_push,
    status,
    tag_create,
    tag_list,
    worktree_add,
    worktree_list,
    worktree_remove,
)

# push/pull/fetch are tested with a local bare repo acting as remote (see test_push_pull_fetch)
from gh_mcp.run import CommandError


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def test_status_clean_repo(git_repo):
    result = status(str(git_repo))
    assert "nothing to commit" in result or "clean" in result


def test_status_with_changes(git_repo_with_changes):
    result = status(str(git_repo_with_changes))
    assert "staged.txt" in result
    assert "unstaged.txt" in result


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------

def test_diff_empty_on_clean_repo(git_repo):
    result = diff(str(git_repo))
    assert result == "(no output) from `git diff`"


def test_diff_shows_unstaged_changes(git_repo):
    (Path(git_repo) / "file.txt").write_text("hello\n")
    subprocess.run(["git", "add", "file.txt"], cwd=git_repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add file"],
        cwd=git_repo, capture_output=True,
    )
    (Path(git_repo) / "file.txt").write_text("hello world\n")
    result = diff(str(git_repo))
    assert "hello world" in result or "+hello world" in result or "hello" in result


def test_diff_staged(git_repo_with_changes):
    result = diff(str(git_repo_with_changes), staged=True)
    assert "staged" in result


def test_diff_invalid_ref_raises(git_repo):
    with pytest.raises(CommandError):
        diff(str(git_repo), commit="bad;ref")


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------

def test_log_shows_commits(git_repo):
    result = log(str(git_repo))
    assert "initial commit" in result


def test_log_oneline(git_repo):
    result = log(str(git_repo), oneline=True)
    # oneline format: hash message — no newlines within entry
    lines = [l for l in result.splitlines() if l.strip()]
    assert len(lines) >= 1
    assert "initial commit" in lines[0]


def test_log_n_limit(git_repo):
    for i in range(5):
        (Path(git_repo) / f"f{i}.txt").write_text(f"{i}\n")
        subprocess.run(["git", "add", f"f{i}.txt"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"commit {i}"],
            cwd=git_repo, capture_output=True,
        )
    result = log(str(git_repo), n=3)
    lines = [l for l in result.splitlines() if l.strip()]
    assert len(lines) == 3


def test_log_base_range(git_repo):
    """base..HEAD shows only commits on the branch, not the base."""
    base_sha = log(str(git_repo), n=1).split()[0]

    branch_create(str(git_repo), name="feat", checkout=True)
    for i in range(3):
        (Path(git_repo) / f"feat{i}.txt").write_text(f"{i}\n")
        add(str(git_repo), [f"feat{i}.txt"])
        commit(str(git_repo), f"feat commit {i}")

    result = log(str(git_repo), base=base_sha)
    lines = [l for l in result.splitlines() if l.strip()]
    assert len(lines) == 3
    assert all("feat commit" in l for l in lines)


def test_log_base_branch_range(git_repo):
    """base..branch works when branch is explicitly named."""
    branch_create(str(git_repo), name="feat", checkout=True)
    (Path(git_repo) / "x.txt").write_text("x\n")
    add(str(git_repo), ["x.txt"])
    commit(str(git_repo), "feat: add x")

    checkout(str(git_repo), "main")
    result = log(str(git_repo), base="main", branch="feat")
    assert "feat: add x" in result


def test_log_graph(git_repo):
    """graph flag produces graph decoration characters."""
    result = log(str(git_repo), graph=True)
    assert "*" in result


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def test_show_head(git_repo):
    result = show(str(git_repo), ref="HEAD")
    assert "initial commit" in result


# ---------------------------------------------------------------------------
# blame
# ---------------------------------------------------------------------------

def test_blame_file(git_repo):
    result = blame(str(git_repo), path="README.md")
    assert "test repo" in result or "README" in result


# ---------------------------------------------------------------------------
# add + commit
# ---------------------------------------------------------------------------

def test_add_and_commit(git_repo):
    (Path(git_repo) / "new.txt").write_text("content\n")
    add(str(git_repo), ["new.txt"])
    result = commit(str(git_repo), message="add new.txt")
    assert "new.txt" in result or "add new.txt" in result or "master" in result or "main" in result


def test_add_invalid_path_raises(git_repo):
    with pytest.raises(CommandError):
        add(str(git_repo), ["bad|path"])


def test_commit_empty_message_raises(git_repo):
    with pytest.raises(CommandError):
        commit(str(git_repo), message="   ")


def test_commit_nothing_staged_raises(git_repo):
    with pytest.raises(CommandError):
        commit(str(git_repo), message="should fail")


# ---------------------------------------------------------------------------
# branch operations
# ---------------------------------------------------------------------------

def test_branch_list(git_repo):
    result = branch_list(str(git_repo))
    assert "main" in result


def test_branch_list_verbose(git_repo):
    result = branch_list(str(git_repo), verbose=True)
    assert "main" in result


def test_branch_create_and_checkout(git_repo):
    branch_create(str(git_repo), name="feature/test", checkout=True)
    result = branch_list(str(git_repo))
    assert "feature/test" in result


def test_branch_create_invalid_name_raises(git_repo):
    with pytest.raises(CommandError):
        branch_create(str(git_repo), name="bad;name")


def test_branch_delete(git_repo):
    branch_create(str(git_repo), name="to-delete", checkout=False)
    branch_delete(str(git_repo), name="to-delete")
    result = branch_list(str(git_repo))
    assert "to-delete" not in result


def test_branch_delete_unmerged_requires_force(git_repo):
    branch_create(str(git_repo), name="unmerged", checkout=True)
    (Path(git_repo) / "extra.txt").write_text("extra\n")
    add(str(git_repo), ["extra.txt"])
    commit(str(git_repo), "extra commit")
    checkout(str(git_repo), "main")
    with pytest.raises(CommandError):
        branch_delete(str(git_repo), name="unmerged", force=False)


# ---------------------------------------------------------------------------
# checkout
# ---------------------------------------------------------------------------

def test_checkout_existing_branch(git_repo):
    branch_create(str(git_repo), name="other", checkout=False)
    checkout(str(git_repo), "other")
    result = branch_list(str(git_repo))
    assert "* other" in result or "other" in result


def test_checkout_invalid_ref_raises(git_repo):
    with pytest.raises(CommandError):
        checkout(str(git_repo), "nonexistent-branch-xyz")


# ---------------------------------------------------------------------------
# stash
# ---------------------------------------------------------------------------

def test_stash_push_and_pop(git_repo):
    (Path(git_repo) / "stashed.txt").write_text("will be stashed\n")
    stash_push(str(git_repo), message="test stash")
    lst = stash_list(str(git_repo))
    assert "test stash" in lst
    stash_pop(str(git_repo))
    assert (Path(git_repo) / "stashed.txt").exists()


def test_stash_list_empty(git_repo):
    result = stash_list(str(git_repo))
    assert "(no output)" in result


# ---------------------------------------------------------------------------
# remote
# ---------------------------------------------------------------------------

def test_remote_list_empty(git_repo):
    result = remote_list(str(git_repo))
    assert "(no output)" in result


def test_remote_add(git_repo, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", str(other)], capture_output=True)
    remote_add(str(git_repo), name="upstream", url=str(other))
    result = remote_list(str(git_repo))
    assert "upstream" in result


# ---------------------------------------------------------------------------
# tags
# ---------------------------------------------------------------------------

def test_tag_create_and_list(git_repo):
    tag_create(str(git_repo), name="v1.0.0")
    result = tag_list(str(git_repo))
    assert "v1.0.0" in result


def test_tag_create_annotated(git_repo):
    tag_create(str(git_repo), name="v2.0.0", message="release v2")
    result = tag_list(str(git_repo))
    assert "v2.0.0" in result


# ---------------------------------------------------------------------------
# worktrees
# ---------------------------------------------------------------------------

def test_worktree_add_and_list_and_remove(git_repo, tmp_path):
    wt_path = str(tmp_path / "worktree1")
    worktree_add(str(git_repo), path=wt_path, branch="wt-branch", create_branch=True)
    result = worktree_list(str(git_repo))
    assert wt_path in result
    worktree_remove(str(git_repo), path=wt_path)
    result2 = worktree_list(str(git_repo))
    assert wt_path not in result2


# ---------------------------------------------------------------------------
# reset and restore
# ---------------------------------------------------------------------------

def test_reset_soft(git_repo):
    (Path(git_repo) / "r.txt").write_text("r\n")
    add(str(git_repo), ["r.txt"])
    commit(str(git_repo), "add r")
    reset(str(git_repo), ref="HEAD~1", mode="soft")
    result = status(str(git_repo))
    assert "r.txt" in result


def test_reset_hard_removes_changes(git_repo):
    (Path(git_repo) / "h.txt").write_text("h\n")
    add(str(git_repo), ["h.txt"])
    commit(str(git_repo), "add h")
    reset(str(git_repo), ref="HEAD~1", mode="hard")
    assert not (Path(git_repo) / "h.txt").exists()


def test_reset_invalid_mode_raises(git_repo):
    with pytest.raises(CommandError):
        reset(str(git_repo), mode="invalid")


def test_restore_discards_changes(git_repo):
    readme = Path(git_repo) / "README.md"
    original = readme.read_text()
    readme.write_text("modified\n")
    restore(str(git_repo), paths=["README.md"])
    assert readme.read_text() == original


# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------

def test_clean_dry_run(git_repo):
    (Path(git_repo) / "untracked.txt").write_text("untracked\n")
    result = clean(str(git_repo), dry_run=True)
    assert "untracked.txt" in result


def test_clean_removes_files(git_repo):
    (Path(git_repo) / "toclean.txt").write_text("clean me\n")
    clean(str(git_repo), force=True)
    assert not (Path(git_repo) / "toclean.txt").exists()


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

def test_merge_branch(git_repo):
    branch_create(str(git_repo), name="feature", checkout=True)
    (Path(git_repo) / "feature.txt").write_text("feature\n")
    add(str(git_repo), ["feature.txt"])
    commit(str(git_repo), "add feature")
    checkout(str(git_repo), "main")
    result = merge(str(git_repo), branch="feature")
    assert "feature" in result or "Already up to date" in result or "Merge" in result or "Fast-forward" in result


# ---------------------------------------------------------------------------
# merge-base
# ---------------------------------------------------------------------------


def test_merge_base_returns_fork_point(git_repo):
    """fork point is the commit that was HEAD before each branch diverged."""
    fork_sha = log(str(git_repo), n=1).split()[0]

    branch_create(str(git_repo), name="feat", checkout=True)
    (Path(git_repo) / "feat.txt").write_text("feat\n")
    add(str(git_repo), ["feat.txt"])
    commit(str(git_repo), "feat")

    checkout(str(git_repo), "main")
    (Path(git_repo) / "main.txt").write_text("main\n")
    add(str(git_repo), ["main.txt"])
    commit(str(git_repo), "main work")

    result = merge_base(str(git_repo), branch="feat", base="main")
    assert result.startswith(fork_sha)


def test_merge_base_symmetric(git_repo):
    """argument order doesn't matter."""
    branch_create(str(git_repo), name="feat", checkout=True)
    (Path(git_repo) / "feat.txt").write_text("feat\n")
    add(str(git_repo), ["feat.txt"])
    commit(str(git_repo), "feat")

    a = merge_base(str(git_repo), branch="feat", base="main")
    b = merge_base(str(git_repo), branch="main", base="feat")
    assert a == b


def test_merge_base_invalid_ref_raises(git_repo):
    with pytest.raises(CommandError):
        merge_base(str(git_repo), branch="HEAD", base="; rm -rf /")


# ---------------------------------------------------------------------------
# push / pull / fetch (uses a local bare repo as remote)
# ---------------------------------------------------------------------------

@pytest.fixture()
def git_repo_with_remote(git_repo: Path, tmp_path: Path):
    """repo with a local bare clone acting as 'origin'."""
    bare = tmp_path / "bare.git"
    subprocess.run(
        ["git", "clone", "--bare", str(git_repo), str(bare)],
        check=True, capture_output=True,
    )
    remote_add(str(git_repo), name="origin", url=str(bare))
    return git_repo, bare


def test_push_and_fetch(git_repo_with_remote):
    repo, bare = git_repo_with_remote
    (repo / "pushed.txt").write_text("pushed\n")
    add(str(repo), ["pushed.txt"])
    commit(str(repo), "add pushed")
    push(str(repo), remote="origin", branch="main")

    clone_dir = repo.parent / "clone2"
    subprocess.run(
        ["git", "clone", str(bare), str(clone_dir)],
        check=True, capture_output=True,
    )
    assert (clone_dir / "pushed.txt").exists()


def test_pull_updates_repo(git_repo_with_remote, tmp_path):
    repo, bare = git_repo_with_remote
    # push a commit from a second clone to the bare remote
    clone2 = tmp_path / "clone2"
    subprocess.run(["git", "clone", str(bare), str(clone2)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=clone2, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=clone2, capture_output=True)
    (clone2 / "from_clone2.txt").write_text("from clone2\n")
    subprocess.run(["git", "add", "from_clone2.txt"], cwd=clone2, capture_output=True)
    subprocess.run(["git", "commit", "-m", "from clone2"], cwd=clone2, capture_output=True)
    subprocess.run(["git", "push"], cwd=clone2, capture_output=True)

    # pull into the original repo
    pull(str(repo), remote="origin", branch="main")
    assert (repo / "from_clone2.txt").exists()


def test_fetch_nonexistent_remote_fails(git_repo):
    with pytest.raises(CommandError):
        fetch(str(git_repo), remote="nonexistent")


# ---------------------------------------------------------------------------
# rebase — clean and conflict resolution
# ---------------------------------------------------------------------------

def test_rebase_no_conflict(git_repo):
    """rebase onto a branch that doesn't conflict completes cleanly."""
    branch_create(str(git_repo), name="feature", checkout=True)
    (Path(git_repo) / "feature.txt").write_text("feature\n")
    add(str(git_repo), ["feature.txt"])
    commit(str(git_repo), "feature: add feature.txt")

    checkout(str(git_repo), "main")
    (Path(git_repo) / "other.txt").write_text("other\n")
    add(str(git_repo), ["other.txt"])
    commit(str(git_repo), "main: add other.txt")

    checkout(str(git_repo), "feature")
    result = rebase(str(git_repo), onto="main")
    assert "Successfully rebased" in result or "is up to date" in result or "Fast-forwarded" in result


def test_rebase_conflict_resolve_and_continue(git_repo):
    """conflict resolution: git_add then rebase_continue must not hang or open an editor."""
    # create conflicting edit on feature branch
    branch_create(str(git_repo), name="feature", checkout=True)
    readme = Path(git_repo) / "README.md"
    readme.write_text("feature edit\n")
    add(str(git_repo), ["README.md"])
    commit(str(git_repo), "feature: edit README")

    # create conflicting edit on main
    checkout(str(git_repo), "main")
    readme.write_text("main edit\n")
    add(str(git_repo), ["README.md"])
    commit(str(git_repo), "main: edit README")

    # rebase feature onto main — expect conflict
    checkout(str(git_repo), "feature")
    with pytest.raises(CommandError):
        rebase(str(git_repo), onto="main")

    # resolve conflict
    readme.write_text("resolved\n")
    add(str(git_repo), ["README.md"])

    # continue — must complete without opening an editor (GIT_EDITOR=true)
    result = rebase_continue(str(git_repo))
    assert "Successfully rebased" in result or "Applied" in result or "rebased" in result.lower()

    # confirm feature is now ahead of main with the rebased commit
    log_result = log(str(git_repo), n=3)
    assert "feature: edit README" in log_result


def test_rebase_abort(git_repo):
    """rebase_abort restores the pre-rebase state."""
    branch_create(str(git_repo), name="feature", checkout=True)
    readme = Path(git_repo) / "README.md"
    readme.write_text("feature\n")
    add(str(git_repo), ["README.md"])
    commit(str(git_repo), "feature: edit")

    checkout(str(git_repo), "main")
    readme.write_text("main\n")
    add(str(git_repo), ["README.md"])
    commit(str(git_repo), "main: edit")

    checkout(str(git_repo), "feature")
    with pytest.raises(CommandError):
        rebase(str(git_repo), onto="main")

    rebase_abort(str(git_repo))
    # back on feature with original content
    assert readme.read_text() == "feature\n"


# ---------------------------------------------------------------------------
# commit --amend
# ---------------------------------------------------------------------------

def test_commit_amend_keeps_single_commit(git_repo):
    """amend must replace HEAD, not create a new commit."""
    (Path(git_repo) / "a.txt").write_text("a\n")
    add(str(git_repo), ["a.txt"])
    commit(str(git_repo), "first")

    before = log(str(git_repo), n=10).count("\n")

    (Path(git_repo) / "b.txt").write_text("b\n")
    add(str(git_repo), ["b.txt"])
    commit(str(git_repo), "first (amended)", amend=True)

    after_log = log(str(git_repo), n=10)
    assert after_log.count("\n") == before
    assert "first (amended)" in after_log
    assert "first\n" not in after_log.replace("first (amended)", "")


def test_commit_amend_reword_without_staged_changes(git_repo):
    """amend with nothing staged just rewrites HEAD's message."""
    (Path(git_repo) / "a.txt").write_text("a\n")
    add(str(git_repo), ["a.txt"])
    commit(str(git_repo), "original message")

    commit(str(git_repo), "reworded message", amend=True, allow_empty=True)

    log_result = log(str(git_repo), n=5)
    assert "reworded message" in log_result
    assert "original message" not in log_result


# ---------------------------------------------------------------------------
# rebase --onto (three-point)
# ---------------------------------------------------------------------------

def test_rebase_onto_moves_commits_to_new_base(git_repo):
    """git rebase --onto <newbase> <upstream> transplants commits between refs."""
    # main: initial
    # topic: branches off main, adds topic.txt
    # feature: branches off topic, adds feature.txt
    # we want feature's commits replayed directly onto main (skipping topic).
    branch_create(str(git_repo), name="topic", checkout=True)
    (Path(git_repo) / "topic.txt").write_text("topic\n")
    add(str(git_repo), ["topic.txt"])
    commit(str(git_repo), "topic: add topic.txt")

    branch_create(str(git_repo), name="feature", checkout=True)
    (Path(git_repo) / "feature.txt").write_text("feature\n")
    add(str(git_repo), ["feature.txt"])
    commit(str(git_repo), "feature: add feature.txt")

    # rebase --onto main topic feature: replay commits reachable from feature
    # but not topic, onto main. drops topic.txt, keeps feature.txt.
    rebase(str(git_repo), onto="main", upstream="topic", branch="feature")

    assert (Path(git_repo) / "feature.txt").exists()
    assert not (Path(git_repo) / "topic.txt").exists()
    log_result = log(str(git_repo), n=5)
    assert "feature: add feature.txt" in log_result
    assert "topic: add topic.txt" not in log_result


def test_rebase_onto_without_branch_arg(git_repo):
    """upstream without branch rebases the current HEAD."""
    branch_create(str(git_repo), name="topic", checkout=True)
    (Path(git_repo) / "topic.txt").write_text("topic\n")
    add(str(git_repo), ["topic.txt"])
    commit(str(git_repo), "topic: add topic.txt")

    branch_create(str(git_repo), name="feature", checkout=True)
    (Path(git_repo) / "feature.txt").write_text("feature\n")
    add(str(git_repo), ["feature.txt"])
    commit(str(git_repo), "feature: add feature.txt")

    # already on feature; omit the branch arg
    rebase(str(git_repo), onto="main", upstream="topic")

    assert (Path(git_repo) / "feature.txt").exists()
    assert not (Path(git_repo) / "topic.txt").exists()


def test_rebase_branch_without_upstream_raises(git_repo):
    """branch without upstream is a misconfiguration."""
    with pytest.raises(CommandError):
        rebase(str(git_repo), onto="main", branch="feature")


# ---------------------------------------------------------------------------
# prune — local-only cleanup
# ---------------------------------------------------------------------------

def _setup_repo_with_gone_branch(git_repo: Path, tmp_path: Path) -> Path:
    """build a repo where local branch 'feature' tracks an origin ref that
    has since been deleted — so its upstream appears as [gone]."""
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "clone", "--bare", str(git_repo), str(bare)], check=True, capture_output=True)
    remote_add(str(git_repo), name="origin", url=str(bare))

    branch_create(str(git_repo), name="feature", checkout=True)
    (git_repo / "f.txt").write_text("f\n")
    add(str(git_repo), ["f.txt"])
    commit(str(git_repo), "feature work")
    push(str(git_repo), remote="origin", branch="feature", set_upstream=True)

    # delete the branch on the bare remote; local still tracks origin/feature
    subprocess.run(["git", "branch", "-D", "feature"], cwd=bare, check=True, capture_output=True)
    # refresh local remote-tracking state so [gone] shows up
    fetch(str(git_repo), remote="origin")

    checkout(str(git_repo), "main")
    return git_repo


def test_prune_deletes_gone_branches(git_repo, tmp_path):
    repo = _setup_repo_with_gone_branch(git_repo, tmp_path)

    before = branch_list(str(repo))
    assert "feature" in before

    result = prune(str(repo), remote_refs=False, worktrees=False)

    after = branch_list(str(repo))
    assert "feature" not in after
    assert "feature" in result


def test_prune_dry_run_does_not_delete(git_repo, tmp_path):
    repo = _setup_repo_with_gone_branch(git_repo, tmp_path)

    result = prune(str(repo), dry_run=True)
    assert "dry-run" in result
    assert "would delete feature" in result
    # branch still there
    assert "feature" in branch_list(str(repo))


def test_prune_skips_current_branch(git_repo, tmp_path):
    """even if the current branch's upstream is gone, it is not deleted."""
    repo = _setup_repo_with_gone_branch(git_repo, tmp_path)
    # stay on the gone-upstream branch
    checkout(str(repo), "feature")

    prune(str(repo))

    # current branch preserved
    assert "feature" in branch_list(str(repo))


def test_prune_worktree_cleans_deleted_directory(git_repo, tmp_path):
    wt = tmp_path / "detached-wt"
    worktree_add(str(git_repo), path=str(wt), branch="wt-branch")
    # simulate manual deletion of the worktree directory
    subprocess.run(["rm", "-rf", str(wt)], check=True)

    result = prune(str(git_repo), remote_refs=False, gone_branches=False)

    listing = worktree_list(str(git_repo))
    assert str(wt) not in listing
    assert "worktree prune" in result


def test_prune_all_flags_off_is_noop(git_repo):
    result = prune(
        str(git_repo),
        remote_refs=False,
        gone_branches=False,
        worktrees=False,
    )
    assert result == "(no output) from `git prune`"


def test_prune_invalid_remote_rejected(git_repo):
    with pytest.raises(CommandError):
        prune(str(git_repo), remote="bad;name")

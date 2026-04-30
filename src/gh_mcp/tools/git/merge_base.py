from ...app import tool
from ...run import _validate_ref, format_result, run


@tool("git")
def merge_base(repo_path: str = ".", branch: str = "HEAD", base: str = "origin/main") -> str:
    """find the best common ancestor of two commits (git merge-base).

    returns the SHA of the most recent commit reachable from both refs,
    i.e. where `branch` forked from `base`. defaults answer the common
    question: where did the current branch diverge from origin/main?

    merge-base is symmetric — the order of `branch` and `base` doesn't
    matter; the names just reflect typical intent.

    for related queries, prefer the existing tools:
      - "what changed on my branch?" → git_diff(commit="origin/main...HEAD")
        (three-dot diff uses the merge base automatically).
      - "what commits are on my branch?" → git_log(base="origin/main")
        (the base..HEAD range uses the merge base automatically).
    use this tool when you actually need the fork-point SHA.
    """
    args = [
        "git",
        "merge-base",
        _validate_ref(branch, "branch"),
        _validate_ref(base, "base"),
    ]
    return format_result(run(args, cwd=repo_path), "git merge-base")

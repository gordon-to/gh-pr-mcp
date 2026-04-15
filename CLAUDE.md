# gh-mcp — codebase guide

## Project overview

MCP server that wraps `git` and `gh` (GitHub CLI) into structured, typed tools.
Goal: replace all raw git/gh shell usage with named tools that have explicit permission levels.

## Running tests

```bash
uv run pytest          # all tests
uv run pytest -x       # stop on first failure
uv run pytest tests/test_git_tools.py   # git tools only
```

## Development workflow

This repo uses worktrees so the main branch always points at a stable copy:

```
/Users/ag/projects/gh_mcp       # main branch — stable, used by global MCP config
/Users/ag/projects/gh-mcp-dev   # feat/* branch — active development
```

- **Never commit directly to main.** All changes go through PRs.
- When starting a new feature: `git_worktree_add` to create a fresh worktree on a new branch.
- The `.mcp.json` in this repo points at the dev worktree so Claude tests against the latest code.

## Architecture

```
src/gh_mcp/
  server.py       — FastMCP app, tool registrations, _wrap() error handler
  run.py          — run(), run_ok(), _validate_ref(), _validate_path(), CommandError
  tools/
    git.py        — all git_* implementations (pure functions, no MCP coupling)
    gh.py         — all gh_* implementations (pure functions, no MCP coupling)
tests/
  conftest.py     — git_repo, git_repo_with_changes fixtures (tmp_path based)
  test_git_tools.py  — integration tests against real git
  test_gh_tools.py   — unit tests with subprocess.run mocked
```

## Tool design rules

1. **One tool per operation** — no `run_git_command` catch-all. This is what enables per-tool permissions.
2. **All inputs validated** — `_validate_ref()` and `_validate_path()` before any subprocess call.
3. **`subprocess.run` with list args only** — never `shell=True`. The validators are defense-in-depth, not the primary protection.
4. **`run()` raises `CommandError` on non-zero exit** — `_wrap()` in server.py catches and returns as string.
5. **`run_ok()` returns combined stdout+stderr regardless of exit** — use for commands where partial output is useful (e.g. `git diff`).

## Permission levels

Match tool names in Claude Code's `settings.json` permissions:

| Tier | Tool names | Suggested permission |
|------|-----------|---------------------|
| `git:read` | `git_status`, `git_diff`, `git_log`, `git_show`, `git_blame`, `git_branch_list`, `git_remote_list`, `git_stash_list`, `git_worktree_list`, `git_tag_list` | `allow` |
| `git:local-write` | `git_add`, `git_commit`, `git_branch_create`, `git_checkout`, `git_stash_push`, `git_stash_pop`, `git_init` | `allow` |
| `git:remote-read` | `git_fetch`, `git_pull`, `git_clone` | `allow` |
| `git:remote-write` | `git_push`, `git_remote_add`, `git_tag_create` | `ask` |
| `git:integrate` | `git_merge`, `git_rebase`, `git_rebase_abort`, `git_rebase_continue`, `git_cherry_pick`, `git_worktree_add`, `git_worktree_remove` | `ask` |
| `git:local-destructive` | `git_reset`, `git_restore`, `git_clean`, `git_branch_delete` | `ask` |
| `git:remote-destructive` | `git_push_force` | `ask` / `block` |
| `gh:read` | `gh_pr_list`, `gh_pr_view`, `gh_pr_diff`, `gh_pr_checks`, `gh_pr_review_threads`, `gh_issue_list`, `gh_issue_view`, `gh_run_list`, `gh_run_view`, `gh_run_job_view`, `gh_workflow_list`, `gh_repo_view`, `gh_release_list`, `gh_release_view` | `allow` |
| `gh:write` | `gh_pr_create`, `gh_pr_comment`, `gh_pr_review`, `gh_pr_add_review`, `gh_pr_reply_comment`, `gh_pr_checkout`, `gh_issue_create`, `gh_issue_comment`, `gh_issue_close`, `gh_issue_edit`, `gh_run_rerun`, `gh_run_cancel`, `gh_workflow_run` | `ask` |
| `gh:merge` | `gh_pr_merge`, `gh_pr_close`, `gh_repo_create`, `gh_release_create` | `ask` |

## Adding a new tool

1. Implement the function in `tools/git.py` or `tools/gh.py` (no MCP imports).
2. Register it with `@mcp.tool()` in `server.py`.
3. Add tests — integration test for git tools, mock test for gh tools.
4. Update the permission table in this file and in `README.md`.

## Python conventions

- Python ≥ 3.11 — use `str | None` union syntax, not `Optional`.
- No `unwrap()`/`expect()` equivalents — always raise `CommandError` with context.
- Functions in `tools/*.py` are pure: they take primitives, return strings, raise `CommandError`.
- Comments only where logic isn't obvious. Lowercase for inline comments.

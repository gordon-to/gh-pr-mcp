# gh-mcp — codebase guide

## Project overview

A minimal MCP server for the GitHub operations that `gh` and `git` don't cover well on their own. Two reasons a tool earns a place here:

1. It composes verbose `gh` output into a short summary that saves tokens.
2. It calls the GitHub REST or GraphQL API directly for things `gh` can't do in one shot (resolve/unresolve threads, reply to / edit / delete a review comment by id, submit a review with inline comments at specific lines).

Anything else — `git status`, `git diff`, `gh pr create`, `gh issue list`, etc. — is faster and more flexible from the shell directly. Don't add tools for them.

## Running tests

```bash
uv run pytest          # all tests
uv run pytest -x       # stop on first failure
```

## Development workflow

Two fixed roles, strictly separated:

- `/Users/ag/projects/gh_mcp` — always on `main`. This is the **stable base repo** and the default server referenced by the global MCP config (`~/.claude.json`). Never do feature work here.
- `/Users/ag/projects/gh-mcp-<slug>/` — a **worktree** on a feature branch. This is where agents work. The committed `.mcp.json` makes each worktree its own hot-reload server (uv runs from the worktree's cwd), so Claude Code opened inside the worktree tests against the agent's own in-flight changes.

Starting a feature:

```
git worktree add /Users/ag/projects/gh-mcp-<slug> -b claude-<slug>
cd /Users/ag/projects/gh-mcp-<slug>
# start Claude Code here — its MCP server runs from this worktree's code
```

Rules:

- **Never commit directly to main.** PR every change.
- **Never do feature work in the base repo.** If you find yourself on a non-main branch there, stop, move to a worktree.
- After merging a PR, update the base repo (`git checkout main && git pull` in `/Users/ag/projects/gh_mcp`) so the global server picks up the new tools on next restart.
- Remove the worktree once the branch is merged (`git worktree remove …`).

## Architecture

```
src/gh_mcp/
  server.py       — FastMCP app, tool registration entrypoint
  app.py          — mcp instance + @tool decorator
  run.py          — run_ok(), _validate_ref(), CommandError, format_result
  tools/gh/
    _api.py                  — gh api REST + GraphQL helpers
    pr_view.py               — pr_view, pr_checks, pr_files, pr_review_threads
    pr_list.py               — pr_list
    pr_review.py             — pr_add_review, pr_reply_comment
    pr_resolve_thread.py     — pr_resolve_thread, pr_unresolve_thread
    pr_edit_comment.py
    pr_delete_comment.py
    run_view.py              — run_view, run_job_view
tests/
  test_gh_tools.py           — unit tests with subprocess.run mocked
```

## Tool design rules

1. **`subprocess.run` with list args only** — never `shell=True`. `_validate_ref()` is defense-in-depth, not the primary protection.
2. **Pure functions in `tools/gh/*.py`** — take primitives, return strings, raise `CommandError`. No MCP coupling.
3. **`run_ok()` returns combined stdout+stderr regardless of exit** — use for commands where partial output is useful.
4. **Compose API output into short summaries** — if a tool just shells out verbatim, it doesn't earn its place. If you can't show why the helper saves tokens or unlocks an API call `gh` can't make, don't add it.

## Permission levels

Tool names match Claude Code's `settings.json` permissions. All thirteen tools are intended to be `allow` — the model picks them when the structured output or API access is worth it. Pair this with a Bash deny on `gh api …` so direct API calls go through these helpers instead.

| Tool | Permission | Notes |
|------|-----------|-------|
| `gh_pr_view`, `gh_pr_list`, `gh_pr_checks`, `gh_pr_files`, `gh_pr_review_threads` | `allow` | Read-only, composed summaries |
| `gh_run_view`, `gh_run_job_view` | `allow` | Read-only, useful when CI logs are large |
| `gh_pr_add_review`, `gh_pr_reply_comment` | `allow` | Posts review content |
| `gh_pr_edit_comment`, `gh_pr_delete_comment` | `allow` | Modifies review content |
| `gh_pr_resolve_thread`, `gh_pr_unresolve_thread` | `allow` | GraphQL mutations |

## Adding a new tool

Before adding anything, ask: *can this be done by shelling out to `git` or `gh` directly?* If yes, don't add a tool. If the value is "saves tokens" or "the API supports this and `gh` doesn't", proceed:

1. Implement the function in a new file under `tools/gh/` (no MCP imports).
2. Re-export it from `tools/gh/__init__.py`.
3. Decorate it with `@tool("gh")`.
4. Add a mock-based test in `test_gh_tools.py`.
5. Update the table in this file and in `README.md`.

## Python conventions

- Python ≥ 3.11 — use `str | None` union syntax, not `Optional`.
- No `unwrap()`/`expect()` equivalents — always raise `CommandError` with context.
- Comments only where logic isn't obvious. Lowercase for inline comments.

# gh-pr-mcp

A minimal MCP (Model Context Protocol) server exposing a focused set of GitHub PR and review helpers that the `gh` CLI doesn't cover well: structured PR review threads, GraphQL thread resolve/unresolve, inline-comment review submission, and per-comment edit/delete via the REST API.

> Published to PyPI as `gh-pr-mcp`. The console script and MCP server are both named `gh-pr-mcp`.

## Philosophy

`git` and `gh` are already great at what they do. Wrapping them tool-by-tool just bloats the agent's tool list and gets in the way. The tools that earn a spot here are the ones that:

1. **Reduce token spend** by composing verbose `gh` JSON output into a tight summary (e.g. `pr_view`, `pr_list`, `run_view`, `run_job_view`, `pr_checks`), or
2. **Use the GitHub API directly** for operations the `gh` CLI can't do in a single call (review-thread resolve/unresolve via GraphQL, replying to a specific review comment, editing/deleting review comments, posting a review with inline comments at specific lines).

Everything else — `git status`, `git diff`, `gh pr create`, `gh issue list`, etc. — is faster, simpler, and more flexible to call via the shell directly.

## Tools

| Tool | What it does | Why it's here |
|------|--------------|--------------|
| `gh_pr_view` | PR details, body, reviews, comments, checks rollup, review decision + pending reviewers | Token-reducing summary |
| `gh_pr_list` | Open/closed PRs with mergeable state | Token-reducing summary |
| `gh_pr_checks` | CI check status | Token-reducing summary |
| `gh_pr_files` | Changed-files diffstat (status, +adds/-dels, renames), no patch blobs | Token-reducing summary for un-checked-out PRs |
| `gh_run_view` | Workflow run status + job list | Token-reducing summary |
| `gh_run_job_view` | Per-job details and (large) step logs | Helps when CI logs are massive |
| `gh_pr_review_threads` | Inline review comments grouped into threads, filterable by bot/human/active/outdated/resolved/unresolved | REST + GraphQL combined; `gh` cannot do this |
| `gh_pr_resolve_thread` | Mark a review thread resolved | GraphQL mutation only |
| `gh_pr_unresolve_thread` | Mark a review thread unresolved | GraphQL mutation only |
| `gh_pr_reply_comment` | Reply to a specific inline review comment by id | REST; no `gh` equivalent |
| `gh_pr_edit_comment` | Edit an existing review comment | REST; no `gh` equivalent |
| `gh_pr_delete_comment` | Delete a review comment | REST; no `gh` equivalent |
| `gh_pr_add_review` | Submit a review with inline comments at specific lines | REST; `gh pr review` only supports top-level body |

Recommended permission setup: allow everything in this server, and (separately) deny `Bash(gh api …)` so the model is funnelled through these helpers rather than rolling its own API calls.

## Development

```bash
uv sync
uv run pytest          # tests
uv run pyrefly check   # type check
uv run gh-pr-mcp       # run the server over stdio
```

## MCP configuration

### Project-scoped (worktree under active development)

`.mcp.json` in your project root points at the worktree:

```json
{
  "mcpServers": {
    "gh-pr-mcp-dev": {
      "command": "uvx",
      "args": ["--from", "/path/to/gh-pr-mcp-dev", "gh-pr-mcp"]
    }
  }
}
```

### Global config (stable)

From PyPI:

```json
{
  "mcpServers": {
    "gh-pr-mcp": {
      "command": "uvx",
      "args": ["gh-pr-mcp"]
    }
  }
}
```

Or straight from the repo without PyPI:

```json
{
  "mcpServers": {
    "gh-pr-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/gordon-to/gh-pr-mcp", "gh-pr-mcp"]
    }
  }
}
```

`gh` must be installed and authenticated (`gh auth login`) — the tools shell out to it.

## Architecture

```
src/gh_mcp/
├── server.py        # FastMCP app + tool registration
├── app.py           # mcp + @tool decorator
├── run.py           # subprocess helpers + input validation
└── tools/gh/
    ├── _api.py                # gh api GET/POST/PATCH/DELETE + GraphQL helpers
    ├── pr_view.py             # pr_view, pr_checks, pr_files, pr_review_threads
    ├── pr_list.py             # pr_list
    ├── pr_review.py           # pr_add_review, pr_reply_comment
    ├── pr_resolve_thread.py   # pr_resolve_thread, pr_unresolve_thread
    ├── pr_edit_comment.py
    ├── pr_delete_comment.py
    └── run_view.py            # run_view, run_job_view
```

## License

[AGPL-3.0-only](LICENSE). If you run a modified version as a network service, the AGPL requires you to offer that modified source to its users.

# gh-mcp

An MCP (Model Context Protocol) server that exposes `git` and `gh` (GitHub CLI) operations as structured tools — enabling AI agents to perform all version control and GitHub workflows through explicit, permission-controlled tool calls rather than raw shell commands.

## Goals

- **Replace raw git/gh usage** — every VCS operation is a named tool with typed inputs
- **Simplify permission management** — tools are grouped by risk level so you can grant broad access to read-only ops and require confirmation only for destructive/remote writes
- **Full workflow coverage** — branches, commits, PRs, issues, releases, worktrees, CI runs

## Tool Categories

| Category | Examples | Permission level |
|----------|----------|-----------------|
| **Git: read** | `git_status`, `git_diff`, `git_log`, `git_branch_list` | Always allow |
| **Git: local write** | `git_add`, `git_commit`, `git_branch_create`, `git_stash_push` | Always allow |
| **Git: remote** | `git_push`, `git_pull`, `git_fetch` | Ask |
| **Git: destructive** | `git_reset`, `git_restore`, `git_clean`, `git_push_force` | Ask |
| **GitHub: read** | `gh_pr_list`, `gh_issue_list`, `gh_run_list`, `gh_repo_view` | Always allow |
| **GitHub: write** | `gh_pr_create`, `gh_issue_create`, `gh_pr_comment` | Ask |
| **GitHub: merge/destroy** | `gh_pr_merge`, `gh_pr_close`, `gh_repo_create` | Ask |

## Development

```bash
# Install with uv
uv sync

# Run tests
uv run pytest

# Run server directly
uv run gh-mcp
```

## MCP Configuration

### Project-scoped (for development / testing latest changes)

Add to `.mcp.json` in your project root (points at the worktree copy):

```json
{
  "mcpServers": {
    "gh-mcp-dev": {
      "command": "uvx",
      "args": ["--from", "/path/to/gh-mcp-dev", "gh-mcp"]
    }
  }
}
```

### Global Claude config (stable — points at main)

```json
{
  "mcpServers": {
    "gh-mcp": {
      "command": "uvx",
      "args": ["gh-mcp"]
    }
  }
}
```

## Architecture

```
src/gh_mcp/
├── server.py        # FastMCP app + tool registration
├── tools/
│   ├── git.py       # All git_* tools
│   └── gh.py        # All gh_* tools
└── run.py           # Subprocess helpers + input validation
```

"""subprocess helpers and input validation."""

import os
import re
import subprocess


# pattern for safe ref values.
# we use subprocess list args (no shell=True) so shell metacharacters in the
# value itself won't be interpreted. we still block the worst offenders.
_REF_PATTERN = re.compile(r"^[a-zA-Z0-9._/\-~^@:{}\[\]]+$")

# this server is always non-interactive (stdio MCP). prevent gh from
# opening editors or prompting for credentials — both hang indefinitely.
_ENV = {
    **os.environ,
    "GIT_EDITOR": "true",
    "GIT_SEQUENCE_EDITOR": "true",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_PAGER": "cat",
    "GH_PROMPT_DISABLED": "1",
}


class CommandError(Exception):
    pass


def _validate_ref(value: str, label: str = "ref") -> str:
    """reject refs that could be used for shell injection."""
    if not value or not _REF_PATTERN.match(value):
        raise CommandError(f"invalid {label}: {value!r}")
    return value


def resolve_cwd(repo_path: str | None = None) -> str:
    """working directory for a gh/git subprocess when repo isn't given explicitly.

    an explicit repo_path wins. otherwise we must NOT fall back to our own
    process cwd: as a stdio MCP server we're launched with
    `uv run --directory <base> gh-pr-mcp`, so the process cwd is the server's
    source tree, almost never the repo the user is working in (this is the
    common case in a worktree). Claude Code exports the client's launch dir as
    CLAUDE_PROJECT_DIR (and PWD), so prefer those for repo auto-detection.
    """
    if repo_path and repo_path not in (".", ""):
        return repo_path
    for var in ("CLAUDE_PROJECT_DIR", "PWD"):
        val = os.environ.get(var)
        if val and os.path.isdir(val):
            return val
    return "."


def run_ok(args: list[str], cwd: str | None = None) -> str:
    """run a command, return combined stdout+stderr regardless of exit code."""
    result = subprocess.run(
        args,
        cwd=resolve_cwd(cwd),
        capture_output=True,
        text=True,
        env=_ENV,
    )
    return (result.stdout + result.stderr).strip()


def format_result(output: str, command: str = "") -> str:
    if not output.strip():
        return "(no output)" + (f" from `{command}`" if command else "")
    return output.strip()

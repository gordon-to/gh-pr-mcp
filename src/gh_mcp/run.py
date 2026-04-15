"""subprocess helpers and input validation."""

import re
import subprocess


# patterns for safe identifiers.
# we use subprocess list args (no shell=True) so shell metacharacters in the
# value itself won't be interpreted. we still block the worst offenders.
_REF_PATTERN = re.compile(r'^[a-zA-Z0-9._/\-~^@:{}\[\]]+$')
_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9._/\- ]+$')


class CommandError(Exception):
    pass


def _validate_ref(value: str, label: str = "ref") -> str:
    """reject refs that could be used for shell injection."""
    if not value or not _REF_PATTERN.match(value):
        raise CommandError(f"invalid {label}: {value!r}")
    return value


def _validate_path(value: str, label: str = "path") -> str:
    if not value:
        raise CommandError(f"{label} must not be empty")
    # allow ./ and ../ prefix sequences but not null bytes or shell metacharacters
    if any(c in value for c in '\x00|;&`$(){}[]<>\\!'):
        raise CommandError(f"invalid {label}: {value!r}")
    return value


def run(args: list[str], cwd: str | None = None) -> str:
    """run a command, return stdout, raise CommandError on non-zero exit."""
    result = subprocess.run(
        args,
        cwd=cwd or ".",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or "(no output)"
        raise CommandError(f"command failed (exit {result.returncode}): {detail}")
    return result.stdout


def run_ok(args: list[str], cwd: str | None = None) -> str:
    """run a command, return combined stdout+stderr regardless of exit code."""
    result = subprocess.run(
        args,
        cwd=cwd or ".",
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip()


def require_git_repo(cwd: str) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CommandError(f"not a git repository: {cwd}")


def format_result(output: str, command: str = "") -> str:
    if not output.strip():
        return f"(no output)" + (f" from `{command}`" if command else "")
    return output.strip()

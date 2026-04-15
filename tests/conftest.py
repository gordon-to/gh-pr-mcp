"""shared fixtures for gh-mcp tests."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """initialize a temporary git repo with an initial commit."""
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    readme = tmp_path / "README.md"
    readme.write_text("# test repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    return tmp_path


@pytest.fixture()
def git_repo_with_changes(git_repo: Path) -> Path:
    """repo with staged and unstaged changes."""
    (git_repo / "staged.txt").write_text("staged content\n")
    subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, check=True, capture_output=True)
    (git_repo / "unstaged.txt").write_text("unstaged content\n")
    return git_repo

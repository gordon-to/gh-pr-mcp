"""tests for GitHub CLI tools.

gh tools wrap the `gh` CLI so tests mock subprocess.run to avoid hitting
the real GitHub API. We verify that tools construct the right commands and
parse JSON responses correctly.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from gh_mcp.run import CommandError
from gh_mcp.tools.gh import (
    issue_close,
    issue_comment,
    issue_create,
    issue_list,
    issue_view,
    pr_checks,
    pr_close,
    pr_comment,
    pr_create,
    pr_list,
    pr_merge,
    pr_review,
    pr_view,
    release_create,
    release_list,
    release_view,
    repo_create,
    repo_view,
    run_list,
    run_rerun,
    run_view,
)


def _mock_run(returncode: int = 0, stdout: str = "", stderr: str = ""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ---------------------------------------------------------------------------
# pr_list
# ---------------------------------------------------------------------------

def test_pr_list_formats_output():
    prs = [
        {
            "number": 1,
            "title": "feat: add thing",
            "author": {"login": "alice"},
            "state": "OPEN",
            "headRefName": "feat/thing",
            "updatedAt": "2024-01-15T10:00:00Z",
            "isDraft": False,
        }
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(prs))):
        result = pr_list()
    assert "#1" in result
    assert "feat: add thing" in result
    assert "alice" in result


def test_pr_list_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")):
        result = pr_list()
    assert "no pull requests" in result


def test_pr_list_draft_shown():
    prs = [{
        "number": 2, "title": "WIP", "author": {"login": "bob"},
        "state": "OPEN", "headRefName": "wip", "updatedAt": "2024-01-01T00:00:00Z",
        "isDraft": True,
    }]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(prs))):
        result = pr_list()
    assert "DRAFT" in result


def test_pr_list_passes_state_flag():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")) as mock:
        pr_list(state="closed")
    cmd = mock.call_args[0][0]
    assert "--state" in cmd
    assert "closed" in cmd


def test_pr_list_invalid_base_raises():
    with pytest.raises(CommandError):
        pr_list(base="bad;base")


# ---------------------------------------------------------------------------
# pr_view
# ---------------------------------------------------------------------------

def test_pr_view_formats_output():
    pr_data = {
        "number": 5, "title": "fix bug", "author": {"login": "carol"},
        "state": "OPEN", "body": "fixes the thing",
        "baseRefName": "main", "headRefName": "fix/bug",
        "reviews": [], "comments": [], "isDraft": False,
        "mergeable": "MERGEABLE", "statusCheckRollup": [],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(pr_data))):
        result = pr_view("5")
    assert "PR #5" in result
    assert "fix bug" in result
    assert "fixes the thing" in result


def test_pr_view_shows_reviews():
    pr_data = {
        "number": 6, "title": "reviewed", "author": {"login": "dan"},
        "state": "OPEN", "body": "",
        "baseRefName": "main", "headRefName": "fix/x",
        "reviews": [{"author": {"login": "eve"}, "state": "APPROVED"}],
        "comments": [], "isDraft": False,
        "mergeable": "MERGEABLE", "statusCheckRollup": [],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(pr_data))):
        result = pr_view("6")
    assert "eve" in result
    assert "APPROVED" in result


# ---------------------------------------------------------------------------
# pr_create
# ---------------------------------------------------------------------------

def test_pr_create_passes_title_and_body():
    with patch("subprocess.run", return_value=_mock_run(stdout="https://github.com/r/pr/1")) as mock:
        pr_create(title="my PR", body="description", base="main")
    cmd = mock.call_args[0][0]
    assert "--title" in cmd
    assert "my PR" in cmd
    assert "--body" in cmd


def test_pr_create_fill_when_no_title():
    with patch("subprocess.run", return_value=_mock_run(stdout="https://github.com/r/pr/2")) as mock:
        pr_create()
    cmd = mock.call_args[0][0]
    assert "--fill" in cmd


def test_pr_create_draft_flag():
    with patch("subprocess.run", return_value=_mock_run(stdout="url")) as mock:
        pr_create(title="draft", draft=True)
    cmd = mock.call_args[0][0]
    assert "--draft" in cmd


def test_pr_create_invalid_base_raises():
    with pytest.raises(CommandError):
        with patch("subprocess.run", return_value=_mock_run(stdout="url")):
            pr_create(base="bad|base")


# ---------------------------------------------------------------------------
# pr_comment
# ---------------------------------------------------------------------------

def test_pr_comment_sends_body():
    with patch("subprocess.run", return_value=_mock_run(stdout="ok")) as mock:
        pr_comment("3", body="looks good")
    cmd = mock.call_args[0][0]
    assert "--body" in cmd
    assert "looks good" in cmd


def test_pr_comment_empty_body_raises():
    with pytest.raises(CommandError):
        pr_comment("3", body="  ")


# ---------------------------------------------------------------------------
# pr_review
# ---------------------------------------------------------------------------

def test_pr_review_approve():
    with patch("subprocess.run", return_value=_mock_run(stdout="ok")) as mock:
        pr_review("4", event="approve")
    cmd = mock.call_args[0][0]
    assert "--approve" in cmd


def test_pr_review_request_changes():
    with patch("subprocess.run", return_value=_mock_run(stdout="ok")) as mock:
        pr_review("4", event="request-changes", body="please fix X")
    cmd = mock.call_args[0][0]
    assert "--request-changes" in cmd


def test_pr_review_invalid_event_raises():
    with pytest.raises(CommandError):
        pr_review("4", event="invalid")


# ---------------------------------------------------------------------------
# pr_merge
# ---------------------------------------------------------------------------

def test_pr_merge_squash():
    with patch("subprocess.run", return_value=_mock_run(stdout="merged")) as mock:
        pr_merge("7", method="squash")
    cmd = mock.call_args[0][0]
    assert "--squash" in cmd


def test_pr_merge_invalid_method_raises():
    with pytest.raises(CommandError):
        pr_merge("7", method="bad")


def test_pr_merge_delete_branch_default():
    with patch("subprocess.run", return_value=_mock_run(stdout="merged")) as mock:
        pr_merge("8")
    cmd = mock.call_args[0][0]
    assert "--delete-branch" in cmd


# ---------------------------------------------------------------------------
# pr_close
# ---------------------------------------------------------------------------

def test_pr_close():
    with patch("subprocess.run", return_value=_mock_run(stdout="closed")) as mock:
        pr_close("9", comment="no longer needed")
    cmd = mock.call_args[0][0]
    assert "--comment" in cmd


# ---------------------------------------------------------------------------
# pr_checks
# ---------------------------------------------------------------------------

def test_pr_checks():
    with patch("subprocess.run", return_value=_mock_run(stdout="✓ ci/test passing")):
        result = pr_checks("10")
    assert "passing" in result


# ---------------------------------------------------------------------------
# issue_list
# ---------------------------------------------------------------------------

def test_issue_list_formats_output():
    issues = [{
        "number": 1, "title": "bug report",
        "author": {"login": "alice"}, "state": "OPEN",
        "labels": [{"name": "bug"}], "assignees": [],
        "updatedAt": "2024-02-01T00:00:00Z",
    }]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(issues))):
        result = issue_list()
    assert "#1" in result
    assert "bug report" in result
    assert "bug" in result


def test_issue_list_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")):
        result = issue_list()
    assert "no issues" in result


# ---------------------------------------------------------------------------
# issue_view
# ---------------------------------------------------------------------------

def test_issue_view_shows_comments():
    issue_data = {
        "number": 3, "title": "help needed",
        "author": {"login": "bob"}, "state": "OPEN",
        "body": "please help", "labels": [], "assignees": [],
        "comments": [{"author": {"login": "carol"}, "body": "sure thing"}],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(issue_data))):
        result = issue_view("3")
    assert "carol" in result
    assert "sure thing" in result


# ---------------------------------------------------------------------------
# issue_create
# ---------------------------------------------------------------------------

def test_issue_create_sends_title():
    with patch("subprocess.run", return_value=_mock_run(stdout="https://github.com/r/i/1")) as mock:
        issue_create(title="new bug", body="description")
    cmd = mock.call_args[0][0]
    assert "--title" in cmd
    assert "new bug" in cmd


def test_issue_create_empty_title_raises():
    with pytest.raises(CommandError):
        issue_create(title="  ")


def test_issue_create_with_labels():
    with patch("subprocess.run", return_value=_mock_run(stdout="url")) as mock:
        issue_create(title="thing", label=["bug", "help wanted"])
    cmd = mock.call_args[0][0]
    assert cmd.count("--label") == 2


# ---------------------------------------------------------------------------
# issue_comment / issue_close
# ---------------------------------------------------------------------------

def test_issue_comment():
    with patch("subprocess.run", return_value=_mock_run(stdout="ok")) as mock:
        issue_comment("5", body="hello")
    cmd = mock.call_args[0][0]
    assert "comment" in cmd
    assert "hello" in cmd


def test_issue_close_with_reason():
    with patch("subprocess.run", return_value=_mock_run(stdout="closed")) as mock:
        issue_close("6", reason="completed")
    cmd = mock.call_args[0][0]
    assert "--reason" in cmd
    assert "completed" in cmd


# ---------------------------------------------------------------------------
# repo_view
# ---------------------------------------------------------------------------

def test_repo_view_formats_output():
    repo_data = {
        "name": "my-repo", "description": "cool repo",
        "defaultBranchRef": {"name": "main"},
        "isPrivate": True, "stargazerCount": 5, "forkCount": 2,
        "openIssues": [], "url": "https://github.com/user/my-repo",
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(repo_data))):
        result = repo_view()
    assert "my-repo" in result
    assert "[private]" in result
    assert "main" in result


# ---------------------------------------------------------------------------
# repo_create
# ---------------------------------------------------------------------------

def test_repo_create_private_by_default():
    with patch("subprocess.run", return_value=_mock_run(stdout="url")) as mock:
        repo_create("new-repo")
    cmd = mock.call_args[0][0]
    assert "--private" in cmd


def test_repo_create_public():
    with patch("subprocess.run", return_value=_mock_run(stdout="url")) as mock:
        repo_create("new-repo", private=False)
    cmd = mock.call_args[0][0]
    assert "--public" in cmd


def test_repo_create_empty_name_raises():
    with pytest.raises(CommandError):
        repo_create("")


# ---------------------------------------------------------------------------
# run_list / run_view / run_rerun
# ---------------------------------------------------------------------------

def test_run_list_formats_output():
    runs = [{
        "databaseId": 123, "name": "CI",
        "status": "completed", "conclusion": "success",
        "headBranch": "main", "event": "push",
        "startedAt": "2024-03-01T10:00:00Z",
    }]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(runs))):
        result = run_list()
    assert "#123" in result
    assert "success" in result


def test_run_view_formats_output():
    run_data = {
        "databaseId": 456, "name": "CI",
        "status": "completed", "conclusion": "failure",
        "headBranch": "feat/x", "event": "pull_request",
        "jobs": [{"name": "test", "conclusion": "failure"}],
        "startedAt": "2024-03-01T10:00:00Z",
        "updatedAt": "2024-03-01T10:05:00Z",
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(run_data))):
        result = run_view("456")
    assert "failure" in result
    assert "test" in result


def test_run_rerun_failed_only():
    with patch("subprocess.run", return_value=_mock_run(stdout="ok")) as m:
        run_rerun("789")
    cmd = m.call_args[0][0]
    assert "--failed" in cmd


# ---------------------------------------------------------------------------
# release_list / release_view / release_create
# ---------------------------------------------------------------------------

def test_release_list_formats_output():
    releases = [{
        "tagName": "v1.0.0", "name": "First Release",
        "isDraft": False, "isPrerelease": False,
        "publishedAt": "2024-01-01T00:00:00Z",
    }]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(releases))):
        result = release_list()
    assert "v1.0.0" in result
    assert "First Release" in result


def test_release_view_formats_output():
    release_data = {
        "tagName": "v2.0.0", "name": "v2",
        "isDraft": False, "isPrerelease": False,
        "body": "## Changes\n- thing",
        "publishedAt": "2024-06-01T00:00:00Z",
        "author": {"login": "alice"},
        "assets": [{"name": "binary.tar.gz"}],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(release_data))):
        result = release_view("v2.0.0")
    assert "v2.0.0" in result
    assert "binary.tar.gz" in result


def test_release_create_generates_notes_by_default():
    with patch("subprocess.run", return_value=_mock_run(stdout="url")) as mock:
        release_create("v3.0.0")
    cmd = mock.call_args[0][0]
    assert "--generate-notes" in cmd


def test_release_create_draft():
    with patch("subprocess.run", return_value=_mock_run(stdout="url")) as mock:
        release_create("v3.1.0", draft=True)
    cmd = mock.call_args[0][0]
    assert "--draft" in cmd

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
    pr_add_review,
    pr_checks,
    pr_close,
    pr_comment,
    pr_create,
    pr_list,
    pr_merge,
    pr_reply_comment,
    pr_review,
    pr_review_threads,
    pr_view,
    release_create,
    release_list,
    release_view,
    repo_create,
    repo_view,
    run_cancel,
    run_job_view,
    run_list,
    run_rerun,
    run_view,
    workflow_list,
    workflow_run,
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


# ---------------------------------------------------------------------------
# pr_review_threads
# ---------------------------------------------------------------------------

def test_pr_review_threads_groups_by_root():
    comments = [
        {
            "id": 10, "user": {"login": "alice"}, "body": "why not use X here?",
            "path": "src/foo.py", "line": 42, "original_line": 42,
            "side": "RIGHT", "diff_hunk": "@@ -40,6 +40,7 @@\n+    result = compute()",
            "in_reply_to_id": None,
        },
        {
            "id": 11, "user": {"login": "bob"}, "body": "good point, will fix",
            "path": "src/foo.py", "line": 42, "original_line": 42,
            "side": "RIGHT", "diff_hunk": "",
            "in_reply_to_id": 10,
        },
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(comments))):
        result = pr_review_threads("5")
    assert "Thread #10" in result
    assert "src/foo.py:42" in result
    assert "alice" in result
    assert "bob" in result
    assert "↳" in result  # reply indicator


def test_pr_review_threads_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")):
        result = pr_review_threads("5")
    assert "no inline" in result


def test_pr_review_threads_uses_api_endpoint():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")) as mock:
        pr_review_threads("7")
    cmd = mock.call_args[0][0]
    assert "gh" in cmd
    assert "api" in cmd
    assert "pulls/7/comments" in " ".join(cmd)


# ---------------------------------------------------------------------------
# pr_add_review
# ---------------------------------------------------------------------------

def test_pr_add_review_posts_to_reviews_endpoint():
    response = {
        "id": 99, "state": "COMMENT",
        "user": {"login": "claude"},
        "body": "looks good overall",
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(response))) as mock:
        result = pr_add_review("5", event="COMMENT", body="looks good overall")
    cmd = mock.call_args[0][0]
    assert "api" in cmd
    assert "pulls/5/reviews" in " ".join(cmd)
    assert "#99" in result
    assert "COMMENT" in result


def test_pr_add_review_with_inline_comments():
    response = {"id": 100, "state": "REQUEST_CHANGES", "user": {"login": "reviewer"}, "body": ""}
    inline = [{"path": "src/main.py", "line": 10, "body": "rename this"}]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(response))) as mock:
        result = pr_add_review("5", event="REQUEST_CHANGES", inline_comments=inline)
    # verify the JSON payload sent to stdin contains the comment
    call_kwargs = mock.call_args
    stdin_data = call_kwargs[1]["input"]
    payload = json.loads(stdin_data)
    assert payload["event"] == "REQUEST_CHANGES"
    assert len(payload["comments"]) == 1
    assert payload["comments"][0]["path"] == "src/main.py"
    assert payload["comments"][0]["line"] == 10
    assert "#100" in result


def test_pr_add_review_invalid_event_raises():
    with pytest.raises(CommandError):
        pr_add_review("5", event="INVALID")


def test_pr_add_review_missing_inline_field_raises():
    with pytest.raises(CommandError):
        pr_add_review("5", event="COMMENT", inline_comments=[{"path": "f.py", "body": "x"}])


# ---------------------------------------------------------------------------
# pr_reply_comment
# ---------------------------------------------------------------------------

def test_pr_reply_comment_posts_with_in_reply_to():
    response = {"id": 55, "user": {"login": "me"}, "body": "fixed!"}
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(response))) as mock:
        result = pr_reply_comment("5", comment_id=10, body="fixed!")
    call_kwargs = mock.call_args
    stdin_data = call_kwargs[1]["input"]
    payload = json.loads(stdin_data)
    assert payload["in_reply_to"] == 10
    assert payload["body"] == "fixed!"
    assert "#55" in result


def test_pr_reply_comment_empty_body_raises():
    with pytest.raises(CommandError):
        pr_reply_comment("5", comment_id=10, body="  ")


# ---------------------------------------------------------------------------
# run_cancel
# ---------------------------------------------------------------------------

def test_run_cancel_sends_correct_command():
    with patch("subprocess.run", return_value=_mock_run(stdout="✓ cancelled")) as mock:
        result = run_cancel("999")
    cmd = mock.call_args[0][0]
    assert "cancel" in cmd
    assert "999" in cmd
    assert "✓" in result or "cancelled" in result


# ---------------------------------------------------------------------------
# run_job_view
# ---------------------------------------------------------------------------

def test_run_job_view_formats_steps():
    run_data = {
        "jobs": [{
            "name": "test",
            "conclusion": "failure",
            "status": "completed",
            "steps": [
                {"name": "checkout", "conclusion": "success", "status": "completed"},
                {"name": "run tests", "conclusion": "failure", "status": "completed"},
            ],
        }]
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(run_data))):
        result = run_job_view("123")
    assert "test" in result
    assert "checkout" in result
    assert "run tests" in result
    assert "failure" in result


def test_run_job_view_with_job_name_passes_flag():
    with patch("subprocess.run", return_value=_mock_run(stdout="log output")) as mock:
        run_job_view("123", job_name="test", log=True)
    cmd = mock.call_args[0][0]
    assert "--job" in cmd
    assert "--log" in cmd


def test_run_job_view_empty_jobs():
    with patch("subprocess.run", return_value=_mock_run(stdout='{"jobs": []}')):
        result = run_job_view("123")
    assert "no jobs" in result


# ---------------------------------------------------------------------------
# workflow_list
# ---------------------------------------------------------------------------

def test_workflow_list_formats_output():
    workflows = [
        {"id": 1, "name": "CI", "state": "active", "path": ".github/workflows/ci.yml"},
        {"id": 2, "name": "Release", "state": "active", "path": ".github/workflows/release.yml"},
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(workflows))):
        result = workflow_list()
    assert "CI" in result
    assert "ci.yml" in result
    assert "Release" in result


def test_workflow_list_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")):
        result = workflow_list()
    assert "no workflows" in result


def test_workflow_list_passes_json_flag():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")) as mock:
        workflow_list()
    cmd = mock.call_args[0][0]
    assert "--json" in cmd


# ---------------------------------------------------------------------------
# workflow_run
# ---------------------------------------------------------------------------

def test_workflow_run_sends_workflow_name():
    with patch("subprocess.run", return_value=_mock_run(stdout="✓ triggered")) as mock:
        workflow_run("ci.yml")
    cmd = mock.call_args[0][0]
    assert "workflow" in cmd
    assert "run" in cmd
    assert "ci.yml" in cmd


def test_workflow_run_with_ref_and_inputs():
    with patch("subprocess.run", return_value=_mock_run(stdout="ok")) as mock:
        workflow_run("ci.yml", ref="main", inputs={"env": "prod"})
    cmd = mock.call_args[0][0]
    assert "--ref" in cmd
    assert "main" in cmd
    assert "-f" in cmd
    assert "env=prod" in cmd


def test_workflow_run_empty_name_raises():
    with pytest.raises(CommandError):
        workflow_run("  ")

"""tests for GitHub tools.

gh tools wrap `gh` and the GitHub API so tests mock subprocess.run to avoid
hitting the real GitHub API. We verify that tools construct the right
commands/payloads and parse responses correctly.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from gh_mcp.run import CommandError, resolve_cwd
from gh_mcp.tools.gh import (
    pr_add_review,
    pr_checks,
    pr_delete_comment,
    pr_edit_comment,
    pr_files,
    pr_list,
    pr_reply_comment,
    pr_resolve_thread,
    pr_review_threads,
    pr_unresolve_thread,
    pr_view,
    run_job_view,
    run_view,
)


def _mock_run(returncode: int = 0, stdout: str = "", stderr: str = ""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ---------------------------------------------------------------------------
# resolve_cwd — repo auto-detection working directory
# ---------------------------------------------------------------------------


def test_resolve_cwd_explicit_path_wins(tmp_path):
    assert resolve_cwd(str(tmp_path)) == str(tmp_path)


def test_resolve_cwd_falls_back_to_claude_project_dir(tmp_path):
    # "." would resolve to the server's own fixed cwd; instead we use the
    # client's launch dir that Claude Code exports.
    with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}, clear=True):
        assert resolve_cwd(".") == str(tmp_path)
        assert resolve_cwd("") == str(tmp_path)
        assert resolve_cwd(None) == str(tmp_path)


def test_resolve_cwd_prefers_claude_project_dir_over_pwd(tmp_path):
    proj = tmp_path / "proj"
    pwd = tmp_path / "pwd"
    proj.mkdir()
    pwd.mkdir()
    env = {"CLAUDE_PROJECT_DIR": str(proj), "PWD": str(pwd)}
    with patch.dict("os.environ", env, clear=True):
        assert resolve_cwd(".") == str(proj)


def test_resolve_cwd_falls_back_to_pwd_when_no_project_dir(tmp_path):
    with patch.dict("os.environ", {"PWD": str(tmp_path)}, clear=True):
        assert resolve_cwd(".") == str(tmp_path)


def test_resolve_cwd_ignores_nonexistent_env_dirs():
    env = {"CLAUDE_PROJECT_DIR": "/no/such/dir/xyz", "PWD": "/also/missing"}
    with patch.dict("os.environ", env, clear=True):
        assert resolve_cwd(".") == "."


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
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
        }
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(prs))):
        result = pr_list()
    assert "#1" in result
    assert "feat: add thing" in result
    assert "alice" in result
    assert "mergeable: MERGEABLE" in result
    assert "state: CLEAN" in result


def test_pr_list_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")):
        result = pr_list()
    assert "no pull requests" in result


def test_pr_list_draft_shown():
    prs = [
        {
            "number": 2,
            "title": "WIP",
            "author": {"login": "bob"},
            "state": "OPEN",
            "headRefName": "wip",
            "updatedAt": "2024-01-01T00:00:00Z",
            "isDraft": True,
            "mergeable": "CONFLICTING",
            "mergeStateStatus": "DIRTY",
        }
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(prs))):
        result = pr_list()
    assert "DRAFT" in result
    assert "CONFLICTING" in result
    assert "DIRTY" in result


def test_pr_list_missing_mergeable_fields_falls_back_to_unknown():
    prs = [
        {
            "number": 3,
            "title": "x",
            "author": {"login": "carol"},
            "state": "OPEN",
            "headRefName": "x",
            "updatedAt": "2024-01-01T00:00:00Z",
            "isDraft": False,
        }
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(prs))):
        result = pr_list()
    assert "mergeable: UNKNOWN" in result
    assert "state: UNKNOWN" in result


def test_pr_list_requests_mergeable_json_fields():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")) as mock:
        pr_list()
    cmd = mock.call_args[0][0]
    json_idx = cmd.index("--json")
    fields = cmd[json_idx + 1]
    assert "mergeable" in fields
    assert "mergeStateStatus" in fields


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
        "number": 5,
        "title": "fix bug",
        "author": {"login": "carol"},
        "state": "OPEN",
        "body": "fixes the thing",
        "baseRefName": "main",
        "headRefName": "fix/bug",
        "reviews": [],
        "comments": [],
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(pr_data))):
        result = pr_view("5")
    assert "PR #5" in result
    assert "fix bug" in result
    assert "fixes the thing" in result


def test_pr_view_shows_reviews():
    pr_data = {
        "number": 6,
        "title": "reviewed",
        "author": {"login": "dan"},
        "state": "OPEN",
        "body": "",
        "baseRefName": "main",
        "headRefName": "fix/x",
        "reviews": [{"author": {"login": "eve"}, "state": "APPROVED"}],
        "comments": [],
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(pr_data))):
        result = pr_view("6")
    assert "eve" in result
    assert "APPROVED" in result


def test_pr_view_shows_review_decision_and_pending_reviewers():
    pr_data = {
        "number": 7,
        "title": "needs review",
        "author": {"login": "dan"},
        "state": "OPEN",
        "body": "",
        "baseRefName": "main",
        "headRefName": "fix/y",
        "reviews": [],
        "comments": [],
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [],
        "reviewDecision": "CHANGES_REQUESTED",
        "reviewRequests": [{"login": "frank"}, {"slug": "backend"}],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(pr_data))):
        result = pr_view("7")
    assert "review decision: CHANGES_REQUESTED" in result
    assert "awaiting review: frank, team/backend" in result


def test_pr_view_omits_review_lines_when_absent():
    pr_data = {
        "number": 8,
        "title": "no decision",
        "author": {"login": "dan"},
        "state": "OPEN",
        "body": "",
        "baseRefName": "main",
        "headRefName": "fix/z",
        "reviews": [],
        "comments": [],
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [],
        "reviewDecision": "",
        "reviewRequests": [],
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(pr_data))):
        result = pr_view("8")
    assert "review decision" not in result
    assert "awaiting review" not in result


def test_pr_view_requests_review_decision_fields():
    with patch(
        "subprocess.run", return_value=_mock_run(stdout="{}")
    ) as mock:
        pr_view("9")
    json_arg = mock.call_args[0][0][mock.call_args[0][0].index("--json") + 1]
    assert "reviewDecision" in json_arg
    assert "reviewRequests" in json_arg


# ---------------------------------------------------------------------------
# pr_files
# ---------------------------------------------------------------------------


def test_pr_files_formats_diffstat():
    files = [
        {"filename": "src/a.py", "status": "modified", "additions": 10, "deletions": 2},
        {"filename": "tests/b.py", "status": "added", "additions": 50, "deletions": 0},
        {"filename": "old.py", "status": "removed", "additions": 0, "deletions": 40},
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(files))):
        result = pr_files("5")
    assert "3 files  +60 -42" in result
    assert "M  src/a.py  +10 -2" in result
    assert "A  tests/b.py  +50 -0" in result
    assert "D  old.py  +0 -40" in result


def test_pr_files_shows_rename_origin():
    files = [
        {
            "filename": "src/new.py",
            "status": "renamed",
            "additions": 1,
            "deletions": 1,
            "previous_filename": "src/old.py",
        }
    ]
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(files))):
        result = pr_files("5")
    assert "R  src/new.py (from src/old.py)  +1 -1" in result


def test_pr_files_empty():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")):
        result = pr_files("5")
    assert result == "no files changed"


def test_pr_files_hits_paginated_files_endpoint():
    with patch("subprocess.run", return_value=_mock_run(stdout="[]")) as mock:
        pr_files("5")
    cmd = mock.call_args[0][0]
    assert "--paginate" in cmd
    assert any("pulls/5/files" in part for part in cmd)


# ---------------------------------------------------------------------------
# pr_checks
# ---------------------------------------------------------------------------


def test_pr_checks():
    with patch("subprocess.run", return_value=_mock_run(stdout="✓ ci/test passing")):
        result = pr_checks("10")
    assert "passing" in result


# ---------------------------------------------------------------------------
# run_view
# ---------------------------------------------------------------------------


def test_run_view_formats_output():
    run_data = {
        "databaseId": 456,
        "name": "CI",
        "status": "completed",
        "conclusion": "failure",
        "headBranch": "feat/x",
        "event": "pull_request",
        "jobs": [{"name": "test", "conclusion": "failure"}],
        "startedAt": "2024-03-01T10:00:00Z",
        "updatedAt": "2024-03-01T10:05:00Z",
    }
    with patch("subprocess.run", return_value=_mock_run(stdout=json.dumps(run_data))):
        result = run_view("456")
    assert "failure" in result
    assert "test" in result


# ---------------------------------------------------------------------------
# run_job_view
# ---------------------------------------------------------------------------


def test_run_job_view_formats_steps():
    run_data = {
        "jobs": [
            {
                "name": "test",
                "conclusion": "failure",
                "status": "completed",
                "steps": [
                    {
                        "name": "checkout",
                        "conclusion": "success",
                        "status": "completed",
                    },
                    {
                        "name": "run tests",
                        "conclusion": "failure",
                        "status": "completed",
                    },
                ],
            }
        ]
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
# pr_review_threads
# ---------------------------------------------------------------------------


def _make_comment(
    cid: int,
    login: str,
    body: str,
    path: str = "src/foo.py",
    line: int = 42,
    position: int | None = 5,
    user_type: str = "User",
    in_reply_to_id: int | None = None,
) -> dict:
    return {
        "id": cid,
        "user": {"login": login, "type": user_type},
        "body": body,
        "path": path,
        "line": line,
        "original_line": line,
        "position": position,
        "in_reply_to_id": in_reply_to_id,
    }


def _threads_side_effect(comments: list[dict], meta: dict | None = None) -> list:
    """side_effect returning the REST-comments then the GraphQL-threads response.

    meta maps root comment databaseId -> {"resolve_id": str, "resolved": bool}.
    tests using this helper must pass repo="owner/name" to skip the repo-view call.
    """
    nodes = []
    for cid, info in (meta or {}).items():
        nodes.append(
            {
                "id": info.get("resolve_id", f"THREAD_{cid}"),
                "isResolved": info.get("resolved", False),
                "comments": {"nodes": [{"databaseId": cid}]},
            }
        )
    graphql = {
        "data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": nodes}}}}
    }
    return [
        _mock_run(stdout=json.dumps(comments)),
        _mock_run(stdout=json.dumps(graphql)),
    ]


def test_pr_review_threads_groups_replies_under_root():
    comments = [
        _make_comment(10, "alice", "why not use X?"),
        _make_comment(11, "bob", "good point", in_reply_to_id=10),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    thread = data["threads"][0]
    assert thread["thread_id"] == 10
    assert thread["file"] == "src/foo.py"
    assert thread["line"] == 42
    assert thread["author"]["login"] == "alice"
    assert len(thread["replies"]) == 1
    assert thread["replies"][0]["author"]["login"] == "bob"


def test_pr_review_threads_outdated_when_position_null():
    comments = [
        _make_comment(20, "carol", "old comment", position=None),
        _make_comment(21, "dan", "current comment", position=3),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    threads = {t["thread_id"]: t for t in data["threads"]}
    assert threads[20]["outdated"] is True
    assert threads[21]["outdated"] is False
    assert data["summary"]["outdated"] == 1
    assert data["summary"]["active"] == 1


def test_pr_review_threads_bot_detection():
    comments = [
        _make_comment(30, "claude-bot", "automated feedback", user_type="Bot"),
        _make_comment(31, "alice", "human feedback", user_type="User"),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    threads = {t["thread_id"]: t for t in data["threads"]}
    assert threads[30]["author"]["type"] == "bot"
    assert threads[31]["author"]["type"] == "human"
    assert data["summary"]["bot"] == 1
    assert data["summary"]["human"] == 1


def test_pr_review_threads_filter_bot():
    comments = [
        _make_comment(40, "bot-reviewer", "style issue", user_type="Bot"),
        _make_comment(41, "alice", "logic issue", user_type="User"),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r", kind="bot")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["author"]["type"] == "bot"


def test_pr_review_threads_filter_human():
    comments = [
        _make_comment(50, "bot-reviewer", "style issue", user_type="Bot"),
        _make_comment(51, "alice", "logic issue", user_type="User"),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r", kind="human")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["author"]["login"] == "alice"


def test_pr_review_threads_filter_outdated():
    comments = [
        _make_comment(60, "alice", "old", position=None),
        _make_comment(61, "alice", "current", position=2),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r", kind="outdated")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["outdated"] is True


def test_pr_review_threads_filter_active():
    comments = [
        _make_comment(70, "alice", "old", position=None),
        _make_comment(71, "alice", "current", position=2),
    ]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r", kind="active")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["outdated"] is False


def test_pr_review_threads_invalid_kind_raises():
    with patch("subprocess.run", side_effect=_threads_side_effect([])):
        with pytest.raises(CommandError):
            pr_review_threads("5", repo="o/r", kind="nonsense")


def test_pr_review_threads_empty_returns_json():
    with patch("subprocess.run", side_effect=_threads_side_effect([])):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    assert data["threads"] == []
    assert data["summary"]["total"] == 0


def test_pr_review_threads_uses_api_endpoint():
    with patch("subprocess.run", side_effect=_threads_side_effect([])) as mock:
        pr_review_threads("7", repo="o/r")
    cmd = mock.call_args_list[0][0][0]
    assert "api" in cmd
    assert "pulls/7/comments" in " ".join(cmd)


def test_pr_review_threads_thread_id_usable_for_reply():
    """thread_id should be a plain int matching comment_id for pr_reply_comment."""
    comments = [_make_comment(99, "alice", "needs work")]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments)):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    assert data["threads"][0]["thread_id"] == 99


def test_pr_review_threads_includes_resolve_id_and_resolved_state():
    comments = [
        _make_comment(200, "alice", "nit: rename"),
        _make_comment(201, "alice", "refactor this"),
    ]
    meta = {
        200: {"resolve_id": "PRRT_abc", "resolved": True},
        201: {"resolve_id": "PRRT_xyz", "resolved": False},
    }
    with patch("subprocess.run", side_effect=_threads_side_effect(comments, meta)):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    threads = {t["thread_id"]: t for t in data["threads"]}
    assert threads[200]["resolve_id"] == "PRRT_abc"
    assert threads[200]["resolved"] is True
    assert threads[201]["resolve_id"] == "PRRT_xyz"
    assert threads[201]["resolved"] is False
    assert data["summary"]["resolved"] == 1
    assert data["summary"]["unresolved"] == 1


def test_pr_review_threads_filter_unresolved():
    comments = [
        _make_comment(300, "alice", "done"),
        _make_comment(301, "alice", "still pending"),
    ]
    meta = {
        300: {"resolve_id": "PRRT_a", "resolved": True},
        301: {"resolve_id": "PRRT_b", "resolved": False},
    }
    with patch("subprocess.run", side_effect=_threads_side_effect(comments, meta)):
        result = pr_review_threads("5", repo="o/r", kind="unresolved")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["thread_id"] == 301


def test_pr_review_threads_filter_resolved():
    comments = [
        _make_comment(400, "alice", "done"),
        _make_comment(401, "alice", "still pending"),
    ]
    meta = {
        400: {"resolve_id": "PRRT_a", "resolved": True},
        401: {"resolve_id": "PRRT_b", "resolved": False},
    }
    with patch("subprocess.run", side_effect=_threads_side_effect(comments, meta)):
        result = pr_review_threads("5", repo="o/r", kind="resolved")
    data = json.loads(result)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["thread_id"] == 400


def test_pr_review_threads_missing_meta_defaults_to_empty():
    """if GraphQL doesn't return a thread for a comment, resolve_id is '' and resolved is False."""
    comments = [_make_comment(500, "alice", "orphan")]
    with patch("subprocess.run", side_effect=_threads_side_effect(comments, meta=None)):
        result = pr_review_threads("5", repo="o/r")
    data = json.loads(result)
    assert data["threads"][0]["resolve_id"] == ""
    assert data["threads"][0]["resolved"] is False


# ---------------------------------------------------------------------------
# pr_add_review
# ---------------------------------------------------------------------------


def test_pr_add_review_posts_to_reviews_endpoint():
    response = {
        "id": 99,
        "state": "COMMENT",
        "user": {"login": "claude"},
        "body": "looks good overall",
    }
    with patch(
        "subprocess.run", return_value=_mock_run(stdout=json.dumps(response))
    ) as mock:
        result = pr_add_review("5", event="COMMENT", body="looks good overall")
    cmd = mock.call_args[0][0]
    assert "api" in cmd
    assert "pulls/5/reviews" in " ".join(cmd)
    assert "#99" in result
    assert "COMMENT" in result


def test_pr_add_review_with_inline_comments():
    response = {
        "id": 100,
        "state": "REQUEST_CHANGES",
        "user": {"login": "reviewer"},
        "body": "",
    }
    inline = [{"path": "src/main.py", "line": 10, "body": "rename this"}]
    with patch(
        "subprocess.run", return_value=_mock_run(stdout=json.dumps(response))
    ) as mock:
        result = pr_add_review("5", event="REQUEST_CHANGES", inline_comments=inline)
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
        pr_add_review(
            "5", event="COMMENT", inline_comments=[{"path": "f.py", "body": "x"}]
        )


# ---------------------------------------------------------------------------
# pr_reply_comment
# ---------------------------------------------------------------------------


def test_pr_reply_comment_posts_with_in_reply_to():
    response = {"id": 55, "user": {"login": "me"}, "body": "fixed!"}
    with patch(
        "subprocess.run", return_value=_mock_run(stdout=json.dumps(response))
    ) as mock:
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
# pr_resolve_thread / pr_unresolve_thread
# ---------------------------------------------------------------------------


def _graphql_response(mutation: str, thread_id: str, resolved: bool) -> str:
    return json.dumps(
        {"data": {mutation: {"thread": {"id": thread_id, "isResolved": resolved}}}}
    )


def test_pr_resolve_thread_calls_graphql_mutation():
    response = _graphql_response("resolveReviewThread", "PRRT_abc", True)
    with patch("subprocess.run", return_value=_mock_run(stdout=response)) as mock:
        result = pr_resolve_thread("PRRT_abc")
    cmd = mock.call_args[0][0]
    assert cmd[:4] == ["gh", "api", "graphql", "--input"]
    payload = json.loads(mock.call_args[1]["input"])
    assert "resolveReviewThread" in payload["query"]
    assert payload["variables"] == {"id": "PRRT_abc"}
    assert "resolved=True" in result


def test_pr_unresolve_thread_calls_graphql_mutation():
    response = _graphql_response("unresolveReviewThread", "PRRT_xyz", False)
    with patch("subprocess.run", return_value=_mock_run(stdout=response)) as mock:
        result = pr_unresolve_thread("PRRT_xyz")
    payload = json.loads(mock.call_args[1]["input"])
    assert "unresolveReviewThread" in payload["query"]
    assert payload["variables"] == {"id": "PRRT_xyz"}
    assert "resolved=False" in result


def test_pr_resolve_thread_empty_id_raises():
    with pytest.raises(CommandError):
        pr_resolve_thread("")


def test_pr_unresolve_thread_empty_id_raises():
    with pytest.raises(CommandError):
        pr_unresolve_thread("   ")


def test_pr_resolve_thread_surfaces_graphql_errors():
    response = json.dumps({"data": None, "errors": [{"message": "thread not found"}]})
    with patch("subprocess.run", return_value=_mock_run(stdout=response)):
        with pytest.raises(CommandError, match="thread not found"):
            pr_resolve_thread("PRRT_missing")


def test_pr_resolve_thread_surfaces_nonzero_exit():
    with patch(
        "subprocess.run", return_value=_mock_run(returncode=1, stderr="HTTP 401")
    ):
        with pytest.raises(CommandError, match="HTTP 401"):
            pr_resolve_thread("PRRT_abc")


# ---------------------------------------------------------------------------
# pr_edit_comment
# ---------------------------------------------------------------------------


def test_pr_edit_comment_patches_correct_endpoint():
    response = {"id": 77, "user": {"login": "me"}, "body": "updated text"}
    with patch(
        "subprocess.run", return_value=_mock_run(stdout=json.dumps(response))
    ) as mock:
        result = pr_edit_comment(comment_id=77, body="updated text")
    args = mock.call_args[0][0]
    assert "--method" in args
    assert "PATCH" in args
    assert "pulls/comments/77" in " ".join(args)
    stdin_data = mock.call_args[1]["input"]
    payload = json.loads(stdin_data)
    assert payload["body"] == "updated text"
    assert "#77" in result
    assert "me" in result


def test_pr_edit_comment_empty_body_raises():
    with pytest.raises(CommandError):
        pr_edit_comment(comment_id=77, body="   ")


def test_pr_edit_comment_nonzero_exit_raises():
    with patch(
        "subprocess.run", return_value=_mock_run(returncode=1, stderr="HTTP 404")
    ):
        with pytest.raises(CommandError, match="HTTP 404"):
            pr_edit_comment(comment_id=99, body="oops")


# ---------------------------------------------------------------------------
# pr_delete_comment
# ---------------------------------------------------------------------------


def test_pr_delete_comment_sends_delete_to_correct_endpoint():
    with patch("subprocess.run", return_value=_mock_run()) as mock:
        result = pr_delete_comment(comment_id=42)
    args = mock.call_args[0][0]
    assert "--method" in args
    assert "DELETE" in args
    assert "pulls/comments/42" in " ".join(args)
    assert result == "comment #42 deleted"


def test_pr_delete_comment_nonzero_exit_raises():
    with patch(
        "subprocess.run", return_value=_mock_run(returncode=1, stderr="HTTP 404")
    ):
        with pytest.raises(CommandError, match="HTTP 404"):
            pr_delete_comment(comment_id=99)

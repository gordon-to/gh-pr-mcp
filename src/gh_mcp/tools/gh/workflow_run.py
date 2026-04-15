from ...run import CommandError, _validate_ref, format_result, run
from ._api import _repo_args


def workflow_run(
    workflow: str,
    ref: str = "",
    inputs: dict[str, str] | None = None,
    repo: str = "",
    repo_path: str = ".",
) -> str:
    """trigger a workflow_dispatch event (gh workflow run). gh:write.

    workflow: workflow name, id, or filename (e.g. 'ci.yml').
    ref: branch or tag to run on (default: repo default branch).
    inputs: dict of workflow input key=value pairs.
    """
    if not workflow.strip():
        raise CommandError("workflow must not be empty")
    args = ["gh", "workflow", "run", workflow] + _repo_args(repo)
    if ref:
        args += ["--ref", _validate_ref(ref, "ref")]
    for k, v in (inputs or {}).items():
        args += ["-f", f"{k}={v}"]
    return format_result(run(args, cwd=repo_path), f"gh workflow run {workflow}")

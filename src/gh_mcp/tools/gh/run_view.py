import json

from ...run import format_result, run_ok
from ._api import _repo_args


def run_view(run_id: str | int, repo: str = "", log: bool = False, repo_path: str = ".") -> str:
    """view a workflow run's details or logs (gh run view)."""
    args = ["gh", "run", "view", str(run_id)] + _repo_args(repo)
    if log:
        args.append("--log")
    else:
        args.append("--json")
        args.append("databaseId,name,status,conclusion,headBranch,event,jobs,startedAt,updatedAt")
    raw = run_ok(args, cwd=repo_path)
    if log:
        return format_result(raw, f"gh run view {run_id} --log")
    try:
        d = json.loads(raw)
        lines = [
            f"Run #{d['databaseId']}: {d['name']}",
            f"status: {d['status']}  conclusion: {d.get('conclusion', 'pending')}",
            f"branch: {d['headBranch']}  event: {d['event']}",
        ]
        if d.get("jobs"):
            lines.append("\njobs:")
            for job in d["jobs"]:
                lines.append(f"  {job['name']}: {job.get('conclusion') or job.get('status')}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh run view {run_id}")


def run_job_view(
    run_id: str | int,
    job_name: str = "",
    repo: str = "",
    log: bool = False,
    repo_path: str = ".",
) -> str:
    """view details or logs for a specific job within a run (gh run view --job).

    job_name: partial match for the job name shown in run_view output.
    log: fetch full step-by-step logs for the job.
    """
    args = ["gh", "run", "view", str(run_id)] + _repo_args(repo)
    if job_name:
        args += ["--job", job_name]
    if log:
        args.append("--log")
    else:
        args += ["--json", "jobs"]
    raw = run_ok(args, cwd=repo_path)
    if log or job_name:
        return format_result(raw, f"gh run view {run_id} --job {job_name}")
    try:
        d = json.loads(raw)
        jobs = d.get("jobs", [])
        if not jobs:
            return "no jobs found"
        lines = []
        for job in jobs:
            lines.append(f"{job['name']}: {job.get('conclusion') or job.get('status')}")
            for step in job.get("steps", []):
                lines.append(f"  [{step.get('conclusion') or step.get('status', '?'):8}] {step['name']}")
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh run view {run_id}")

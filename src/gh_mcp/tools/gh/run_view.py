import json
import re

from ...app import tool
from ...run import CommandError, format_result, run_ok
from ._api import _repo_args

_LOG_TAIL_LINES = 200
# gh --log lines are "<job>\t<step>\t<timestamp> <message>"; actions log files
# start with a BOM, which survives into the first line's timestamp field.
_LOG_TS = re.compile(r"^\ufeff?\d{4}-\d{2}-\d{2}T[0-9:.]+Z ?")
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


@tool("gh")
def run_view(
    run_id: str | int, repo: str = "", log: bool = False, repo_path: str = ""
) -> str:
    """view a workflow run's details or logs (gh run view)."""
    args = ["gh", "run", "view", str(run_id)] + _repo_args(repo, cwd=repo_path)
    if log:
        args.append("--log")
    else:
        args.append("--json")
        args.append(
            "databaseId,name,status,conclusion,headBranch,event,jobs,startedAt,updatedAt"
        )
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
                lines.append(
                    f"  {job['name']}: {job.get('conclusion') or job.get('status')}"
                )
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return format_result(raw, f"gh run view {run_id}")


def _match_job(jobs: list[dict], job_name: str, run_id: str | int) -> dict:
    """the one job whose name matches job_name; exact match beats substring."""
    lowered = job_name.lower()
    exact = [j for j in jobs if j["name"].lower() == lowered]
    matches = exact or [j for j in jobs if lowered in j["name"].lower()]
    if not matches:
        names = ", ".join(j["name"] for j in jobs) or "(none)"
        raise CommandError(
            f"no job matching {job_name!r} in run {run_id}; jobs: {names}"
        )
    if len(matches) > 1:
        names = ", ".join(j["name"] for j in matches)
        raise CommandError(f"job name {job_name!r} matches multiple jobs: {names}")
    return matches[0]


def _compose_log(raw: str, command: str) -> str:
    """group log lines under job/step headers, strip timestamps, tail long logs."""
    if not raw.strip():
        return format_result(raw, command)
    lines: list[str] = []
    current = None
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            if (parts[0], parts[1]) != current:
                current = (parts[0], parts[1])
                lines.append(f"== {parts[0]} / {parts[1]} ==")
            lines.append(_ANSI.sub("", _LOG_TS.sub("", parts[2])))
        else:
            # lines that don't match gh's log format (e.g. gh's own errors)
            lines.append(line)
    if len(lines) > _LOG_TAIL_LINES:
        cut = len(lines) - _LOG_TAIL_LINES
        tail = lines[cut:]
        header = next(
            (ln for ln in reversed(lines[: cut + 1]) if ln.startswith("== ")), None
        )
        if header and not tail[0].startswith("== "):
            tail.insert(0, header)
        notice = f"... {cut} earlier lines omitted (full log: `{command}`) ..."
        return "\n".join([notice, *tail])
    return "\n".join(lines)


@tool("gh")
def run_job_view(
    run_id: str | int = "",
    job_name: str = "",
    repo: str = "",
    log: bool = False,
    repo_path: str = "",
) -> str:
    """view details or logs for a specific job within a run (gh run view --job).

    run_id: the run's id. optional when job_name is a numeric job id.
    job_name: numeric job id, or a case-insensitive partial match on the job
    names shown in run_view output.
    log: fetch the job's step logs (timestamps stripped, long output tailed).
    """
    run_id = str(run_id).strip()
    if not run_id and not job_name.isdigit():
        raise CommandError(
            "run_id is required unless job_name is a numeric job id "
            "(the id in a checks url: .../actions/runs/<run_id>/job/<job_id>)"
        )
    base = ["gh", "run", "view", *([run_id] if run_id else [])] + _repo_args(
        repo, cwd=repo_path
    )

    def load_jobs(job_id: str = "") -> list[dict]:
        args = base + (["--job", job_id] if job_id else []) + ["--json", "jobs"]
        raw = run_ok(args, cwd=repo_path)
        try:
            return json.loads(raw).get("jobs", [])
        except json.JSONDecodeError as e:
            raise CommandError(f"gh run view {run_id} failed: {raw[:300]}") from e

    # gh's --job flag only accepts a numeric job id, so names resolve locally
    # against the run's job list.
    job_id = job_name if job_name.isdigit() else ""
    matched = None
    if job_name and not job_id:
        matched = _match_job(load_jobs(), job_name, run_id)
        job_id = str(matched["databaseId"])

    if log:
        args = base + (["--job", job_id] if job_id else []) + ["--log"]
        raw = run_ok(args, cwd=repo_path)
        return _compose_log(raw, f"gh run view {run_id} --job {job_id} --log")

    jobs = [matched] if matched else load_jobs(job_id)
    if not jobs:
        return "no jobs found"
    lines = []
    for job in jobs:
        lines.append(
            f"{job['name']} (id {job.get('databaseId', '?')}): "
            f"{job.get('conclusion') or job.get('status')}"
        )
        for step in job.get("steps", []):
            lines.append(
                f"  [{step.get('conclusion') or step.get('status', '?'):8}] {step['name']}"
            )
    return "\n".join(lines)

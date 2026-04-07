from pathlib import Path

from core.config import settings


def get_job_artifact_path(job_id: str) -> Path | None:
    artifact_dir = Path(settings.artifacts.root_path) / job_id
    if not artifact_dir.is_dir():
        return None

    files = sorted(path for path in artifact_dir.rglob("*") if path.is_file())
    return files[0] if files else None


def build_invocation_artifact_uri(invocation_id: str, job_id: str | None) -> str | None:
    if not job_id:
        return None
    if get_job_artifact_path(job_id) is None:
        return None
    return f"/api/invocations/{invocation_id}/artifact"

from __future__ import annotations

import asyncio
import json
import logging
import textwrap
import uuid
from decimal import Decimal
from typing import Any

import grpc
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from gateway_stubs import gateway_pb2, gateway_pb2_grpc
from models.service import Service

logger = logging.getLogger(__name__)


CSV_CLEANING_SLUG = "csv-cleaning-demo"


DEFAULT_CSV = textwrap.dedent(
    """\
    full_name,email,city,age
     alice smith ,ALICE@example.com, brussels ,29
    "Bob Jones",bob@example.com,liege,
    Charlie Brown,,Namur,41
    Alice Smith,alice@example.com,Brussels,29
    Dana White,dana@example.com, ghent,35
    "Eve, Marie",EVE@example.com,"mons, belgium", 34
    Frank Black,frank@example.com,Charleroi,0
    Gina Gray,gina@example.com,  antwerp  ,
    Henry Stone, HENRY@EXAMPLE.COM ,Liege, 52
    Ivy North,ivy@example.com,Arlon,27
    Jack West,jack@example.com,Brussels,0031
    Kate South,kate@example.com,Brussels,31
    Lara Bloom,LARA@example.com,Brussels,31
    " Mike Doe ",mike@example.com,"namur ",unknown
    Nora East,nora@example.com,Mechelen,44
    Oscar Reed,oscar@example.com,Hasselt,38
    Paul Reed,OSCAR@example.com,Hasselt,39
    Quinn Lake,quinn@example.com,Bruges,26
    Rita Vale,rita@example.com,Spa,19
    Sam Hill,sam@example.com,,23
    """
).strip()


CSV_CLEANING_DESCRIPTION = textwrap.dedent(
    """\
    Service de démonstration pour nettoyer des contacts CSV et valider les traitements de données sur la marketplace fédérée.

    Fonctionnement :
    - Lit le contenu CSV fourni dans la requête d'invocation ou utilise le jeu de données de démonstration intégré.
    - Normalise les noms, les adresses e-mail, les villes et les âges manquants.
    - Supprime les lignes sans adresse e-mail et les adresses e-mail en double.
    - Retourne un résumé JSON structuré et un artefact CSV nettoyé.

    Payload d'invocation recommandé :
    {"csv_content": "full_name,email,city,age\\n Alice Smith ,ALICE@example.com, brussels ,29"}

    Contrat de résultat :
    - Le résumé JSON structuré contient le nombre de lignes en entrée, de lignes nettoyées, de lignes supprimées, de doublons et le fichier de sortie.
    - Un artefact CSV nommé cleaned_contacts.csv contient les lignes nettoyées.
    """
).strip()


CSV_CLEANING_CODE = textwrap.dedent(
    """\
    import csv
    import json
    import os
    from io import StringIO
    from pathlib import Path


    DEFAULT_CSV = __DEFAULT_CSV__


    def load_args() -> dict:
        args_path = os.environ.get("JOB_ARGS_PATH")
        if not args_path:
            return {}
        path = Path(args_path)
        if not path.is_file():
            return {}
        with path.open() as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}


    def normalize_text(value: str | None, *, title_case: bool = False) -> str:
        cleaned = (value or "").strip()
        return cleaned.title() if title_case else cleaned


    def clean_csv(csv_content: str) -> tuple[list[dict[str, str]], dict[str, int]]:
        rows = list(csv.DictReader(StringIO(csv_content)))
        seen_emails: set[str] = set()
        cleaned_rows: list[dict[str, str]] = []
        missing_email_count = 0
        duplicate_email_count = 0

        for row in rows:
            email = normalize_text(row.get("email")).lower()
            if not email:
                missing_email_count += 1
                continue
            if email in seen_emails:
                duplicate_email_count += 1
                continue

            seen_emails.add(email)
            cleaned_rows.append({
                "full_name": normalize_text(row.get("full_name"), title_case=True),
                "email": email,
                "city": normalize_text(row.get("city"), title_case=True),
                "age": normalize_text(row.get("age")) or "unknown",
            })

        stats = {
            "input_rows": len(rows),
            "cleaned_rows": len(cleaned_rows),
            "dropped_rows": missing_email_count + duplicate_email_count,
            "missing_email_rows": missing_email_count,
            "duplicate_email_rows": duplicate_email_count,
        }
        return cleaned_rows, stats


    def main() -> None:
        params = load_args()
        csv_content = str(params.get("csv_content") or DEFAULT_CSV)
        output_filename = str(params.get("output_filename") or "cleaned_contacts.csv")

        cleaned_rows, stats = clean_csv(csv_content)

        out_dir = Path("/workspace")
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / output_filename
        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["full_name", "email", "city", "age"])
            writer.writeheader()
            writer.writerows(cleaned_rows)

        print(json.dumps({**stats, "output_file": str(output_path)}))


    if __name__ == "__main__":
        main()
    """
).replace("__DEFAULT_CSV__", json.dumps(DEFAULT_CSV)).strip()


CSV_CLEANING_SERVICE: dict[str, Any] = {
    "name": "CSV Cleaning Demo",
    "slug": CSV_CLEANING_SLUG,
    "description": CSV_CLEANING_DESCRIPTION,
    "category": "data-processing",
    "tags": ["csv", "data-cleaning", "contacts", "docker"],
    "service_type": "data",
    "version": "1.0.0",
    "status": "active",
    "price_type": "free",
    "price_amount": None,
    "currency": "EUR",
    "visibility": "public",
    "execution_mode": "async",
    "input_schema": {
        "csv_content": "string",
        "output_filename": "string",
    },
    "output_schema": {
        "input_rows": "integer",
        "cleaned_rows": "integer",
        "dropped_rows": "integer",
        "missing_email_rows": "integer",
        "duplicate_email_rows": "integer",
        "output_file": "string",
    },
    "max_concurrency": 4,
    "timeout_s": 120,
    "terms_of_use": None,
}


CSV_CLEANING_EXECUTION_CONFIG: dict[str, Any] = {
    "image": "python:3.14-slim",
    "code": CSV_CLEANING_CODE,
    "command": "python /workspace/run.py",
    "default_args": {
        "csv_content": DEFAULT_CSV,
        "output_filename": "cleaned_contacts.csv",
    },
    "default_env": {
        "PYTHONUNBUFFERED": "1",
    },
    "min_cpu": 1,
    "min_gpu": 0,
    "min_mem_mb": 256,
    "retry_count": 0,
}


GPU_STRESS_SLUG = "gpu-stress-benchmark"

GPU_STRESS_IMAGE = "pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime"


GPU_STRESS_DESCRIPTION = textwrap.dedent(
    """\
    Service de benchmark GPU synthétique pour valider la planification et l'exécution de charges fortement consommatrices de GPU sur la marketplace fédérée.

    Fonctionnement :
    - Alloue de grands tenseurs CUDA et exécute des multiplications de matrices répétées sur le GPU.
    - Génère une charge de calcul GPU soutenue, plutôt qu'une simple sonde courte ou un préchauffage de modèle.
    - Retourne des métadonnées de benchmark structurées et un artefact CSV contenant les temps de chaque itération.

    Prérequis d'exécution :
    - Un worker doit déclarer au moins 1 GPU et exposer des tags compatibles avec ce service : gpu, cuda, docker.
    - L'hôte qui exécute le worker doit disposer d'un pilote NVIDIA fonctionnel et de NVIDIA Container Toolkit.
    - L'image de conteneur configurée doit déjà contenir une version de PyTorch compatible CUDA.

    Payloads d'invocation recommandés :
    - Démarrage prudent pour les petits GPU : {"matrix_size": 8192, "iterations": 20, "warmup_steps": 5, "dtype": "float16"}
    - Charge plus forte pour les GPU de 8 Go ou plus : {"matrix_size": 12288, "iterations": 30, "warmup_steps": 5, "dtype": "float16"}

    Contrat de résultat :
    - Le résumé JSON structuré contient le nom du GPU, le type des tenseurs, la taille des matrices, le nombre d'itérations, le temps écoulé, le pic de mémoire GPU et la latence moyenne par itération.
    - Un artefact CSV nommé gpu_benchmark_metrics.csv contient les temps de chaque itération.

    Points d'attention :
    - Il s'agit d'un benchmark synthétique, pas d'une charge d'inférence de modèle.
    - Si aucun worker n'expose de GPU, l'invocation peut rester acceptée sans jamais démarrer.
    """
).strip()


GPU_STRESS_CODE = textwrap.dedent(
    """\
    import csv
    import json
    import os
    import time
    from pathlib import Path

    import torch


    def load_args() -> dict:
        args_path = os.environ.get("JOB_ARGS_PATH")
        if not args_path:
            return {}
        path = Path(args_path)
        if not path.is_file():
            return {}
        with path.open() as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}


    def main() -> None:
        if not torch.cuda.is_available():
            raise SystemExit("CUDA is not available inside the job container")

        params = load_args()
        matrix_size = int(params.get("matrix_size", 12288))
        iterations = int(params.get("iterations", 30))
        warmup_steps = int(params.get("warmup_steps", 5))
        dtype_name = str(params.get("dtype", "float16")).lower()

        dtype_map = {
            "float16": torch.float16,
            "float32": torch.float32,
            "bfloat16": torch.bfloat16,
        }
        if dtype_name not in dtype_map:
            raise SystemExit(f"Unsupported dtype: {dtype_name}")
        dtype = dtype_map[dtype_name]

        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(device)
        total_mem_mb = torch.cuda.get_device_properties(device).total_memory / (1024 * 1024)

        torch.manual_seed(42)
        a = torch.randn((matrix_size, matrix_size), device=device, dtype=dtype)
        b = torch.randn((matrix_size, matrix_size), device=device, dtype=dtype)

        for _ in range(warmup_steps):
            c = torch.matmul(a, b)
            torch.cuda.synchronize()
            del c

        torch.cuda.reset_peak_memory_stats(device)
        timings_ms = []
        benchmark_started = time.perf_counter()

        for _ in range(iterations):
            step_started = time.perf_counter()
            c = torch.matmul(a, b)
            torch.cuda.synchronize()
            timings_ms.append((time.perf_counter() - step_started) * 1000.0)
            del c

        elapsed_s = time.perf_counter() - benchmark_started
        peak_gpu_mem_mb = torch.cuda.max_memory_allocated(device) / (1024 * 1024)
        avg_iteration_ms = sum(timings_ms) / len(timings_ms)

        out_dir = Path("/workspace")
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = out_dir / "gpu_benchmark_metrics.csv"
        with artifact_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["iteration", "elapsed_ms"])
            for idx, elapsed_ms in enumerate(timings_ms, start=1):
                writer.writerow([idx, round(elapsed_ms, 3)])

        result = {
            "device": str(device),
            "gpu_name": gpu_name,
            "matrix_size": matrix_size,
            "iterations": iterations,
            "warmup_steps": warmup_steps,
            "dtype": dtype_name,
            "elapsed_s": round(elapsed_s, 4),
            "avg_iteration_ms": round(avg_iteration_ms, 3),
            "peak_gpu_mem_mb": round(peak_gpu_mem_mb, 2),
            "gpu_total_mem_mb": round(total_mem_mb, 2),
            "output_file": str(artifact_path),
        }
        print(json.dumps(result))


    if __name__ == "__main__":
        main()
    """
).strip()


GPU_STRESS_SERVICE: dict[str, Any] = {
    "name": "GPU Stress Benchmark",
    "slug": GPU_STRESS_SLUG,
    "description": GPU_STRESS_DESCRIPTION,
    "category": "benchmark",
    "tags": ["gpu", "cuda", "docker", "benchmark", "stress"],
    "service_type": "compute",
    "version": "1.0.0",
    "status": "active",
    "price_type": "free",
    "price_amount": None,
    "currency": "EUR",
    "visibility": "public",
    "execution_mode": "async",
    "input_schema": {
        "matrix_size": "integer",
        "iterations": "integer",
        "warmup_steps": "integer",
        "dtype": "string",
    },
    "output_schema": {
        "device": "string",
        "gpu_name": "string",
        "matrix_size": "integer",
        "iterations": "integer",
        "warmup_steps": "integer",
        "dtype": "string",
        "elapsed_s": "number",
        "avg_iteration_ms": "number",
        "peak_gpu_mem_mb": "number",
        "gpu_total_mem_mb": "number",
        "output_file": "string",
    },
    "max_concurrency": 1,
    "timeout_s": 900,
    "terms_of_use": None,
}


GPU_STRESS_EXECUTION_CONFIG: dict[str, Any] = {
    "image": GPU_STRESS_IMAGE,
    "code": GPU_STRESS_CODE,
    "command": "python /workspace/run.py",
    # Intentionally small defaults so an empty invocation payload still runs;
    # increase matrix_size/iterations for a real stress run.
    "default_args": {
        "matrix_size": 2048,
        "iterations": 3,
        "warmup_steps": 1,
        "dtype": "float16",
    },
    "default_env": {
        "PYTHONUNBUFFERED": "1",
    },
    "min_cpu": 2,
    "min_gpu": 1,
    "min_mem_mb": 4096,
    "retry_count": 0,
}


async def _upsert_service(session: AsyncSession, fixture: dict[str, Any]) -> Service:
    result = await session.execute(select(Service).where(Service.slug == fixture["slug"]))
    service = result.scalar_one_or_none()

    values = dict(fixture)
    values["provider_site_id"] = settings.marketplace.site_id
    if values["price_amount"] is not None:
        values["price_amount"] = Decimal(str(values["price_amount"]))

    if service is None:
        service = Service(id=str(uuid.uuid7()), **values)
        session.add(service)
        logger.info("Seeded fixture service: %s", fixture["slug"])
    else:
        if service.slug != slugify(values["name"]):
            logger.warning(
                "Fixture service %s has a slug that does not match its name",
                service.slug,
            )
        for key, value in values.items():
            setattr(service, key, value)
        logger.info("Updated fixture service: %s", fixture["slug"])

    await session.commit()
    await session.refresh(service)
    return service


async def _register_execution_config(
    grpc_channel: grpc.aio.Channel,
    slug: str,
    config: dict[str, Any],
) -> None:
    stub = gateway_pb2_grpc.GatewayServiceStub(grpc_channel)
    request = gateway_pb2.RegisterServiceConfigRequest(
        service_slug=slug,
        retry_count=int(config.get("retry_count", 0)),
    )
    if config.get("image"):
        request.image = config["image"]
    if config.get("code"):
        request.code = config["code"]
    if config.get("command"):
        request.command = config["command"]
    if config.get("default_args"):
        request.default_args.update(config["default_args"])
    if config.get("default_env"):
        request.default_env.update(config["default_env"])
    if config.get("min_cpu") is not None:
        request.min_cpu = int(config["min_cpu"])
    if config.get("min_gpu") is not None:
        request.min_gpu = int(config["min_gpu"])
    if config.get("min_mem_mb") is not None:
        request.min_mem_mb = int(config["min_mem_mb"])

    response = await asyncio.wait_for(stub.RegisterServiceConfig(request), timeout=10)
    action = "created" if response.created else "updated"
    logger.info("Fixture execution config %s for service: %s", action, slug)


def _enabled_fixtures() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """Return (slug, service_fixture, execution_config) for each enabled demo."""
    fixtures: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    if not settings.fixtures.enabled:
        return fixtures
    if settings.fixtures.seed_csv_cleaning_demo:
        fixtures.append(
            (CSV_CLEANING_SLUG, CSV_CLEANING_SERVICE, CSV_CLEANING_EXECUTION_CONFIG)
        )
    if settings.fixtures.seed_gpu_stress_demo:
        fixtures.append(
            (GPU_STRESS_SLUG, GPU_STRESS_SERVICE, GPU_STRESS_EXECUTION_CONFIG)
        )
    return fixtures


async def seed_demo_services(
    session: AsyncSession,
) -> None:
    """Seed demo marketplace service catalog rows."""
    for _slug, service_fixture, _config in _enabled_fixtures():
        await _upsert_service(session, service_fixture)


async def register_demo_execution_configs(
    grpc_channel: grpc.aio.Channel,
    attempts: int = 6,
    delay_s: float = 5.0,
) -> None:
    """Register demo provider execution configs without blocking app startup."""
    for slug, _service_fixture, config in _enabled_fixtures():
        for attempt in range(1, attempts + 1):
            try:
                await _register_execution_config(grpc_channel, slug, config)
                break
            except (asyncio.TimeoutError, grpc.RpcError) as exc:
                logger.warning(
                    "Fixture execution config registration failed for %s "
                    "(attempt %d/%d): %s",
                    slug,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt < attempts:
                    await asyncio.sleep(delay_s)
        else:
            logger.error(
                "Fixture execution config registration exhausted retries for %s",
                slug,
            )

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
    CSV contact cleaning demo service for validating data-processing jobs in the federated marketplace.

    What it does:
    - Reads CSV content from the invocation payload, or uses the bundled demo fixture.
    - Normalizes names, email addresses, cities, and missing ages.
    - Drops rows without an email address and removes duplicate email addresses.
    - Returns a structured JSON summary and a cleaned CSV artifact.

    Recommended invocation payload:
    {"csv_content": "full_name,email,city,age\\n Alice Smith ,ALICE@example.com, brussels ,29"}

    Result contract:
    - Structured JSON summary includes input row count, cleaned row count, dropped row count, duplicate count, and output file.
    - A CSV artifact named cleaned_contacts.csv contains the cleaned rows.
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


async def seed_demo_services(
    session: AsyncSession,
) -> None:
    """Seed demo marketplace service catalog rows."""
    if not settings.fixtures.enabled:
        return
    if not settings.fixtures.seed_csv_cleaning_demo:
        return

    await _upsert_service(session, CSV_CLEANING_SERVICE)


async def register_demo_execution_configs(
    grpc_channel: grpc.aio.Channel,
    attempts: int = 6,
    delay_s: float = 5.0,
) -> None:
    """Register demo provider execution configs without blocking app startup."""
    if not settings.fixtures.enabled:
        return
    if not settings.fixtures.seed_csv_cleaning_demo:
        return

    for attempt in range(1, attempts + 1):
        try:
            await _register_execution_config(
                grpc_channel,
                CSV_CLEANING_SLUG,
                CSV_CLEANING_EXECUTION_CONFIG,
            )
            return
        except (asyncio.TimeoutError, grpc.RpcError) as exc:
            logger.warning(
                "Fixture execution config registration failed for %s "
                "(attempt %d/%d): %s",
                CSV_CLEANING_SLUG,
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                await asyncio.sleep(delay_s)

    logger.error(
        "Fixture execution config registration exhausted retries for %s",
        CSV_CLEANING_SLUG,
    )

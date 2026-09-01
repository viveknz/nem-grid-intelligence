"""Local ingest script for the Open Electricity API.

Runs OUTSIDE Databricks — Free Edition restricts outbound network access
from notebooks, so this fetches data locally and lands it to data/raw/.
A bronze notebook then reads the uploaded file from the Unity Catalog
volume (nem_intel.bronze.raw_landing). See docs/02_data_sources.md.

Requires OPENELECTRICITY_API_KEY set in the environment. Never hardcode
the key — the official client reads it from the environment automatically.

Usage:
    python -m nem.ingest.open_electricity
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from nem.logging_config import get_logger

logger = get_logger(__name__)

RAW_DATA_DIR = Path("data/raw")

# NEM market time is fixed AEST (UTC+10) year-round, no daylight saving,
# regardless of which state a request originates from. The API expects
# date_start/date_end as NAIVE timestamps in this local time — a
# timezone-aware UTC datetime causes a 400 with no useful error message,
# because the installed SDK version only surfaces the "detail" key on
# error responses, while this endpoint's actual message is under "error".
# Confirmed via a direct curl call bypassing the SDK. See build log
# 2026-09-01/02.
NEM_TZ = ZoneInfo("Australia/Brisbane")


def default_date_range(days: int = 7, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Compute a naive NEM-local-time (date_start, date_end) pair.

    `now` is injectable so this is testable without depending on the
    actual current time.
    """
    now = now or datetime.now(NEM_TZ)
    date_end = now.replace(minute=0, second=0, microsecond=0, tzinfo=None)
    date_start = date_end - timedelta(days=days)
    return date_start, date_end


def fetch_nem_power_by_region_fueltech(
    client: Any,
    date_start: datetime,
    date_end: datetime,
    interval: str = "1h",
) -> list[dict]:
    """Fetch NEM power data broken down by region and fuel technology group.

    Region breakdown (primary_grouping) is what makes rooftop solar's
    contribution visible per NEM region without any spatial join — see
    doc 02 source 1. fueltech_group (secondary_grouping) separates rooftop
    solar from other generation types.

    `client` is injected rather than constructed here so tests can pass a
    fake client instead of hitting the real API.

    NOTE: this does NOT use the SDK's response.to_records() — that method
    only reads result.columns, which the installed SDK version (0.11.3)
    leaves as None for whichever dimension was used as primary_grouping.
    The region is still present, just encoded in result.name instead
    (format: "{metric}_{region}|{secondary_value}", e.g. "power_NSW1|battery")
    — confirmed via a live diagnostic call. Parsing that string is a
    workaround for an SDK gap, not a documented API contract, so this
    needs re-checking if the SDK version changes. See build log
    2026-09-02.
    """
    from openelectricity.types import DataMetric

    response = client.get_network_data(
        network_code="NEM",
        metrics=[DataMetric.POWER],
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping="network_region",
        secondary_grouping="fueltech_group",
    )

    records: list[dict] = []
    for series in response.data:
        name_prefix = f"{series.metric}_"
        for result in series.results:
            if not result.name.startswith(name_prefix) or "|" not in result.name:
                logger.warning(
                    "unexpected result.name format, skipping this result: %r", result.name
                )
                continue
            region, fueltech_group = result.name[len(name_prefix):].split("|", 1)
            for point in result.data:
                records.append({
                    "interval": point.timestamp.isoformat(),
                    "network_region": region,
                    "fueltech_group": fueltech_group,
                    series.metric: point.value,
                })

    logger.info("fetched %d records from Open Electricity API", len(records))
    return records


def write_records_to_csv(records: list[dict], output_path: Path) -> None:
    """Write a list of record dicts to CSV, creating parent dirs as needed.

    Pure function, deliberately separate from the API call — this is the
    part that's easy and cheap to unit test.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        logger.warning("no records to write — writing empty file with no rows: %s", output_path)
        output_path.write_text("")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info("wrote %d rows to %s", len(records), output_path)


def dated_filename(prefix: str, run_time: datetime | None = None) -> str:
    """Build a dated filename so repeated runs don't overwrite each other."""
    run_time = run_time or datetime.now(NEM_TZ)
    return f"{prefix}_{run_time.strftime('%Y%m%d_%H%M%S')}.csv"


def main() -> None:
    if not os.environ.get("OPENELECTRICITY_API_KEY"):
        logger.error("OPENELECTRICITY_API_KEY not set in environment — aborting")
        raise SystemExit(1)

    from openelectricity import OEClient

    date_start, date_end = default_date_range(days=7)

    logger.info("fetching NEM power data (network-local time): %s to %s", date_start, date_end)

    with OEClient() as client:
        records = fetch_nem_power_by_region_fueltech(client, date_start, date_end)

    output_path = RAW_DATA_DIR / dated_filename("nem_power_region_fueltech")
    write_records_to_csv(records, output_path)


if __name__ == "__main__":
    main()

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
    doc 02 source 1. fueltech (secondary_grouping) separates rooftop solar
    from other generation types.

    Uses "fueltech" rather than the coarser "fueltech_group" — the latter
    merges solar_rooftop and solar_utility into a single "solar" bucket,
    which loses exactly the distinction this project needs. Confirmed via
    a live query that returned only "solar" under fueltech_group, then via
    UnitFueltechType inspection that solar_rooftop/solar_utility/solar_thermal
    exist separately at the "fueltech" level. See build log 2026-09-02.

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
        secondary_grouping="fueltech",
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
            region, fueltech = result.name[len(name_prefix):].split("|", 1)
            for point in result.data:
                records.append({
                    "interval": point.timestamp.isoformat(),
                    "network_region": region,
                    "fueltech": fueltech,
                    series.metric: point.value,
                })

    logger.info("fetched %d records from Open Electricity API", len(records))
    return records


def fetch_nem_demand_by_region(
    client: Any,
    date_start: datetime,
    date_end: datetime,
    interval: str = "1h",
) -> list[dict]:
    """Fetch NEM demand and demand_gross by region.

    demand: operational demand (grid draw) — excludes rooftop solar, since
    it isn't centrally dispatched/measured the way scheduled generation is.
    demand_gross: demand + rooftop solar generation. This is OpenElectricity's
    own formal definition (opennem/opennem GitHub issue #398):
        demand_gross = demand_and_nonsched + rooftop_generation
    The gap between demand and demand_gross is rooftop solar's suppression
    effect on grid demand, directly — this is the core signal for the
    project's minimum-demand question.

    Uses get_market, not get_network_data — demand lives on a separate
    endpoint (MarketMetric, not DataMetric). get_market has no
    secondary_grouping parameter, so result.name is "{metric}_{region}"
    (no pipe separator), unlike the power fetch. Confirmed via a live
    diagnostic call. See build log 2026-09-05.

    Returns one record per (interval, region), with demand and demand_gross
    as separate columns on the same row — wide format, ready to join
    against fetch_nem_power_by_region_fueltech's output later.
    """
    from openelectricity.types import MarketMetric

    response = client.get_market(
        network_code="NEM",
        metrics=[MarketMetric.DEMAND, MarketMetric.DEMAND_GROSS],
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping="network_region",
    )

    by_key: dict[tuple, dict] = {}
    for series in response.data:
        name_prefix = f"{series.metric}_"
        for result in series.results:
            if not result.name.startswith(name_prefix):
                logger.warning(
                    "unexpected result.name format, skipping this result: %r", result.name
                )
                continue
            region = result.name[len(name_prefix):]
            for point in result.data:
                ts = point.timestamp.isoformat()
                key = (ts, region)
                record = by_key.setdefault(key, {"interval": ts, "network_region": region})
                record[series.metric] = point.value

    records = list(by_key.values())
    logger.info("fetched %d demand records from Open Electricity API", len(records))
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

    logger.info("fetching NEM data (network-local time): %s to %s", date_start, date_end)

    with OEClient() as client:
        power_records = fetch_nem_power_by_region_fueltech(client, date_start, date_end)
        demand_records = fetch_nem_demand_by_region(client, date_start, date_end)

    power_path = RAW_DATA_DIR / dated_filename("nem_power_region_fueltech")
    write_records_to_csv(power_records, power_path)

    demand_path = RAW_DATA_DIR / dated_filename("nem_demand_region")
    write_records_to_csv(demand_records, demand_path)


if __name__ == "__main__":
    main()

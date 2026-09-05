"""Backfill orchestration for the Open Electricity API.

Runs OUTSIDE Databricks, same as open_electricity.py — see that module's
docstring for why. This handles the historical pull specifically: chunking
requests to respect the API's per-interval date range limits (32 days for
hourly — see docs.openelectricity.org.au/api-reference/data-limits), and
resuming cleanly if interrupted partway through.

Usage:
    python -m nem.ingest.backfill --start 2015-01-01 --end 2026-09-05
"""

import argparse
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from nem.ingest.open_electricity import (
    fetch_nem_demand_by_region,
    fetch_nem_power_by_region_fueltech,
    write_records_to_csv,
)
from nem.logging_config import get_logger

logger = get_logger(__name__)

BACKFILL_DIR = Path("data/raw/backfill")

# Confirmed via docs.openelectricity.org.au/api-reference/data-limits —
# hourly interval's maximum range per request.
HOURLY_MAX_RANGE_DAYS = 32

# Undocumented rate limits — this is a courtesy pause between chunk
# requests, not a value derived from any published number.
SECONDS_BETWEEN_CHUNKS = 1.0


def chunk_date_range(
    start: datetime, end: datetime, max_days: int
) -> Iterator[tuple[datetime, datetime]]:
    """Split (start, end) into consecutive (chunk_start, chunk_end) pairs,
    each spanning at most max_days, covering the full range with no gaps
    or overlaps.

    Pure function — the actual chunking logic, easy to test exhaustively
    without touching the network.
    """
    current_start = start
    while current_start < end:
        current_end = min(current_start + timedelta(days=max_days), end)
        yield (current_start, current_end)
        current_start = current_end


def chunk_output_path(prefix: str, chunk_start: datetime, chunk_end: datetime) -> Path:
    """Deterministic filename per chunk, so a completed chunk can be
    detected and skipped on a re-run — this is what makes the backfill
    resumable rather than all-or-nothing."""
    start_str = chunk_start.strftime("%Y%m%d")
    end_str = chunk_end.strftime("%Y%m%d")
    return BACKFILL_DIR / f"{prefix}_{start_str}_{end_str}.csv"


def run_backfill(
    client: Any,
    start: datetime,
    end: datetime,
    max_days: int = HOURLY_MAX_RANGE_DAYS,
    sleep_seconds: float = SECONDS_BETWEEN_CHUNKS,
) -> dict:
    """Run the full backfill, chunk by chunk, skipping chunks whose output
    file already exists.

    `client` is injected for the same reason as in open_electricity.py —
    testability without a real API key.

    Returns a summary dict: total chunks, chunks skipped (already done),
    chunks fetched this run, total rows written across both power and
    demand data.
    """
    chunks = list(chunk_date_range(start, end, max_days))
    logger.info("backfill plan: %d chunks from %s to %s", len(chunks), start, end)

    summary = {"total_chunks": len(chunks), "skipped": 0, "fetched": 0, "total_rows": 0}

    for i, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        power_path = chunk_output_path("nem_power_region_fueltech", chunk_start, chunk_end)
        demand_path = chunk_output_path("nem_demand_region", chunk_start, chunk_end)

        if power_path.exists() and demand_path.exists():
            logger.info("chunk %d/%d already done, skipping: %s to %s",
                        i, len(chunks), chunk_start, chunk_end)
            summary["skipped"] += 1
            continue

        logger.info("chunk %d/%d fetching: %s to %s", i, len(chunks), chunk_start, chunk_end)

        power_records = fetch_nem_power_by_region_fueltech(client, chunk_start, chunk_end)
        write_records_to_csv(power_records, power_path)

        demand_records = fetch_nem_demand_by_region(client, chunk_start, chunk_end)
        write_records_to_csv(demand_records, demand_path)

        summary["fetched"] += 1
        summary["total_rows"] += len(power_records) + len(demand_records)

        if i < len(chunks):
            time.sleep(sleep_seconds)

    logger.info(
        "backfill complete: %d chunks total, %d skipped, %d fetched, %d rows written",
        summary["total_chunks"], summary["skipped"], summary["fetched"], summary["total_rows"],
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill NEM power and demand data.")
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date, YYYY-MM-DD")
    args = parser.parse_args()

    if not os.environ.get("OPENELECTRICITY_API_KEY"):
        logger.error("OPENELECTRICITY_API_KEY not set in environment — aborting")
        raise SystemExit(1)

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")

    from openelectricity import OEClient

    with OEClient() as client:
        run_backfill(client, start, end)


if __name__ == "__main__":
    main()

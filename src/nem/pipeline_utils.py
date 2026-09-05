"""Shared helpers for the run_log convention (docs/04_engineering_standards.md
section 5): every pipeline notebook writes one row to nem_intel.gold.run_log
recording what it did.

build_run_log_row is deliberately pure — it just shapes a dict, no Spark,
no Unity Catalog — so it's fully unit-testable. The actual write (creating
the table if needed, appending the row) lives in each notebook, since that
part needs a live Unity Catalog connection and can't be meaningfully
tested outside Databricks.
"""

from datetime import datetime


def build_run_log_row(
    notebook_name: str,
    start_time: datetime,
    end_time: datetime,
    rows_in: int,
    rows_out: int,
    status: str,
) -> dict:
    """Shape a single run_log row. status should be 'success' or 'failed'."""
    if status not in ("success", "failed"):
        raise ValueError(f"status must be 'success' or 'failed', got {status!r}")

    return {
        "notebook_name": notebook_name,
        "start_time": start_time,
        "end_time": end_time,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "status": status,
    }

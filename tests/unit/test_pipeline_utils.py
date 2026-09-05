"""Unit tests for nem.pipeline_utils."""

from datetime import datetime

import pytest

from nem.pipeline_utils import build_run_log_row


def test_build_run_log_row_shapes_all_fields_correctly():
    start = datetime(2026, 9, 5, 10, 0, 0)
    end = datetime(2026, 9, 5, 10, 5, 0)

    row = build_run_log_row(
        notebook_name="01_load_power_demand",
        start_time=start,
        end_time=end,
        rows_in=1000,
        rows_out=980,
        status="success",
    )

    assert row["notebook_name"] == "01_load_power_demand"
    assert row["start_time"] == start
    assert row["end_time"] == end
    assert row["rows_in"] == 1000
    assert row["rows_out"] == 980
    assert row["status"] == "success"


def test_build_run_log_row_rejects_invalid_status():
    with pytest.raises(ValueError):
        build_run_log_row(
            notebook_name="test",
            start_time=datetime.now(),
            end_time=datetime.now(),
            rows_in=1,
            rows_out=1,
            status="maybe",
        )


@pytest.mark.parametrize("status", ["success", "failed"])
def test_build_run_log_row_accepts_valid_statuses(status):
    row = build_run_log_row(
        notebook_name="test",
        start_time=datetime.now(),
        end_time=datetime.now(),
        rows_in=1,
        rows_out=1,
        status=status,
    )
    assert row["status"] == status

"""Unit tests for nem.ingest.open_electricity.

No network calls — the API client is mocked throughout. These test our
code's behavior (correct call shape, correct CSV output), not Open
Electricity's API itself.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from nem.ingest.open_electricity import (
    dated_filename,
    fetch_nem_power_by_region_fueltech,
    write_records_to_csv,
)


def test_fetch_calls_client_with_correct_grouping():
    """Region + fueltech_group grouping is what makes rooftop solar's
    regional contribution visible — this is the one thing that must not
    silently change."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.to_records.return_value = [
        {"interval": "2026-01-01T00:00:00Z", "network_region": "NSW1",
         "fueltech_group": "solar_rooftop", "power": 120.5},
    ]
    mock_client.get_network_data.return_value = mock_response

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)

    result = fetch_nem_power_by_region_fueltech(mock_client, start, end)

    mock_client.get_network_data.assert_called_once()
    call_kwargs = mock_client.get_network_data.call_args.kwargs
    assert call_kwargs["network_code"] == "NEM"
    assert call_kwargs["primary_grouping"] == "network_region"
    assert call_kwargs["secondary_grouping"] == "fueltech_group"
    assert call_kwargs["date_start"] == start
    assert call_kwargs["date_end"] == end
    assert len(result) == 1


def test_fetch_returns_empty_list_when_no_data():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.to_records.return_value = []
    mock_client.get_network_data.return_value = mock_response

    result = fetch_nem_power_by_region_fueltech(
        mock_client,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    assert result == []


def test_write_records_to_csv_writes_header_and_rows(tmp_path):
    records = [
        {"region": "NSW1", "fueltech_group": "solar_rooftop", "power": 100.0},
        {"region": "VIC1", "fueltech_group": "coal", "power": 500.0},
    ]
    output_path = tmp_path / "test_output.csv"

    write_records_to_csv(records, output_path)

    content = output_path.read_text()
    lines = content.strip().split("\n")
    assert lines[0] == "region,fueltech_group,power"
    assert len(lines) == 3  # header + 2 rows


def test_write_records_to_csv_creates_parent_dirs(tmp_path):
    output_path = tmp_path / "nested" / "dir" / "output.csv"
    write_records_to_csv([{"a": 1}], output_path)
    assert output_path.exists()


def test_write_records_to_csv_handles_empty_list(tmp_path):
    output_path = tmp_path / "empty.csv"
    write_records_to_csv([], output_path)
    assert output_path.exists()
    assert output_path.read_text() == ""


def test_dated_filename_includes_timestamp():
    run_time = datetime(2026, 3, 15, 14, 30, 0, tzinfo=timezone.utc)
    result = dated_filename("nem_power", run_time)
    assert result == "nem_power_20260315_143000.csv"


def test_dated_filename_default_prefix_only():
    result = dated_filename("test")
    assert result.startswith("test_")
    assert result.endswith(".csv")

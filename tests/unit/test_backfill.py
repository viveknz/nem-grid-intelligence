"""Unit tests for nem.ingest.backfill.

Network is always mocked. Filesystem uses tmp_path so tests never touch
the real data/raw/backfill directory.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from nem.ingest.backfill import (
    chunk_date_range,
    chunk_output_path,
    run_backfill,
)


def test_chunk_date_range_covers_full_span_no_gaps():
    start = datetime(2015, 1, 1)
    end = datetime(2015, 6, 1)
    chunks = list(chunk_date_range(start, end, max_days=32))

    assert chunks[0][0] == start
    assert chunks[-1][1] == end
    # every chunk's end must equal the next chunk's start — no gap, no overlap
    for (s1, e1), (s2, e2) in zip(chunks, chunks[1:]):
        assert e1 == s2


def test_chunk_date_range_respects_max_days():
    start = datetime(2015, 1, 1)
    end = datetime(2015, 12, 31)
    chunks = list(chunk_date_range(start, end, max_days=32))

    for chunk_start, chunk_end in chunks:
        assert (chunk_end - chunk_start).days <= 32


def test_chunk_date_range_single_chunk_when_span_fits():
    start = datetime(2015, 1, 1)
    end = datetime(2015, 1, 15)  # well under 32 days
    chunks = list(chunk_date_range(start, end, max_days=32))
    assert len(chunks) == 1
    assert chunks[0] == (start, end)


def test_chunk_date_range_empty_when_start_equals_end():
    start = datetime(2015, 1, 1)
    chunks = list(chunk_date_range(start, start, max_days=32))
    assert chunks == []


def test_chunk_output_path_is_deterministic():
    start = datetime(2015, 1, 1)
    end = datetime(2015, 2, 2)
    path1 = chunk_output_path("nem_power", start, end)
    path2 = chunk_output_path("nem_power", start, end)
    assert path1 == path2
    assert "20150101" in str(path1)
    assert "20150202" in str(path1)


def test_run_backfill_skips_chunks_with_existing_output(tmp_path, monkeypatch):
    """The whole point of resumability — a chunk whose output files already
    exist must not be re-fetched."""
    import nem.ingest.backfill as backfill_module
    monkeypatch.setattr(backfill_module, "BACKFILL_DIR", tmp_path)

    start = datetime(2015, 1, 1)
    end = datetime(2015, 1, 10)  # fits in one chunk

    # Pre-create both output files to simulate a completed prior run
    power_path = backfill_module.chunk_output_path("nem_power_region_fueltech", start, end)
    demand_path = backfill_module.chunk_output_path("nem_demand_region", start, end)
    power_path.write_text("interval,network_region,fueltech,power\n")
    demand_path.write_text("interval,network_region,demand,demand_gross\n")

    mock_client = MagicMock()
    summary = run_backfill(mock_client, start, end, max_days=32, sleep_seconds=0)

    assert summary["skipped"] == 1
    assert summary["fetched"] == 0
    mock_client.get_network_data.assert_not_called()
    mock_client.get_market.assert_not_called()


def test_run_backfill_fetches_missing_chunks(tmp_path, monkeypatch):
    import nem.ingest.backfill as backfill_module
    monkeypatch.setattr(backfill_module, "BACKFILL_DIR", tmp_path)

    start = datetime(2015, 1, 1)
    end = datetime(2015, 1, 10)

    ts = datetime(2015, 1, 1, 10, 0)
    mock_client = MagicMock()
    mock_client.get_network_data.return_value = SimpleNamespace(data=[
        SimpleNamespace(metric="power", results=[
            SimpleNamespace(name="power_NSW1|coal_black", data=[SimpleNamespace(timestamp=ts, value=100.0)]),
        ]),
    ])
    mock_client.get_market.return_value = SimpleNamespace(data=[
        SimpleNamespace(metric="demand", results=[
            SimpleNamespace(name="demand_NSW1", data=[SimpleNamespace(timestamp=ts, value=7000.0)]),
        ]),
    ])

    summary = run_backfill(mock_client, start, end, max_days=32, sleep_seconds=0)

    assert summary["fetched"] == 1
    assert summary["skipped"] == 0
    assert summary["total_rows"] == 2  # 1 power record + 1 demand record

    power_path = backfill_module.chunk_output_path("nem_power_region_fueltech", start, end)
    demand_path = backfill_module.chunk_output_path("nem_demand_region", start, end)
    assert power_path.exists()
    assert demand_path.exists()


def test_run_backfill_processes_multiple_chunks(tmp_path, monkeypatch):
    import nem.ingest.backfill as backfill_module
    monkeypatch.setattr(backfill_module, "BACKFILL_DIR", tmp_path)

    start = datetime(2015, 1, 1)
    end = datetime(2015, 3, 15)  # spans 3 chunks at max_days=32

    mock_client = MagicMock()
    mock_client.get_network_data.return_value = SimpleNamespace(data=[])
    mock_client.get_market.return_value = SimpleNamespace(data=[])

    summary = run_backfill(mock_client, start, end, max_days=32, sleep_seconds=0)

    assert summary["total_chunks"] == 3
    assert summary["fetched"] == 3
    assert mock_client.get_network_data.call_count == 3
    assert mock_client.get_market.call_count == 3

"""Unit tests for nem.transform.bronze_ingest.

First tests in the repo to use a real (local, single-process) Spark
session rather than pure Python / mocks — see tests/conftest.py.
"""

from nem.transform.bronze_ingest import DEMAND_SCHEMA, POWER_SCHEMA, load_csvs


def test_load_csvs_reads_power_schema_correctly(spark, tmp_path):
    csv_content = (
        "interval,network_region,fueltech,power\n"
        "2015-01-01T00:00:00+10:00,NSW1,coal_black,5200.5\n"
        "2015-01-01T00:00:00+10:00,NSW1,solar_rooftop,0.0\n"
    )
    csv_file = tmp_path / "chunk1.csv"
    csv_file.write_text(csv_content)

    df = load_csvs(spark, str(csv_file), POWER_SCHEMA)

    assert df.count() == 2
    assert set(df.columns) == {"interval", "network_region", "fueltech", "power", "_source_file"}
    row = df.filter(df.fueltech == "coal_black").first()
    assert row["network_region"] == "NSW1"
    assert row["power"] == 5200.5


def test_load_csvs_reads_demand_schema_correctly(spark, tmp_path):
    csv_content = (
        "interval,network_region,demand,demand_gross\n"
        "2015-01-01T00:00:00+10:00,NSW1,7900.0,8300.0\n"
    )
    csv_file = tmp_path / "demand_chunk1.csv"
    csv_file.write_text(csv_content)

    df = load_csvs(spark, str(csv_file), DEMAND_SCHEMA)

    assert df.count() == 1
    row = df.first()
    assert row["demand"] == 7900.0
    assert row["demand_gross"] == 8300.0


def test_load_csvs_adds_source_file_lineage_column(spark, tmp_path):
    csv_file = tmp_path / "chunk1.csv"
    csv_file.write_text("interval,network_region,fueltech,power\n2015-01-01T00:00:00+10:00,NSW1,coal_black,100.0\n")

    df = load_csvs(spark, str(csv_file), POWER_SCHEMA)

    source_file = df.first()["_source_file"]
    assert "chunk1.csv" in source_file


def test_load_csvs_reads_multiple_files_via_glob(spark, tmp_path):
    (tmp_path / "chunk1.csv").write_text(
        "interval,network_region,fueltech,power\n2015-01-01T00:00:00+10:00,NSW1,coal_black,100.0\n"
    )
    (tmp_path / "chunk2.csv").write_text(
        "interval,network_region,fueltech,power\n2015-02-01T00:00:00+10:00,VIC1,wind,200.0\n"
    )

    df = load_csvs(spark, str(tmp_path / "*.csv"), POWER_SCHEMA)

    assert df.count() == 2
    regions = {r["network_region"] for r in df.collect()}
    assert regions == {"NSW1", "VIC1"}

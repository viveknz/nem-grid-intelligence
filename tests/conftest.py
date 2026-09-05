"""Shared pytest fixtures.

The `spark` fixture provides a local, single-process SparkSession for
testing transform functions against small in-memory DataFrames — no
cluster, no real data, fast enough to run on every commit (per doc 04
section 6). Session-scoped so it starts once per test run, not once per
test — Spark session startup is slow enough that per-test scope would
make the suite noticeably slower for no benefit.
"""

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("nem-grid-intelligence-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()

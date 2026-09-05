# Databricks notebook source
# MAGIC %md
# MAGIC # 01_bronze / 01_load_power_demand
# MAGIC
# MAGIC Loads the backfilled Open Electricity CSVs (power by region/fueltech,
# MAGIC demand and demand_gross by region) from the landing volume into bronze
# MAGIC Delta tables. Explicit schema, minimal transformation — real cleaning
# MAGIC and typing (interval string -> timestamp) happens in silver, Phase 2.
# MAGIC
# MAGIC First pipeline notebook in the repo, so it also creates the run_log
# MAGIC table (docs/04_engineering_standards.md section 5) that every future
# MAGIC pipeline notebook writes a row to.
# MAGIC
# MAGIC **BACKFILL-ONLY — do not schedule this notebook as-is.** It writes
# MAGIC with `mode("overwrite")`, replacing the whole table on every run.
# MAGIC That's correct for a one-time historical load, but would silently
# MAGIC destroy history if run on a schedule against only new incremental
# MAGIC data. Ongoing/incremental ingestion needs a separate notebook with
# MAGIC append + dedup logic — not built yet. See build log 2026-09-05.
# MAGIC
# MAGIC **Reads:** `/Volumes/nem_intel/bronze/raw_landing/backfill/*.csv`
# MAGIC **Writes:** `nem_intel.bronze.region_power_fueltech_hourly`,
# MAGIC `nem_intel.bronze.region_demand_hourly`, one row to
# MAGIC `nem_intel.gold.run_log`

# COMMAND ----------

import os
import sys
from datetime import datetime, timezone

_src_path = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "src"))
if _src_path not in sys.path:
    sys.path.append(_src_path)

from nem.logging_config import get_logger
from nem.pipeline_utils import build_run_log_row
from nem.transform.bronze_ingest import DEMAND_SCHEMA, POWER_SCHEMA, load_csvs

logger = get_logger(__name__)

NOTEBOOK_NAME = "01_load_power_demand"
VOLUME_PATH = "/Volumes/nem_intel/bronze/raw_landing/backfill"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ensure run_log table exists
# MAGIC
# MAGIC Created once here since this is the first pipeline notebook to run.
# MAGIC Every later pipeline notebook can assume it already exists.

# COMMAND ----------

spark.sql("""
    CREATE TABLE IF NOT EXISTS nem_intel.gold.run_log (
        notebook_name STRING,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        rows_in BIGINT,
        rows_out BIGINT,
        status STRING
    )
    COMMENT 'One row per pipeline notebook run — what ran, how many rows in/out, success or failure.'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load and write

# COMMAND ----------

start_time = datetime.now(timezone.utc)
status = "failed"  # only flipped to "success" if everything below completes
rows_in = 0
rows_out = 0

try:
    power_df = load_csvs(spark, f"{VOLUME_PATH}/nem_power_region_fueltech_*.csv", POWER_SCHEMA)
    power_count = power_df.count()
    logger.info("read %d rows from power CSVs", power_count)
    rows_in += power_count

    power_df.write.mode("overwrite").format("delta").saveAsTable(
        "nem_intel.bronze.region_power_fueltech_hourly"
    )
    logger.info("wrote %d rows to nem_intel.bronze.region_power_fueltech_hourly", power_count)
    rows_out += power_count

    demand_df = load_csvs(spark, f"{VOLUME_PATH}/nem_demand_region_*.csv", DEMAND_SCHEMA)
    demand_count = demand_df.count()
    logger.info("read %d rows from demand CSVs", demand_count)
    rows_in += demand_count

    demand_df.write.mode("overwrite").format("delta").saveAsTable(
        "nem_intel.bronze.region_demand_hourly"
    )
    logger.info("wrote %d rows to nem_intel.bronze.region_demand_hourly", demand_count)
    rows_out += demand_count

    status = "success"

except Exception:
    logger.exception("bronze load failed")
    raise

finally:
    end_time = datetime.now(timezone.utc)
    run_log_row = build_run_log_row(
        notebook_name=NOTEBOOK_NAME,
        start_time=start_time,
        end_time=end_time,
        rows_in=rows_in,
        rows_out=rows_out,
        status=status,
    )
    spark.createDataFrame([run_log_row]).write.mode("append").saveAsTable("nem_intel.gold.run_log")
    logger.info("run_log entry written: status=%s, rows_in=%d, rows_out=%d", status, rows_in, rows_out)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table comments
# MAGIC
# MAGIC Genie reads these to decide which column answers a question — doc 04
# MAGIC section 8. Not skipping this even at bronze layer.

# COMMAND ----------

spark.sql("""
    COMMENT ON TABLE nem_intel.bronze.region_power_fueltech_hourly IS
    'Hourly generation by NEM region and fuel technology, from Open Electricity. Rooftop solar (solar_rooftop) is a distinct fueltech value here, separate from solar_utility.'
""")
spark.sql("""
    COMMENT ON TABLE nem_intel.bronze.region_demand_hourly IS
    'Hourly operational demand and demand_gross by NEM region, from Open Electricity. demand_gross - demand = rooftop solar suppression effect (see opennem/opennem issue #398 for the formal definition).'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify

# COMMAND ----------

power_table_count = spark.table("nem_intel.bronze.region_power_fueltech_hourly").count()
demand_table_count = spark.table("nem_intel.bronze.region_demand_hourly").count()

assert power_table_count > 0, "power table is empty after write"
assert demand_table_count > 0, "demand table is empty after write"

logger.info(
    "PHASE 1 BRONZE LOAD PASSED: %d power rows, %d demand rows",
    power_table_count, demand_table_count,
)

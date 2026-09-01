# Databricks notebook source
# MAGIC %md
# MAGIC # 00_verify / 01_check_catalog_and_volume
# MAGIC
# MAGIC Phase 0 capability check. Confirms Unity Catalog is usable on Free
# MAGIC Edition: creates the project catalog, the three layer schemas, and a
# MAGIC volume for the land-then-upload ingestion pattern (doc 02 — outbound
# MAGIC network access from notebooks is restricted, so raw files are landed
# MAGIC locally, uploaded to this volume, then read by a bronze notebook).
# MAGIC
# MAGIC **Reads:** nothing
# MAGIC **Writes:** creates `nem_intel` catalog, `bronze`/`silver`/`gold` schemas,
# MAGIC and `nem_intel.bronze.raw_landing` volume. No data written.

# COMMAND ----------

from nem.logging_config import get_logger

logger = get_logger(__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create catalog and schemas

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS nem_intel
# MAGIC COMMENT 'NEM Grid Intelligence Agent — bronze/silver/gold lakehouse for minimum demand analysis';
# MAGIC
# MAGIC CREATE SCHEMA IF NOT EXISTS nem_intel.bronze COMMENT 'Raw landed data, minimal transformation';
# MAGIC CREATE SCHEMA IF NOT EXISTS nem_intel.silver COMMENT 'Cleaned, typed, geometry-validated data';
# MAGIC CREATE SCHEMA IF NOT EXISTS nem_intel.gold COMMENT 'Certified metrics and serving tables';

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create landing volume

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS nem_intel.bronze.raw_landing
# MAGIC COMMENT 'Land-then-upload target for locally fetched source files (Open Electricity API, CER CSVs, etc.)';

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify

# COMMAND ----------

catalogs = [r["catalog"] for r in spark.sql("SHOW CATALOGS").collect()]
assert "nem_intel" in catalogs, "nem_intel catalog not found after creation"
logger.info("catalog check passed: nem_intel exists")

schemas = [r["databaseName"] for r in spark.sql("SHOW SCHEMAS IN nem_intel").collect()]
for expected in ["bronze", "silver", "gold"]:
    assert expected in schemas, f"schema {expected} not found in nem_intel"
logger.info("schema check passed: %s", schemas)

volumes = [r["volume_name"] for r in spark.sql("SHOW VOLUMES IN nem_intel.bronze").collect()]
assert "raw_landing" in volumes, "raw_landing volume not found in nem_intel.bronze"
logger.info("volume check passed: nem_intel.bronze.raw_landing exists")

logger.info("PHASE 0 CHECK PASSED: catalog, schemas, and landing volume all confirmed")

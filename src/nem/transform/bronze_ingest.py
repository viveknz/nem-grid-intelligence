"""Bronze layer loading — reads raw CSVs landed in the UC volume and
returns a typed DataFrame ready to write as Delta.

Kept deliberately close to raw: explicit schema, minimal transformation
(just adding source-file lineage). Real cleaning, validation, and typing
(e.g. interval string -> timestamp) happens in silver (Phase 2) — bronze's
job is an honest, typed copy of what was actually landed, per doc 04's
bronze/silver/gold split.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

# interval stays StringType here deliberately — it's ISO8601 with a UTC
# offset (e.g. "2015-01-01T00:00:00+10:00") as written by the ingest
# script. Casting to TimestampType is a silver concern, not bronze's.
POWER_SCHEMA = StructType([
    StructField("interval", StringType(), False),
    StructField("network_region", StringType(), False),
    StructField("fueltech", StringType(), False),
    StructField("power", DoubleType(), True),
])

DEMAND_SCHEMA = StructType([
    StructField("interval", StringType(), False),
    StructField("network_region", StringType(), False),
    StructField("demand", DoubleType(), True),
    StructField("demand_gross", DoubleType(), True),
])


def load_csvs(spark: SparkSession, path_glob: str, schema: StructType) -> DataFrame:
    """Read all CSVs matching path_glob into one DataFrame.

    Uses an explicit schema rather than inferSchema — inference is slow
    and unreliable across hundreds of files landed at different times,
    and an explicit schema fails loudly if a file's shape ever drifts
    rather than silently guessing wrong. Adds _source_file for lineage,
    via the _metadata.file_path hidden column rather than the legacy
    input_file_name() function — Unity Catalog governed reads reject
    input_file_name() outright (UC_COMMAND_NOT_SUPPORTED), confirmed
    live. _metadata.file_path is the current, UC-safe equivalent.
    """
    return (
        spark.read
        .option("header", True)
        .schema(schema)
        .csv(path_glob)
        .withColumn("_source_file", col("_metadata.file_path"))
    )

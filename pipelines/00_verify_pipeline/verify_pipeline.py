# Phase 0 capability check: confirms Lakeflow Declarative Pipelines runs on
# Free Edition, and that expectations (data quality gates) are enforced.
#
# This is a throwaway verification pipeline, not part of the real medallion
# build. Delete the pipeline (Workflows > Pipelines) once confirmed — Free
# Edition allows only one active pipeline per pipeline type, and the real
# silver-to-gold pipeline in Phase 3 needs that slot.
#
# Target: nem_intel.bronze (set via pipeline settings, not in this file)

from pyspark import pipelines as sdp


@sdp.materialized_view(
    name="phase0_pipeline_check",
    comment="Phase 0 capability check row set. Safe to drop after verification.",
)
@sdp.expect("check_id_not_null", "check_id IS NOT NULL")
def phase0_pipeline_check():
    return spark.range(5).withColumnRenamed("id", "check_id")

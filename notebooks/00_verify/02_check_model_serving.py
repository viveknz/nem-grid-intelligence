# Databricks notebook source
# MAGIC %md
# MAGIC # 00_verify / 02_check_model_serving
# MAGIC
# MAGIC Phase 0 capability check. Free Edition docs state limits exist on model
# MAGIC serving (no GPU endpoints, no provisioned throughput, "certain models
# MAGIC not available") but don't say which pay-per-token models actually work
# MAGIC on this account. This notebook discovers and tests live rather than
# MAGIC assuming.
# MAGIC
# MAGIC Resolves open decision #3 (doc 00): which foundation model endpoint is
# MAGIC available and what its quota is.
# MAGIC
# MAGIC **Reads:** nothing
# MAGIC **Writes:** nothing. Read-only capability probe.

# COMMAND ----------

import os
import sys

_src_path = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "src"))
if _src_path not in sys.path:
    sys.path.append(_src_path)

from nem.logging_config import get_logger

logger = get_logger(__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC ## List available serving endpoints
# MAGIC
# MAGIC Databricks auto-provisions pay-per-token Foundation Model API endpoints
# MAGIC per workspace, prefixed `databricks-`. This lists whatever actually
# MAGIC exists on this account rather than assuming a specific model name.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
all_endpoints = list(w.serving_endpoints.list())

logger.info("total serving endpoints found: %d", len(all_endpoints))
for e in all_endpoints:
    logger.info("endpoint: %s | state: %s", e.name, e.state)

foundation_endpoints = [e for e in all_endpoints if e.name.startswith("databricks-")]

assert foundation_endpoints, (
    "no databricks- prefixed (Foundation Model API) endpoints found. "
    "Either none are provisioned on this account, or the naming convention "
    "has changed — check Serving tab in the workspace UI manually."
)
logger.info("foundation model endpoints: %s", [e.name for e in foundation_endpoints])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query one endpoint with a trivial request
# MAGIC
# MAGIC Confirms the endpoint isn't just listed but actually responds, and
# MAGIC surfaces real token usage and quota errors rather than assumed ones.

# COMMAND ----------

import requests

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
host = ctx.apiUrl().get()
token = ctx.apiToken().get()

target_endpoint = foundation_endpoints[0].name
logger.info("testing endpoint: %s", target_endpoint)

url = f"{host}/serving-endpoints/{target_endpoint}/invocations"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {
    "messages": [{"role": "user", "content": "Reply with exactly one word: OK"}],
    "max_tokens": 10,
}

response = requests.post(url, headers=headers, json=payload, timeout=30)

logger.info("HTTP status: %d", response.status_code)

if response.status_code == 429:
    logger.warning("rate limited (429) — quota is real and tight enough to hit on a single test call")
    logger.warning("response body: %s", response.text)
elif response.status_code != 200:
    logger.error("unexpected status %d: %s", response.status_code, response.text)
else:
    body = response.json()
    logger.info("response body: %s", body)
    usage = body.get("usage", {})
    logger.info("token usage — prompt: %s, completion: %s, total: %s",
                usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens"))

response.raise_for_status()
logger.info("PHASE 0 CHECK PASSED: %s responded successfully", target_endpoint)

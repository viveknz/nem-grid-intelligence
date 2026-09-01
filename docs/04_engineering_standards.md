# 04 Engineering Standards

**Project:** NEM Grid Intelligence Agent
**Status:** Active. This document is binding on all code in the repo.
**Last updated:** 2026-09-01

---

## 1. Repository

**Proposed name:** `nem-grid-intelligence`

Public. A private repo cannot be read by someone assessing your work, which defeats
the purpose.

### Layout

```
nem-grid-intelligence/
├── README.md
├── CLAUDE.md                  # conventions, for later autonomous work
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── docs/
│   ├── 00_project_brief.md
│   ├── 01_platform_constraints.md
│   ├── 02_data_sources.md
│   ├── 03_data_model.md
│   ├── 04_engineering_standards.md
│   ├── 05_spatial_curriculum.md
│   ├── 06_agent_architecture.md
│   └── 07_build_log.md
├── src/
│   └── nem/
│       ├── __init__.py
│       ├── logging_config.py
│       ├── ingest/
│       ├── transform/
│       ├── spatial/
│       └── agent/
├── notebooks/
│   ├── 00_verify/
│   ├── 01_bronze/
│   ├── 02_silver/
│   ├── 03_spatial/
│   └── 04_gold/
├── pipelines/                 # Lakeflow Declarative Pipeline definitions
├── genie/                     # instructions, trusted queries, question bank
├── app/                       # Streamlit app, deployed by Databricks Apps
│   ├── app.yaml
│   ├── app.py
│   └── requirements.txt
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

Two things about this layout are deliberate.

`app/` sits at the repo root with its own `app.yaml` and `requirements.txt`, because
Databricks Apps expects `app.yaml` at the root of whatever source path you give it.
Point the app at `app`, not at the repo root, or it tries to serve the notebooks too.

`src/nem/` holds the real logic. Notebooks are thin. Section 4 explains why.

## 2. Git workflow

The repo is the source of truth. Databricks pulls from it. Never edit a notebook in
the Databricks UI and call that the current version.

### Loop

```bash
# 1. work locally, files arrive from Claude into the repo
git add <files>
git commit -m "phase 3: add H3 polygon coverage for postcode boundaries"
git push origin main

# 2. in Databricks: Workspace > your Git folder > Pull
```

### Setup, once

```bash
git clone git@github.com:viveknz/nem-grid-intelligence.git
cd nem-grid-intelligence
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

SSH is already configured for the `viveknz` account from the previous project. If
Databricks asks for credentials when creating the Git folder, use the PAT rather than
the SSH key, since the workspace connects over HTTPS.

### Commit messages

`<phase>: <what changed>`. Present tense, lower case, no trailing full stop.

Good: `phase 2: validate postcode geometry and drop invalid rings`
Bad: `Updated files`

Commit at the end of every working section, not in one lump at the end of a phase. The
commit history is part of what a reviewer reads.

### Branching

Work on `main`. This is a solo project and branch ceremony would be theatre. The one
exception: if a phase involves an experiment that might be abandoned, branch it, and
either merge or delete rather than leaving it open.

## 3. Notebook format

Notebooks are committed as Databricks source `.py` files. Never `.ipynb`, which carries
output cells that can contain data and make diffs unreadable.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # 03_spatial / 01_postcode_h3
# MAGIC
# MAGIC Converts postcode polygons to H3 cells at resolution 7.
# MAGIC
# MAGIC **Reads:** `nem_intel.silver.postcode_boundary`
# MAGIC **Writes:** `nem_intel.silver.postcode_h3`

# COMMAND ----------

from nem.logging_config import get_logger
from nem.spatial.h3_index import polygons_to_h3

logger = get_logger(__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load
```

Every notebook header states what it reads and what it writes. That header is what
makes the repo navigable to someone who did not build it.

## 4. Where logic lives

**Notebooks orchestrate. Modules compute.**

A notebook should read a table, call a function, write a table, and log. The
transformation itself lives in `src/nem/` as a plain Python function that takes a
DataFrame and returns a DataFrame.

The reason is testability. You cannot run a notebook under pytest, but you can import a
function and assert on its output. If the logic is inside the notebook, it is untested
by construction.

```python
# src/nem/spatial/h3_index.py
def polygons_to_h3(df: DataFrame, geom_col: str, resolution: int) -> DataFrame:
    """Explode polygon geometry into covering H3 cells at the given resolution."""
    ...
```

```python
# in the notebook
result = polygons_to_h3(spark.table("nem_intel.silver.postcode_boundary"), "geometry", 7)
```

This is the single most important convention in this document. It is also the habit
that most distinguishes a data engineer from someone who writes notebooks.

## 5. Error logging

One logging configuration, imported everywhere.

```python
# src/nem/logging_config.py
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
```

Rules:

- Never use `print`
- Log row counts before and after every write, so a silent data loss shows up in the log
- Catch exceptions at the notebook level, log with `logger.exception`, then re raise.
  Swallowing an exception to let a job "succeed" is worse than failing.
- Log the table name and record count on every write:
  `logger.info("wrote %s rows to %s", df.count(), table_name)`

### Run log table

Every pipeline notebook writes one row to `nem_intel.gold.run_log`: notebook name,
start time, end time, rows in, rows out, status. This is cheap and it makes the
article's "how do you know it worked" section easy to write.

## 6. Testing

### Unit tests

`tests/unit/` tests functions in `src/nem/` against small in memory DataFrames. No
cluster, no real data, fast enough to run on every commit.

```python
def test_polygons_to_h3_covers_full_polygon(spark):
    df = spark.createDataFrame([("2000", SQUARE_WKT)], ["postcode", "geometry"])
    result = polygons_to_h3(df, "geometry", 7)
    assert result.count() > 0
    assert result.select("h3_cell").distinct().count() == result.count()
```

### Integration tests

`tests/integration/` runs against real tables in the workspace. Slower, run manually at
the end of a phase, marked so unit runs skip them.

```python
@pytest.mark.integration
def test_gold_demand_has_no_null_regions():
    ...
```

### Spatial tests specifically

Spatial bugs are quiet. A bad projection does not raise an error, it just gives you
wrong areas. So spatial functions get property based assertions rather than only
example based ones:

- Interpolated values must sum to the source total, within tolerance
- Every H3 cell produced must fall inside or on the boundary of its source polygon
- Converting a polygon to H3 and back must not lose more than an agreed percentage of area

These three checks catch most of what goes wrong in areal interpolation.

### Gate

```bash
pytest tests/unit -v                    # every commit
pytest tests/integration -v -m integration   # end of phase
```

A phase is not finished until the relevant tests pass. Not "mostly pass".

## 7. Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Catalog | lower snake | `nem_intel` |
| Schema | layer name | `bronze`, `silver`, `gold` |
| Table | `<grain>_<subject>` | `region_demand_5min` |
| Column | lower snake, unit suffixed | `demand_mw`, `area_km2` |
| Notebook | `NN_verb_noun` | `01_load_demand` |
| Python module | lower snake | `h3_index.py` |

Units go in the column name. `demand` is ambiguous. `demand_mw` is not, and it stops
Genie guessing.

## 8. Documentation as you go

Every gold table gets a `COMMENT`. Every gold column gets a `COMMENT`. This is not
housekeeping, it is what Genie reads to decide which column answers a question, so
skipping it degrades the product directly.

`07_build_log.md` gets an entry at the end of each working section: what was done, what
broke, what was decided. Written at the time, not reconstructed later.

## 9. Later: autonomous building

Not in use yet. Recorded so the option stays open.

When Vivek is ready, `CLAUDE.md` at the repo root carries these conventions and Claude
Code works against the repo directly, with `pytest tests/unit` as the gate before any
commit. That mode is cheaper in context than this chat because it reads only the files
it needs. It does not start until Vivek says so.

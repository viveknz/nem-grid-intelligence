# NEM Grid Intelligence Agent

Agentic analytics application over Australian National Electricity Market data.
A user asks a question in plain English; an agent decides which tools to call,
runs SQL and spatial queries against a governed lakehouse, and returns an answer
with the working shown.

**Status:** Design complete, build starting. See `docs/07_build_log.md` for the
running record and `docs/00_project_brief.md` for scope.

## The question this answers

> Where is rooftop solar suppressing daytime demand hard enough to create a
> minimum demand problem, and what weather conditions make it worse?

## Stack

Databricks Free Edition. Unity Catalog, Delta Lake, Lakeflow Declarative
Pipelines, Workflows, AI/BI Genie, Databricks Apps (Streamlit), foundation
model serving, MLflow.

## Data attribution

- Open Electricity API — CC BY-NC 4.0. Non-commercial use only.
- Clean Energy Regulator small-scale installation data — Australian Government
  open data.
- Further sources listed in `docs/02_data_sources.md`, with licence status.

## Repo layout

See `docs/04_engineering_standards.md` section 1 for the full layout and the
reasoning behind it.

## Local setup

```bash
git clone git@github.com:viveknz/nem-grid-intelligence.git
cd nem-grid-intelligence
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Testing

```bash
pytest tests/unit -v                          # every commit
pytest tests/integration -v -m integration     # end of phase
```

A phase is not finished until its tests pass.

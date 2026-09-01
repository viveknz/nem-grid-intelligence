# 00 Project Brief

**Project:** NEM Grid Intelligence Agent
**Owner:** Vivek Kumar
**Platform:** Databricks Free Edition
**Status:** Design. No code written yet.
**Last updated:** 2026-09-01

---

## 1. What this is

An agentic analytics application over Australian National Electricity Market data.
A user asks a question in plain English. An agent decides which tools to call, runs
SQL and spatial queries against a governed lakehouse, and returns an answer with the
working shown.

This is deliberately not a dashboard with a chat box stapled on. The distinction
matters for the portfolio outcome described in section 3.

## 2. The problem it addresses

Distributors and market participants hold demand, generation and weather data in
separate systems at different grains. Demand arrives by NEM region every five
minutes. Weather arrives by station. Rooftop solar arrives by postcode. Nobody can
answer a question that crosses all three without a data engineer writing bespoke SQL,
so the questions mostly go unasked.

The specific question this project makes answerable:

> Where is rooftop solar suppressing daytime demand hard enough to create a minimum
> demand problem, and what weather conditions make it worse?

Minimum demand is a genuine operational headache for Australian distributors. When
daytime grid demand falls too low, voltage management and system security both get
harder. It is the inverse of the peak demand problem everyone already understands,
which makes it a good story: it is real, it is current, and it is not the obvious
answer someone would reach for.

## 3. Why this project, and what it has to prove

Two goals running at once.

**Portfolio.** A hiring manager looking for Databricks skills should be able to open
the repo and see governed data, tested transformations, a semantic layer, and an agent
with an evaluation harness. The bar is that the repo is defensible in an interview,
which means the author can explain every design decision in it.

**Skill acquisition.** Three specific gaps this build is meant to close:

| Gap | How this project closes it |
|-----|---------------------------|
| Spatial analytics | Areal interpolation, H3 indexing, point interpolation, geometry validity. Section 5. |
| Python in a production shape | Every transform is tested. Nothing ships without a pytest run passing. |
| Agentic systems | Tool definitions, orchestration, and an eval set that scores agent answers. |

Spatial is the priority. It is the least transferable by reading someone else's code
and the most valuable in a utility context.

## 4. Scope

### In scope

- Bronze, silver and gold Delta tables in Unity Catalog
- Lakeflow Declarative Pipelines for silver to gold
- A scheduled Workflow
- H3 spatial layer joining postcode-grain solar to region-grain demand
- Genie space with certified metrics and curated instructions
- A Databricks dashboard
- A Databricks App (Streamlit) as the front end
- An agent with defined tools, running on Databricks foundation model serving
- An evaluation harness that scores agent answers against a fixed question set
- A written article and a recorded walkthrough

### Out of scope

- Anything touching AusNet internal data. All sources are public and openly licensed.
- Extending or modifying the existing `vic-powerline-bushfire-genie` project. That app
  is finished and stays as it is.
- Real-time streaming. Batch only, on a schedule.
- Any paid API. The build and the running app both cost nothing.

### Explicitly deferred

- Forecasting. A demand forecast is an obvious extension and a good phase 8, but it is
  not needed to prove the architecture and it invites scope creep. Revisit after the
  agent works.

## 5. The spatial layer

This is the section to get right, because it is where the learning is.

Demand and generation data has no geometry. It arrives by NEM region, of which there
are five. Joining five polygons to anything is not spatial analytics, it is a lookup
table. So the spatial content has to come from data that is genuinely fine grained.

**Recommended primary spatial source: distributed solar by postcode.**

Postcode boundaries are irregular polygons that do not nest inside NEM regions. Moving
a value from postcode grain to region grain therefore requires areal interpolation,
weighted by something sensible rather than by raw polygon area. This is the technique
most people get wrong and it is worth doing properly.

Techniques this forces you to learn:

1. Reading and validating polygon geometry, including self intersections and invalid rings
2. Coordinate reference systems, and why area calculations in EPSG:4326 are wrong
3. Polygon to H3 conversion, and the difference between covering and containment
4. Areal interpolation, including dasymetric weighting by population or dwelling count
5. Aggregating H3 cells upward through resolutions without double counting

**Recommended secondary spatial source: weather station points.**

Weather arrives at irregularly spaced station points. Turning that into a value per H3
cell requires interpolation across a surface, which is a different problem to polygon
reallocation and teaches nearest neighbour search and inverse distance weighting.

**Open question for doc 03:** which H3 resolution. Postcodes in inner Melbourne are
small and postcodes in western Victoria are enormous, so a single resolution will
either be too coarse for the city or generate an unusable cell count for the country.
This needs a decision, and the decision needs a reason written down.

## 6. Databricks surface to be exercised

The project is partly a demonstration of platform coverage, so the surface area is
deliberate rather than incidental.

| Capability | Where it is used |
|-----------|-----------------|
| Unity Catalog | Catalog, schemas, table comments, tags, lineage |
| Delta Lake | All tables, with time travel demonstrated in the article |
| Lakeflow Declarative Pipelines | Silver to gold, with expectations as data quality gates |
| Workflows | Scheduled daily refresh |
| SQL warehouse | Serving layer for dashboard and Genie |
| AI/BI Genie | Semantic layer with certified metrics and trusted queries |
| Dashboards | Executive view |
| Databricks Apps | Streamlit front end |
| Model serving | Foundation model endpoint backing the agent |
| MLflow | Agent tracing and evaluation runs |

Confirmed unavailable on Free Edition and therefore not part of the design: Agent
Bricks, Lakebase database instances, R and Scala, custom compute. Confirmed constrained:
outbound network access is limited to a set of trusted domains, so ingestion is batch
file landing rather than direct API calls from a notebook. Doc 01 covers this properly.

## 7. Definition of done

The project is finished when all of the following are true.

1. A clean clone of the repo, run against an empty catalog, produces every gold table
2. `pytest` passes with no skips
3. The Genie space answers all questions in the question bank correctly
4. The agent scores above an agreed threshold on the eval set
5. The app is deployed and reachable
6. Every table and column in gold has a comment
7. The article is published and the walkthrough recorded
8. Vivek can explain, without notes, why every spatial design decision was made

Point 8 is not decoration. It is the difference between this being a portfolio piece
and being a repo with someone else's fingerprints on it.

## 8. Phases

Detail lives in the build log. High level shape, following the pattern that worked on
the previous project:

- **Phase 0** Capability verification. Prove each Databricks feature works on Free
  Edition before designing around it.
- **Phase 1** Ingestion to bronze. One notebook per source.
- **Phase 2** Silver. Cleaning, typing, geometry validation.
- **Phase 3** Spatial. H3 indexing and areal interpolation. The hard phase.
- **Phase 4** Gold and semantic layer.
- **Phase 5** Genie space, instructions, trusted queries, question bank.
- **Phase 6** Agent. Tools, orchestration, eval harness.
- **Phase 7** App and dashboard.
- **Phase 8** Write-up, walkthrough, publication.

Each phase ends with a test that runs and a short explain-back on the spatial content.

## 9. Working agreement

- Git first. The repo is the source of truth and Databricks pulls from it.
- No code pasted into chat. Everything arrives as a file.
- One step at a time. A step is not finished until its test passes.
- Design and review happen in the Claude chat. Autonomous building happens in Claude
  Code against the repo, where the context cost is lower.
- Autonomy increases when Vivek says so, not before.

## 10. Open decisions

Carried into the next documents rather than guessed at here.

| # | Decision | Resolved in |
|---|----------|------------|
| 1 | Confirm solar-by-postcode data is available under an open licence at usable granularity | 02 |
| 2 | H3 resolution, and whether to use more than one | 03 |
| 3 | Weighting variable for areal interpolation | 03 |
| 4 | Which foundation model endpoint is available and what its quota is | 01 |
| 5 | Repo name | 04 |

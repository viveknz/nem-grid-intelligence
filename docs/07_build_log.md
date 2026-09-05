# 07 Build Log

**Project:** NEM Grid Intelligence Agent
**Started:** not yet
**Last updated:** 2026-09-01

Running record of what was built, what broke, and what was decided. Written at the time,
not reconstructed afterwards. One entry per working session.

The purpose is not neatness. Three things depend on this file:

- The article at the end is written from it
- Decisions get revisited months later and the reason needs to survive
- A reviewer reading the repo can see how the thing was actually built, including the
  dead ends, which is more convincing than a clean narrative

Record failures. A log with no problems in it reads as fiction.

---

## Entry template

Copy this block for each session.

```
## YYYY-MM-DD | Phase N | <short title>

**Goal**
What this session set out to do.

**Done**
What was actually completed. Notebooks, tables, tests.

**Broke**
What failed and how it was fixed. Include the error text if it was non-obvious.

**Decided**
Design decisions made, and the alternative that was rejected.

**Learned**
Especially spatial. What was not understood before this session that is now.

**Next**
The single next step. Not a plan, one step.

**Commits**
`abc1234` short message
```

---

## Open decisions

Moved here from the brief. Struck through when resolved, with the answer and the date.

| # | Decision | Raised | Status |
|---|----------|--------|--------|
| 1 | H3 resolution, and whether to use more than one | Doc 00 | Open |
| 2 | Weighting variable for areal interpolation | Doc 00 | Open |
| 3 | Which foundation model endpoint is available and its quota | Doc 00 | Open |
| 4 | Weather source: Open-Meteo or BOM fallback | Doc 02 | Open |
| 5 | ABS ASGS edition, and handling postcodes that changed between editions | Doc 02 | Open |
| 6 | Open Electricity API rate limits on a free key | Doc 02 | Open |
| 7 | Repo name confirmed as `nem-grid-intelligence` | Doc 04 | Open |

---

## Known limits

Things that are wrong or incomplete by design, carried into the article rather than
hidden. Started with the ones already known.

- **CER certificate lag.** Installation counts for recent months undercount, because
  certificate approval trails installation by up to twelve months. Any trend on the most
  recent year will show a false decline. Must be stated in Genie instructions.
- **Open Electricity licence.** CC BY-NC 4.0. Attribution required, non-commercial only.
- **Open Electricity Pro tier cost.** Currently free, granted after a direct request,
  but Open Electricity has indicated it's expected to become a paid tier with further
  contact to follow. Conflicts with the project's stated "no paid APIs" constraint if
  it happens. Fallback is the Community plan's 2-year window, which still covers the
  project's core framing question. Watch for contact from Open Electricity about this.

---

## Sessions

## 2026-09-01 | Phase 0 | Repo bootstrap

**Goal**
Create the GitHub repo, lay out the directory structure from doc 04 section 1,
get the four existing docs into `docs/`, and confirm Databricks can pull it.

**Done**
- Created `nem-grid-intelligence` on GitHub, public
- Built the full directory skeleton: `docs/`, `src/nem/` with `ingest/`,
  `transform/`, `spatial/`, `agent/` and `__init__.py` in each; `notebooks/`
  with `00_verify` through `04_gold`; `pipelines/`, `genie/`, `app/`; `tests/`
  with `unit/`, `integration/`, and a placeholder `conftest.py`
- Copied `00_project_brief.md`, `02_data_sources.md`,
  `04_engineering_standards.md`, `07_build_log.md` into `docs/`
- Added `requirements.txt` (empty, Phase 0) and `requirements-dev.txt`
  (pytest, pytest-mock)
- Added `.gitattributes` pinning LF line endings for `.sh`, `.py`, `.sql`,
  `.md`, `.yaml`, `.json`
- Added `.gitignore`, including the local `sync.sh` helper
- Connected the Databricks Git folder to the repo and pulled — `docs/` and
  `src/` confirmed visible in the workspace

**Broke**
- First attempt at the directory skeleton was skipped entirely — went
  straight to committing the loose files (`README.md`, `sync.sh`,
  `.gitattributes`, `.gitignore`) without ever creating `docs/` or `src/`
  locally. Databricks pull correctly showed nothing, because there was
  nothing to pull. Fixed by generating the full skeleton plus docs as one
  bundle and re-running.
- GitHub flagged an LF/CRLF mismatch warning on push, before `.gitattributes`
  existed. Not yet destructive at that point, but `sync.sh` itself is a bash
  script, so a CRLF checkout on Windows would have broken its shebang. Fixed
  by adding `.gitattributes` with `eol=lf` pinned per file type, then
  `git add --renormalize .`
- `sync.sh` was committed into the repo before `.gitignore` was updated to
  exclude it. Adding the line to `.gitignore` alone didn't remove it, since
  `.gitignore` only stops *untracked* files from being added — a file
  already tracked stays tracked until explicitly untracked. Fixed with
  `git rm --cached sync.sh`.

**Decided**
- `sync.sh` stays out of the repo entirely (local helper, not a deliverable)
  rather than committing it as a documented dev tool. Rejected alternative:
  commit it under a `scripts/` folder so it travels with the repo — rejected
  because it's Windows/Git-Bash-specific glue for this one workflow, not
  something a reviewer needs to see to assess the project.
- Line endings pinned via `.gitattributes` at the repo level rather than
  relying on each contributor's local `core.autocrlf`. Rejected alternative:
  tell Vivek to set `autocrlf` locally — rejected because it doesn't travel
  with the repo and would silently break again for anyone else who clones it.

**Learned**
- `.gitignore` only governs untracked files. Once git already knows about a
  file, ignoring it later is a no-op until it's untracked with
  `git rm --cached`.
- CRLF conversion isn't just cosmetic — it can break a script's shebang line
  outright, so any executable text file crossing Windows needs `eol=lf`
  pinned, not left to default config.

**Next**
Phase 0 capability verification — confirm each Databricks feature the project
depends on (Unity Catalog, SQL warehouse, model serving endpoint, Genie,
Lakeflow) actually works on Free Edition before designing around it.

**Commits**
Fill in from `git log --oneline` on your machine — hashes weren't visible to
me from chat. Should be roughly, in order:
`____` phase 0: bootstrap repo structure and docs
`____` phase 0: pin line endings with gitattributes
`____` phase 0: ignore local sync script

## 2026-09-01 | Phase 0 | Model serving verification

**Goal**
Resolve open decision #3 — confirm whether a foundation model serving
endpoint is actually available on this Free Edition account, and what its
quota looks like. Also settled whether prior work (the bushfire Genie
project) already proves other Phase 0 capabilities.

**Done**
- Confirmed with Vivek that the bushfire project already built and ran a
  Genie space and a Databricks App on this same Free Edition account — those
  two capabilities don't need re-verification here. Certified metrics within
  Genie were not exercised there, so that stays open for Phase 5.
- Researched current Free Edition model serving limits (docs, not memory):
  limits on active endpoint count, no GPU endpoints, no provisioned
  throughput, no custom models on GPU/batch inference — but the docs don't
  say which pay-per-token models are actually present on this account.
- Wrote and ran `notebooks/00_verify/02_check_model_serving.py`: lists all
  serving endpoints via the Databricks SDK, filters to `databricks-`
  prefixed (Foundation Model API) ones, sends a live test request to one.
- 11 ready endpoints found: `gpt-oss-120b`, `gpt-oss-20b`,
  `qwen3-next-80b-a3b-instruct`, `qwen35-122b-a10b`, `llama-4-maverick`,
  `gemma-3-12b`, `meta-llama-3-1-8b-instruct`, `meta-llama-3-3-70b-instruct`,
  plus three embedding-only endpoints (`gte-large-en`, `bge-large-en`,
  `qwen3-embedding-0-6b`).
- Test call to `databricks-gpt-oss-120b` returned HTTP 200, no quota issue
  on a single request.

**Broke**
Nothing broke this session — clean run.

**Decided**
- Open decision #3 split into two parts. Part one — does a usable endpoint
  exist at all — resolved yes, capability confirmed. Part two — which
  specific model backs the agent — deferred to Phase 6. Rejected deciding it
  now: a one-line "say OK" probe proves the endpoint responds, it says
  nothing about tool-calling reliability, which is the property that
  actually matters for an agent. Picking a model on chat-only evidence would
  be guessing ahead of the real test.
- Genie space and Databricks App capability checks skipped for this project,
  on the basis that the bushfire project already proved both work on this
  account. Certified metrics specifically were not proven there, so that
  narrower capability stays a genuine open question for Phase 5, not
  assumed covered by the broader "Genie works" result.

**Learned**
`gpt-oss-120b` is a reasoning model — it spends output tokens on an internal
reasoning summary before producing a final answer. A `max_tokens: 10` test
call returned `finish_reason: length` with only a fragment of reasoning
text, no actual answer. Not a Free Edition restriction, just how reasoning
models allocate tokens, but it means any real use of a reasoning-style
endpoint needs a much larger token budget than an instruct model would, or
the response gets cut off before it says anything useful.

**Next**
Move to the next Phase 0 capability check (SQL warehouse / Genie / Apps /
Lakeflow — whichever Vivek picks), or start closing out Phase 0 if enough
has been proven to move into Phase 1 design.

**Commits**
Fill in from `git log --oneline`:
`____` phase 0: add catalog verification notebook and logger
`____` phase 0: fix nem package path in verify notebook
`____` phase 0: add model serving verification notebook

## 2026-09-01 | Phase 0 | Lakeflow Declarative Pipelines verification

**Goal**
Confirm Lakeflow Declarative Pipelines actually runs on this Free Edition
account. Docs were ambiguous: the Free Edition limitations page implies it's
available (lists a quota — one active pipeline per pipeline type), but
separate Azure Databricks docs state pipelines require the Premium plan.

**Done**
- Wrote a throwaway verification pipeline (`pipelines/00_verify_pipeline/`)
  — a materialized view over `spark.range(5)` with a data-quality expectation
  attached, targeting `nem_intel.bronze`.
- Found a pre-existing pipeline on the account, `dbdemos_pipeline_cdc_main_dbdemos_sdp_cdc`,
  left over from an earlier tutorial. Confirmed with Vivek it was safe to
  ignore rather than delete outright, since testing whether pipeline
  creation succeeded or hit a quota error either way answered the real
  question.
- Created the pipeline via Workflows > Pipelines > Create pipeline > ETL
  pipeline. Confirmed: it's offered as a normal option, no Premium-plan
  upgrade gate shown anywhere in the flow.
- Ran it. Result: 5 rows written, expectation "1 met", zero errors, zero
  warnings.

**Broke**
The pipeline editor's quick-create flow scaffolds its own workspace project
folder (`transformations/my_transformation.py`) rather than binding to the
git-tracked source file already pushed to `pipelines/00_verify_pipeline/`.
Worked around it for this throwaway test by pasting the code directly into
the editor's placeholder file. Not acceptable for the real Phase 3 pipeline,
which needs to stay git-sourced per the working agreement — needs a proper
answer (likely: point the pipeline's source code path setting explicitly at
the git folder, rather than accepting the auto-scaffolded project) before
Phase 3.

**Decided**
- Lakeflow Declarative Pipelines is available and works on this account.
  The "requires Premium plan" language in Azure Databricks docs is read as
  referring to Azure workspace-tier licensing, a different product
  structure from the AWS-hosted Free Edition this project runs on — not a
  restriction that applies here. Confirmed by the live test rather than
  taken on faith from either doc source.
- Left both the verify pipeline and the stale demo pipeline in place for
  now rather than cleaning up immediately. Free Edition's one-pipeline-per-
  type quota means this needs resolving before Phase 3 creates the real
  pipeline, but it's not blocking anything today.

**Learned**
Doc sources can disagree even when both are current and official — Azure
Databricks and AWS-hosted Free Edition aren't the same product despite
sharing documentation domains in places. When docs conflict on a Free
Edition–specific question, the Free Edition limitations page is the more
authoritative source, but a live test settles it properly either way.

**Next**
Register for the Open Electricity API key (Phase 1 blocker per doc 02).

**Commits**
`____` phase 0: add lakeflow verification pipeline source

---

## 2026-09-01 | Phase 1 | Open Electricity API registration

**Goal**
Resolve doc 02's open question on Open Electricity rate limits by
registering for a key, and settle whether the Community plan's historical
data window is enough for the project.

**Done**
- Researched current Open Electricity API docs (not from memory — this
  product is in active beta and changes). Confirmed: Community plan gives a
  2-year historical window (recently extended from 1 year per their
  changelog), Academic and Enterprise give full history back to 1999.
  Community/Academic are both non-commercial only; commercial use needs
  Enterprise.
- Checked for a published Academic-access application process. None exists
  publicly — no eligibility criteria, no self-service form. Only path found
  was contacting the team directly (GitHub discussions or Twitter) and
  asking honestly.
- Drafted an honest access-request description: describes the project
  plainly as a personal, non-commercial portfolio build, not institutional
  research, and asks whether Academic tier fits.
- Registered for a Community account at platform.openelectricity.org.au and
  generated an API key.

**Broke**
Nothing broke this session.

**Decided**
- Proceed on the Community plan's 2-year historical window rather than
  chase Academic access further right now. Rejected alternative: delay
  Phase 1 pending an Academic access reply with no published timeline.
  The framing question (current minimum demand, not long historical trend)
  doesn't obviously need more than 2 years, so this isn't assumed to be a
  real constraint yet — worth revisiting only if Phase 2/3 analysis
  specifically needs longer history.
- The 2-year window, once confirmed as the final answer, becomes a stated
  limitation in doc 02 and the article, the same way the CER certificate lag
  is handled — documented rather than engineered around.

**Learned**
Community's historical window was 1 year until recently and was extended to
2 years — Open Electricity is actively changing its access model, so limits
here should be treated as live facts to re-check periodically, not settled
ones to assume from this conversation later in the project.

**Next**
Build the local ingest script (`src/nem/ingest/`) that reads
`OPENELECTRICITY_API_KEY` from the environment and lands data to
`data/raw/`, per the land-then-upload pattern in doc 02.

**Commits**
No commits this session — registration and research only, no repo changes.


## 2026-09-02 | Phase 1 | Open Electricity ingest script

**Goal**
Build the local ingest script for the Open Electricity API — the first
real data pull for the project, and the first script following the
land-then-upload pattern from doc 02.

**Done**
- Wrote `src/nem/ingest/open_electricity.py`: fetches NEM power data via
  the official SDK, grouped by region and fuel technology, writes dated
  CSV to `data/raw/`.
- Wrote 12 unit tests covering date-range logic, response parsing, and
  CSV writing — all mocked, no network calls, no real API key needed to
  run the suite.
- Registered the OPENELECTRICITY_API_KEY environment variable locally and
  ran the script for real against live data.
- Confirmed final output: all 5 NEM regions present (NSW1, QLD1, SA1,
  TAS1, VIC1), rooftop solar showing as its own category distinct from
  utility-scale solar, ~6,900 rows for a 7-day hourly pull.

**Broke**
Three separate bugs, found and fixed in sequence, each only surfacing once
the previous one was cleared:

1. **Timezone rejection.** The API silently returns 400 with no useful
   error message when sent timezone-aware (UTC) timestamps — it wants naive
   timestamps in NEM local time (fixed AEST, no daylight saving). Traced
   the real cause via a raw curl call bypassing the SDK, since the SDK's
   own error handling swallowed the actual message (it looks for a
   `detail` key on error responses; this endpoint's error text is under
   `error` instead, so the SDK fell back to a generic "Bad Request").
   Fixed by building a `default_date_range()` helper that produces naive
   local-time timestamps via `zoneinfo`.
2. **Missing tzdata on Windows.** `zoneinfo` needs an IANA tzdata source,
   which Linux/macOS ship at the OS level but Windows doesn't. Fixed by
   adding the `tzdata` PyPI package to `requirements.txt`.
3. **Region silently dropped from output.** The SDK's `response.to_records()`
   convenience method only reads `result.columns`, which is documented to
   populate only the *secondary* grouping — whatever was requested as
   `primary_grouping` (network_region, in our case) is left as `None` in
   that structure. The region is still returned by the API, just encoded
   in `result.name` (format: `power_NSW1|battery`), which `to_records()`
   never reads. Confirmed via a one-off diagnostic script that printed the
   raw response shape. Fixed by parsing `result.name` directly instead of
   calling `to_records()`.

A fourth issue, not a bug exactly: the initial query used
`secondary_grouping="fueltech_group"`, which merges rooftop and
utility-scale solar into a single `solar` category — the opposite of what
doc 00 assumed. Switched to the finer-grained `secondary_grouping="fueltech"`,
confirmed via `UnitFueltechType` inspection that `solar_rooftop`,
`solar_utility`, and `solar_thermal` exist as separate values at that level.

**Decided**
- Parse `result.name` directly rather than depend on `response.to_records()`
  for anything involving primary_grouping. Rejected alternative: request
  data without a primary grouping and do the region split ourselves
  client-side — rejected because the server-side grouping is doing real
  work (organizing results into per-region series) that would otherwise
  need reimplementing.
- Use `fueltech` (granular) instead of `fueltech_group` (simplified) as
  the standard secondary grouping for this project, since the rooftop vs.
  utility-scale distinction is central to the framing question. This
  should be treated as the project's default going forward, not a
  one-off choice for this script.

**Learned**
- Official SDKs can have real gaps even in officially documented,
  actively maintained libraries — this one silently drops a whole
  dimension of the data it was asked for. Worth verifying against raw API
  responses rather than trusting a convenience method's output blindly,
  especially when a value that was explicitly requested doesn't show up
  in the result.
- "Simplified" vs "granular" grouping options aren't just cosmetic —
  fueltech_group's solar bucket would have made the entire minimum-demand
  analysis impossible to build, since it erases the one distinction the
  whole project depends on. Grouping choices need checking against actual
  output, not assumed from a parameter name.

**Next**
Decide what date range and metrics the real Phase 1 backfill should pull
(this session used a 7-day test window and power only — the real ingest
needs a defined backfill strategy within the 2-year Community window, and
probably needs `demand` and `energy` metrics alongside `power`).

**Commits**
Fill in from `git log --oneline`:
`____` phase 1: add open electricity ingest script and tests
`____` phase 1: fix naive local-time date range for open electricity api
`____` phase 1: add tzdata dependency for windows zoneinfo support
`____` phase 1: parse region from result.name, sdk to_records() drops it
`____` phase 1: use granular fueltech grouping to separate rooftop and utility solar


## 2026-09-05 | Phase 1 | Open Electricity Pro tier confirmed

**Goal**
Verify what the newly granted Pro tier access actually unlocks, following an email
from Open Electricity confirming an upgrade.

**Done**
- Received confirmation that the account was moved to a Pro tier, in response to the
  honest access request sent earlier (portfolio project, not institutional research).
- Ran a one-off diagnostic query for January 2021 data — 5 years back, well outside
  the Community plan's 2-year window — using the already-tested ingest functions.
  Returned 264 records successfully, confirming full historical access is live.

**Broke**
Nothing broke this session — the diagnostic script itself failed twice before running
cleanly, but both failures were local environment issues, not project bugs: the venv
wasn't active in a fresh terminal (script ran against system Python, which doesn't
have `tzdata` installed), and the API key wasn't re-exported in the new terminal
session (`export` doesn't persist across terminal restarts).

**Decided**
Documented the future paid-tier risk in doc 02 and doc 07's known limits rather than
deciding a fallback plan now. The Community plan's 2-year window remains a workable
fallback if Pro access is ever withdrawn or requires payment, so this isn't urgent —
worth deciding for real only if/when Open Electricity actually gets in touch about
ongoing usage.

**Learned**
`export` in Git Bash only lasts for the current terminal session. Anything needed
across sessions (the API key, in this case) either needs re-exporting each time or
adding to `~/.bashrc` — with the tradeoff that a key in `~/.bashrc` sits in plaintext
on disk permanently rather than only in memory for one session.

**Next**
Decide the backfill date range and metrics (`demand`, `energy` alongside `power`) for
the real Phase 1 historical pull, now that the historical window question is settled.

**Commits**
No commits this session — verification and documentation only.

## 2026-09-05 | Phase 1 | Bronze load — backfill complete

**Goal**
Upload the completed backfill CSVs to the Unity Catalog volume and write the
first bronze notebook to load them into Delta tables, completing Phase 1.

**Done**
- Installed and authenticated the Databricks CLI (`databricks auth login`,
  OAuth browser flow) — two stale profiles needed re-authenticating before
  the CLI would work.
- Uploaded all 270 backfill CSVs to `nem_intel.bronze.raw_landing/backfill`
  via `databricks fs cp -r`. File count confirmed matching on both sides.
- Built `src/nem/transform/bronze_ingest.py` (`load_csvs`, explicit schemas
  for power and demand) and `src/nem/pipeline_utils.py`
  (`build_run_log_row`) — first modules needing real PySpark rather than
  pure Python, so also added a local Spark test fixture
  (`tests/conftest.py`) and `pyspark` to `requirements-dev.txt`.
- Built `notebooks/01_bronze/01_load_power_demand.py`: reads both CSV sets
  from the volume, writes `nem_intel.bronze.region_power_fueltech_hourly`
  and `nem_intel.bronze.region_demand_hourly`, creates and writes to
  `nem_intel.gold.run_log` (first pipeline notebook, so this table didn't
  exist yet), adds table comments.
- Final verified load: 4,546,247 power rows, 513,360 demand rows. Power
  count is an exact match against local file line counts minus header
  rows (4,546,382 total lines − 135 header rows across chunk files) — zero
  data loss between local CSVs and the Delta table.

**Broke**
- Local pytest with the new Spark fixture hung, then crashed, on Windows —
  traced to a `ConnectionRefusedError` after Ctrl+C, meaning the JVM
  process died outright during the glob-multiple-files test. Root cause:
  Windows doesn't ship `winutils.exe`, which some Hadoop/Spark local
  filesystem operations (glob matching among them) need, and without it
  some operations crash the JVM rather than just warning. Decided not to
  chase a fix this session — local pyspark testing isn't required for the
  actual pipeline to run, since Databricks' real Spark is unaffected.
  Logged as a follow-up, not fixed.
- First real run of the bronze notebook failed:
  `UC_COMMAND_NOT_SUPPORTED` — Unity Catalog governed reads reject the
  legacy `input_file_name()` function outright, wanting `_metadata.file_path`
  instead. Fixed in `bronze_ingest.py`, verified correct via local Spark
  tests (still passing on Linux, confirming this was a genuine fix and not
  Windows-specific).
- Second run failed with the *identical* error, despite the fix being
  confirmed present in the pulled file. Cause: Databricks caches imported
  Python modules within a running session — re-running cells after a git
  pull doesn't reload changed `.py` files under `src/` unless the Python
  process is explicitly restarted. Fixed with `%restart_python`, then a
  full top-to-bottom re-run.

**Decided**
- This notebook is backfill-only — writes with `mode("overwrite")`, correct
  for a one-time full historical load, wrong if scheduled against
  incremental data (would silently destroy history each run). Explicitly
  documented as such in the notebook header. Ongoing/incremental ingestion
  will be a separate notebook with append + dedup logic, built later —
  rejected building both now, since the incremental design isn't needed
  until scheduling actually becomes the next concern.
- Local pyspark/Windows testing fix deferred rather than solved — the
  actual goal (bronze data loaded and verified in Databricks) doesn't
  depend on it, and this session was already long.

**Learned**
- Unity Catalog disallows some legacy Spark functions outright rather than
  just deprecating them — `input_file_name()` is a hard error under UC,
  not a warning. `_metadata.file_path` is the current equivalent.
- Databricks notebook sessions cache imported modules like any long-running
  Python process. A git pull updates files on disk; it does not reload
  already-imported modules in an active session. `%restart_python` (or
  detach/reattach) is required to pick up source changes mid-session —
  worth remembering for every future notebook debugging cycle, not just
  this one.
- Windows-specific PySpark issues (winutils.exe, JVM crashes on certain
  local filesystem operations) are a real, recurring category of friction
  for local testing that doesn't show up in Databricks itself. Worth
  planning around (e.g., WSL) rather than re-discovering each time.

**Next**
Phase 1 is complete. Move to Phase 2 (silver: cleaning, typing, geometry
validation) or resolve remaining open decisions (ABS boundary edition,
weather source) first — Vivek's call next session.

**Commits**
Fill in from `git log --oneline`:
`____` phase 1: add bronze loading notebook, run_log convention, spark test fixture
`____` phase 1: use _metadata.file_path for uc-safe lineage tracking
`____` phase 1: mark bronze notebook as backfill-only, not schedulable

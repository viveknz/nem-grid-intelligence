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


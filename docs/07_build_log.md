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

_No entries yet. First entry goes here after Phase 0._

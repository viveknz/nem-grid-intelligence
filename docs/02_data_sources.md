# 02 Data Sources

**Project:** NEM Grid Intelligence Agent (flagship)
**Status:** Sources 1 and 2 verified. Sources 3, 4 and 5 need confirmation before Phase 1.
**Last updated:** 2026-09-01

Scope note: this document covers the flagship only. The EV and solar-home projects get
their own source documents when they start.

---

## Summary

| # | Source | Grain | Licence | Verified |
|---|--------|-------|---------|:--------:|
| 1 | Open Electricity API | NEM region, 5 or 30 min | CC BY-NC 4.0 | Yes |
| 2 | CER small-scale installation postcode data | Postcode, monthly | Australian Government open data | Yes |
| 3 | ABS ASGS Postal Areas boundaries | Postcode polygon | CC BY 4.0 | No |
| 4 | Weather observations | Station point, hourly | TBC | No |
| 5 | ABS Census dwelling counts by POA | Postcode | CC BY 4.0 | No |

---

## 1. Open Electricity API (primary)

**What it gives.** Programmatic access to Australian electricity market data covering
real time generation, demand, price and historical data across the NEM and the Western
Australian market. Generation breaks down by fuel technology group, which includes coal,
gas, wind, hydro, battery and rooftop solar as separate categories.

**Why this matters for the project.** Rooftop solar appears as its own fuel technology,
so you get regional rooftop solar contribution directly from this one source. The public
dashboard shows it running around 13 per cent of the mix on a recent seven day window.
That is the minimum demand signal, available without any spatial work at all. The
postcode layer in source 2 then refines it geographically rather than being the only way
to see it.

**Access.** Requires an API key. Register at the Open Electricity Platform. Official
Python SDK reads the `OPENELECTRICITY_API_KEY` environment variable, so no credentials
go in code.

**Licence.** CC BY-NC 4.0, non-commercial, unless stated otherwise. Attribution is
required. Two consequences: attribution goes in the README, the article, and the app
footer. And this project can never be presented as commercial work or sold. For a
portfolio piece that is not a constraint, but it must be stated rather than discovered
later.

**Ingestion approach.** Free Edition restricts outbound network access from notebooks,
so the API cannot be called from Databricks directly. The pattern is:

1. A local Python script calls the API and writes dated CSV or Parquet to `data/raw/`
2. Files are uploaded to a Unity Catalog volume
3. A bronze notebook reads the volume and writes Delta

That local script lives in `src/nem/ingest/` and is tested like everything else. It also
becomes the thing you point at in an interview when asked how you handle credentials.

**Open question.** Rate limits on a free API key are not documented in what I found.
Needs checking after registration, since it determines how much history you can backfill
and how often the scheduled job can run.

---

## 2. CER small-scale installation postcode data

**What it gives.** The Clean Energy Regulator publishes monthly small-scale renewable
energy installation data files listing small generation units, meaning small-scale solar,
wind and hydro systems, with kW capacity by installed postcode. Solar capacity is
published as a CSV covering 2011 to present, roughly 2.4 MB, with a separate file for
2001 to 2010. Batteries were added from 1 July 2025 when they became eligible under the
scheme, and monthly certificate data by postcode and installation date for batteries
became available in April 2026.

**Scale.** Nearly seven million small-scale installations in total.

**Grain and caveats.** Monthly, by postcode. The data only includes installations whose
certificate applications were approved, so pending applications are missing and recent
months undercount. There is a twelve month certificate creation window, which means
recent figures keep rising after publication. This matters: any trend line on the last
year of data will look like a decline that is not real. It goes in the article's known
limits section and it goes in the Genie instructions so the agent does not report it as
a finding.

**Ingestion.** Direct CSV download, no key. Same land-then-upload pattern as source 1.

**Battery angle.** Battery capacity by postcode from mid 2025 is genuinely new data that
few portfolio projects will have used. Worth including even if it only supports one
question, because it dates the project as current.

---

## 3. ABS ASGS Postal Areas boundaries

**Needed for.** The polygons that make source 2 spatial. Without these, postcode data is
just a code column.

**Status: unverified.** I have not confirmed the current download URL, format, or which
ASGS edition to use. Note that AURIN's historical CER datasets were aggregated to Postal
Areas from the 2016 ASGS, while census data you would use for weighting is 2021. Mixing
editions silently misaligns boundaries.

**Decision required before Phase 3.** Which ASGS edition, and how to handle postcodes
that changed between editions. This is exactly the kind of quiet spatial bug that gives
wrong answers without erroring.

---

## 4. Weather observations

**Needed for.** Correlating temperature with demand, and as the second spatial technique,
interpolating point observations across a surface.

**Status: unverified, and the obvious source is a problem.** BOM does not publish a clean
open bulk historical API. Their observation feeds are shallow and awkward to backfill.

**Recommended alternative to investigate:** Open-Meteo's historical archive. No API key,
free for non-commercial use, hourly history going back decades, queryable by latitude and
longitude. If it holds up, it is a much better fit than BOM for this project. It also
sidesteps the licensing ambiguity around BOM data reuse.

**Fallback:** BOM daily observations for a handful of capital city stations, which is
enough for a demand correlation but too sparse for meaningful interpolation.

This is the biggest open risk in the source list. Resolve it before designing Phase 3.

---

## 5. ABS Census dwelling counts by Postal Area

**Needed for.** Weighting the areal interpolation. Reallocating postcode solar capacity
to H3 cells by raw polygon area assumes solar is spread evenly across the postcode,
including over farmland, parks and water. It is not. Weighting by dwelling count is
dasymetric interpolation and it is the correct approach.

**Status: unverified.** 2021 Census data by POA is published, but the exact table and
download path need confirming.

**Note.** The Australian PV Institute already does something similar, calculating the
percentage of houses with a PV system per postcode and adjusting for dwelling growth
against the 2021 census. Worth reading their method before writing yours, then citing
the difference.

---

## Sources deliberately excluded

**Kaggle energy datasets.** Copilot offered these as an easier option. They are generic,
usually American, and carry no story. Using one would make the project indistinguishable
from a tutorial.

**UK smart meter and OEHU data.** Suggested by Copilot for the smart meter concept. Wrong
country for an Australian audience. The Ausgrid dataset replaces it in the solar-home
project.

**AusNet internal data.** Out of scope permanently.

---

## Next actions

Before Phase 1 can start, three things need resolving:

1. Register for an Open Electricity API key and record the rate limits
2. Confirm the weather source, Open-Meteo or fallback
3. Confirm the ABS boundary edition and the census table for dwelling counts

Item 2 is the one that could change the design.

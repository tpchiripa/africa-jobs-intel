# africa-jobs-intel

**Live dashboard: [africa-jobs-intel.onrender.com](https://africa-jobs-intel.onrender.com)**

African job-market intelligence — extracting skills-demand signals from job postings, starting with South Africa's data/tech job market. What began as manually skimming job adverts for product ideas turned into a validated pipeline covering 9 roles across 6 industries, and a live dashboard showing what employers are actually asking for, with direct links to apply.

## What it does

For each tracked role (Data Analyst, Data Engineer, Data Scientist, Software Engineer, Business Analyst, Accountant, Registered Nurse, Civil Engineer, Marketing Specialist), the pipeline:
1. Pulls real job postings from public sources
2. Matches posting text against a hand-built, validated skill taxonomy
3. Reports what share of postings mention each skill — with the raw count, not just a percentage
4. Publishes it all through a live dashboard: single-role skill breakdowns, side-by-side role comparison with common/differentiator analysis, a market snapshot, skill search, and direct links to the real postings

Every number distinguishes **observation** (what employers wrote) from **interpretation** — the dashboard's "About this data" section explains the methodology and limitations in full.

## How it fits together

### Data pipeline
- **`scrapers/fetch_adzuna.py`** — pulls postings from the [Adzuna API](https://developer.adzuna.com/) (South Africa). Primary skill-signal source — returns a real (if truncated to ~500 chars) description snippet.
- **`scrapers/fetch_careers24.py`** / **`scrapers/fetch_fuzu.py`** — secondary sources, both honestly scoped to posting-volume tracking only (neither exposes enough description text for reliable skill matching — see their docstrings for why).
- **`data/raw/manual_template.csv`** — same CSV schema, for sources without an API where postings are collected by hand.
- **`skills_taxonomy.csv`** — flat synonym mapping (e.g. "Power BI" / "PowerBI" / "power-bi" → `power_bi`), spanning Technology, Finance, Healthcare, Engineering, and Marketing. Built and validated incrementally — see Status below for how a couple of real bugs got caught and fixed along the way.
- **`analysis/skill_extraction.py`** — matches postings against the taxonomy, prints a report, and appends results to two persistent logs: `data/skill_demand_log.csv` (skill percentages) and `data/postings_index.csv` (title/company/location/URL for direct application links — deliberately excludes full description text so it stays small and safe to commit, unlike `data/raw/*.csv` which is gitignored as disposable working data).
- **`analysis/weekly_report.py`** — generates a dated markdown report from the log.

### Dashboard (live at the link above)
- **`api/`** — FastAPI backend. `data_access.py` is the tested data layer (pure Python, no FastAPI dependency); `main.py` is a thin routing layer on top, and also serves the frontend as static files.
- **`static/`** — the frontend itself: single-role view, compare mode with a common/differentiator summary, a market snapshot, skill search, and a full methodology section. No frontend framework — plain HTML/CSS/JS, deployed as one service with the API.
- **`data/role_industry_map.csv`** — maps each role label to a display name and industry for the dashboard's grouping.
- **`docs/future-platform-architecture.md`** — a full "Africa Labour Market Intelligence Platform" architecture spec (multi-industry, canonical data model, CV matching, predictive ML, etc.), saved for reference. **Not current scope.**

## Setup (local development)

python -m venv venv
venv\Scripts\activate # Windows
pip install -r requirements.txt
copy .env.example .env # then fill in your Adzuna credentials


## Usage

Fetch postings and update the skill/postings logs:

python scrapers/fetch_adzuna.py "data analyst"
python analysis/skill_extraction.py data/raw/data_analyst.csv


Generate a markdown report:

python analysis/weekly_report.py


Run the dashboard locally:

uvicorn api.main:app --reload

Then open http://127.0.0.1:8000.

## Deployment

Deployed on [Render](https://render.com) (free tier) as a single service — see `DEPLOY.md` for the full setup. Render auto-redeploys on every push, so updating the live data is just: fetch → run skill_extraction → commit → push.

Known limitation: the free tier spins down after ~15 minutes idle and takes 10-30 seconds to wake on the next visit.

## Status

**Live, v1.** Core validation complete across 9 South African roles spanning 5 industries, each with a distinct, credible skill profile backed by real posting data — from Data Engineer's ETL/cloud-led profile to Accountant's reporting/tax/audit-led one. Two real bugs were caught and fixed during development rather than shipped silently: a Registered Nurse self-match artifact (the search term itself was accidentally a taxonomy synonym, producing a meaningless 100%) and a "latest run" detection bug that could silently merge two different runs' data on the same day (fixed by adding precise run timestamps). The dashboard adds direct application links, a compare-mode common/differentiator analysis, and a full methodology section distinguishing observation from interpretation.

## Roadmap

- [x] South Africa: validate signal via Adzuna API pull, multiple roles
- [x] Expand taxonomy across 5 industries (Technology, Finance, Healthcare, Engineering, Marketing)
- [x] Add Careers24 and Fuzu as honestly-scoped secondary (volume-only) sources
- [x] Persistent, run-id-tracked results log
- [x] Weekly aggregation report
- [x] FastAPI backend + dashboard frontend, deployed live on Render
- [x] Direct job application links, sample-size transparency labels, methodology section
- [ ] Nigeria: manual CSV collection from Jobberman
- [ ] Location breakdown per role (needs city-name normalization)
- [ ] Skill categorization (Technical / Tools / Cloud / Soft Skills groupings)
- [ ] Retry/backoff handling for transient API errors
- [ ] Revisit `docs/future-platform-architecture.md` once/if the project outgrows its current scale

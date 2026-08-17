# africa-jobs-intel

African job-market intelligence — extracting skills-demand signals from job postings, starting with South Africa's data/tech job market.

## How it fits together

- **`scrapers/fetch_adzuna.py`** — pulls postings from the [Adzuna API](https://developer.adzuna.com/) (covers South Africa) and writes them to `data/raw/*.csv`. Primary skill-signal source — Adzuna returns a real (if truncated to ~500 chars) description snippet.
- **`scrapers/fetch_careers24.py`** — scrapes Careers24.com listing pages (no public API exists). **Scoped to posting-volume/frequency tracking only** — listing cards contain title/location/date/company but no description text, so skill matches against this source are unreliable. Not fed into skill-frequency conclusions.
- **`scrapers/fetch_fuzu.py`** — pulls Kenya postings from Fuzu.com's JSON-LD structured-data block (title + URL only). Fuzu is a JavaScript-rendered React site, so a plain HTTP request can't reach the actual job-card HTML. **Scoped to volume tracking only**, same as Careers24, and thinner still (no company/location/description at all). BrighterMonday was tried first but its search-results URLs are explicitly disallowed in robots.txt — skipped rather than worked around.
- **`data/raw/manual_template.csv`** — same CSV schema, for sources without an API where postings are collected by hand.
- **`analysis/skill_extraction.py`** — reads any CSV in `data/raw/` matching the schema, regardless of source, matches against `skills_taxonomy.csv`, prints skill frequency, and appends results to `data/skill_demand_log.csv` (see below).
- **`skills_taxonomy.csv`** — flat synonym mapping (e.g. "Power BI" / "PowerBI" / "power-bi" → `power_bi`). Extend this as new terms show up in postings.
- **`data/skill_demand_log.csv`** — persistent, append-only log of every analysis run (date, role label, total postings, skill, count, %). This is what makes trend-over-time analysis possible without a database — each run adds dated rows rather than overwriting the last run's output.
- **`docs/future-platform-architecture.md`** — a full "Africa Labour Market Intelligence Platform" architecture spec (multi-industry, canonical data model, dedup, API, ML roadmap, etc.), saved for reference. **Not current scope** — the project is deliberately staying at its current CSV-based, tech/data-focused, single-country scale until that scope is actually warranted. See the doc for the reasoning.

The point of the shared CSV schema: the analysis layer never needs to know or care whether a posting came from an API call or was pasted in by hand. New sources just need to output the same columns.

## Setup

python -m venv venv
venv\Scripts\activate # Windows
pip install -r requirements.txt
copy .env.example .env # then fill in your Adzuna credentials


## Usage

Fetch postings:

python scrapers/fetch_adzuna.py "data analyst"
python scrapers/fetch_careers24.py "data analyst" 1
python scrapers/fetch_fuzu.py "data analyst"

Analyze skill frequency (single file or whole folder) — also logs results to `data/skill_demand_log.csv`:

python analysis/skill_extraction.py data/raw/data_analyst.csv
python analysis/skill_extraction.py data/raw/


## Status

Core validation complete: Adzuna pipeline confirmed working and reproducible across two roles (Data Analyst vs Data Engineer, South Africa) with clearly differentiated, credible skill signal — ETL/cloud/Python/big-data skew Data Engineer, dashboarding/Power BI skew Data Analyst. Careers24 and Fuzu added as secondary sources, both honestly scoped to volume tracking only. Results now persist across runs via `data/skill_demand_log.csv` instead of disappearing from the terminal. A larger multi-industry platform architecture was proposed and deliberately deferred — see `docs/future-platform-architecture.md`.

## Roadmap

- [x] South Africa: validate signal via Adzuna API pull (Data Analyst, Data Engineer roles)
- [x] Expand taxonomy with containerization/big-data/orchestration terms, validate differentiation holds
- [x] Add Careers24 as a second source (scoped to volume tracking, not skill signal)
- [x] Add Fuzu (Kenya) as a third source (scoped to volume tracking — JS-rendered site, title+URL only)
- [x] Persistent results log so skill-frequency data survives between runs (`data/skill_demand_log.csv`)
- [ ] Nigeria: manual CSV collection from Jobberman
- [ ] Add retry/backoff handling for transient API errors (hit a 503 from Adzuna once)
- [ ] Consider headless-browser rendering (Selenium/Playwright) if Fuzu's full descriptions become worth the added complexity
- [ ] Weekly aggregation report built on top of `skill_demand_log.csv`
- [ ] Practice-scenario generator built on top of validated skill clusters
- [ ] Revisit `docs/future-platform-architecture.md` once/if the project outgrows its current scale





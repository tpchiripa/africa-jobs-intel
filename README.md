# africa-jobs-intel

African job-market intelligence — extracting skills-demand signals from job postings, starting with South Africa's data/tech job market.

## How it fits together

- **`scrapers/fetch_adzuna.py`** — pulls postings from the [Adzuna API](https://developer.adzuna.com/) (covers South Africa) and writes them to `data/raw/*.csv`.
- **`data/raw/manual_template.csv`** — same CSV schema, for sources without an API (e.g. BrighterMonday, Fuzu for Kenya) where postings are collected by hand for now.
- **`analysis/skill_extraction.py`** — reads any CSV in `data/raw/` matching the schema, regardless of source, matches against `skills_taxonomy.csv`, and reports skill frequency.
- **`skills_taxonomy.csv`** — flat synonym mapping (e.g. "Power BI" / "PowerBI" / "power-bi" → `power_bi`). Extend this as new terms show up in postings.

The point of the shared CSV schema: the analysis layer never needs to know or care whether a posting came from an API call or was pasted in by hand. New sources (a Kenya or Nigeria scraper, a different API) just need to output the same columns.

## Setup

```
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then fill in your Adzuna credentials
```

## Usage

Fetch postings:
```
python scrapers/fetch_adzuna.py "data analyst"
```

Analyze skill frequency (single file or whole folder):
```
python analysis/skill_extraction.py data/raw/data_analyst.csv
python analysis/skill_extraction.py data/raw/
```

## Status

Early validation stage — proving the skill-clustering signal is real before building the practice-scenario generator on top of it.

## Roadmap

- [ ] South Africa: validate signal via Adzuna API pull (Data Analyst, Data Engineer roles)
- [ ] Kenya: manual CSV collection from BrighterMonday/Fuzu, same schema
- [ ] Nigeria: manual CSV collection from Jobberman
- [ ] Weekly aggregation report
- [ ] Practice-scenario generator built on top of validated skill clusters

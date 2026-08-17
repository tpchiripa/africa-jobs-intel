# Future Platform Architecture (Reference Only)

**Status: NOT current scope. Saved for later reference.**

This document was provided on 2026-08-17 as a full architecture spec for
evolving this project into a general-purpose "Africa Labour Market
Intelligence Platform" — covering all industries (not just tech/data),
with a canonical data model, deduplication, occupation normalization,
a database, an API, a frontend, predictive ML, and eventual B2B/B2G
use cases.

## Why this isn't being implemented now

As of 2026-08-17, the actual project is: one validated skill-signal
source (Adzuna, South Africa, Data Analyst vs Data Engineer), two
honestly-scoped volume-only sources (Careers24, Fuzu), a flat CSV
taxonomy, and no database/API/frontend/tests. This document assumes
a canonical schema, dedup engine, occupation taxonomy, and multi-month
team effort that doesn't match where the project stands — a few days
into part-time solo validation work.

Decision (2026-08-17): keep building at current scale — CSV-based,
single-country, tech/data-focused, manual runs — rather than adopting
this architecture now. Revisit this document once/if the current
approach outgrows its scale (e.g. multiple countries with real skill
signal, a reason to query historical trends, or someone other than
the builder needing to use the data).

## What's worth borrowing sooner, at small scale

- **Observed vs. inference vs. prediction discipline** (the doc's
  section 27) — already informally practiced (e.g. labeling Careers24/
  Fuzu as "volume only, not skill signal"). Worth keeping explicit.
- **A lightweight persistent results log** — instead of a full
  canonical database, just append each `skill_extraction.py` run's
  output (date, role, country, source, skill, count, pct) to a CSV,
  so results aren't lost between runs and trends become visible over
  time. This is a small, cheap step — not the full canonical model
  the doc describes.

## Full original document

The complete architecture spec is preserved below verbatim.

---

You are a senior data-platform architect, ML engineer, data scientist, product strategist, and technical lead.

I am developing an existing project called:

AFRICA JOBS INTEL

The repository already contains working job-market ingestion and analysis functionality. DO NOT rewrite the project from scratch.

Your task is to inspect the existing repository, understand what has already been implemented, and evolve it into a production-oriented:

AFRICA LABOUR MARKET INTELLIGENCE PLATFORM

The platform must provide immediate practical value TODAY while being architected to expand far beyond technology/data jobs.

============================================================
1. CURRENT PROJECT STATE
============================================================

The repository currently contains functionality including:

- Adzuna job ingestion
- Careers24 scraper
- Fuzu scraper
- JSON-LD extraction
- JS-rendered website handling
- job-volume tracking
- skill extraction
- skill taxonomy
- expanded technology/data-engineering taxonomy
- raw data directory handling
- analysis scripts
- job posting datasets
- comparison of job-market skill signals

Recent work includes:

- Adzuna ingestion and skill extraction
- Data Analyst vs Data Engineer skill analysis
- Careers24 volume tracking
- Fuzu scraping
- expanded taxonomy including:
  - ETL
  - SQL
  - Python
  - AWS
  - Azure
  - Databricks
  - Spark
  - Big Data
  - containers
  - data warehousing
  - etc.

IMPORTANT:

The existing work is valuable.

Do NOT throw it away.

Do NOT replace working components simply because you would design them differently.

First inspect the repository and produce an architectural assessment.

============================================================
2. CORE PRODUCT VISION
============================================================

Transform the current project from:

"job scraping + skill extraction"

into:

"Africa Labour Market Intelligence Platform"

The platform should answer questions such as:

1. What jobs are employers demanding?
2. Which occupations are growing?
3. Which skills are becoming more important?
4. Which skills are declining?
5. Where geographically is demand concentrated?
6. Which industries are hiring?
7. Which employers are hiring?
8. What salary ranges are being offered?
9. What experience levels are being requested?
10. Which skills frequently appear together?
11. What skills are associated with particular occupations?
12. Which occupations are emerging?
13. Which skills appear to be emerging?
14. What skills are difficult for employers to source?
15. How does demand differ between African countries?
16. How does demand differ between industries?
17. How does demand differ between junior, mid and senior positions?
18. How does the African labour market compare across time?
19. What skills are likely to become more important in the future?
20. What career or workforce interventions could respond to those trends?

The system MUST NOT be restricted to data/technology jobs.

============================================================
3. GENERAL OCCUPATION ARCHITECTURE
============================================================

Design the platform around a generalized occupational taxonomy.

Examples:

Technology, Finance, Healthcare, Engineering, Business, Education,
Construction, Agriculture, Energy, Mining, Logistics, Hospitality,
Retail — each with multiple occupation families.

The taxonomy MUST be extensible. Do not hardcode the application
around technology.

============================================================
4. CANONICAL DATA MODEL
============================================================

Design a normalized canonical model covering: Job, Company, Location,
Country, Industry, Occupation, Skill, Salary, EducationRequirement,
ExperienceRequirement, EmploymentType, Source, JobPostingEvent,
SkillDemandObservation (skill, country, occupation, industry,
time_period, job_count, share_of_jobs, growth_rate).

The model must support historical analysis.

============================================================
5. DATA INGESTION ARCHITECTURE
============================================================

Preserve existing scrapers. Build modular ingestion (sources/adzuna,
careers24, fuzu, future_sources) producing a common canonical job
format via: SOURCE -> RAW INGESTION -> VALIDATION -> NORMALIZATION ->
DEDUPLICATION -> ENRICHMENT -> STORAGE -> ANALYTICS. Don't let
source-specific logic contaminate downstream analytics.

============================================================
6. DATA QUALITY
============================================================

Handle missing fields, malformed records, duplicate jobs/companies,
inconsistent titles/countries/currencies/dates, salary anomalies, HTML
noise, scraper failures, stale/repeated postings, schema differences.
Track records discovered/accepted/rejected/duplicated/normalized/
enriched. Make data-quality problems observable.

============================================================
7. JOB DEDUPLICATION
============================================================

The same job may appear across sources. Don't count each occurrence
as independent. Use combinations of company, title, location,
normalized description, salary, posting date, source identifiers.
Start deterministic/fuzzy before embeddings. Document tradeoffs.

============================================================
8. OCCUPATION NORMALIZATION
============================================================

Titles vary ("Data Analyst" / "BI Analyst" / "Reporting Analyst").
Support raw_title, normalized_title, occupation, occupation_family,
industry. Preserve both raw and normalized data — never destroy the
original title.

============================================================
9. SKILL INTELLIGENCE
============================================================

Identify technical skills, tools, certifications, domain knowledge,
business/soft skills, regulatory knowledge, education requirements.
Start with taxonomy/keyword matching; architect for later NLP,
embeddings, semantic similarity, LLM-assisted classification, NER.
Don't introduce LLM complexity before reliable baselines exist.

============================================================
10. SKILL RELATIONSHIPS
============================================================

Build skill co-occurrence analysis (e.g. Python<->SQL, AWS<->Spark,
Accounting<->ERP). Generate co-occurrence matrices, skill networks,
clusters, bundles — to discover skills commonly requested together.

============================================================
11. LABOUR MARKET ANALYTICS
============================================================

Job demand by country/city/occupation/industry/company/source/month/
seniority. Skill demand: most-demanded, fastest-growing, declining,
emerging, combinations, by occupation/industry/geography. Salary
intelligence: distribution, median, by occupation/experience/country/
skill, trends. Workforce requirements: education, experience,
certifications, remote/hybrid/on-site, employment type.

============================================================
12. TIME SERIES FOUNDATION
============================================================

Historical observations at occupation x country x month, skill x
occupation x country x month, industry x country x month granularity.
Essential structure — don't build predictive models before this
exists properly.

============================================================
13. IMMEDIATE PRODUCT VALUE
============================================================

Build dashboards before ML: Global Africa overview (total jobs,
countries, industries, occupations, fastest-growing occupations/
skills); Country labour market (top occupations/industries/skills,
salary ranges, hiring companies, emerging skills); Occupation
intelligence (demand trend, top skills, salary, requirements,
industries/countries hiring); Skill intelligence (jobs/occupations/
industries/countries requiring it, growth trend, combinations).

============================================================
14. CAREER INTELLIGENCE
============================================================

Users enter their skills; platform compares against observed labour-
market demand, returns strongest matches, missing skills, emerging
skills, adjacent occupations, recommended skill combinations. Start
with transparent rules and measurable evidence, not a sophisticated
recommendation engine.

============================================================
15. EMPLOYER INTELLIGENCE
============================================================

Eventually: "what skills are competitors hiring for", "what
occupations are companies expanding", salary market, hard-to-find
talent. Potential B2B value.

============================================================
16. EDUCATION / TRAINING INTELLIGENCE
============================================================

Universities/colleges/bootcamps could eventually ask what skills
employers demand, which courses are becoming less relevant, what to
add to curricula, which occupations are growing. Potential commercial
direction.

============================================================
17. WORKFORCE / POLICY INTELLIGENCE
============================================================

Architect for eventual government/development-sector use: growing
occupations, high/low-opportunity regions, emerging skills, workforce
shortages, training-program alignment. Don't implement now — just
ensure the architecture can support it later.

============================================================
18. PREDICTIVE ML
============================================================

Only after sufficient historical data exists. Primary problem:
predict future skill demand (1/3/6/12 months). Start with baselines
(naive forecast, moving average, linear regression, ARIMA), then
Random Forest/XGBoost/LightGBM, then investigate deep learning (LSTM,
GRU, Temporal CNN, Transformers) only if enough data exists, temporal
structure supports it, it beats strong baselines, and it's evaluated
properly. Don't use deep learning because it sounds impressive.

============================================================
19. EMERGING OCCUPATION DETECTION
============================================================

Explore detecting emerging occupations via posting volume growth, new
skills appearing, skill diversity, geographic expansion, salary
movement, industry expansion. Create a transparent "Emerging
Occupation Score."

============================================================
20. AI / NLP ROADMAP
============================================================

Phase 1: rules + taxonomy. Phase 2: TF-IDF/classical NLP. Phase 3:
embeddings. Phase 4: semantic skill extraction. Phase 5: LLM-assisted
enrichment. Phase 6: predictive ML. Phase 7: deep learning. Don't skip
directly to Phase 6.

============================================================
21. TECHNOLOGY ARCHITECTURE
============================================================

Prefer modular architecture. Potential stack: Python, PostgreSQL,
Pandas, SQL, FastAPI, Docker. Optional as scale increases: Kafka,
Spark, dbt, Airflow, Redis, object storage, DuckDB, MLflow. Frontend:
React/Next.js. Analytics: Grafana/custom dashboard/Power BI. Don't
introduce technologies merely to look impressive — every technology
must solve a real problem.

============================================================
22. OBSERVABILITY
============================================================

Track scraper success rate, records per source, ingestion latency,
failed jobs, duplicate rate, data-quality rate, database health,
pipeline execution, model performance. Design for eventual Prometheus/
Grafana but don't over-engineer the MVP.

============================================================
23. API DESIGN
============================================================

Eventually expose intelligence via API: GET /jobs, /occupations,
/skills, /industries, /countries, /skills/{skill}/trend,
/occupations/{occupation}/demand, /countries/{country}/labour-market,
/skills/emerging, /occupations/emerging, /career-match. Must serve the
frontend and allow future third-party integrations.

============================================================
24. COMMERCIAL PRODUCT THINKING
============================================================

Potential users: job seekers, students, universities, training
providers, recruiters, employers, HR departments, workforce
consultants, governments, development organizations, investors. Don't
attempt to serve all of them in V1 — choose a practical initial user,
architect for expansion.

============================================================
25. MVP PRIORITY
============================================================

Reliable multi-source ingestion, canonical job schema, deduplication,
occupation normalization, skill extraction, historical storage,
labour-market analytics, country/occupation/skill-trend analysis,
basic career intelligence, dashboard. Must work even without
sophisticated AI.

============================================================
26. WHAT NOT TO DO
============================================================

Don't rewrite the whole project; add dozens of scrapers before
stabilizing architecture; build a chatbot first; use LLMs everywhere;
use deep learning without sufficient data; build an overly complex
microservice architecture; introduce Kubernetes prematurely; build an
enormous frontend before the data model is stable; hardcode technology
jobs; make unsupported labour-market claims; treat scraped job counts
as equivalent to total market demand; ignore sampling bias between
sources.

============================================================
27. ANALYTICAL RIGOUR
============================================================

Clearly distinguish OBSERVED DATA from INFERENCE from PREDICTION.
Example — Observed: "23% of collected South African data-engineering
postings mentioned Azure." Inference: "Azure appears strongly
associated with South African data-engineering hiring." Prediction:
"The model forecasts increased Azure demand over the next six
months." Never present predictions as facts. Document sampling bias,
source bias, geographic/scraper coverage, duplicate risk, missing
salary data, temporal bias, occupation classification errors.

============================================================
28. TESTING
============================================================

Tests for scraper output, schema validation, normalization,
deduplication, skill extraction, taxonomy mapping, database
operations, API endpoints, analytical calculations. Representative
fixtures. Project should be reproducible from a fresh clone.

============================================================
29. DOCUMENTATION
============================================================

README should cover: what the platform does, why it exists,
architecture, data sources, data model, pipeline, analytics, current
capabilities, limitations, roadmap, installation, running the
pipeline/analysis/API/dashboard. Architecture diagrams where useful.

============================================================
30. IMPLEMENTATION PROCESS
============================================================

Before modifying code: inspect the entire repository; identify
existing modules/scrapers/data formats/taxonomy/analysis scripts/
dependencies/config/tests/README/database/frontend-backend; produce
an architecture assessment; identify what's reusable and what's
technical debt; create a prioritized roadmap; implement incrementally
— not massive changes in one step. After each major change: run
tests, validate existing functionality, document changes, preserve
backward compatibility where practical.

============================================================
31. REQUIRED FIRST RESPONSE
============================================================

Before changing code, provide: current architecture summary; what's
already good; what needs improvement; proposed target architecture;
proposed database schema; proposed directory structure; MVP scope;
future architecture; ML roadmap; commercial/product roadmap; risks
and limitations; exact implementation order. Then wait for approval
before making large architectural changes.

============================================================
32. FINAL PRODUCT VISION
============================================================

                 AFRICA LABOUR MARKET INTELLIGENCE
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
 JOB MARKET             SKILL MARKET          OCCUPATION MARKET
 INTELLIGENCE            INTELLIGENCE           INTELLIGENCE
       |                      |                      |
       +----------------------+----------------------+
                              |
                              v
                       PREDICTIVE ENGINE
                              |
             +----------------+----------------+
             v                v                v
        Career          Workforce          Education
        Intelligence   Intelligence       Intelligence
             |                |                |
             +----------------+----------------+
                              v
                         B2B / B2G API

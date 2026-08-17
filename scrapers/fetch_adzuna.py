"""
Pulls job postings from the Adzuna API and writes them to a CSV file
in data/raw/. CSV is the interchange format for the rest of the pipeline,
so anything downstream (skill extraction, aggregation) doesn't care
whether a posting came from the API or was pasted in by hand.

Get free credentials at https://developer.adzuna.com/
Adzuna covers South Africa (country code "za"). Kenya and Nigeria are
not currently on Adzuna, so those will need a different source later —
this script is written so that source can plug in the same CSV shape.

KNOWN LIMITATION: Adzuna's search API only returns a snippet of each
job description (~500 chars), not the full posting text, and there is
no parameter to request more (confirmed via their docs:
https://developer.adzuna.com/docs/search). Skill counts from this data
are directional, not exhaustive — they'll under-count skills that are
mentioned later in a posting's full requirements list. Getting full
text would require a second pass that fetches each posting's
redirect_url and scrapes the source page, which is slower, more
fragile, and out of scope for this validation stage.
"""

import csv
import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = "za"  # Adzuna country code for South Africa
BASE_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search"

# CSV columns every downstream script expects, regardless of source
FIELDNAMES = [
    "source",
    "posting_id",
    "title",
    "company",
    "location",
    "description",
    "url",
    "date_posted",
    "date_fetched",
]


def fetch_page(query: str, page: int = 1, results_per_page: int = 50) -> dict:
    if not APP_ID or not APP_KEY:
        sys.exit(
            "Missing ADZUNA_APP_ID / ADZUNA_APP_KEY. "
            "Copy .env.example to .env and fill in your credentials."
        )

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": query,
        "results_per_page": results_per_page,
        "content-type": "application/json",
        # Note: no full_description param exists on this endpoint — Adzuna
        # only returns a snippet. See module docstring above.
    }
    response = requests.get(f"{BASE_URL}/{page}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_postings(query: str, max_pages: int = 3) -> list[dict]:
    rows = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for page in range(1, max_pages + 1):
        data = fetch_page(query, page=page)
        results = data.get("results", [])
        if not results:
            break

        for job in results:
            rows.append(
                {
                    "source": "adzuna",
                    "posting_id": job.get("id", ""),
                    "title": job.get("title", ""),
                    "company": (job.get("company") or {}).get("display_name", ""),
                    "location": (job.get("location") or {}).get("display_name", ""),
                    "description": (job.get("description") or "").replace("\n", " "),
                    "url": job.get("redirect_url", ""),
                    "date_posted": job.get("created", ""),
                    "date_fetched": fetched_at,
                }
            )

    return rows


def write_csv(rows: list[dict], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    file_exists = os.path.exists(out_path)
    with open(out_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "data analyst"
    out_file = f"data/raw/{query.replace(' ', '_')}.csv"

    print(f"Fetching '{query}' postings from Adzuna (South Africa)...")
    postings = fetch_postings(query)
    write_csv(postings, out_file)
    print(f"Wrote {len(postings)} postings to {out_file}")
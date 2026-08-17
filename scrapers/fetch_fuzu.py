"""
Pulls job postings from Fuzu.com search pages and writes them to the
same CSV schema as fetch_adzuna.py / fetch_careers24.py.

IMPORTANT — READ BEFORE RUNNING:
Fuzu is a JavaScript-rendered (React) site. A plain HTTP request does
NOT receive the job-card HTML you see when browsing — that's built by
JavaScript after the page loads. Confirmed by inspecting raw page
source on 2026-08-17: the initial HTML response contains only scripts
and metadata, no job cards.

What IS reliably present in the raw HTML: a JSON-LD <script
type="application/ld+json"> block containing an ItemList of the first
10 results — title and URL only, no company/location/description.
This script extracts that block. It cannot be extended to pull full
descriptions without a headless browser (Selenium/Playwright), which
is a bigger undertaking deliberately out of scope for now.

SCOPE (matches the Careers24 decision from 2026-08-16): this source
is for posting volume/frequency tracking only, not skill-signal
extraction — there's no description text to match against.

Only pulls page 1 (10 results) per search — Fuzu's own llms.txt asks
crawlers to avoid parameterized URLs, and pagination beyond page 1
wasn't confirmed as compatible with that guidance, so this stays
conservative rather than guessing.

RESPECTFUL SCRAPING:
  - A real User-Agent identifying a browser, not a bare Python script
  - Only fetches the single search-results page per role — no crawling
    beyond what's needed
  - Check https://www.fuzu.com's Terms before scaling this up
"""

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

BASE_URL = "https://www.fuzu.com/kenya/job"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

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


def fetch_search_page_html(query: str) -> str:
    role_slug = query.strip().lower().replace(" ", "-")
    url = f"{BASE_URL}/{role_slug}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def extract_json_ld_jobs(html: str) -> list[dict]:
    matches = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    for raw in matches:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "itemListElement" in data:
            return data["itemListElement"]
    return []


def parse_listings(html: str) -> list[dict]:
    items = extract_json_ld_jobs(html)
    fetched_at = datetime.now(timezone.utc).isoformat()

    rows = []
    for item in items:
        url = item.get("url", "")
        posting_id = url.rstrip("/").split("/")[-1] if url else ""

        rows.append(
            {
                "source": "fuzu",
                "posting_id": posting_id,
                "title": item.get("name", ""),
                "company": "",
                "location": "",
                "description": "",
                "url": url,
                "date_posted": "",
                "date_fetched": fetched_at,
            }
        )
    return rows


def fetch_postings(query: str) -> list[dict]:
    html = fetch_search_page_html(query)
    return parse_listings(html)


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
    out_file = f"data/raw/fuzu_{query.replace(' ', '_')}.csv"

    print(f"Fetching '{query}' postings from Fuzu (Kenya, page 1 only)...")
    postings = fetch_postings(query)
    if not postings:
        print("No postings found — JSON-LD structure may have changed, or the role slug didn't match. Check the URL manually first.")
    write_csv(postings, out_file)
    print(f"Wrote {len(postings)} postings to {out_file}")
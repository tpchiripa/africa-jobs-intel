"""
Scrapes job postings from Careers24.com and writes them to the same
CSV schema as fetch_adzuna.py, so this source plugs into the existing
pipeline (skill_extraction.py doesn't care where a row came from).

IMPORTANT — READ BEFORE RUNNING:
Careers24 has no public API, so this works by parsing their HTML
directly. Card selectors were confirmed against real page source
(view-source, Ctrl+U) on 2026-08-16. The search URL pattern was
confirmed from a real browser search on the same date:
    https://www.careers24.com/jobs/lc-cape-town/kw-data-analyst/rmt-incl/
"lc-" = location slug, "kw-" = keyword slug (spaces -> hyphens),
"rmt-incl/" = include remote jobs.

STILL UNVERIFIED: the pagination pattern for page > 1 (guessed as
"page-N/" appended to the URL — not yet confirmed against a real
"next page" click). If page 2+ returns the same results as page 1,
or errors, that's the next thing to check by clicking "next page"
on the live site and comparing the URL.

KNOWN LIMITATION: company name is only present as an image `alt`
attribute, and only on SOME cards — several listings have no
company image at all. Expect the `company` column to be empty for
a meaningful share of rows. This is a real gap in what the site
exposes on listing pages, not a bug in the scraper.

ALSO: listing cards only contain title/location/date/company, no
actual job description text — so skill_extraction.py will have far
less to match against here than with Adzuna's snippet. Useful for
posting volume/frequency by role, weaker for skill-signal purposes.

RESPECTFUL SCRAPING — please keep these in place:
  - REQUEST_DELAY_SECONDS between requests (don't hammer the site)
  - A real User-Agent identifying a browser, not a bare Python script
  - A sane max_pages default (don't pull the entire site in one run)
  - Check https://www.careers24.com's Site Terms before scaling this
    up or using it for anything beyond personal experimentation.
"""

import csv
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.careers24.com/jobs"
REQUEST_DELAY_SECONDS = 2  # be polite — don't hammer the server
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Confirmed against real Careers24 page source on 2026-08-16.
SELECTORS = {
    "job_card": "div.job-card",
    "title": "a[data-control='vacancy-title'] h2",
    "link": "a[data-control='vacancy-title']",
    "info_list": "div.job-card-left ul li",  # location, job type, posted date, in that order
    "company_img": "div.job-card-right img",  # alt attribute holds company name, when present
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


def build_search_url(query: str, location: str = "cape-town", page: int = 1) -> str:
    keyword_slug = query.strip().lower().replace(" ", "-")
    location_slug = location.strip().lower().replace(" ", "-")
    url = f"{BASE_URL}/lc-{location_slug}/kw-{keyword_slug}/rmt-incl/"
    if page > 1:
        url += f"page-{page}/"  # UNVERIFIED — see docstring
    return url


def fetch_page_html(query: str, page: int, location: str = "cape-town") -> str:
    url = build_search_url(query, location=location, page=page)
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(SELECTORS["job_card"])
    fetched_at = datetime.now(timezone.utc).isoformat()

    rows = []
    for card in cards:
        title_el = card.select_one(SELECTORS["title"])
        link_el = card.select_one(SELECTORS["link"])
        info_items = card.select(SELECTORS["info_list"])
        company_img = card.select_one(SELECTORS["company_img"])

        location = info_items[0].get_text(strip=True) if len(info_items) > 0 else ""
        posted_raw = info_items[2].get_text(" ", strip=True) if len(info_items) > 2 else ""
        date_match = re.search(r"Posted:\s*([\d]{1,2}\s+\w+\s+\d{4})", posted_raw)
        date_posted = date_match.group(1) if date_match else posted_raw

        url = link_el["href"] if link_el and link_el.has_attr("href") else ""
        if url and url.startswith("/"):
            url = "https://www.careers24.com" + url

        posting_id = card.get("data-id", "")

        rows.append(
            {
                "source": "careers24",
                "posting_id": posting_id,
                "title": title_el.get_text(strip=True) if title_el else "",
                "company": company_img.get("alt", "") if company_img else "",
                "location": location,
                "description": card.get_text(" ", strip=True),
                "url": url,
                "date_posted": date_posted,
                "date_fetched": fetched_at,
            }
        )
    return rows


def fetch_postings(query: str, max_pages: int = 1, location: str = "cape-town") -> list[dict]:
    all_rows = []
    for page in range(1, max_pages + 1):
        print(f"  Fetching page {page}...")
        html = fetch_page_html(query, page, location=location)
        rows = parse_listings(html)
        if not rows:
            print(f"  No listings found on page {page} — selectors may need fixing, or you've reached the end of results.")
            break
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY_SECONDS)
    return all_rows


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
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1  # start small!
    out_file = f"data/raw/careers24_{query.replace(' ', '_')}.csv"

    print(f"Fetching '{query}' postings from Careers24 ({max_pages} page(s))...")
    postings = fetch_postings(query, max_pages=max_pages)
    write_csv(postings, out_file)
    print(f"Wrote {len(postings)} postings to {out_file}")
"""
Reads job posting CSVs from data/raw/ (doesn't matter whether they came
from fetch_adzuna.py or were pasted in by hand using manual_template.csv —
same schema, same result), matches posting descriptions against
skills_taxonomy.csv, and prints/writes skill frequency counts.

Also appends each run's results to data/skill_demand_log.csv so
results persist across runs and machines instead of vanishing when
the terminal closes — see log_results() below for details.

Usage:
    python analysis/skill_extraction.py data/raw/data_analyst.csv
    python analysis/skill_extraction.py data/raw/          # all CSVs in folder
"""

import csv
import glob
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone


def load_taxonomy(path: str = "skills_taxonomy.csv") -> dict[str, str]:
    """Returns {synonym_lowercase: skill_id}"""
    synonym_to_skill = {}
    # utf-8-sig strips a leading BOM if present (common when a CSV has been
    # saved from Windows Notepad), so the header still reads as "skill_id"
    # instead of "\ufeffskill_id".
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            synonym_to_skill[row["synonym"].strip().lower()] = row["skill_id"].strip()
    return synonym_to_skill


def compile_patterns(synonym_to_skill: dict[str, str]) -> dict[str, re.Pattern]:
    """
    Compiles a word-boundary regex per synonym so "reporting" doesn't
    match inside "report", "sql" doesn't match inside a longer token, etc.
    """
    return {
        synonym: re.compile(r"\b" + re.escape(synonym) + r"\b")
        for synonym in synonym_to_skill
    }


def load_postings(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def extract_skills(
    text: str,
    synonym_to_skill: dict[str, str],
    patterns: dict[str, re.Pattern],
) -> set[str]:
    text_lower = (text or "").lower()
    found = set()
    for synonym, pattern in patterns.items():
        if pattern.search(text_lower):
            found.add(synonym_to_skill[synonym])
    return found


def analyze(csv_paths: list[str], taxonomy_path: str = "skills_taxonomy.csv"):
    synonym_to_skill = load_taxonomy(taxonomy_path)
    patterns = compile_patterns(synonym_to_skill)

    skill_counts = Counter()
    total_postings = 0

    for path in csv_paths:
        postings = load_postings(path)
        total_postings += len(postings)
        for posting in postings:
            combined_text = f"{posting.get('title', '')} {posting.get('description', '')}"
            skills_found = extract_skills(combined_text, synonym_to_skill, patterns)
            skill_counts.update(skills_found)

    return skill_counts, total_postings


def print_report(skill_counts: Counter, total_postings: int):
    print(f"\nAnalyzed {total_postings} postings\n")
    print(f"{'Skill':<20} {'Count':<8} {'% of postings'}")
    print("-" * 45)
    for skill, count in skill_counts.most_common():
        pct = (count / total_postings * 100) if total_postings else 0
        print(f"{skill:<20} {count:<8} {pct:.1f}%")


def log_results(
    skill_counts: Counter,
    total_postings: int,
    label: str,
    log_path: str = "data/skill_demand_log.csv",
) -> None:
    """
    Appends this run's results to a persistent log so they aren't lost
    the moment the terminal closes. One row per skill per run, so the
    same log can later answer "how has X skill's share changed over
    time for role Y" without needing a database — just filter the CSV.

    This is deliberately NOT the full canonical data model described in
    docs/future-platform-architecture.md — it's the small, cheap step
    worth doing at the project's current scale. See that doc for the
    larger version if/when this outgrows a flat log file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    file_exists = os.path.exists(log_path)
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    fieldnames = ["run_date", "label", "total_postings", "skill", "count", "pct"]
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for skill, count in skill_counts.most_common():
            pct = round((count / total_postings * 100), 1) if total_postings else 0
            writer.writerow(
                {
                    "run_date": run_date,
                    "label": label,
                    "total_postings": total_postings,
                    "skill": skill,
                    "count": count,
                    "pct": pct,
                }
            )


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "data/raw/"

    if os.path.isdir(arg):
        paths = [
            p for p in glob.glob(os.path.join(arg, "*.csv"))
            if not p.endswith("manual_template.csv")
        ]
    else:
        paths = [arg]

    if not paths:
        sys.exit(f"No CSV files found at {arg}")

    counts, total = analyze(paths)
    print_report(counts, total)

    # Derive a readable label from the input, e.g. "data/raw/data_analyst.csv"
    # -> "data_analyst", or the folder name for a whole-directory run.
    label = os.path.splitext(os.path.basename(arg.rstrip("/\\")))[0] or "all"
    log_results(counts, total, label=label)
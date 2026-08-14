
"""
Reads job posting CSVs from data/raw/ (doesn't matter whether they came
from fetch_adzuna.py or were pasted in by hand using manual_template.csv —
same schema, same result), matches posting descriptions against
skills_taxonomy.csv, and prints/writes skill frequency counts.

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


def load_taxonomy(path: str = "skills_taxonomy.csv") -> dict[str, str]:
    """Returns {synonym_lowercase: skill_id}"""
    synonym_to_skill = {}
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
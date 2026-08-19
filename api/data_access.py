"""
Data access layer for the dashboard API. Deliberately has NO dependency
on FastAPI — it's pure Python reading CSVs, so it can be tested directly
without needing a running server. api/main.py is a thin routing layer
on top of these functions.

Reuses the same "keep only each label's most recent run" logic that
analysis/weekly_report.py uses, so the API and the markdown report
never disagree about which numbers are current.
"""

import csv
import os
from collections import defaultdict
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "data", "skill_demand_log.csv")
ROLE_MAP_PATH = os.path.join(BASE_DIR, "data", "role_industry_map.csv")


def load_log(log_path: str = LOG_PATH) -> list[dict]:
    if not os.path.exists(log_path):
        return []
    with open(log_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_role_map(path: str = ROLE_MAP_PATH) -> dict[str, dict]:
    """Returns {label: {display_name, industry}}. Missing labels fall
    back to a title-cased version of the label with industry 'Other',
    so the API never breaks just because a new role hasn't been added
    to role_industry_map.csv yet."""
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {
            row["label"]: {"display_name": row["display_name"], "industry": row["industry"]}
            for row in csv.DictReader(f)
        }


def _last_contiguous_block(rows: list[dict]) -> list[dict]:
    """LEGACY FALLBACK ONLY — see weekly_report.py for why this is
    unreliable and only used for rows logged before run_id existed."""
    if not rows:
        return rows
    blocks = [[rows[0]]]
    for prev, curr in zip(rows, rows[1:]):
        if int(curr["count"]) > int(prev["count"]):
            blocks.append([curr])
        else:
            blocks[-1].append(curr)
    return blocks[-1]


def latest_run_per_label(rows: list[dict]) -> dict[str, list[dict]]:
    """
    Groups rows by label, keeping only the most recent run's rows.
    Uses run_id (a precise timestamp) when present — unambiguous even
    across multiple same-day runs. Falls back to a same-day count
    heuristic only for legacy rows logged before run_id existed.
    """
    has_run_id = any(row.get("run_id") for row in rows)

    if has_run_id:
        by_label: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_label[row["label"]].append(row)

        result: dict[str, list[dict]] = {}
        for label, label_rows in by_label.items():
            rows_with_id = [r for r in label_rows if r.get("run_id")]
            if rows_with_id:
                latest_run_id = max(r["run_id"] for r in rows_with_id)
                result[label] = [r for r in label_rows if r.get("run_id") == latest_run_id]
            else:
                result[label] = _last_contiguous_block(label_rows)
        return result

    by_label_and_date: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        key = (row["label"], row["run_date"])
        by_label_and_date[key].append(row)

    latest_date_per_label: dict[str, str] = {}
    for label, run_date in by_label_and_date:
        if label not in latest_date_per_label or run_date > latest_date_per_label[label]:
            latest_date_per_label[label] = run_date

    result: dict[str, list[dict]] = {}
    for label, latest_date in latest_date_per_label.items():
        same_day_runs = [
            r for r in rows if r["label"] == label and r["run_date"] == latest_date
        ]
        result[label] = _last_contiguous_block(same_day_runs)
    return result


def get_snapshot(top_n: int = 5) -> dict:
    """
    Homepage snapshot: the highest single skill percentages seen across
    ANY role (a leaderboard, not a per-role top-N), and the roles with
    the largest posting samples. Both derived from data already in the
    log — no new collection needed.
    """
    rows = load_log()
    role_map = load_role_map()
    latest = latest_run_per_label(rows)

    all_skill_entries = []
    for label, role_rows in latest.items():
        info = role_map.get(label, {"display_name": label.replace("_", " ").title()})
        for r in role_rows:
            all_skill_entries.append(
                {
                    "role_label": label,
                    "role_display_name": info["display_name"],
                    "skill": r["skill"],
                    "pct": float(r["pct"]),
                }
            )
    all_skill_entries.sort(key=lambda e: e["pct"], reverse=True)

    most_active = []
    for label, role_rows in latest.items():
        info = role_map.get(label, {"display_name": label.replace("_", " ").title()})
        total = int(role_rows[0]["total_postings"]) if role_rows else 0
        most_active.append({"label": label, "display_name": info["display_name"], "total_postings": total})
    most_active.sort(key=lambda r: r["total_postings"], reverse=True)

    return {
        "top_skills": all_skill_entries[:top_n],
        "most_active_roles": most_active[:top_n],
    }


def sample_size_label(total_postings: int) -> str:
    """
    Product-transparency label, not a formal statistical confidence
    interval — just an honest signal about how much weight a reader
    should put on a small sample.
    """
    if total_postings < 20:
        return "Limited observations"
    elif total_postings < 50:
        return "Emerging signal"
    elif total_postings < 100:
        return "Moderate evidence"
    else:
        return "Strong observed sample"


def get_meta() -> dict:
    """Overall stats for the dashboard header."""
    rows = load_log()
    role_map = load_role_map()
    latest = latest_run_per_label(rows)

    roles = []
    industries = set()
    total_postings = 0
    latest_date = ""

    for label, role_rows in latest.items():
        info = role_map.get(label, {"display_name": label.replace("_", " ").title(), "industry": "Other"})
        total = int(role_rows[0]["total_postings"]) if role_rows else 0
        run_date = role_rows[0]["run_date"] if role_rows else ""
        total_postings += total
        industries.add(info["industry"])
        latest_date = max(latest_date, run_date)
        roles.append(
            {
                "label": label,
                "display_name": info["display_name"],
                "industry": info["industry"],
                "total_postings": total,
                "run_date": run_date,
                "sample_size_label": sample_size_label(total),
            }
        )

    roles.sort(key=lambda r: (r["industry"], r["display_name"]))

    return {
        "roles": roles,
        "role_count": len(roles),
        "industry_count": len(industries),
        "industries": sorted(industries),
        "total_postings_analyzed": total_postings,
        "last_updated": latest_date,
    }


def get_role_skills(label: str, top: int = 15) -> dict | None:
    rows = load_log()
    role_map = load_role_map()
    latest = latest_run_per_label(rows)

    if label not in latest:
        return None

    role_rows = latest[label]
    info = role_map.get(label, {"display_name": label.replace("_", " ").title(), "industry": "Other"})
    total = int(role_rows[0]["total_postings"]) if role_rows else 0

    return {
        "label": label,
        "display_name": info["display_name"],
        "industry": info["industry"],
        "total_postings": total,
        "sample_size_label": sample_size_label(total),
        "run_date": role_rows[0]["run_date"] if role_rows else "",
        "skills": [
            {"skill": r["skill"], "count": int(r["count"]), "pct": float(r["pct"])}
            for r in role_rows[:top]
        ],
    }


def get_comparison(labels: list[str]) -> dict:
    """
    Cross-role comparison for the given labels. Only includes skills
    that appear in at least 2 of the requested roles, matching the
    same logic weekly_report.py uses for its comparison table.
    """
    rows = load_log()
    role_map = load_role_map()
    latest = latest_run_per_label(rows)

    valid_labels = [l for l in labels if l in latest]

    skill_by_label_pct: dict[str, dict[str, float]] = defaultdict(dict)
    for label in valid_labels:
        for row in latest[label]:
            skill_by_label_pct[row["skill"]][label] = float(row["pct"])

    comparison_skills = []
    for skill, present_in in sorted(skill_by_label_pct.items()):
        if len(present_in) < 2:
            continue
        comparison_skills.append({"skill": skill, "by_role": present_in})

    # Sort by max pct across roles, descending, so the most prominent
    # shared skills appear first.
    comparison_skills.sort(key=lambda s: max(s["by_role"].values()), reverse=True)

    role_labels = [
        {
            "label": l,
            "display_name": role_map.get(l, {}).get("display_name", l.replace("_", " ").title()),
        }
        for l in valid_labels
    ]

    return {"roles": role_labels, "skills": comparison_skills}


def search_skills(query: str) -> list[dict]:
    """Finds all (role, skill, pct) entries where the skill id contains
    the query string, across every role's latest run."""
    rows = load_log()
    role_map = load_role_map()
    latest = latest_run_per_label(rows)
    query_lower = query.strip().lower()

    if not query_lower:
        return []

    results = []
    for label, role_rows in latest.items():
        info = role_map.get(label, {"display_name": label.replace("_", " ").title()})
        for row in role_rows:
            if query_lower in row["skill"].lower():
                results.append(
                    {
                        "role_label": label,
                        "role_display_name": info["display_name"],
                        "skill": row["skill"],
                        "count": int(row["count"]),
                        "pct": float(row["pct"]),
                    }
                )

    results.sort(key=lambda r: r["pct"], reverse=True)
    return results


def load_postings_index(path: str = None) -> list[dict]:
    if path is None:
        path = os.path.join(BASE_DIR, "data", "postings_index.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get_role_postings(label: str, limit: int = 10) -> list[dict]:
    """
    Real job postings with direct application links for a role, from
    its most recent run only (same run_id logic as skill data, so the
    links shown always match the skill percentages currently displayed
    for that role — not a stale batch from an earlier run).
    """
    rows = load_postings_index()
    if not rows:
        return []

    label_rows = [r for r in rows if r["label"] == label]
    if not label_rows:
        return []

    latest_run_id = max(r["run_id"] for r in label_rows)
    latest_rows = [r for r in label_rows if r["run_id"] == latest_run_id]

    return [
        {
            "title": r["title"],
            "company": r["company"],
            "location": r["location"],
            "url": r["url"],
            "date_posted": r["date_posted"],
        }
        for r in latest_rows[:limit]
    ]

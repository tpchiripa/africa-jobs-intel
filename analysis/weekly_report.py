"""
Reads data/skill_demand_log.csv (built up by analysis/skill_extraction.py
over however many runs have happened) and produces a readable markdown
report: top skills per role, and a cross-role comparison table for
skills that appear in more than one role's results.

Called "weekly" as the intended cadence once this is run on a schedule,
but works fine on however much history actually exists — even a single
day's worth, as it is right now.

For each role label, uses only the MOST RECENT run's numbers (if the
same label was run more than once on record, earlier runs are treated
as superseded — e.g. the first thin Business Analyst run before the
taxonomy was expanded is not blended with the corrected run).

Usage:
    python analysis/weekly_report.py
    python analysis/weekly_report.py --top 10
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone


def load_log(log_path: str = "data/skill_demand_log.csv") -> list[dict]:
    if not os.path.exists(log_path):
        sys.exit(
            f"No log found at {log_path}. Run analysis/skill_extraction.py "
            "at least once first — it writes this file automatically."
        )
    with open(log_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def latest_run_per_label(rows: list[dict]) -> dict[str, list[dict]]:
    """
    Groups rows by label, keeping only the rows from that label's most
    recent run_date. If a label was run more than once on the same
    date (e.g. before/after a taxonomy fix), keeps the LAST occurrence
    in file order for that date, since skill_demand_log.csv is
    append-only and later rows reflect the more current taxonomy.
    """
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


def _last_contiguous_block(rows: list[dict]) -> list[dict]:
    """
    same_day_runs may contain rows from more than one run on the same
    date, concatenated in file order (run 1's rows, then run 2's rows).
    Since each run starts a fresh set of skills in descending count
    order, detect a new run by the count column going back up compared
    to the row before it, and keep only the rows from the last block.
    """
    if not rows:
        return rows
    blocks = [[rows[0]]]
    for prev, curr in zip(rows, rows[1:]):
        if int(curr["count"]) > int(prev["count"]):
            blocks.append([curr])
        else:
            blocks[-1].append(curr)
    return blocks[-1]


def build_report(latest: dict[str, list[dict]], top_n: int = 10) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Skill Demand Report — generated {generated_at}",
        "",
        "Observed data only — these are raw keyword-match percentages "
        "from collected postings, not verified labour-market totals. "
        "See docs/future-platform-architecture.md for the distinction "
        "between observed data, inference, and prediction.",
        "",
    ]

    for label, rows in sorted(latest.items()):
        total = rows[0]["total_postings"] if rows else "?"
        run_date = rows[0]["run_date"] if rows else "?"
        lines.append(f"## {label} ({total} postings, as of {run_date})")
        lines.append("")
        lines.append("| Skill | Count | % of postings |")
        lines.append("|---|---|---|")
        for row in rows[:top_n]:
            lines.append(f"| {row['skill']} | {row['count']} | {row['pct']}% |")
        lines.append("")

    lines.append("## Cross-role comparison")
    lines.append("")
    skill_by_label_pct: dict[str, dict[str, str]] = defaultdict(dict)
    for label, rows in latest.items():
        for row in rows:
            skill_by_label_pct[row["skill"]][label] = row["pct"]

    labels = sorted(latest.keys())
    header = "| Skill | " + " | ".join(labels) + " |"
    divider = "|---|" + "|".join(["---"] * len(labels)) + "|"
    lines.append(header)
    lines.append(divider)
    for skill in sorted(skill_by_label_pct):
        present_in = skill_by_label_pct[skill]
        if len(present_in) < 2:
            continue
        row_cells = [f"{present_in.get(l, '—')}%" if l in present_in else "—" for l in labels]
        lines.append(f"| {skill} | " + " | ".join(row_cells) + " |")

    return "\n".join(lines)


def save_report(content: str, out_dir: str = "reports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = os.path.join(out_dir, f"report_{date_str}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


if __name__ == "__main__":
    top_n = 10
    if "--top" in sys.argv:
        idx = sys.argv.index("--top")
        if idx + 1 < len(sys.argv):
            top_n = int(sys.argv[idx + 1])

    rows = load_log()
    latest = latest_run_per_label(rows)

    if not latest:
        sys.exit("Log file exists but has no rows yet.")

    report = build_report(latest, top_n=top_n)
    out_path = save_report(report)

    print(report)
    print(f"\n---\nSaved to {out_path}")
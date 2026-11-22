#!/usr/bin/env python3
"""Rank paper candidates from CSV or JSON using transparent, configurable heuristics."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_scores(records: list[dict[str, Any]], current_year: int | None = None) -> list[dict[str, Any]]:
    if not records:
        return []

    current_year = current_year or date.today().year
    max_citations = max((max(0.0, to_float(r.get("citations"))) for r in records), default=0.0)
    log_denominator = math.log1p(max_citations) if max_citations > 0 else 1.0

    scored = []
    for record in records:
        relevance = min(100.0, max(0.0, to_float(record.get("relevance"))))
        figure_relevance = min(100.0, max(0.0, to_float(record.get("figure_relevance"))))
        citations = max(0.0, to_float(record.get("citations")))
        year = int(to_float(record.get("year"), 0))

        citation_score = (math.log1p(citations) / log_denominator * 100.0) if max_citations > 0 else 0.0
        age = max(0, current_year - year) if year > 0 else 100
        recency_score = 100.0 * (0.5 ** (age / 5.0)) if year > 0 else 0.0

        total = (
            0.40 * relevance
            + 0.25 * figure_relevance
            + 0.20 * citation_score
            + 0.15 * recency_score
        )

        item = dict(record)
        item["citation_score"] = round(citation_score, 2)
        item["recency_score"] = round(recency_score, 2)
        item["weighted_score"] = round(total, 2)
        scored.append(item)

    return sorted(scored, key=lambda x: x["weighted_score"], reverse=True)


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("papers", [])
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list or an object with a 'papers' list.")
        return [dict(x) for x in data]

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    if not records:
        raise ValueError("No paper records found.")
    fields = list(records[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input .csv or .json candidate list")
    parser.add_argument("--output", type=Path, default=Path("ranked-papers.csv"), help="Output CSV path")
    parser.add_argument("--year", type=int, default=date.today().year, help="Reference year for recency scoring")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"Input file does not exist: {args.input}")

    try:
        records = load_records(args.input)
        ranked = calculate_scores(records, current_year=args.year)
        write_csv(ranked, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Ranked {len(ranked)} paper(s) -> {args.output}")
    if ranked:
        print("Top candidates:")
        for index, item in enumerate(ranked[:5], start=1):
            print(f"{index}. {item.get('title', '(untitled)')} — {item['weighted_score']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

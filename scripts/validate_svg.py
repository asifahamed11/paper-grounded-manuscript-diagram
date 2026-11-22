#!/usr/bin/env python3
"""Perform basic structural checks on an SVG file; not a visual or scientific validator."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="SVG file to inspect")
    parser.add_argument("--json", dest="json_path", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    if not args.svg.is_file():
        parser.error(f"SVG file not found: {args.svg}")

    report = {
        "file": str(args.svg),
        "valid_xml": False,
        "root_is_svg": False,
        "has_width": False,
        "has_height": False,
        "has_viewBox": False,
        "text_element_count": 0,
        "external_references": [],
        "warnings": [],
        "errors": [],
    }

    try:
        tree = ET.parse(args.svg)
        root = tree.getroot()
        report["valid_xml"] = True
        tag = root.tag.rsplit("}", 1)[-1]
        report["root_is_svg"] = tag == "svg"
        report["has_width"] = bool(root.attrib.get("width"))
        report["has_height"] = bool(root.attrib.get("height"))
        report["has_viewBox"] = bool(root.attrib.get("viewBox") or root.attrib.get("viewbox"))

        for element in root.iter():
            local_tag = element.tag.rsplit("}", 1)[-1]
            if local_tag == "text":
                report["text_element_count"] += 1
            for key, value in element.attrib.items():
                local_key = key.rsplit("}", 1)[-1]
                if local_key in {"href", "src"} and re.match(r"^(https?:)?//", value.strip()):
                    report["external_references"].append(value.strip())

        if not report["root_is_svg"]:
            report["errors"].append("Root element is not <svg>.")
        if not report["has_viewBox"]:
            report["warnings"].append("No viewBox found; scaling may be less predictable.")
        if not report["has_width"] or not report["has_height"]:
            report["warnings"].append("Explicit width and/or height is missing.")
        if report["text_element_count"] == 0:
            report["warnings"].append("No SVG <text> elements found; text may be converted to paths or absent.")
        if report["external_references"]:
            report["warnings"].append("External references found; ensure they are available at submission time.")
    except ET.ParseError as exc:
        report["errors"].append(f"XML parse error: {exc}")

    passed = report["valid_xml"] and report["root_is_svg"] and not report["errors"]
    report["passed_basic_structural_checks"] = passed

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report written to {args.json_path}")

    if not passed:
        return 1
    print("Basic SVG structure passed. Visual and scientific inspection are still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

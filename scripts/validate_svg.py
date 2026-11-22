#!/usr/bin/env python3
"""Perform basic structural checks on an SVG file; not a visual or scientific validator."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def validate(path: Path) -> dict:
    """Check standalone static SVG; no geometry or scientific correctness claim."""
    report = {"file":str(path), "valid_xml":False, "root_is_svg":False,
              "has_width":False, "has_height":False, "has_viewBox":False,
              "text_element_count":0, "external_references":[], "warnings":[], "errors":[]}
    try:
        raw=path.read_text(encoding='utf-8-sig')
        if '<!ENTITY' in raw.upper():
            raise ValueError('Entity declarations are not supported in standalone SVG')
        if re.search(r'<\?xml-stylesheet\b',raw,re.I):
            raise ValueError('External stylesheet processing instructions are not supported')
        root=ET.fromstring(raw);report['valid_xml']=True
        report['root_is_svg']=root.tag in {'svg','{http://www.w3.org/2000/svg}svg'}
        for field in ('width','height'):
            value=root.get(field,'')
            report['has_'+field]=bool(value)
            if not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)(?:px|pt|pc|mm|cm|in)?',value) or float(re.match(r'[\d.]+',value).group()) <= 0:
                report['errors'].append(f'{field} must be a positive absolute SVG length')
        viewbox=root.get('viewBox','')
        report['has_viewBox']=bool(viewbox)
        try:
            parts=[float(v) for v in re.split(r'[\s,]+',viewbox.strip())]
            import math
            if len(parts)!=4 or not all(math.isfinite(v) for v in parts) or min(parts[2:])<=0:raise ValueError()
        except ValueError:report['errors'].append('viewBox must contain four finite numbers and positive width/height')
        if not report['root_is_svg']:report['errors'].append('Root element is not an SVG element')
        for e in root.iter():
            tag=e.tag.rsplit('}',1)[-1]
            if tag=='text':report['text_element_count']+=1
            if tag in {'script','foreignObject','animate','animateTransform','animateMotion','set','discard'}:report['errors'].append(f'Active element is not allowed: {tag}')
            for key,value in e.attrib.items():
                local=key.rsplit('}',1)[-1]
                if local.lower().startswith('on'):report['errors'].append(f'Event handler is not allowed: {local}')
                if local in {'href','src'}:
                    value=value.strip()
                    if not value.startswith('#'):
                        if not re.fullmatch(r'data:image/(?:png|jpeg);base64,[A-Za-z0-9+/=\s]+',value):
                            report['external_references'].append(value)
                for target in re.findall(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)',value,re.I):
                    if not target.startswith('#'):report['external_references'].append(target)
            if tag=='style':
                css=''.join(e.itertext())
                if re.search(r'@import|expression\s*\(',css,re.I):report['errors'].append('External or executable CSS is not allowed')
                for target in re.findall(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)',css,re.I):
                    if not target.startswith('#'):report['external_references'].append(target)
        if report['external_references']:report['errors'].append('Nonlocal references found; embed permitted assets or use local fragments')
        if not report['text_element_count']:report['warnings'].append('No editable SVG text found; labels may be outlined or absent')
        if root.find('{http://www.w3.org/2000/svg}title') is None and root.find('title') is None:
            report['warnings'].append('Descriptive title is missing')
    except (OSError,ET.ParseError,ValueError) as exc:report['errors'].append(str(exc))
    report['errors']=list(dict.fromkeys(report['errors']))
    report['passed_basic_structural_checks']=report['valid_xml'] and report['root_is_svg'] and not report['errors']
    report['visual_review']='not performed by structural validator'
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="SVG file to inspect")
    parser.add_argument("--json", dest="json_path", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    if not args.svg.is_file():
        parser.error(f"SVG file not found: {args.svg}")

    report = validate(args.svg)
    passed = report['passed_basic_structural_checks']

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.json_path:
        args.json_path.parent.mkdir(parents=True,exist_ok=True)
        args.json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report written to {args.json_path}")

    if not passed:
        return 1
    print("Basic SVG structure passed. Visual and scientific inspection are still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

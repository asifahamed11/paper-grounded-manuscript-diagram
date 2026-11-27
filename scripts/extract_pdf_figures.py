#!/usr/bin/env python3
"""Extract embedded raster images and render PDF pages for figure inspection.

Requires PyMuPDF. This helper does not reliably isolate vector figures or infer
figure boundaries; rendered page images should also be inspected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return value or "paper"


def caption_candidates(page):
    """Locate figure-like captions in the text layer; a reader still checks each page."""
    pattern = re.compile(r'^(?:supplementary\s+)?fig(?:ure)?\.?\s+([A-Z]?\d+(?:\.\d+)?[a-z]?)'
                         r'(?=\s|[.:\u2013\u2014]|$)', re.IGNORECASE)
    candidates = []
    for block in page.get_text('blocks'):
        if len(block) < 7 or block[6] != 0:
            continue
        text = ' '.join(block[4].split())
        match = pattern.match(text)
        if match:
            candidates.append({
                'figure_label': match[1],
                'text_excerpt': text[:240],
                'bbox_pt': [round(coord, 2) for coord in block[:4]],
            })
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Input PDF file")
    parser.add_argument("--output-dir", type=Path, default=Path("extracted_figures"))
    parser.add_argument("--dpi", type=int, default=180, help="Page render resolution (default: 180)")
    parser.add_argument("--start-page", type=int, default=1, help="First page, 1-based")
    parser.add_argument("--end-page", type=int, default=None, help="Last page, 1-based; defaults to final page")
    parser.add_argument("--pages-only", action="store_true", help="Export full pages and candidate captions without raster fragments")
    args = parser.parse_args()

    if not args.pdf.is_file():
        parser.error(f"PDF file not found: {args.pdf}")
    if args.dpi < 72 or args.dpi > 600:
        parser.error("--dpi must be between 72 and 600")
    if args.start_page < 1:
        parser.error("--start-page must be at least 1")

    try:
        import pymupdf
    except ImportError:
        print("Missing dependency. Install with: python -m pip install PyMuPDF", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(args.pdf.stem)

    try:
        image_count = 0
        render_count = 0
        index = []
        scale = args.dpi / 72.0
        matrix = pymupdf.Matrix(scale, scale)
        with pymupdf.open(args.pdf) as document:
            total_pages = len(document)
            end_page = total_pages if args.end_page is None else args.end_page
            if end_page < args.start_page or end_page > total_pages:
                parser.error(f"Page range must be within 1..{total_pages}")

            for page_number in range(args.start_page, end_page + 1):
                page = document[page_number - 1]
                page_path = args.output_dir / f"{stem}_page_{page_number:03d}.png"
                page.get_pixmap(matrix=matrix, alpha=False).save(page_path)
                render_count += 1
                index.append({'pdf_page': page_number, 'page_image': page_path.name,
                              'caption_candidates': caption_candidates(page)})
                if args.pages_only:
                    continue

                for image_index, image_info in enumerate(page.get_images(full=True), start=1):
                    extracted = document.extract_image(image_info[0])
                    if not extracted:
                        continue
                    extension = extracted.get("ext", "bin")
                    image_path = args.output_dir / (
                        f"{stem}_page_{page_number:03d}_image_{image_index:02d}.{extension}"
                    )
                    image_path.write_bytes(extracted["image"])
                    image_count += 1
        index_path = args.output_dir / f'{stem}_figure_candidates.json'
        index_path.write_text(json.dumps({
            'pdf': args.pdf.name, 'pages': index,
            'review': 'Candidate captions from the text layer. Confirm figure identity and relevance on the full page.',
        }, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    except Exception as exc:
        print(f"Could not process PDF: {exc}", file=sys.stderr)
        return 1

    print(f"Rendered {render_count} page(s) and extracted {image_count} embedded image(s).")
    print(f"Candidate caption index: {index_path.resolve()}")
    print("Note: inspect page renders too; vector figures may not appear as embedded raster images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

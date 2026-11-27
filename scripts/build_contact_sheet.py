#!/usr/bin/env python3
"""Build a labeled contact sheet from images in a directory. Requires Pillow."""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path


SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("contact-sheet.png"))
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--pages-only", action="store_true", help="Use full-page renders produced by extract_pdf_figures.py")
    parser.add_argument("--thumb-width", type=int, default=420)
    parser.add_argument("--thumb-height", type=int, default=560)
    parser.add_argument("--label-height", type=int, default=42)
    args = parser.parse_args()

    if not args.image_dir.is_dir():
        parser.error(f"Directory not found: {args.image_dir}")
    if args.columns < 1 or min(args.thumb_width,args.thumb_height) < 100 or args.label_height < 24:
        parser.error("Columns must be >= 1, thumbnail dimensions >= 100, label height >= 24")

    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError:
        print("Missing dependency. Install with: python -m pip install Pillow", file=sys.stderr)
        return 2

    paths = sorted(p for p in args.image_dir.iterdir() if p.suffix.lower() in SUPPORTED and p.resolve()!=args.output.resolve())
    if args.pages_only:
        paths = [path for path in paths if re.search(r"_page_\d+\.png$", path.name, re.IGNORECASE)]
    if not paths:
        print(f"No supported images found in {args.image_dir}", file=sys.stderr)
        return 1

    cards = []
    for path in paths:
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                thumb = ImageOps.contain(image,(args.thumb_width,args.thumb_height),method=Image.Resampling.LANCZOS)
                cards.append((path.name, thumb.copy()))
        except Exception as exc:
            print(f"Skipping {path.name}: {exc}", file=sys.stderr)

    if not cards:
        print("No images could be opened.", file=sys.stderr)
        return 1

    card_width = args.thumb_width
    card_height = max(img.height for _, img in cards) + args.label_height
    rows = math.ceil(len(cards) / args.columns)
    canvas = Image.new("RGB", (args.columns * card_width, rows * card_height), "white")
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()

    for index, (name, image) in enumerate(cards):
        x = (index % args.columns) * card_width
        y = (index // args.columns) * card_height
        canvas.paste(image, (x, y))
        label = name if len(name) <= 52 else name[:49] + "..."
        draw.text((x + 8, y + image.height + 8), label, fill="black", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    print(f"Created contact sheet with {len(cards)} image(s): {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

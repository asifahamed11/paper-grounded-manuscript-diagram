#!/usr/bin/env python3
"""Prepare a local icon as cropped RGBA PNG, with background QA previews.

No network calls, model downloads or image generation. White mode removes only
border-connected near-white pixels; it is not a general segmentation model.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import sys


def white_cutout(image, tolerance=8):
    """Keep enclosed white details; remove the connected exterior only."""
    from PIL import Image
    width, height = image.size
    pixels = list(image.getdata())
    seen = bytearray(width * height)
    queue = deque()
    def enqueue(x, y):
        i = y * width + x
        if not seen[i] and min(pixels[i][:3]) >= 255 - tolerance:
            seen[i] = 1
            queue.append((x, y))
    border = [(x, y) for x in range(width) for y in (0, height - 1)]
    border += [(x, y) for y in range(1, height - 1) for x in (0, width - 1)]
    if sum(min(pixels[y * width + x][:3]) >= 255-tolerance for x, y in border) / len(border) < .98:
        raise ValueError('Exterior is not uniformly white; use a reviewed segmentation mask or regenerate with margin')
    for x, y in border:
        enqueue(x, y)
    while queue:
        x, y = queue.popleft()
        for X, Y in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if 0 <= X < width and 0 <= Y < height:
                enqueue(X, Y)
    result = Image.new('RGBA', image.size)
    result.putdata([(r, g, b, 0 if seen[i] else a) for i, (r, g, b, a) in enumerate(pixels)])
    return result


def solid_matte(image, foreground):
    """Recover antialiased alpha for a declared single-colour glyph on white.

    Reject pixels inconsistent with that two-colour mixture rather than
    destroying multi-colour artwork or white interior details.
    """
    from PIL import Image
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', foreground):
        raise ValueError('foreground must be #RRGGBB')
    fg = tuple(int(foreground[i:i+2], 16) for i in (1, 3, 5))
    direction = [255-c for c in fg]
    norm = sum(c*c for c in direction)
    if norm < 1000:
        raise ValueError('Foreground is too close to white for reliable matting')
    data = []
    for r, g, b, a in image.getdata():
        if a != 255:
            raise ValueError('Solid-colour white matting requires opaque input')
        alpha = max(0., min(1., sum((255-c)*d for c, d in zip((r,g,b), direction)) / norm))
        if max(abs(c-(255-alpha*d)) for c, d in zip((r,g,b), direction)) > 4:
            raise ValueError('Image is not a single-colour glyph on white; omit --foreground and use exterior/mask mode')
        data.append((*fg, round(255*alpha)))
    result = Image.new('RGBA', image.size)
    result.putdata(data)
    return result


def prepare(source, output, mode='auto', tolerance=8, padding=8, mask=None, foreground=None, unmatte_white=False):
    from PIL import Image, ImageChops, ImageOps, ImageDraw
    source, output = Path(source), Path(output)
    outputs=[output,output.with_suffix('.json'),output.with_name(output.stem+'-background-check.png')]
    if any(source.resolve()==p.resolve() or p.exists() for p in outputs):
        raise ValueError('Choose a new output PNG; source and existing outputs are preserved')
    if output.suffix.lower() != '.png':
        raise ValueError('Output must be a PNG')
    if mode not in {'auto', 'alpha', 'white'} or not 0 <= tolerance <= 32 or not 2 <= padding <= 128:
        raise ValueError('Use auto/alpha/white, tolerance 0..32 and padding 2..128 pixels')
    with Image.open(source) as original:
        if min(original.size)<2 or original.width * original.height > 16_777_216 or getattr(original, 'n_frames', 1) != 1:
            raise ValueError('Use one icon per file, no animation, maximum 16 megapixels')
        image = ImageOps.exif_transpose(original).convert('RGBA')
    alpha = image.getchannel('A')
    used_mode = 'alpha' if mode == 'auto' and alpha.getextrema()[0] < 255 else ('white' if mode == 'auto' else mode)
    warnings = []
    if mask:
        with Image.open(mask) as raw_mask:
            if raw_mask.size != image.size:
                raise ValueError('Mask dimensions must match the oriented source image')
            matte = raw_mask.getchannel('A') if raw_mask.mode == 'RGBA' else raw_mask.convert('L')
        image.putalpha(ImageChops.multiply(alpha, matte))
        used_mode = 'local-mask'
        if foreground:
            raise ValueError('--foreground cannot be combined with --mask')
    elif foreground:
        if used_mode != 'white':
            raise ValueError('--foreground is only for an opaque single-colour glyph on white')
        image = solid_matte(image, foreground)
        used_mode = 'single-colour-white-matte'
    elif used_mode == 'white':
        if alpha.getextrema() != (255, 255):
            raise ValueError('Preserve existing transparency with auto/alpha mode')
        image = white_cutout(image, tolerance)
        warnings.append('Exterior-only white removal: inspect antialias halos, near-white features and enclosed gaps; use a mask or regenerate if needed')
    if unmatte_white:
        if not mask:
            raise ValueError('--unmatte-white requires a mask for an image originally composited on white')
        pixels = []
        for r, g, b, a in image.getdata():
            pixels.append(tuple(max(0, min(255, round((c-255*(1-a/255))/(a/255)))) for c in (r,g,b)) + (a,) if a else (0,0,0,0))
        image.putdata(pixels)
    alpha = image.getchannel('A')
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError('No foreground remains; input may be blank or removal too aggressive')
    if alpha.getextrema()[0] == 255:
        raise ValueError('No transparent background; supply a cutout, white exterior or reviewed mask')
    if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == image.width or bbox[3] == image.height:
        raise ValueError('Foreground reaches the source edge; regenerate with clear margin to avoid clipping')
    cropped = image.crop(bbox)
    result = Image.new('RGBA', (cropped.width+2*padding, cropped.height+2*padding))
    result.paste(cropped, (padding, padding))
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output)
    # A white preview alone hides a bad cutout. Inspect all three at 100% and print size.
    preview = Image.new('RGB', (result.width*3, result.height), 'white')
    for i, bg in enumerate(('#FFFFFF', '#30343B', None)):
        tile = Image.new('RGBA', result.size, bg or '#D0D0D0')
        if bg is None:
            draw = ImageDraw.Draw(tile)
            for y in range(0, tile.height, 12):
                for x in range(0, tile.width, 12):
                    if (x//12+y//12)%2:
                        draw.rectangle((x,y,x+11,y+11), fill='#F0F0F0')
        preview.paste(Image.alpha_composite(tile, result).convert('RGB'), (i*result.width, 0))
    preview.save(output.with_name(output.stem+'-background-check.png'))
    report = {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(), 'mode':used_mode,
              'original_size_px':list(image.size), 'crop_bbox_px':list(bbox),
              'output_size_px':list(result.size), 'padding_px':padding, 'warnings':warnings,
              'visual_review':'pending; inspect white, dark and checkerboard preview',
              'generation':'not performed by this helper', 'model_inference':'not performed by this helper'}
    output.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['auto','alpha','white'], default='auto')
    parser.add_argument('--tolerance', type=int, default=8)
    parser.add_argument('--padding', type=int, default=8)
    parser.add_argument('--mask', type=Path)
    parser.add_argument('--foreground', help='Exact #RRGGBB, only for single-colour glyphs on white')
    parser.add_argument('--unmatte-white', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.source, args.output, args.mode, args.tolerance, args.padding,
                                 args.mask, args.foreground, args.unmatte_white), indent=2))
        return 0
    except (ValueError, OSError, ImportError) as exc:
        print(f'Cannot prepare icon: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

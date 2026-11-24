"""Pure-Vector Scientific Icon Library for Academic Figures.

Normalized on a 24x24 grid. 100% free, local, stdlib + matplotlib.
Provides:
  - 30 curated scientific icons (Data, AI/Compute, Science)
  - Direct Matplotlib vector rendering (PathPatch / Line2D)
  - Standalone SVG export & data URI for Draw.io
"""
from __future__ import annotations

import base64
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple
import xml.etree.ElementTree as ET

ICONS: Dict[str, Dict[str, Any]] = {
    # --- Data (10) ---
    'database': {
        'category': 'data',
        'paths': [
            'M 3 6 C 3 4 7 3 12 3 C 17 3 21 4 21 6 C 21 8 17 9 12 9 C 7 9 3 8 3 6 Z',
            'M 3 6 L 3 12 C 3 14 7 15 12 15 C 17 15 21 14 21 12 L 21 6',
            'M 3 12 L 3 18 C 3 20 7 21 12 21 C 17 21 21 20 21 18 L 21 12',
        ],
    },
    'table': {
        'category': 'data',
        'paths': [
            'M 3 3 H 21 V 21 H 3 Z',
            'M 3 9 H 21',
            'M 9 3 V 21',
            'M 15 3 V 21',
            'M 3 15 H 21',
        ],
    },
    'document': {
        'category': 'data',
        'paths': [
            'M 4 2 H 14 L 20 8 V 22 H 4 Z',
            'M 14 2 V 8 H 20',
            'M 8 13 H 16 M 8 17 H 14',
        ],
    },
    'documents': {
        'category': 'data',
        'paths': [
            'M 7 2 H 17 L 21 6 V 18 H 17',
            'M 3 6 H 13 L 18 11 V 22 H 3 Z',
            'M 13 6 V 11 H 18',
        ],
    },
    'folder': {
        'category': 'data',
        'paths': [
            'M 2 5 C 2 4 3 3 4 3 H 9 L 11 6 H 20 C 21 6 22 7 22 8 V 19 C 22 20 21 21 20 21 H 4 C 3 21 2 20 2 19 Z',
            'M 2 10 H 22',
        ],
    },
    'cloud': {
        'category': 'data',
        'paths': [
            'M 6.5 19 H 18 C 20.2 19 22 17.2 22 15 C 22 12.9 20.4 11.2 18.3 11 C 17.8 7.6 14.9 5 11.5 5 C 8.6 5 6.2 6.8 5.3 9.4 C 3.4 9.9 2 11.6 2 13.7 C 2 16.6 4 19 6.5 19 Z',
        ],
    },
    'globe': {
        'category': 'data',
        'paths': [
            'M 12 2 C 6.5 2 2 6.5 2 12 C 2 17.5 6.5 22 12 22 C 17.5 22 22 17.5 22 12 C 22 6.5 17.5 2 12 2 Z',
            'M 2 12 H 22',
            'M 12 2 C 8.5 2 6 6.5 6 12 C 6 17.5 8.5 22 12 22 C 15.5 22 18 17.5 18 12 C 18 6.5 15.5 2 12 2 Z',
        ],
    },
    'satellite': {
        'category': 'data',
        'paths': [
            'M 4 15 C 4 9 9 4 15 4',
            'M 12 12 L 18 6',
            'M 17 5 L 19 7',
            'M 9 15 L 6 21 M 6 18 L 10 20',
        ],
    },
    'sensor': {
        'category': 'data',
        'paths': [
            'M 12 14 V 21 M 9 21 H 15',
            'M 10.5 12.5 C 10.5 11.7 11.2 11 12 11 C 12.8 11 13.5 11.7 13.5 12.5 C 13.5 13.3 12.8 14 12 14 C 11.2 14 10.5 13.3 10.5 12.5 Z',
            'M 8 9 C 10.2 7 13.8 7 16 9',
            'M 5 6 C 8.8 3 15.2 3 19 6',
        ],
    },
    'waveform': {
        'category': 'data',
        'paths': [
            'M 2 12 H 5 L 8 4 L 12 20 L 16 8 L 19 14 H 22',
        ],
    },

    # --- AI / Compute (10) ---
    'brain': {
        'category': 'ai_compute',
        'paths': [
            'M 12 4 C 9 4 7 5.5 6 7 C 4 8 3 10.5 3 13 C 3 16 5 18.5 7.5 19 C 8.5 20.5 10 21 12 21 M 12 4 C 15 4 17 5.5 18 7 C 20 8 21 10.5 21 13 C 21 16 19 18.5 16.5 19 C 15.5 20.5 14 21 12 21 M 12 4 V 21',
            'M 6 11 C 8 11 9.5 13 12 13 C 14.5 13 16 11 18 11',
            'M 7.5 15 C 9 15 10.5 16.5 12 16.5 C 13.5 16.5 15 15 16.5 15',
        ],
    },
    'neural_net': {
        'category': 'ai_compute',
        'paths': [
            'M 4 6 L 12 4 M 4 6 L 12 12 M 4 6 L 12 20',
            'M 4 18 L 12 4 M 4 18 L 12 12 M 4 18 L 12 20',
            'M 12 4 L 20 8 M 12 4 L 20 16',
            'M 12 12 L 20 8 M 12 12 L 20 16',
            'M 12 20 L 20 8 M 12 20 L 20 16',
            'M 2.5 6 C 2.5 5.2 3.2 4.5 4 4.5 C 4.8 4.5 5.5 5.2 5.5 6 C 5.5 6.8 4.8 7.5 4 7.5 C 3.2 7.5 2.5 6.8 2.5 6 Z',
            'M 2.5 18 C 2.5 17.2 3.2 16.5 4 16.5 C 4.8 16.5 5.5 17.2 5.5 18 C 5.5 18.8 4.8 19.5 4 19.5 C 3.2 19.5 2.5 18.8 2.5 18 Z',
            'M 10.5 4 C 10.5 3.2 11.2 2.5 12 2.5 C 12.8 2.5 13.5 3.2 13.5 4 C 13.5 4.8 12.8 5.5 12 5.5 C 11.2 5.5 10.5 4.8 10.5 4 Z',
            'M 10.5 12 C 10.5 11.2 11.2 10.5 12 10.5 C 12.8 10.5 13.5 11.2 13.5 12 C 13.5 12.8 12.8 13.5 12 13.5 C 11.2 13.5 10.5 12.8 10.5 12 Z',
            'M 10.5 20 C 10.5 19.2 11.2 18.5 12 18.5 C 12.8 18.5 13.5 19.2 13.5 20 C 13.5 20.8 12.8 21.5 12 21.5 C 11.2 21.5 10.5 20.8 10.5 20 Z',
            'M 18.5 8 C 18.5 7.2 19.2 6.5 20 6.5 C 20.8 6.5 21.5 7.2 21.5 8 C 21.5 8.8 20.8 9.5 20 9.5 C 19.2 9.5 18.5 8.8 18.5 8 Z',
            'M 18.5 16 C 18.5 15.2 19.2 14.5 20 14.5 C 20.8 14.5 21.5 15.2 21.5 16 C 21.5 16.8 20.8 17.5 20 17.5 C 19.2 17.5 18.5 16.8 18.5 16 Z',
        ],
    },
    'cpu': {
        'category': 'ai_compute',
        'paths': [
            'M 6 6 H 18 V 18 H 6 Z',
            'M 9 9 H 15 V 15 H 9 Z',
            'M 9 2 V 6 M 12 2 V 6 M 15 2 V 6',
            'M 9 18 V 22 M 12 18 V 22 M 15 18 V 22',
            'M 2 9 H 6 M 2 12 H 6 M 2 15 H 6',
            'M 18 9 H 22 M 18 12 H 22 M 18 15 H 22',
        ],
    },
    'code': {
        'category': 'ai_compute',
        'paths': [
            'M 7 8 L 3 12 L 7 16',
            'M 17 8 L 21 12 L 17 16',
            'M 14 4 L 10 20',
        ],
    },
    'layers': {
        'category': 'ai_compute',
        'paths': [
            'M 12 2 L 21 7 L 12 12 L 3 7 Z',
            'M 3 12 L 12 17 L 21 12',
            'M 3 17 L 12 22 L 21 17',
        ],
    },
    'filter': {
        'category': 'ai_compute',
        'paths': [
            'M 2 4 H 22',
            'M 2 4 L 10 13 V 20 L 14 22 V 13 L 22 4',
        ],
    },
    'merge': {
        'category': 'ai_compute',
        'paths': [
            'M 4 4 C 8 8 10 12 12 14 V 21',
            'M 20 4 C 16 8 14 12 12 14',
            'M 9 18 L 12 21 L 15 18',
        ],
    },
    'split': {
        'category': 'ai_compute',
        'paths': [
            'M 12 3 V 10 C 12 12 10 16 4 20',
            'M 12 10 C 12 12 14 16 20 20',
            'M 4 16 L 4 20 L 8 20',
            'M 20 16 L 20 20 L 16 20',
        ],
    },
    'sliders': {
        'category': 'ai_compute',
        'paths': [
            'M 3 6 H 21 M 8 3 V 9',
            'M 3 12 H 21 M 16 9 V 15',
            'M 3 18 H 21 M 10 15 V 21',
        ],
    },
    'gear': {
        'category': 'ai_compute',
        'paths': [
            'M 9.5 12 C 9.5 10.6 10.6 9.5 12 9.5 C 13.4 9.5 14.5 10.6 14.5 12 C 14.5 13.4 13.4 14.5 12 14.5 C 10.6 14.5 9.5 13.4 9.5 12 Z',
            'M 11 2 H 13 L 13.5 4.5 C 14.3 4.8 15 5.3 15.7 5.9 L 18 5 L 19.4 6.4 L 18.5 8.7 C 19.1 9.4 19.5 10.1 19.8 11 L 22 11.5 V 13.5 L 19.8 14 C 19.5 14.9 19.1 15.6 18.5 16.3 L 19.4 18.6 L 18 20 L 15.7 19.1 C 15 19.7 14.3 20.2 13.5 20.5 L 13 23 H 11 L 10.5 20.5 C 9.7 20.2 9 19.7 8.3 19.1 L 6 20 L 4.6 18.6 L 5.5 16.3 C 4.9 15.6 4.5 14.9 4.2 14 L 2 13.5 V 11.5 L 4.2 11 C 4.5 10.1 4.9 9.4 5.5 8.7 L 4.6 6.4 L 6 5 L 8.3 5.9 C 9 5.3 9.7 4.8 10.5 4.5 Z',
        ],
    },

    # --- Science (10) ---
    'microscope': {
        'category': 'science',
        'paths': [
            'M 6 4 L 11 9',
            'M 10 10 L 13 13',
            'M 7 15 H 17',
            'M 11 14 H 13',
            'M 11 9 C 16 9 18 13 18 17 V 19',
            'M 5 21 H 19',
        ],
    },
    'dna': {
        'category': 'science',
        'paths': [
            'M 5 3 C 8 8 16 11 16 16 C 16 18.5 14 20.5 11 21',
            'M 19 3 C 16 8 8 11 8 16 C 8 18.5 10 20.5 13 21',
            'M 6.5 5.5 H 17.5',
            'M 8 8 H 16',
            'M 10 12 H 14',
            'M 8 16 H 16',
            'M 6.5 18.5 H 17.5',
        ],
    },
    'flask': {
        'category': 'science',
        'paths': [
            'M 9 2 H 15 M 10 2 V 7 L 4 19 C 3.5 20 4.2 21 5.3 21 H 18.7 C 19.8 21 20.5 20 20 19 L 14 7 V 2',
            'M 6.5 16 C 9 14.5 15 17.5 17.5 16',
        ],
    },
    'chart_bar': {
        'category': 'science',
        'paths': [
            'M 3 3 V 21 H 21',
            'M 6 21 V 14 H 9 V 21',
            'M 11 21 V 8 H 14 V 21',
            'M 16 21 V 4 H 19 V 21',
        ],
    },
    'chart_line': {
        'category': 'science',
        'paths': [
            'M 3 3 V 21 H 21',
            'M 4 17 L 9 11 L 14 15 L 20 5',
            'M 8 11 C 8 10.4 8.4 10 9 10 C 9.6 10 10 10.4 10 11 C 10 11.6 9.6 12 9 12 C 8.4 12 8 11.6 8 11 Z',
            'M 13 15 C 13 14.4 13.4 14 14 14 C 14.6 14 15 14.4 15 15 C 15 15.6 14.6 16 14 16 C 13.4 16 13 15.6 13 15 Z',
            'M 19 5 C 19 4.4 19.4 4 20 4 C 20.6 4 21 4.4 21 5 C 21 5.6 20.6 6 20 6 C 19.4 6 19 5.6 19 5 Z',
        ],
    },
    'search': {
        'category': 'science',
        'paths': [
            'M 10.5 3 C 6.4 3 3 6.4 3 10.5 C 3 14.6 6.4 18 10.5 18 C 14.6 18 18 14.6 18 10.5 C 18 6.4 14.6 3 10.5 3 Z',
            'M 16 16 L 21 21',
        ],
    },
    'check': {
        'category': 'science',
        'paths': [
            'M 4 12 L 9 17 L 20 6',
        ],
    },
    'alert': {
        'category': 'science',
        'paths': [
            'M 12 3 L 2 20 H 22 Z',
            'M 12 9 V 13',
            'M 12 16.5 V 17',
        ],
    },
    'shield': {
        'category': 'science',
        'paths': [
            'M 12 2 L 4 5 V 11 C 4 16.5 7.5 21 12 22 C 16.5 21 20 16.5 20 11 V 5 Z',
            'M 9 11.5 L 11 13.5 L 15 9.5',
        ],
    },
    'users': {
        'category': 'science',
        'paths': [
            'M 9 6 C 9 4.3 10.3 3 12 3 C 13.7 3 15 4.3 15 6 C 15 7.7 13.7 9 12 9 C 10.3 9 9 7.7 9 6 Z',
            'M 6 20 C 6 16.7 8.7 14 12 14 C 15.3 14 18 16.7 18 20',
            'M 17 8 C 17 6.9 17.9 6 19 6 C 20.1 6 21 6.9 21 8 C 21 9.1 20.1 10 19 10',
            'M 19 14 C 20.7 14 22 15.3 22 17',
        ],
    },
}


def parse_svg_path(d: str, scale_x: float = 1.0, scale_y: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0):
    """Parse SVG path string into Matplotlib Path transformed to target coordinates."""
    from matplotlib.path import Path
    tokens = re.findall(r'[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+)', d)
    verts: List[Tuple[float, float]] = []
    codes: List[int] = []
    i = 0
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    prev_cp_x, prev_cp_y = 0.0, 0.0
    prev_cmd = 'M'
    cmd = 'M'

    def tr(x: float, y: float) -> Tuple[float, float]:
        return offset_x + x * scale_x, offset_y + y * scale_y

    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            if i >= len(tokens) and cmd not in ('Z', 'z'):
                break
        if cmd == 'M':
            x, y = float(tokens[i]), float(tokens[i+1]); i += 2
            verts.append(tr(x, y)); codes.append(Path.MOVETO)
            cur_x, cur_y = x, y; start_x, start_y = x, y
            prev_cmd = 'M'
            cmd = 'L'
        elif cmd == 'm':
            x, y = cur_x + float(tokens[i]), cur_y + float(tokens[i+1]); i += 2
            verts.append(tr(x, y)); codes.append(Path.MOVETO)
            cur_x, cur_y = x, y; start_x, start_y = x, y
            prev_cmd = 'm'
            cmd = 'l'
        elif cmd == 'L':
            x, y = float(tokens[i]), float(tokens[i+1]); i += 2
            verts.append(tr(x, y)); codes.append(Path.LINETO)
            cur_x, cur_y = x, y
            prev_cmd = 'L'
        elif cmd == 'l':
            x, y = cur_x + float(tokens[i]), cur_y + float(tokens[i+1]); i += 2
            verts.append(tr(x, y)); codes.append(Path.LINETO)
            cur_x, cur_y = x, y
            prev_cmd = 'l'
        elif cmd == 'H':
            x = float(tokens[i]); i += 1
            verts.append(tr(x, cur_y)); codes.append(Path.LINETO)
            cur_x = x
            prev_cmd = 'H'
        elif cmd == 'h':
            x = cur_x + float(tokens[i]); i += 1
            verts.append(tr(x, cur_y)); codes.append(Path.LINETO)
            cur_x = x
            prev_cmd = 'h'
        elif cmd == 'V':
            y = float(tokens[i]); i += 1
            verts.append(tr(cur_x, y)); codes.append(Path.LINETO)
            cur_y = y
            prev_cmd = 'V'
        elif cmd == 'v':
            y = cur_y + float(tokens[i]); i += 1
            verts.append(tr(cur_x, y)); codes.append(Path.LINETO)
            cur_y = y
            prev_cmd = 'v'
        elif cmd == 'C':
            x1, y1 = float(tokens[i]), float(tokens[i+1])
            x2, y2 = float(tokens[i+2]), float(tokens[i+3])
            x, y = float(tokens[i+4]), float(tokens[i+5])
            i += 6
            verts.extend([tr(x1, y1), tr(x2, y2), tr(x, y)])
            codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])
            cur_x, cur_y = x, y
            prev_cp_x, prev_cp_y = x2, y2
            prev_cmd = 'C'
        elif cmd == 'c':
            x1, y1 = cur_x + float(tokens[i]), cur_y + float(tokens[i+1])
            x2, y2 = cur_x + float(tokens[i+2]), cur_y + float(tokens[i+3])
            x, y = cur_x + float(tokens[i+4]), cur_y + float(tokens[i+5])
            i += 6
            verts.extend([tr(x1, y1), tr(x2, y2), tr(x, y)])
            codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])
            cur_x, cur_y = x, y
            prev_cp_x, prev_cp_y = x2, y2
            prev_cmd = 'c'
        elif cmd == 'S':
            if prev_cmd in ('C', 'c', 'S', 's'):
                x1, y1 = 2 * cur_x - prev_cp_x, 2 * cur_y - prev_cp_y
            else:
                x1, y1 = cur_x, cur_y
            x2, y2 = float(tokens[i]), float(tokens[i+1])
            x, y = float(tokens[i+2]), float(tokens[i+3])
            i += 4
            verts.extend([tr(x1, y1), tr(x2, y2), tr(x, y)])
            codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])
            cur_x, cur_y = x, y
            prev_cp_x, prev_cp_y = x2, y2
            prev_cmd = 'S'
        elif cmd == 's':
            if prev_cmd in ('C', 'c', 'S', 's'):
                x1, y1 = 2 * cur_x - prev_cp_x, 2 * cur_y - prev_cp_y
            else:
                x1, y1 = cur_x, cur_y
            x2, y2 = cur_x + float(tokens[i]), cur_y + float(tokens[i+1])
            x, y = cur_x + float(tokens[i+2]), cur_y + float(tokens[i+3])
            i += 4
            verts.extend([tr(x1, y1), tr(x2, y2), tr(x, y)])
            codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])
            cur_x, cur_y = x, y
            prev_cp_x, prev_cp_y = x2, y2
            prev_cmd = 's'
        elif cmd == 'Q':
            x1, y1 = float(tokens[i]), float(tokens[i+1])
            x, y = float(tokens[i+2]), float(tokens[i+3])
            i += 4
            verts.extend([tr(x1, y1), tr(x, y)])
            codes.extend([Path.CURVE3, Path.CURVE3])
            cur_x, cur_y = x, y
            prev_cp_x, prev_cp_y = x1, y1
            prev_cmd = 'Q'
        elif cmd == 'q':
            x1, y1 = cur_x + float(tokens[i]), cur_y + float(tokens[i+1])
            x, y = cur_x + float(tokens[i+2]), cur_y + float(tokens[i+3])
            i += 4
            verts.extend([tr(x1, y1), tr(x, y)])
            codes.extend([Path.CURVE3, Path.CURVE3])
            cur_x, cur_y = x, y
            prev_cp_x, prev_cp_y = x1, y1
            prev_cmd = 'q'
        elif cmd in ('Z', 'z'):
            verts.append(tr(start_x, start_y))
            codes.append(Path.CLOSEPOLY)
            cur_x, cur_y = start_x, start_y
            prev_cmd = 'Z'
        else:
            i += 1
    return Path(verts, codes)


def get_icon(name: str) -> Dict[str, Any]:
    """Retrieve icon definition by name."""
    if name not in ICONS:
        raise ValueError(f"Unknown vector icon '{name}'. Available: {list_icons()}")
    return ICONS[name]


def list_icons() -> List[str]:
    """Return sorted list of all available icon names."""
    return sorted(ICONS.keys())


def as_svg(name: str, stroke: str = '#1B2A38', stroke_width: float = 1.75, size: int = 24) -> str:
    """Export icon as a standalone SVG string."""
    icon = get_icon(name)
    path_tags = '\n  '.join(
        f'<path d="{p}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" />'
        for p in icon['paths']
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">\n'
        f'  {path_tags}\n'
        f'</svg>'
    )


def as_data_uri(name: str, stroke: str = '#1B2A38') -> str:
    """Return base64-encoded SVG data URI for embedding in Draw.io or HTML."""
    svg_str = as_svg(name, stroke=stroke)
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('ascii')
    return f"data:image/svg+xml;base64,{b64}"


def draw_matplotlib(ax: Any, box: Tuple[float, float, float, float] | List[float], name: str,
                    color: str = '#1B2A38', line_width: float = 1.15, zorder: float = 4.0):
    """Render the vector icon onto a Matplotlib Axes inside target box [x, y, w, h]."""
    from matplotlib.patches import PathPatch
    icon = get_icon(name)
    x, y, w, h = box
    sx = w / 24.0
    sy = h / 24.0
    artists = []
    for d in icon['paths']:
        mpl_path = parse_svg_path(d, scale_x=sx, scale_y=sy, offset_x=x, offset_y=y)
        patch = PathPatch(mpl_path, facecolor='none', edgecolor=color,
                          linewidth=line_width, capstyle='round', joinstyle='round',
                          zorder=zorder)
        ax.add_patch(patch)
        artists.append(patch)
    return artists


def load_local_svg(path: str | Path) -> Dict[str, Any]:
    """Safely load and parse a local SVG icon file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"SVG icon file not found: {p}")
    text = p.read_text(encoding='utf-8')
    if re.search(r'<!(?:ENTITY|DOCTYPE[^>]*\[)', text, re.IGNORECASE):
        raise ValueError(f"SVG {p.name} contains forbidden entity/doctype declarations")
    if '<?xml-stylesheet' in text.lower():
        raise ValueError(f"SVG {p.name} contains forbidden xml-stylesheet processing instruction")
    if re.search(r'<\s*(?:script|foreignObject)\b', text, re.IGNORECASE):
        raise ValueError(f"SVG {p.name} contains forbidden script or foreignObject elements")
    if re.search(r'\bon[a-zA-Z]+\s*=', text, re.IGNORECASE):
        raise ValueError(f"SVG {p.name} contains forbidden event handler attributes")
    if re.search(r'(?:href|src|url)\s*=\s*["\']\s*(?:https?:|ftp:|data:|file:)', text, re.IGNORECASE):
        raise ValueError(f"SVG {p.name} contains forbidden external resource reference")
    if re.search(r'url\s*\(\s*["\']?\s*(?:https?:|ftp:|data:|file:)', text, re.IGNORECASE):
        raise ValueError(f"SVG {p.name} contains forbidden external URL reference")

    try:
        root_elem = ET.fromstring(text)
    except Exception as exc:
        raise ValueError(f"Invalid SVG XML in {p.name}: {exc}")

    tag = root_elem.tag.split('}')[-1].lower()
    if tag != 'svg':
        raise ValueError(f"Root element of {p.name} must be <svg>")

    vb = root_elem.attrib.get('viewBox') or root_elem.attrib.get('viewbox')
    if vb:
        nums = [float(n) for n in re.findall(r'[-+]?(?:\d*\.\d+|\d+)', vb)]
        if len(nums) == 4:
            viewbox = (nums[0], nums[1], nums[2], nums[3])
        else:
            viewbox = (0.0, 0.0, 24.0, 24.0)
    else:
        w_match = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', root_elem.attrib.get('width', '24'))
        h_match = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', root_elem.attrib.get('height', '24'))
        vw = float(w_match[0]) if w_match else 24.0
        vh = float(h_match[0]) if h_match else 24.0
        viewbox = (0.0, 0.0, vw, vh)

    elements = []
    for elem in root_elem.iter():
        elem_tag = elem.tag.split('}')[-1].lower()
        if elem_tag in ('path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'):
            elements.append((elem_tag, dict(elem.attrib)))

    return {'viewBox': viewbox, 'elements': elements, 'path': str(p)}


def draw_svg_file(ax: Any, box: Tuple[float, float, float, float] | List[float], path: str | Path,
                  color_override: str | None = None, zorder: float = 4.0):
    """Render a local SVG file into target box [x, y, w, h] preserving aspect ratio."""
    from matplotlib.patches import PathPatch, Circle, Rectangle, Ellipse, Polygon
    from matplotlib.path import Path as MplPath

    svg_data = load_local_svg(path)
    vx, vy, vw, vh = svg_data['viewBox']
    if vw <= 0 or vh <= 0:
        vw, vh = 24.0, 24.0

    target_x, target_y, target_w, target_h = box
    scale = min(target_w / vw, target_h / vh)
    fit_w = vw * scale
    fit_h = vh * scale
    offset_x = target_x + (target_w - fit_w) / 2.0 - vx * scale
    offset_y = target_y + (target_h - fit_h) / 2.0 - vy * scale

    artists = []
    default_c = color_override or '#1B2A38'

    for elem_tag, attrib in svg_data['elements']:
        fill_attr = attrib.get('fill')
        stroke_attr = attrib.get('stroke')
        lw_match = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', attrib.get('stroke-width', '1.5'))
        base_lw = float(lw_match[0]) if lw_match else 1.5
        lw = base_lw * scale

        if fill_attr in ('currentColor', 'currentcolor'):
            fill_c = default_c
        elif fill_attr in (None, 'none', ''):
            fill_c = 'none'
        else:
            fill_c = fill_attr

        if stroke_attr in ('currentColor', 'currentcolor'):
            stroke_c = default_c
        elif stroke_attr in (None, 'none', ''):
            stroke_c = 'none' if fill_c != 'none' else default_c
        else:
            stroke_c = stroke_attr

        if fill_c == 'none' and stroke_c == 'none':
            stroke_c = default_c

        if elem_tag == 'path' and 'd' in attrib:
            mpl_path = parse_svg_path(attrib['d'], scale_x=scale, scale_y=scale,
                                      offset_x=offset_x, offset_y=offset_y)
            patch = PathPatch(mpl_path, facecolor=fill_c, edgecolor=stroke_c,
                              linewidth=lw if stroke_c != 'none' else 0,
                              capstyle='round', joinstyle='round', zorder=zorder)
            ax.add_patch(patch)
            artists.append(patch)
        elif elem_tag == 'rect':
            rx_val = float(attrib.get('x', 0))
            ry_val = float(attrib.get('y', 0))
            rw_val = float(attrib.get('width', 0))
            rh_val = float(attrib.get('height', 0))
            px = offset_x + rx_val * scale
            py = offset_y + ry_val * scale
            pw = rw_val * scale
            ph = rh_val * scale
            patch = Rectangle((px, py), pw, ph, facecolor=fill_c, edgecolor=stroke_c,
                              linewidth=lw if stroke_c != 'none' else 0, zorder=zorder)
            ax.add_patch(patch)
            artists.append(patch)
        elif elem_tag == 'circle':
            cx_val = float(attrib.get('cx', 0))
            cy_val = float(attrib.get('cy', 0))
            r_val = float(attrib.get('r', 0))
            patch = Circle((offset_x + cx_val * scale, offset_y + cy_val * scale),
                           radius=r_val * scale, facecolor=fill_c, edgecolor=stroke_c,
                           linewidth=lw if stroke_c != 'none' else 0, zorder=zorder)
            ax.add_patch(patch)
            artists.append(patch)
        elif elem_tag == 'ellipse':
            cx_val = float(attrib.get('cx', 0))
            cy_val = float(attrib.get('cy', 0))
            rx_val = float(attrib.get('rx', 0))
            ry_val = float(attrib.get('ry', 0))
            patch = Ellipse((offset_x + cx_val * scale, offset_y + cy_val * scale),
                            width=2 * rx_val * scale, height=2 * ry_val * scale,
                            facecolor=fill_c, edgecolor=stroke_c,
                            linewidth=lw if stroke_c != 'none' else 0, zorder=zorder)
            ax.add_patch(patch)
            artists.append(patch)
        elif elem_tag == 'line':
            x1 = offset_x + float(attrib.get('x1', 0)) * scale
            y1 = offset_y + float(attrib.get('y1', 0)) * scale
            x2 = offset_x + float(attrib.get('x2', 0)) * scale
            y2 = offset_y + float(attrib.get('y2', 0)) * scale
            l_path = MplPath([(x1, y1), (x2, y2)], [MplPath.MOVETO, MplPath.LINETO])
            patch = PathPatch(l_path, facecolor='none', edgecolor=stroke_c,
                              linewidth=lw, capstyle='round', joinstyle='round', zorder=zorder)
            ax.add_patch(patch)
            artists.append(patch)
        elif elem_tag in ('polyline', 'polygon'):
            pts_raw = [float(n) for n in re.findall(r'[-+]?(?:\d*\.\d+|\d+)', attrib.get('points', ''))]
            if len(pts_raw) >= 4:
                coords = [(offset_x + pts_raw[k] * scale, offset_y + pts_raw[k+1] * scale)
                          for k in range(0, len(pts_raw) - 1, 2)]
                patch = Polygon(coords, closed=(elem_tag == 'polygon'),
                                facecolor=fill_c if elem_tag == 'polygon' else 'none',
                                edgecolor=stroke_c, linewidth=lw, capstyle='round',
                                joinstyle='round', zorder=zorder)
                ax.add_patch(patch)
                artists.append(patch)

    return artists

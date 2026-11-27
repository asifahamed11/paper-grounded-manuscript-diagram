"""Curated Publication Themes for Scientific & Technical Figures."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

try:
    from .node_shapes import palette_role
except ImportError:
    try:
        from scripts.node_shapes import palette_role
    except ImportError:
        from node_shapes import palette_role


THEMES: Dict[str, Dict[str, Any]] = {
    'okabe-ito': {
        'name': 'okabe-ito',
        'text_color': '#0F172A',
        'header_text_color': '#FFFFFF',
        'detail_color': '#334155',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#1E293B',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 4.5,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F8FAFC',
        'fills': {
            'process': '#FFFFFF',
            'data': '#EAF4FA',
            'input': '#F0F8FD',
            'decision': '#FEF5E6',
            'terminator': '#E6F5F0',
            'header': '#0072B2',
        },
        'strokes': {
            'process': '#475569',
            'data': '#0072B2',
            'input': '#0072B2',
            'decision': '#D55E00',
            'terminator': '#009E73',
            'header': '#0072B2',
            'group': '#64748B',
        },
        'accents': {
            'data': '#0072B2',
            'input': '#56B4E9',
            'decision': '#E69F00',
            'terminator': '#009E73',
            'process': '#0072B2',
        },
    },
    'paul-tol-muted': {
        'name': 'paul-tol-muted',
        'text_color': '#111827',
        'header_text_color': '#FFFFFF',
        'detail_color': '#374151',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#2D3748',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 4.5,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F9FAFB',
        'fills': {
            'process': '#FFFFFF',
            'data': '#EDF7FC',
            'input': '#EDF7F5',
            'decision': '#FBF8EA',
            'terminator': '#E9F4EC',
            'header': '#332288',
        },
        'strokes': {
            'process': '#4A5568',
            'data': '#332288',
            'input': '#44AA99',
            'decision': '#999933',
            'terminator': '#117733',
            'header': '#332288',
            'group': '#6B7280',
        },
        'accents': {
            'data': '#332288',
            'input': '#44AA99',
            'decision': '#CC6677',
            'terminator': '#117733',
            'process': '#882255',
        },
    },
    'paul-tol-pale': {
        'name': 'paul-tol-pale',
        'text_color': '#0F172A',
        'header_text_color': '#0F172A',
        'detail_color': '#334155',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#1E293B',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 4.0,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F8FAFC',
        'fills': {
            'process': '#FFFFFF',
            'data': '#CCEEFF',
            'input': '#AACCEE',
            'decision': '#EEEEBB',
            'terminator': '#BBDDBB',
            'header': '#AACCEE',
        },
        'strokes': {
            'process': '#475569',
            'data': '#2B6CB0',
            'input': '#334155',
            'decision': '#856404',
            'terminator': '#1E6B4B',
            'header': '#334155',
            'group': '#64748B',
        },
        'accents': {
            'data': '#2B6CB0',
            'input': '#334155',
            'decision': '#9B4D6B',
            'terminator': '#1E6B4B',
            'process': '#334155',
        },
    },
    'print-mono': {
        'name': 'print-mono',
        'text_color': '#111827',
        'header_text_color': '#FFFFFF',
        'detail_color': '#4B5563',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#111827',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 3.5,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F9FAFB',
        'fills': {
            'process': '#FFFFFF',
            'data': '#F3F4F6',
            'input': '#E5E7EB',
            'decision': '#F9FAFB',
            'terminator': '#F3F4F6',
            'header': '#111827',
        },
        'strokes': {
            'process': '#374151',
            'data': '#374151',
            'input': '#374151',
            'decision': '#111827',
            'terminator': '#374151',
            'header': '#111827',
            'group': '#6B7280',
        },
        'accents': {
            'data': '#111827',
            'input': '#374151',
            'decision': '#111827',
            'terminator': '#374151',
            'process': '#111827',
        },
    },
}

AUTO_FONTS = ['Inter', 'IBM Plex Sans', 'Liberation Sans', 'Arial', 'Helvetica', 'Segoe UI', 'DejaVu Sans']


def resolve_font(requested_font: str = 'DejaVu Sans') -> tuple[str, str]:
    """Resolve requested font or 'auto' to an installed font name and file path."""
    from matplotlib import font_manager
    if requested_font == 'auto':
        for candidate in AUTO_FONTS:
            try:
                font_path = font_manager.findfont(candidate, fallback_to_default=False)
                font_name = font_manager.FontProperties(fname=font_path).get_name()
                return font_name, font_path
            except ValueError:
                continue
        font_path = font_manager.findfont('DejaVu Sans')
        return 'DejaVu Sans', font_path
    try:
        font_path = font_manager.findfont(requested_font, fallback_to_default=False)
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        return font_name, font_path
    except ValueError:
        font_path = font_manager.findfont('DejaVu Sans')
        return 'DejaVu Sans', font_path


def apply_theme(spec: dict) -> dict:
    """Apply theme defaults to a specification copy without modifying explicit overrides."""
    if not isinstance(spec, dict):
        return spec
    resolved = deepcopy(spec)
    if not isinstance(resolved.get('style', {}), dict):
        return resolved
    style = resolved.setdefault('style', {})
    theme_name = style.get('theme')
    if not theme_name:
        return resolved
    if theme_name not in THEMES:
        valid = ', '.join(sorted(THEMES.keys()))
        raise ValueError(f"Unknown theme: {theme_name}. Valid themes: {valid}")
    theme = THEMES[theme_name]

    # Style defaults
    for key in ('connector_color', 'connector_width_pt', 'line_width_pt', 'corner_radius_pt', 'arrow_scale', 'shadow',
                'detail_color', 'detail_font_pt', 'title_detail_gap_pt'):
        if key in theme and key not in style:
            style[key] = theme[key]

    # Node defaults
    nodes = resolved.get('nodes', [])
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            shape = node.get('shape', 'process')
            if not isinstance(shape, str):
                continue
            if shape == 'group':
                if 'container_fill' not in node and 'container_fill' in theme:
                    node['container_fill'] = theme['container_fill']
                if 'stroke_color' not in node and 'group' in theme.get('strokes', {}):
                    node['stroke_color'] = theme['strokes']['group']
                if 'text_color' not in node and 'text_color' in theme:
                    node['text_color'] = theme['text_color']
            else:
                role = palette_role(shape)
                if 'fill' not in node and role in theme.get('fills', {}):
                    node['fill'] = theme['fills'][role]
                if 'stroke_color' not in node and role in theme.get('strokes', {}):
                    node['stroke_color'] = theme['strokes'][role]
                if 'text_color' not in node:
                    if shape == 'header':
                        node['text_color'] = theme.get('header_text_color', '#FFFFFF')
                    else:
                        tc = theme.get('text_color', '#111827')
                        if 'fill' in node:
                            try:
                                from .render_diagram import contrast, color
                            except Exception:
                                try:
                                    from render_diagram import contrast, color
                                except Exception:
                                    try:
                                        from scripts.render_diagram import contrast, color
                                    except Exception:
                                        contrast = color = None
                            if contrast and color:
                                try:
                                    bg_c = color(node['fill'])
                                    if contrast(color(tc), bg_c) < 4.5:
                                        tc = '#000000' if contrast(color('#000000'), bg_c) >= 4.5 else '#FFFFFF'
                                except Exception:
                                    pass
                        node['text_color'] = tc
    return resolved

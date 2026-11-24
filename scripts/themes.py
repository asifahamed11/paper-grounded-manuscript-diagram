"""Curated Publication Themes for Scientific & Technical Figures."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

THEMES: Dict[str, Dict[str, Any]] = {
    'nature-clean': {
        'name': 'nature-clean',
        'text_color': '#0F172A',
        'header_text_color': '#FFFFFF',
        'detail_color': '#475569',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#334155',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 4.5,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F8FAFC',
        'fills': {
            'process': '#FFFFFF',
            'data': '#EBF5F7',
            'input': '#F1F5F9',
            'decision': '#FEF7E6',
            'terminator': '#EAF6EE',
            'header': '#1B4965',
        },
        'strokes': {
            'process': '#94A3B8',
            'data': '#2B7A8B',
            'input': '#64748B',
            'decision': '#C27803',
            'terminator': '#1E7E5C',
            'header': '#1B4965',
            'group': '#94A3B8',
        },
        'accents': {
            'data': '#2B7A8B',
            'input': '#64748B',
            'decision': '#C27803',
            'terminator': '#1E7E5C',
            'process': '#1B4965',
        },
    },
    'ieee-crisp': {
        'name': 'ieee-crisp',
        'text_color': '#0F172A',
        'header_text_color': '#FFFFFF',
        'detail_color': '#334155',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#1E293B',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 3.5,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F8FAFC',
        'fills': {
            'process': '#FFFFFF',
            'data': '#E8F1FA',
            'input': '#F1F5F9',
            'decision': '#FEF7E0',
            'terminator': '#E8F5E9',
            'header': '#0F2942',
        },
        'strokes': {
            'process': '#334155',
            'data': '#1D4ED8',
            'input': '#4A6572',
            'decision': '#B45309',
            'terminator': '#15803D',
            'header': '#0F2942',
            'group': '#4A6572',
        },
        'accents': {
            'data': '#1D4ED8',
            'input': '#4A6572',
            'decision': '#B45309',
            'terminator': '#15803D',
            'process': '#0F2942',
        },
    },
    'neurips-soft': {
        'name': 'neurips-soft',
        'text_color': '#111827',
        'header_text_color': '#FFFFFF',
        'detail_color': '#4B5563',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#374151',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 4.5,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F8FAFC',
        'fills': {
            'process': '#FFFFFF',
            'data': '#EEF2FF',
            'input': '#F0F9FF',
            'decision': '#FEF3C7',
            'terminator': '#ECFDF5',
            'header': '#312E81',
        },
        'strokes': {
            'process': '#94A3B8',
            'data': '#4F46E5',
            'input': '#0284C7',
            'decision': '#B45309',
            'terminator': '#047857',
            'header': '#312E81',
            'group': '#94A3B8',
        },
        'accents': {
            'data': '#4F46E5',
            'input': '#0284C7',
            'decision': '#B45309',
            'terminator': '#047857',
            'process': '#4338CA',
        },
    },
    'biomed-prisma': {
        'name': 'biomed-prisma',
        'text_color': '#1E293B',
        'header_text_color': '#FFFFFF',
        'detail_color': '#475569',
        'detail_font_pt': 8.0,
        'title_detail_gap_pt': 2.2,
        'connector_color': '#475569',
        'connector_width_pt': 1.15,
        'line_width_pt': 0.85,
        'corner_radius_pt': 4.0,
        'arrow_scale': 7.0,
        'shadow': False,
        'container_fill': '#F8FAFC',
        'fills': {
            'process': '#FFFFFF',
            'data': '#EBF5FB',
            'input': '#F4F6F7',
            'decision': '#FEF5E7',
            'terminator': '#EAFAF1',
            'header': '#134E5E',
        },
        'strokes': {
            'process': '#94A3B8',
            'data': '#0284C7',
            'input': '#0D9488',
            'decision': '#EA580C',
            'terminator': '#16A34A',
            'header': '#134E5E',
            'group': '#94A3B8',
        },
        'accents': {
            'data': '#0284C7',
            'input': '#0D9488',
            'decision': '#EA580C',
            'terminator': '#16A34A',
            'process': '#134E5E',
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
            if shape == 'group':
                if 'container_fill' not in node and 'container_fill' in theme:
                    node['container_fill'] = theme['container_fill']
                if 'stroke_color' not in node and 'group' in theme.get('strokes', {}):
                    node['stroke_color'] = theme['strokes']['group']
                if 'text_color' not in node and 'text_color' in theme:
                    node['text_color'] = theme['text_color']
            else:
                if 'fill' not in node and shape in theme.get('fills', {}):
                    node['fill'] = theme['fills'][shape]
                if 'stroke_color' not in node and shape in theme.get('strokes', {}):
                    node['stroke_color'] = theme['strokes'][shape]
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

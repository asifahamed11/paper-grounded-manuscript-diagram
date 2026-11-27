#!/usr/bin/env python3
"""Make an editable first layout from explicit methods and relationships."""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from importlib.util import find_spec
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

try:
    from .render_diagram import box, color, contrast, number, render, validate_spec, wrap_label, _resolve_math, PROFILES
    from .themes import apply_theme, resolve_font, THEMES
    from .node_shapes import AUTOMATIC_SHAPES, list_shapes, palette_role, text_fractions
    from .vector_icons import list_icons, load_local_svg
except ImportError:
    try:
        from scripts.render_diagram import box, color, contrast, number, render, validate_spec, wrap_label, _resolve_math, PROFILES
        from scripts.themes import apply_theme, resolve_font, THEMES
        from scripts.node_shapes import AUTOMATIC_SHAPES, list_shapes, palette_role, text_fractions
        from scripts.vector_icons import list_icons, load_local_svg
    except ImportError:
        from render_diagram import box, color, contrast, number, render, validate_spec, wrap_label, _resolve_math, PROFILES
        from themes import apply_theme, resolve_font, THEMES
        from node_shapes import AUTOMATIC_SHAPES, list_shapes, palette_role, text_fractions
        from vector_icons import list_icons, load_local_svg


MARGIN = 9
GUTTER = 15
MIN_COLUMN = 77
INK = '#172D3C'
MUTED = '#385365'
TINTS = {'data': '#EAF4FA', 'input': '#EDF4F5', 'decision': '#FCF5E4', 'terminator': '#E9F5EF'}
ROLE_COLOURS = {'data': 'blue', 'input': 'sky_blue', 'decision': 'orange', 'terminator': 'green'}


class LabelMeasure:
    def __init__(self, family, math=False):
        import matplotlib as mpl
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        figure = Figure(dpi=144)
        self.renderer = FigureCanvasAgg(figure).get_renderer()
        self.canvas_math = math
        mpl.rcParams['mathtext.fontset'] = 'dejavusans'
        self.artist = figure.text(0, 0, '', fontfamily=family, parse_math=False, linespacing=1.13)

    def box(self, text, size, bold=False, math=None):
        resolved_text, use_math = _resolve_math(text, math, self.canvas_math)
        self.artist.set_parse_math(use_math)
        self.artist.set_text(resolved_text)
        self.artist.set_fontsize(size)
        self.artist.set_fontweight('bold' if bold else 'normal')
        extent = self.artist.get_window_extent(self.renderer)
        return extent.width / 2, extent.height / 2

    def wrapped(self, text, size, bold, width, math=None):
        resolved_text, use_math = _resolve_math(text, math, self.canvas_math)
        wrap = wrap_label(resolved_text, width, lambda line: self.box(line, size, bold, math=math)[0], math=use_math)
        w, h = self.box(wrap, size, bold, math=math)
        return len(wrap.splitlines()), w, h


def graph_rows(nodes, edges, allow_cycles=False, *, order="parent-position"):
    """Assign ranks without changing direction or adding relationships."""
    children, parents = defaultdict(list), defaultdict(list)
    for edge in edges:
        if (not isinstance(edge, dict) or not isinstance(edge.get('from'), str)
                or not isinstance(edge.get('to'), str)
                or edge['from'] not in nodes or edge['to'] not in nodes):
            raise ValueError('Every relationship must name existing from and to nodes')
        children[edge['from']].append(edge['to'])
        parents[edge['to']].append(edge['from'])

    back_edges = set()
    if allow_cycles:
        state = {n: 0 for n in nodes}
        def dfs(u):
            state[u] = 1
            for v in children[u]:
                if state[v] == 1:
                    back_edges.add((u, v))
                elif state[v] == 0:
                    dfs(v)
            state[u] = 2
        for n in nodes:
            if state[n] == 0:
                dfs(n)

    dag_parents = defaultdict(list)
    for edge in edges:
        u, v = edge['from'], edge['to']
        if (u, v) not in back_edges:
            dag_parents[v].append(u)

    active = list(nodes)
    rank = {}
    while active:
        ready = [n for n in active if all(parent in rank for parent in dag_parents[n])]
        if not ready:
            if not allow_cycles:
                raise ValueError('Automatic ranks need an acyclic workflow. Use the manual route for loops.')
            ready = [min(active, key=lambda n: sum(1 for p in dag_parents[n] if p not in rank))]
        for n in ready:
            rank[n] = max((rank[parent] + 1 for parent in dag_parents[n] if parent in rank), default=0)
        active = [n for n in active if n not in rank]
    rows = [[] for _ in range(max(rank.values()) + 1)]
    for n in nodes:
        rows[rank[n]].append(n)
    if order == "parent-position":
        for row in range(1, len(rows)):
            positions = {n: i for i, n in enumerate(rows[row - 1])}
            rows[row].sort(key=lambda n: sum(positions.get(p, 0) for p in dag_parents[n]) / max(1, len(dag_parents[n])))
    elif order != "input":
        raise ValueError('Unknown automatic row order')
    return rows, rank, parents, children


def paper_palette(node, shape):
    role = palette_role(shape)
    node.setdefault('fill', TINTS.get(role, 'white'))
    if role in ROLE_COLOURS:
        node.setdefault('stroke_color', ROLE_COLOURS[role])
    background = color(node['fill'])
    foreground = next(candidate for candidate in (INK, 'black', 'white')
                      if contrast(color(candidate), background) >= 4.5)
    node.setdefault('text_color', foreground)
    node.setdefault('bold', True)


def plan(method, asset_dir=None, theme=None, *, row_order="parent-position", skip_side="right"):
    if not isinstance(method, dict) or not isinstance(method.get('nodes'), list) or not method['nodes']:
        raise ValueError('Supply a method object with a nonempty nodes list')
    if not isinstance(method.get('edges', []), list):
        raise ValueError('edges must be a list')
    for key in ('icons', 'annotations'):
        if not isinstance(method.get(key, []), list):
            raise ValueError(f'{key} must be a list')
    spec = deepcopy(method)
    if 'icons' not in spec:
        auto_icons = []
        for n in spec.get('nodes', []):
            if isinstance(n, dict) and n.get('vector_icon'):
                auto_icons.append({'id': f"ic-{n['id']}", 'node': n['id'], 'vector_icon': n['vector_icon'], 'size_pt': n.get('icon_size_pt', [16, 16])})
        if auto_icons:
            spec['icons'] = auto_icons
    if theme and 'theme' not in spec.get('style', {}):
        spec.setdefault('style', {})['theme'] = theme
    spec = apply_theme(spec)
    canvas = spec.setdefault('canvas', {})
    if not isinstance(canvas, dict):
        raise ValueError('canvas must be an object')
    width = number(canvas.get('width_pt', 360), 'canvas.width_pt')
    size = number(canvas.get('font_pt', 9), 'canvas.font_pt')
    if width < 130 or size < 6:
        raise ValueError('Automatic layouts need at least 130 pt of width and readable text')
    canvas.update(width_pt=width, font_pt=size)
    style = spec.setdefault('style', {})
    if not isinstance(style, dict):
        raise ValueError('style must be an object')
    for key, value in {'stroke_color': '#879AA6', 'connector_color': '#465D6C',
                       'line_width_pt': .8, 'title_detail_gap_pt': 3.2}.items():
        style.setdefault(key, value)
    detail_gap = number(style['title_detail_gap_pt'], 'style.title_detail_gap_pt')
    font_family = canvas.get('font_family', 'DejaVu Sans')
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError('canvas.font_family must be a nonempty font family')
    resolved_family, _ = resolve_font(font_family)
    measure = LabelMeasure(resolved_family, math=canvas.get('math', False))
    nodes = {}
    for node in spec['nodes']:
        if (not isinstance(node, dict) or not isinstance(node.get('id'), str) or not node['id'].strip()
                or not isinstance(node.get('label'), str) or not node['label'].strip()):
            raise ValueError('Every node needs a text id and label')
        if node['id'] in nodes:
            raise ValueError(f'Duplicate node id: {node["id"]}')
        shape = node.get('shape', 'process')
        if shape not in AUTOMATIC_SHAPES:
            raise ValueError('Use a shape supported by the automatic layout. Run --list-shapes for options.')
        if 'detail' in node and (not isinstance(node['detail'], str) or not node['detail'].strip()):
            raise ValueError(f'Node {node["id"]} detail must be text')
        paper_palette(node, shape)
        nodes[node['id']] = node
    edges = spec.get('edges', [])
    rows, rank, parents, children = graph_rows(nodes, edges, allow_cycles=True, order=row_order)
    # Lanes are optional. They pin related method stages to a shared column.
    lanes = spec.pop('lanes', [])
    if (not isinstance(lanes, list) or any(not isinstance(lane, str) or not lane.strip() for lane in lanes)
            or len(set(lanes)) != len(lanes)):
        raise ValueError('lanes must be a list of unique names')
    if lanes:
        col = {n: node.get('lane') for n, node in nodes.items()}
        if any(name not in lanes for name in col.values()):
            raise ValueError('When lanes are supplied, every node must name a lane')
        if any(len({col[n] for n in row}) != len(row) for row in rows):
            raise ValueError('Two nodes share a lane at the same rank. Assign another lane or edit the manual layout.')
    else:
        col = {}
    count = len(lanes) or max(map(len, rows))
    slot_width = (width - 2 * MARGIN - (count - 1) * GUTTER) / count
    direction = spec.pop('direction', 'auto')
    if direction not in ('auto', 'vertical', 'horizontal'):
        raise ValueError('direction must be auto, vertical or horizontal')

    has_edge_labels = any(e.get('label') for e in edges)
    max_label_w = 0.0
    if has_edge_labels:
        max_label_w = max((measure.box(e['label'], max(8.5, size - 0.5), math=e.get('math'))[0] for e in edges if e.get('label')), default=0.0)
    horiz_gutter = max(GUTTER, max_label_w + 14.0) if max_label_w > 0 else GUTTER
    horiz_col_width = (width - 2 * MARGIN - horiz_gutter * (len(rows) - 1)) / max(1, len(rows))

    can_use_horizontal = (not lanes and 2 <= len(rows) <= 5 and horiz_col_width >= 65
                          and not spec.get('annotations'))
    if can_use_horizontal:
        for node in nodes.values():
            pad = number(node.get('padding_pt', 5), 'node padding')
            shape = node.get('shape', 'process')
            width_fraction = text_fractions(shape)[2]
            label_space = horiz_col_width * width_fraction - 2 * max(10, pad)
            if shape == 'decision':
                label_space = horiz_col_width / 2 - 2 * pad
            line_counts = []
            for field, font_size in [('label', node.get('font_pt',size)), ('detail', node.get('detail_font_pt',size))]:
                value = node.get(field, '')
                if not value.strip():
                    continue
                lines, measured, _ = measure.wrapped(value, number(font_size,'node font size'), field=='label', label_space,
                                                    math=node.get('math'))
                if measured > label_space:
                    can_use_horizontal = False
                line_counts.append(lines)
            if any(lines > 2 for lines in line_counts) or sum(line_counts) > 4:
                can_use_horizontal = False

    if direction == 'horizontal' and not can_use_horizontal:
        raise ValueError('This method needs a vertical layout or explicit routes. Check columns, labels and lanes.')

    if direction == 'horizontal':
        horizontal = can_use_horizontal
    elif direction == 'auto':
        horizontal = can_use_horizontal and not spec.get('icons') and not has_edge_labels
    else:
        horizontal = False

    if horizontal:
        column_width = horiz_col_width
    else:
        column_width = (width - 2 * MARGIN - GUTTER * (len(rows) - 1)) / max(1, len(rows))

    if not horizontal and slot_width < MIN_COLUMN and count > 1:
        raise ValueError('This rank is too wide for readable parallel columns. Use a wider figure or split the workflow.')
    asset_root = Path(asset_dir or '.').resolve()
    icons_by_node = {}
    for icon in spec.get('icons', []):
        owner = icon.get('node') if isinstance(icon, dict) else None
        if isinstance(owner, str):
            if 'id' not in icon:
                icon['id'] = f"icon-{owner}"
            if 'alt' not in icon:
                vname = icon.get('vector_icon', 'icon')
                icon['alt'] = f"{vname} icon for {owner}"
        if not isinstance(owner, str) or owner not in nodes or owner in icons_by_node:
            raise ValueError('The automatic layout accepts one local icon per named node')
        if icon.get('vector_icon'):
            vname = icon['vector_icon']
            if not isinstance(vname, str) or vname not in list_icons():
                raise ValueError(f"Unknown vector icon '{vname}'. Available: {list_icons()}")
            requested = icon.get('size_pt', [16, 16])
            if not isinstance(requested, list) or len(requested) != 2:
                raise ValueError('Icon size_pt needs [width, height]')
            iw = number(requested[0], 'icon width')
            ih = number(requested[1], 'icon height')
            if iw <= 0 or ih <= 0:
                raise ValueError('Icon dimensions must be positive')
            icons_by_node[owner] = (icon, iw, ih)
        else:
            name = icon.get('path')
            if (not isinstance(name, str) or '\\' in name or ':' in name or name.startswith('/')
                    or '..' in Path(name).parts or Path(name).suffix.lower() not in ('.png', '.svg')):
                raise ValueError('A planned icon needs a relative PNG or SVG path')
            path = (asset_root / name).resolve()
            if not path.is_relative_to(asset_root):
                raise ValueError('Icon must be inside the method specification directory')
            requested = icon.get('size_pt', [16, 16])
            if not isinstance(requested, list) or len(requested) != 2:
                raise ValueError('Icon size_pt needs [width, height]')
            req_w = number(requested[0], 'icon width')
            req_h = number(requested[1], 'icon height')
            if req_w <= 0 or req_h <= 0:
                raise ValueError('Icon dimensions must be positive')
            if Path(name).suffix.lower() == '.svg':
                svg_data = load_local_svg(path)
                vw, vh = svg_data['viewBox'][2], svg_data['viewBox'][3]
                if vw <= 0 or vh <= 0:
                    vw, vh = 24.0, 24.0
                fit = min(req_w / vw, req_h / vh)
                icons_by_node[owner] = (icon, vw * fit, vh * fit)
            else:
                from PIL import Image
                with Image.open(path) as image:
                    nat_w, nat_h = image.size
                fit = min(req_w / nat_w, req_h / nat_h)
                icons_by_node[owner] = (icon, nat_w * fit, nat_h * fit)
    planned_icons = []
    for row in rows:
        for identifier in row:
            node = nodes[identifier]
            shape = node.get('shape', 'process')
            pad = number(node.get('padding_pt', 5), 'node padding')
            side = max(pad, 10 if shape == 'input' else 7 if shape == 'data' else pad)
            top = max(pad, 8 if shape == 'data' else pad)
            node_size = number(node.get('font_pt', size), 'node font size')
            detail_size = number(node.get('detail_font_pt', size), 'detail font size')
            max_width = slot_width if lanes or len(row) > 1 else min(width - 2 * MARGIN, slot_width * 1.4)
            _, _, width_fraction, height_fraction = text_fractions(shape)
            if shape == 'decision':
                width_fraction = height_fraction = .5
            min_width = 32 if shape == 'operator' else MIN_COLUMN
            natural = max(measure.box(node['label'], node_size, node.get('bold', True), math=node.get('math'))[0],
                          measure.box(node.get('detail',''), detail_size, math=node.get('math'))[0])
            if horizontal:
                max_width = column_width
            box_width = min(max_width, max(min_width, (natural + 2 * side + 14) / width_fraction))
            if (horizontal and shape != 'operator') or (lanes and shape not in ('decision', 'operator')):
                box_width = max_width
            icon_data = icons_by_node.get(identifier)
            if icon_data:
                box_width = min(max_width, max(box_width, natural + 2 * side + 9 + icon_data[1]))
            inner = box_width * width_fraction - side * 2
            if inner <= 0:
                raise ValueError(f'Node {identifier} is too narrow for its shape and padding')
            choices = ('none',) if not icon_data else ('title', 'left', 'top')
            if icon_data and shape not in ('process', 'terminator'):
                choices = ('title',)
            if icon_data and icon_data[0].get('placement') in ('title','left','right','top'):
                choices = (icon_data[0]['placement'],)
            iw, ih = icon_data[1:] if icon_data else (0, 0)
            scored = []
            for position in choices:
                reserve = iw + 8 if position in ('left','right') else 0
                title_width = inner - reserve - (iw + 4 if position == 'title' else 0)
                detail_width = inner - reserve
                if min(title_width, detail_width) <= 0:
                    continue
                title_lines, title_w, title_h = measure.wrapped(node['label'], node_size,
                                                               node.get('bold', True), title_width,
                                                               math=node.get('math'))
                detail_lines, detail_w, detail_h = 0, 0, 0
                if 'detail' in node:
                    detail_lines, detail_w, detail_h = measure.wrapped(node['detail'], detail_size, False, detail_width,
                                                                       math=node.get('math'))
                if title_w > title_width or detail_w > detail_width:
                    continue
                body_h = (max(title_h, ih) if position == 'title' else title_h)
                body_h += detail_gap + detail_h if 'detail' in node else 0
                if position == 'top':
                    body_h += ih + 8
                if position in ('left','right'):
                    body_h = max(body_h, ih)
                height = max(25, (body_h + top + pad + 4) / height_fraction)
                if shape == 'operator':
                    height = max(height, box_width)
                    if height > max_width:
                        continue
                scored.append({'placement': position, 'height_pt': round(height, 2),
                               'title_lines': title_lines, 'detail_lines': detail_lines})
            if not scored:
                raise ValueError(f'Node {identifier} has text that does not fit at the requested width')
            winner = min(scored, key=lambda c: (c['detail_lines'] + c['title_lines'], c['height_pt']))
            final_width = winner['height_pt'] if shape == 'operator' else box_width
            node['box'] = [0, 0, final_width, winner['height_pt']]
            if icon_data:
                planned_icons.append({'node': identifier, 'choice': winner['placement'], 'candidates': scored})
    feedback_edges = [edge for edge in edges if rank[edge['to']] <= rank[edge['from']]]
    skip_edges = [edge for edge in edges if rank[edge['to']] - rank[edge['from']] > 1]
    adjacent_edges = [edge for edge in edges if rank[edge['to']] - rank[edge['from']] == 1]
    if feedback_edges:
        spec.setdefault('layout_plan', {})['feedback_edges'] = [e.get('id', f"{e['from']}->{e['to']}") for e in feedback_edges]
    next_top = MARGIN
    notes = []
    for index, row in enumerate(rows):
        if horizontal:
            col_height = sum(nodes[n]['box'][3] for n in row) + GUTTER * (len(row) - 1)
            if index == 0:
                stacks = (sum(nodes[n]['box'][3] for n in r) + GUTTER * (len(r)-1) for r in rows)
                main_height = max(stacks)
            y = MARGIN + (main_height - col_height) / 2
            for identifier in row:
                bounds = nodes[identifier]['box']
                x_offset = (column_width - bounds[2]) / 2
                bounds[:2] = [MARGIN + index * (column_width + horiz_gutter) + x_offset, y]
                y += bounds[3] + GUTTER
            next_top = main_height + MARGIN
            continue
        height = max(nodes[n]['box'][3] for n in row)
        for position, identifier in enumerate(row):
            bounds = nodes[identifier]['box']
            cx = (MARGIN + slot_width / 2 + lanes.index(col[identifier]) * (slot_width + GUTTER)
                  if lanes else width * (position + .5) / len(row))
            bounds[0] = cx - bounds[2] / 2
            bounds[1] = next_top + (height - bounds[3]) / 2
        outgoing = [edge for edge in edges if rank[edge['from']] == index]
        labelled_edges = [edge for edge in outgoing if edge.get('label')]
        if labelled_edges:
            max_note_h = max(measure.box(edge['label'], max(8.5, size - .5), math=edge.get('math'))[1] + 3
                             for edge in labelled_edges)
            corridor = max(28, round(2 * (max_note_h + 7), 2))
        else:
            corridor = 15
        next_top += height + (corridor if index < len(rows) - 1 else 0)
    for selection in planned_icons:
        identifier, mode = selection['node'], selection['choice']
        node = nodes[identifier]
        icon, iw, ih = icons_by_node[identifier]
        x, y, w, h = node['box']
        icon.update(placement=mode)
        if mode == 'title':
            icon.pop('box', None)
            icon['size_pt'] = [iw, ih]
        else:
            icon.pop('size_pt', None)
            node['icon_space_pt'] = (ih if mode == 'top' else iw) + 8
            ix = x + (w - iw) / 2 if mode == 'top' else x + 4 if mode == 'left' else x + w - iw - 4
            iy = y + 4 if mode == 'top' else y + (h - ih) / 2
            icon['box'] = [ix, iy, iw, ih]

    if horizontal:
        max_b = max(nodes[n]['box'][1] + nodes[n]['box'][3] for n in nodes)
        for s_idx, edge in enumerate(skip_edges):
            u, v = edge['from'], edge['to']
            ux, uy, uw, uh = nodes[u]['box']
            vx, vy, vw, vh = nodes[v]['box']
            track_y = max_b + 12.0 + s_idx * 8.0
            edge['points'] = [[ux + uw / 2, uy + uh], [ux + uw / 2, track_y], [vx + vw / 2, track_y], [vx + vw / 2, vy + vh]]
            edge.setdefault('arrow', 'end')
        min_t = min(nodes[n]['box'][1] for n in nodes)
        for l_idx, edge in enumerate(feedback_edges):
            u, v = edge['from'], edge['to']
            ux, uy, uw, uh = nodes[u]['box']
            vx, vy, vw, vh = nodes[v]['box']
            track_y = min_t - 12.0 - l_idx * 8.0
            if track_y < MARGIN:
                shift_y = MARGIN - track_y
                for n in nodes.values():
                    n['box'][1] += shift_y
                for icon_info in spec.get('icons', []):
                    if 'box' in icon_info:
                        icon_info['box'][1] += shift_y
                min_t += shift_y
                track_y = MARGIN
            edge['points'] = [[ux + uw / 2, uy], [ux + uw / 2, track_y], [vx + vw / 2, track_y], [vx + vw / 2, vy]]
            edge.setdefault('style', 'dashed')
            edge.setdefault('arrow', 'end')
            edge.setdefault('meaning', 'Feedback iteration' if not edge.get('label') else edge.get('label'))
        for edge in adjacent_edges:
            start, finish = edge['from'], edge['to']
            x, y, w, h = nodes[start]['box']
            dx, dy, dw, dh = nodes[finish]['box']
            exits = sorted(children[start], key=lambda name: nodes[name]['box'][1])
            entries = sorted(parents[finish], key=lambda name: nodes[name]['box'][1])
            sy = round(port_coordinate(nodes, start, finish, exits, 1), 5)
            ty = round(port_coordinate(nodes, finish, start, entries, 1), 5)
            mid = (x+w+dx) / 2
            edge['points'] = ([[x+w,sy],[dx,sy]] if abs(sy-ty) < .2
                              else [[x+w,sy],[mid,sy],[mid,ty],[dx,ty]])
    else:
        min_l = min(nodes[n]['box'][0] for n in nodes)
        for l_idx, edge in enumerate(feedback_edges):
            edge_lbl = edge.get('label')
            note_w = measure.box(edge_lbl, size, math=edge.get('math'))[0] + 6.0 if edge_lbl else 0.0
            corridor_w = max(14.0, note_w + 10.0)
            track_x = min_l - corridor_w - l_idx * 10.0
            if track_x < MARGIN:
                shift_x = MARGIN - track_x
                for n in nodes.values():
                    n['box'][0] += shift_x
                for icon_info in spec.get('icons', []):
                    if 'box' in icon_info:
                        icon_info['box'][0] += shift_x
                min_l += shift_x
                track_x = MARGIN
                width += shift_x
                canvas['width_pt'] = width
            u, v = edge['from'], edge['to']
            ux, uy, uw, uh = nodes[u]['box']
            vx, vy, vw, vh = nodes[v]['box']
            edge['points'] = [[ux, uy + uh / 2], [track_x, uy + uh / 2], [track_x, vy + vh / 2], [vx, vy + vh / 2]]
            edge.setdefault('style', 'dashed')
            edge.setdefault('arrow', 'end')
            edge.setdefault('meaning', 'Feedback iteration' if not edge.get('label') else edge.get('label'))
            if edge.get('label'):
                edge_label = edge.pop('label')
                notes.append(branch_note(edge_label, track_x, (uy + uh / 2 + vy + vh / 2) / 2, size, width, measure, math=edge.get('math'), avoid_x=track_x))
        max_r = max(nodes[n]['box'][0] + nodes[n]['box'][2] for n in nodes)
        use_left = skip_side == 'left' and not feedback_edges
        for s_idx, edge in enumerate(skip_edges):
            edge_lbl = edge.get('label')
            note_w = measure.box(edge_lbl, size, math=edge.get('math'))[0] + 6.0 if edge_lbl else 0.0
            corridor_w = max(14.0, note_w + 10.0)
            if use_left:
                track_x = min_l - corridor_w - s_idx * 10.0
                if track_x < MARGIN:
                    shift = MARGIN - track_x
                    for node in nodes.values():
                        node['box'][0] += shift
                    for icon in spec.get('icons', []):
                        if 'box' in icon:
                            icon['box'][0] += shift
                    for edge_routed in skip_edges[:s_idx]:
                        for point in edge_routed['points']:
                            point[0] += shift
                    for note in notes:
                        note['box'][0] += shift
                    min_l += shift
                    width += shift
                    canvas['width_pt'] = width
                    track_x = MARGIN
            else:
                track_x = max_r + corridor_w + s_idx * 10.0
                if track_x + MARGIN > width:
                    width = track_x + MARGIN
                    canvas['width_pt'] = width
            u, v = edge['from'], edge['to']
            ux, uy, uw, uh = nodes[u]['box']
            vx, vy, vw, vh = nodes[v]['box']
            source_x = ux if use_left else ux + uw
            target_x = vx if use_left else vx + vw
            edge['points'] = [[source_x, uy + uh / 2], [track_x, uy + uh / 2],
                              [track_x, vy + vh / 2], [target_x, vy + vh / 2]]
            edge.setdefault('arrow', 'end')
            if edge_lbl:
                edge_label = edge.pop('label')
                notes.append(branch_note(edge_label, track_x, (uy + uh / 2 + vy + vh / 2) / 2, size, width, measure, math=edge.get('math'), avoid_x=track_x))
        for edge in adjacent_edges:
            start, finish = edge['from'], edge['to']
            x, y, w, h = nodes[start]['box']
            dx, dy, dw, dh = nodes[finish]['box']
            exits = sorted(children[start], key=lambda name: nodes[name]['box'][0])
            entries = sorted(parents[finish], key=lambda name: nodes[name]['box'][0])
            sx = port_coordinate(nodes, start, finish, exits, 0)
            tx = port_coordinate(nodes, finish, start, entries, 0)
            sx, tx = round(sx,5), round(tx,5)
            if nodes[start].get('shape') == 'decision' and tx > x + w + 12 and len(rows[rank[start]]) <= 2:
                blocked = any(n != start and x < nodes[n]['box'][0] < tx for n in rows[rank[start]])
                if not blocked:
                    edge['points'] = [[x+w, y+h/2], [tx, y+h/2], [tx, dy]]
                    edge_label = edge.pop('label', None)
                    if edge_label:
                        edge_math = edge.get('math')
                        note_size = max(8.5, size - .5)
                        nw, nh = measure.box(edge_label, note_size, math=edge_math)
                        bh = nh + 3
                        note_y = (y + h / 2) - 3.5 - bh / 2
                        notes.append(branch_note(edge_label, (x + w + tx) / 2, note_y, size, width, measure,
                                                 math=edge_math, avoid_x=tx))
                    continue
            if abs(sx - tx) < .2:
                tx = sx
            corridor_y = (y+h+dy) / 2
            edge['points'] = [[sx, y+h], [tx, dy]] if sx == tx else [[sx,y+h],[sx,corridor_y],[tx,corridor_y],[tx,dy]]
            edge_label = edge.pop('label', None)
            if edge_label:
                edge_math = edge.get('math')
                note_size = max(8.5, size - .5)
                nw, nh = measure.box(edge_label, note_size, math=edge_math)
                bw, bh = nw + 4, nh + 3
                note_y = corridor_y - 3.5 - bh / 2
                if abs(sx - tx) < bw + 7:
                    if max(sx, tx) + 3.5 + bw <= width - MARGIN:
                        note_x = max(sx, tx) + 3.5 + bw / 2
                    else:
                        note_x = min(sx, tx) - 3.5 - bw / 2
                else:
                    note_x = (sx + tx) / 2
                notes.append(branch_note(edge_label, note_x, note_y, size, width, measure,
                                         math=edge_math, avoid_x=sx, sx=sx, tx=tx))
    all_x = [n['box'][0] + n['box'][2] for n in nodes.values()] + [p[0] for e in edges for p in e.get('points', [])]
    if max(all_x) + MARGIN > width:
        canvas['width_pt'] = round(max(all_x) + MARGIN, 3)
    all_y = [n['box'][1] + n['box'][3] for n in nodes.values()] + [p[1] for e in edges for p in e.get('points', [])]
    next_top = max(next_top, max(all_y) + MARGIN)
    notes.extend(spec.get('annotations', []))
    if notes:
        spec['annotations'] = notes
        if any(not isinstance(note, dict) for note in notes):
            raise ValueError('Annotations must be objects')
        next_top = max(next_top, max(y+h for _,y,_,h in (box(n.get('box'), 'note') for n in notes)))
    canvas['height_pt'] = round(next_top + MARGIN + .001, 3)
    layout_plan = spec.setdefault('layout_plan', {})
    layout_plan.update({'method': 'layered', 'reading_direction': 'horizontal' if horizontal else 'vertical',
                        'ranks': rows, 'lanes': lanes, 'icon_choices': planned_icons})
    return validate_spec(spec)


def branch_note(label, x, y, base, width, measure, *, math=None, avoid_x=None, sx=None, tx=None):
    if not isinstance(label, str) or not label.strip():
        raise ValueError('A branch label must be text')
    size = max(8.5, base - .5)
    label_width, label_height = measure.box(label, size, math=math)
    w, h = label_width + 4, label_height + 3
    clearance = 3.5
    left = x - w / 2
    left = max(MARGIN, min(left, width - MARGIN - w))

    if sx is not None and tx is not None:
        if abs(sx - tx) >= w + 2 * clearance:
            if sx < tx:
                left = max(left, sx + clearance)
                left = min(left, tx - clearance - w)
            else:
                left = min(left, sx - clearance - w)
                left = max(left, tx + clearance)
        else:
            if left <= sx <= left + w:
                if sx + clearance + w <= width - MARGIN:
                    left = sx + clearance
                else:
                    left = sx - clearance - w
    elif avoid_x is not None:
        if left <= avoid_x <= left + w:
            if avoid_x + clearance + w <= width - MARGIN:
                left = avoid_x + clearance
            else:
                left = avoid_x - clearance - w

    note = {'label': label, 'box': [round(left, 3), round(y - h / 2, 3), round(w, 3), round(h, 3)],
            'font_pt': size, 'padding_pt': 1, 'text_color': MUTED}
    if math:
        note['math'] = True
    return note


def port_coordinate(nodes, owner, peer, neighbours, axis):
    origin = nodes[owner]['box'][axis]
    size = nodes[owner]['box'][axis+2]
    centre = origin + size / 2
    other = nodes[peer]['box']
    peer_centre = other[axis] + other[axis+2] / 2
    if len(neighbours) == 1 or abs(centre - peer_centre) < .2:
        return centre
    return origin + size * (.17 + .66 * (neighbours.index(peer) + .5) / len(neighbours))


def choose_layout(method, asset_dir=None, *, dpi=600, theme=None, profile=None, fixed_width=False):
    """Try bounded layout variants, preserving relationships and explicit direction or lanes."""
    if not isinstance(method, dict):
        raise ValueError('The method file must contain a JSON object')
    canvas = method.get('canvas', {})
    if not isinstance(canvas, dict):
        raise ValueError('canvas must be an object')
    requested = method.get('direction', 'auto')
    width = number(canvas.get('width_pt', 360), 'canvas.width_pt') if fixed_width else None
    variants = [('default', 'parent-position', requested, 'right')]
    if not method.get('lanes'):
        variants.append(('input-order', 'input', requested, 'right'))
    if requested in ('auto', 'vertical'):
        variants.append(('left-skip-corridor', 'parent-position', 'vertical', 'left'))
    if requested == 'auto':
        variants.extend((direction, 'parent-position', direction, 'right') for direction in ('vertical', 'horizontal'))

    attempts = []
    first_renderable = None
    seen = set()
    with TemporaryDirectory(prefix='diagram-layout-') as scratch:
        for strategy, order, direction, side in variants:
            try:
                candidate = plan({**method, 'direction': direction}, asset_dir, theme,
                                 row_order=order, skip_side=side)
            except ValueError as error:
                attempts.append({'strategy': strategy, 'passed': False, 'errors': [str(error)]})
                continue
            signature = json.dumps([candidate['nodes'], candidate.get('edges', []),
                                    candidate.get('annotations', []), candidate['canvas']], sort_keys=True)
            if signature in seen:
                continue
            seen.add(signature)
            actual_width = candidate['canvas']['width_pt']
            if width is not None and actual_width > width + 1e-6:
                attempts.append({'strategy': strategy, 'passed': False, 'width_pt': actual_width,
                                 'errors': [f'Layout exceeded the fixed {width:g} pt width.']})
                continue
            if first_renderable is None:
                first_renderable = candidate
            report = render(candidate, scratch, 'layout', dpi=dpi, asset_dir=asset_dir,
                            preview_only=True, profile=profile, theme=theme)
            attempts.append({'strategy': strategy, 'passed': report['passed_geometry_checks'],
                             'width_pt': actual_width, 'errors': report['errors']})
            if report['passed_geometry_checks']:
                candidate['layout_plan'].update(selected_strategy=strategy, attempts=attempts)
                return candidate

    if first_renderable is None:
        detail = attempts[0]['errors'][0] if attempts else 'No layout candidate was built.'
        raise ValueError(f'{detail} Use the explicit layout for related panels or re-route the connections.')
    first_renderable['layout_plan'].update(
        selected_strategy=None, attempts=attempts,
        next_step='Inspect the diagnostic and attempt JSON. Keep all important relationships, then re-route or split into panels.'
    )
    return first_renderable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('method', nargs='?', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('diagram-output'))
    parser.add_argument('--stem', default='method')
    parser.add_argument('--dpi', type=int, default=600)
    parser.add_argument('--preview-only', action='store_true')
    parser.add_argument('--drawio', action='store_true')
    parser.add_argument('--tiff', action='store_true')
    parser.add_argument('--eps', action='store_true', help='Export vector EPS format')
    parser.add_argument('--profile', choices=tuple(PROFILES.keys()), help='Export profile constraints')
    parser.add_argument('--theme', choices=tuple(THEMES.keys()), help='Publication theme')
    parser.add_argument('--list-icons', action='store_true', help='List available vector icons')
    parser.add_argument('--list-shapes', action='store_true', help='List shapes for automatic layouts')
    parser.add_argument('--require-sources', action='store_true')
    parser.add_argument('--require-paper-figures', action='store_true',
                        help='Require distinct paper figure records (default minimum: 5)')
    parser.add_argument('--min-paper-figures', type=int, default=5,
                        help='Minimum distinct paper figure records (default: 5)')
    parser.add_argument('--require-design-review', action='store_true')
    parser.add_argument('--require-shape-review', action='store_true',
                        help='Require shape inventories and mapped choices for the method nodes')
    parser.add_argument('--fixed-width', action='store_true', help='Reject layouts wider than the requested canvas')
    parser.add_argument('--doctor', action='store_true', help='Check which local tools are installed')
    args = parser.parse_args()
    if args.list_icons:
        for name in list_icons():
            print(name)
        return 0
    if args.list_shapes:
        descriptions = list_shapes()
        for key in AUTOMATIC_SHAPES:
            print(f'{key}: {descriptions[key]}')
        return 0
    if args.doctor:
        packages = {name: find_spec(module) is not None for name, module in
                    [('matplotlib','matplotlib'), ('Pillow','PIL'), ('PyMuPDF','pymupdf')]}
        print(json.dumps({'local_packages': packages, 'render_available': packages['matplotlib'] and packages['Pillow'],
                          'setup': 'python -m pip install -r requirements-render.txt'}, indent=2))
        return 0 if packages['matplotlib'] and packages['Pillow'] else 2
    if args.method is None:
        parser.error('supply a method JSON or use --doctor')
    try:
        def build():
            source = json.loads(args.method.read_text(encoding='utf-8-sig'))
            return choose_layout(source, args.method.parent, dpi=args.dpi, theme=args.theme,
                                 profile=args.profile, fixed_width=args.fixed_width)
        report = render(build, args.output_dir, stem=args.stem, dpi=args.dpi,
                        asset_dir=args.method.parent, preview_only=args.preview_only, drawio=args.drawio,
                        tiff=args.tiff, profile=args.profile, require_sources=args.require_sources,
                        require_paper_figures=args.require_paper_figures,
                        min_paper_figures=args.min_paper_figures,
                        require_design_review=args.require_design_review,
                        require_shape_review=args.require_shape_review,
                        eps=args.eps, theme=args.theme)
        print(json.dumps({'status': report['status'], 'exports': report['exports'], 'errors': report['errors'],
                          'layout_plan': report.get('layout_plan')}, indent=2))
        return 0 if report['passed_geometry_checks'] else 1
    except (ValueError, OSError, ImportError) as error:
        print(f'Cannot plan diagram: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

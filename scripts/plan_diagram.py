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

if __package__:
    from .render_diagram import box, color, contrast, number, render, validate_spec, wrap_label
else:
    from render_diagram import box, color, contrast, number, render, validate_spec, wrap_label


MARGIN = 9
GUTTER = 15
MIN_COLUMN = 77
INK = '#172D3C'
MUTED = '#385365'
TINTS = {'data': '#EAF4FA', 'input': '#EDF4F5', 'decision': '#FCF5E4', 'terminator': '#E9F5EF'}
ROLE_COLOURS = {'data': 'blue', 'input': 'sky_blue', 'decision': 'orange', 'terminator': 'green'}


class LabelMeasure:
    def __init__(self, family):
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        figure = Figure(dpi=144)
        self.renderer = FigureCanvasAgg(figure).get_renderer()
        self.artist = figure.text(0, 0, '', fontfamily=family, parse_math=False, linespacing=1.13)

    def box(self, text, size, bold=False):
        self.artist.set_text(text)
        self.artist.set_fontsize(size)
        self.artist.set_fontweight('bold' if bold else 'normal')
        extent = self.artist.get_window_extent(self.renderer)
        return extent.width / 2, extent.height / 2

    def wrapped(self, text, size, bold, width):
        wrap = wrap_label(text, width, lambda line: self.box(line, size, bold)[0])
        w, h = self.box(wrap, size, bold)
        return len(wrap.splitlines()), w, h


def graph_rows(nodes, edges):
    """Assign ranks without changing direction or adding relationships."""
    children, parents = defaultdict(list), defaultdict(list)
    for edge in edges:
        if (not isinstance(edge, dict) or not isinstance(edge.get('from'), str)
                or not isinstance(edge.get('to'), str)
                or edge['from'] not in nodes or edge['to'] not in nodes):
            raise ValueError('Every relationship must name existing from and to nodes')
        children[edge['from']].append(edge['to'])
        parents[edge['to']].append(edge['from'])
    active = list(nodes)
    rank = {}
    while active:
        ready = [n for n in active if all(parent in rank for parent in parents[n])]
        if not ready:
            raise ValueError('Automatic ranks need an acyclic workflow. Use the manual route for loops.')
        for n in ready:
            rank[n] = max((rank[parent] + 1 for parent in parents[n]), default=0)
        active = [n for n in active if n not in rank]
    rows = [[] for _ in range(max(rank.values()) + 1)]
    for n in nodes:
        rows[rank[n]].append(n)
    for row in range(1, len(rows)):
        positions = {n: i for i, n in enumerate(rows[row - 1])}
        rows[row].sort(key=lambda n: sum(positions.get(p, 0) for p in parents[n]) / max(1, len(parents[n])))
    return rows, rank, parents, children


def paper_palette(node, shape):
    node.setdefault('fill', TINTS.get(shape, 'white'))
    if shape in ROLE_COLOURS:
        node.setdefault('stroke_color', ROLE_COLOURS[shape])
    background = color(node['fill'])
    foreground = next(candidate for candidate in (INK, 'black', 'white')
                      if contrast(color(candidate), background) >= 4.5)
    node.setdefault('text_color', foreground)
    node.setdefault('bold', True)


def plan(method, asset_dir=None):
    from PIL import Image
    if not isinstance(method, dict) or not isinstance(method.get('nodes'), list) or not method['nodes']:
        raise ValueError('Supply a method object with a nonempty nodes list')
    if not isinstance(method.get('edges', []), list):
        raise ValueError('edges must be a list')
    for key in ('icons', 'annotations'):
        if not isinstance(method.get(key, []), list):
            raise ValueError(f'{key} must be a list')
    spec = deepcopy(method)
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
    measure = LabelMeasure(font_family)
    nodes = {}
    for node in spec['nodes']:
        if (not isinstance(node, dict) or not isinstance(node.get('id'), str) or not node['id'].strip()
                or not isinstance(node.get('label'), str) or not node['label'].strip()):
            raise ValueError('Every node needs a text id and label')
        if node['id'] in nodes:
            raise ValueError(f'Duplicate node id: {node["id"]}')
        shape = node.get('shape', 'process')
        if shape not in ('process', 'data', 'input', 'decision', 'terminator'):
            raise ValueError('Use process, data, input, decision or terminator in the automatic layout')
        if 'detail' in node and not isinstance(node['detail'], str):
            raise ValueError(f'Node {node["id"]} detail must be text')
        paper_palette(node, shape)
        nodes[node['id']] = node
    edges = spec.get('edges', [])
    rows, rank, parents, children = graph_rows(nodes, edges)
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
    column_width = (width - 2 * MARGIN - GUTTER * (len(rows) - 1)) / len(rows)
    can_use_horizontal = (not lanes and 2 <= len(rows) <= 5 and column_width >= 75
                          and not any(e.get('label') for e in edges)
                          and not spec.get('annotations'))
    if can_use_horizontal:
        for node in nodes.values():
            pad = number(node.get('padding_pt', 5), 'node padding')
            label_space = column_width - 2 * max(10, pad)
            if node.get('shape') == 'decision':
                label_space = column_width / 2 - 2 * pad
            line_counts = []
            for field, font_size in [('label', node.get('font_pt',size)), ('detail', node.get('detail_font_pt',size))]:
                value = node.get(field, '')
                if not value.strip():
                    continue
                lines, measured, _ = measure.wrapped(value, number(font_size,'node font size'), field=='label', label_space)
                if measured > label_space:
                    can_use_horizontal = False
                line_counts.append(lines)
            if any(lines > 2 for lines in line_counts) or sum(line_counts) > 4:
                can_use_horizontal = False
    if direction == 'horizontal' and not can_use_horizontal:
        raise ValueError('This method needs a vertical layout or explicit routes. Check columns, labels and lanes.')
    horizontal = can_use_horizontal and direction != 'vertical' and not spec.get('icons')
    if spec.get('icons') and direction == 'horizontal':
        raise ValueError('Use vertical automatic layout or explicit routes for this icon-based figure.')
    if not horizontal and slot_width < MIN_COLUMN and count > 1:
        raise ValueError('This rank is too wide for readable parallel columns. Use a wider figure or split the workflow.')
    asset_root = Path(asset_dir or '.').resolve()
    icons_by_node = {}
    for icon in spec.get('icons', []):
        owner = icon.get('node') if isinstance(icon, dict) else None
        if not isinstance(owner, str) or owner not in nodes or owner in icons_by_node:
            raise ValueError('The automatic layout accepts one local icon per named node')
        name = icon.get('path')
        if (not isinstance(name, str) or '\\' in name or ':' in name or name.startswith('/')
                or '..' in Path(name).parts or Path(name).suffix.lower() != '.png'):
            raise ValueError('A planned icon needs a relative PNG path')
        path = (asset_root / name).resolve()
        if not path.is_relative_to(asset_root):
            raise ValueError('Icon must be inside the method specification directory')
        with Image.open(path) as image:
            iw, ih = image.size
        requested = icon.get('size_pt', [16, 16])
        if not isinstance(requested, list) or len(requested) != 2:
            raise ValueError('Icon size_pt needs [width, height]')
        fit = min(number(requested[0], 'icon width') / iw, number(requested[1], 'icon height') / ih)
        if fit <= 0:
            raise ValueError('Icon dimensions must be positive')
        icons_by_node[owner] = (icon, iw * fit, ih * fit)
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
            shape_factor = 2 if shape == 'decision' else 1
            natural = max(measure.box(node['label'], node_size, node.get('bold', True))[0],
                          measure.box(node.get('detail',''), detail_size)[0])
            box_width = min(max_width, max(MIN_COLUMN, (natural + 2 * side + 14) * shape_factor))
            if horizontal:
                max_width = column_width
                box_width = column_width
            if lanes and shape != 'decision':
                box_width = max_width
            icon_data = icons_by_node.get(identifier)
            if icon_data:
                box_width = min(max_width, max(box_width, natural + 2 * side + 9 + icon_data[1]))
            inner = box_width / shape_factor - side * 2
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
                                                               node.get('bold', True), title_width)
                detail_lines, detail_w, detail_h = 0, 0, 0
                if 'detail' in node:
                    detail_lines, detail_w, detail_h = measure.wrapped(node['detail'], detail_size, False, detail_width)
                if title_w > title_width or detail_w > detail_width:
                    continue
                body_h = (max(title_h, ih) if position == 'title' else title_h)
                body_h += detail_gap + detail_h if 'detail' in node else 0
                if position == 'top':
                    body_h += ih + 8
                if position in ('left','right'):
                    body_h = max(body_h, ih)
                height = max(25, (body_h + top + pad + 4) * shape_factor)
                scored.append({'placement': position, 'height_pt': round(height, 2),
                               'title_lines': title_lines, 'detail_lines': detail_lines})
            if not scored:
                raise ValueError(f'Node {identifier} has text that does not fit at the requested width')
            winner = min(scored, key=lambda c: (c['detail_lines'] + c['title_lines'], c['height_pt']))
            node['box'] = [0, 0, box_width, winner['height_pt']]
            if icon_data:
                planned_icons.append({'node': identifier, 'choice': winner['placement'], 'candidates': scored})
    next_top = MARGIN
    border_pairs = [edge for edge in edges if rank[edge['to']] - rank[edge['from']] != 1]
    if border_pairs:
        raise ValueError('This graph skips ranks. Choose explicit routes for these links or use the manual layout.')
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
                bounds[:2] = [MARGIN + index * (column_width + GUTTER), y]
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
        labelled = any(edge.get('label') for edge in outgoing)
        corridor = 28 if labelled else 15
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
    for edge in edges:
        start, finish = edge['from'], edge['to']
        x, y, w, h = nodes[start]['box']
        dx, dy, dw, dh = nodes[finish]['box']
        if horizontal:
            exits = sorted(children[start], key=lambda name: nodes[name]['box'][1])
            entries = sorted(parents[finish], key=lambda name: nodes[name]['box'][1])
            sy = round(port_coordinate(nodes, start, finish, exits, 1), 5)
            ty = round(port_coordinate(nodes, finish, start, entries, 1), 5)
            mid = (x+w+dx) / 2
            edge['points'] = ([[x+w,sy],[dx,sy]] if abs(sy-ty) < .2
                              else [[x+w,sy],[mid,sy],[mid,ty],[dx,ty]])
            continue
        exits = sorted(children[start], key=lambda name: nodes[name]['box'][0])
        entries = sorted(parents[finish], key=lambda name: nodes[name]['box'][0])
        sx = port_coordinate(nodes, start, finish, exits, 0)
        tx = port_coordinate(nodes, finish, start, entries, 0)
        sx, tx = round(sx,5), round(tx,5)
        if nodes[start].get('shape') == 'decision' and tx > x + w + 12 and len(rows[rank[start]]) <= 2:
            # Exit a right branch from the diamond's side when its corridor is open.
            blocked = any(n != start and x < nodes[n]['box'][0] < tx for n in rows[rank[start]])
            if not blocked:
                edge['points'] = [[x+w, y+h/2], [tx, y+h/2], [tx, dy]]
                if edge.get('label'):
                    notes.append(branch_note(edge['label'], (x+w+tx)/2, y+h/2-7, size, width, measure))
                continue
        if abs(sx - tx) < .2:
            tx = sx
        corridor_y = (y+h+dy) / 2
        edge['points'] = [[sx, y+h], [tx, dy]] if sx == tx else [[sx,y+h],[sx,corridor_y],[tx,corridor_y],[tx,dy]]
        if edge.get('label'):
            midpoint = (sx+tx)/2
            label_x = max(sx,tx)+12 if abs(sx-tx) < 28 else midpoint
            notes.append(branch_note(edge['label'], label_x, corridor_y-7, size, width, measure))
    notes.extend(spec.get('annotations', []))
    if notes:
        spec['annotations'] = notes
        if any(not isinstance(note, dict) for note in notes):
            raise ValueError('Annotations must be objects')
        next_top = max(next_top, max(y+h for _,y,_,h in (box(n.get('box'), 'note') for n in notes)))
    canvas['height_pt'] = round(next_top + MARGIN + .001, 3)
    spec['layout_plan'] = {'method': 'layered', 'reading_direction': 'horizontal' if horizontal else 'vertical',
                           'ranks': rows, 'lanes': lanes, 'icon_choices': planned_icons}
    return validate_spec(spec)


def branch_note(label, x, y, base, width, measure):
    if not isinstance(label, str) or not label.strip():
        raise ValueError('A branch label must be text')
    size = max(8.5, base - .5)
    label_width, label_height = measure.box(label, size)
    w, h = label_width + 4, label_height + 3
    left = max(MARGIN, min(x-w/2, width-MARGIN-w))
    return {'label': label, 'box': [left,y-h/2,w,h], 'font_pt': size, 'padding_pt': 1, 'text_color': MUTED}


def port_coordinate(nodes, owner, peer, neighbours, axis):
    origin = nodes[owner]['box'][axis]
    size = nodes[owner]['box'][axis+2]
    centre = origin + size / 2
    other = nodes[peer]['box']
    peer_centre = other[axis] + other[axis+2] / 2
    if len(neighbours) == 1 or abs(centre - peer_centre) < .2:
        return centre
    return origin + size * (.17 + .66 * (neighbours.index(peer) + .5) / len(neighbours))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('method', nargs='?', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('diagram-output'))
    parser.add_argument('--stem', default='method')
    parser.add_argument('--dpi', type=int, default=600)
    parser.add_argument('--preview-only', action='store_true')
    parser.add_argument('--drawio', action='store_true')
    parser.add_argument('--tiff', action='store_true')
    parser.add_argument('--profile', choices=('plos-one',))
    parser.add_argument('--require-sources', action='store_true')
    parser.add_argument('--doctor', action='store_true', help='Check which local tools are installed')
    args = parser.parse_args()
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
            return plan(source, args.method.parent)
        report = render(build, args.output_dir, stem=args.stem, dpi=args.dpi,
                        asset_dir=args.method.parent, preview_only=args.preview_only, drawio=args.drawio,
                        tiff=args.tiff, profile=args.profile, require_sources=args.require_sources)
        print(json.dumps({'status': report['status'], 'exports': report['exports'], 'errors': report['errors']}, indent=2))
        return 0 if report['passed_geometry_checks'] else 1
    except (ValueError, OSError, ImportError) as error:
        print(f'Cannot plan diagram: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

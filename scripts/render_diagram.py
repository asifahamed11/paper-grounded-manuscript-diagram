#!/usr/bin/env python3
"""Draw a supplied, explicitly laid-out research schematic locally from JSON.

Geometry is in points (72 points/inch), origin top left. This renderer does not
infer methods, select papers or certify scientific correctness. Matplotlib is
loaded only when rendering; schema validation needs the Python standard library.
"""
from __future__ import annotations

import argparse
import copy
from collections import deque
import hashlib
import json
import math
import re
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4
from itertools import combinations
from pathlib import Path

try:
    from .themes import apply_theme, resolve_font, THEMES
    from .vector_icons import draw_matplotlib as draw_vector_icon, list_icons, as_data_uri as vector_as_data_uri, load_local_svg, draw_svg_file
except ImportError:
    try:
        from scripts.themes import apply_theme, resolve_font, THEMES
        from scripts.vector_icons import draw_matplotlib as draw_vector_icon, list_icons, as_data_uri as vector_as_data_uri, load_local_svg, draw_svg_file
    except ImportError:
        from themes import apply_theme, resolve_font, THEMES
        from vector_icons import draw_matplotlib as draw_vector_icon, list_icons, as_data_uri as vector_as_data_uri, load_local_svg, draw_svg_file

PALETTE = {"blue": "#0072B2", "sky_blue": "#56B4E9", "orange": "#E69F00",
           "green": "#009E73", "purple": "#CC79A7", "black": "#000000",
           "yellow": "#F0E442", "vermillion": "#D55E00", "white": "#FFFFFF"}


def color(value):
    if isinstance(value, str):
        value = PALETTE.get(value, value)
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValueError(f"Use a palette name or #RRGGBB colour, got {value!r}")
    return value


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def box(value, name):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{name} must be [x, y, width, height] in points")
    x, y, w, h = [number(v, name) for v in value]
    if w <= 0 or h <= 0:
        raise ValueError(f"{name} width and height must be positive")
    return x, y, w, h


def wrap_label(raw, available, measure, math=False):
    lines = []
    for paragraph in raw.split('\n'):
        line = ''
        tokens = re.findall(r'\S*\$[^$]+\$\S*|\S+', paragraph) if math else paragraph.split()
        for word in tokens:
            proposed = (line + ' ' + word).strip()
            if line and measure(proposed) > available:
                lines.append(line)
                line = word
            else:
                line = proposed
        lines.append(line)
    return '\n'.join(lines)


def validate_label_style(record, name, *, is_node=False):
    for key in ('font_pt', 'detail_font_pt', 'padding_pt', 'title_height_pt',
                'label_height_pt', 'icon_space_pt'):
        if key not in record:
            continue
        value = number(record[key], f'{name}.{key}')
        allows_zero = key in {'padding_pt', 'icon_space_pt'}
        if value < 0 or (value == 0 and not allows_zero):
            raise ValueError(f'{name}.{key} must be {"nonnegative" if allows_zero else "positive"}')
        if key.endswith('font_pt') and value > 36:
            raise ValueError(f'{name}.{key} must be at most 36 pt')
    if 'bold' in record and not isinstance(record['bold'], bool):
        raise ValueError(f'{name}.bold must be true or false')
    if 'math' in record and not isinstance(record['math'], bool):
        raise ValueError(f'{name}.math must be true or false')
    if record.get('align', 'center') not in ('left', 'center'):
        raise ValueError(f'{name}.align must be left or center')
    color(record.get('fill', 'white'))
    color(record.get('text_color', 'black'))
    if 'detail_color' in record:
        color(record['detail_color'])
    if is_node:
        color(record.get('stroke_color', 'black'))


def _is_unambiguous_math(label_text: str) -> bool:
    """Detect whether a string with $...$ contains unambiguous LaTeX math rather than currency."""
    math_spans = re.findall(r'\$([^$]+)\$', label_text)
    if not math_spans:
        return False
    for span in math_spans:
        s = span.strip()
        if not s:
            continue
        # Currency/numbers start with a digit (e.g. $100 in '$100 and $200')
        if s[0].isdigit():
            continue
        # LaTeX commands, subscripts, or superscripts
        if any(ch in s for ch in ('\\', '_', '^')):
            return True
        # Single-letter math variable equations or inequalities (e.g. k_1=1.2, x=0, p<0.05, N=100)
        if re.search(r'[A-Za-z][A-Za-z0-9_]*\s*(=|<|>|≤|≥|≠|∈|~)\s*[-+0-9A-Za-z]', s):
            return True
    return False


def _resolve_math(label_text: str, record_or_math: dict | bool | None = None, canvas_math: bool = False) -> tuple[str, bool]:
    """Decide whether to use Matplotlib mathtext for a label."""
    if isinstance(record_or_math, dict):
        rec_math = record_or_math.get('math') is True
    else:
        rec_math = record_or_math is True
    use_math = rec_math or (canvas_math is True)
    if r'\(' in label_text and r'\)' in label_text:
        parts = re.split(r'(\\\(.*?\\\))', label_text, flags=re.DOTALL)
        converted = []
        for part in parts:
            if part.startswith(r'\(') and part.endswith(r'\)'):
                converted.append('$' + part[2:-2].strip() + '$')
            else:
                converted.append(part.replace('$', r'\$'))
        return ''.join(converted), True
    elif '$' in label_text and (use_math or _is_unambiguous_math(label_text)):
        return label_text, True
    elif rec_math and '$' not in label_text and '\\' in label_text:
        return f'${label_text}$', True
    else:
        return label_text, False


def provenance(spec):
    """Describe supplied provenance and any uncovered substantive elements."""
    sources = spec.get('sources', [])
    if not isinstance(sources, list):
        raise ValueError('sources must be a list')
    source_ids = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError('Each source must be an object')
        for field in ('id', 'title', 'locator'):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f'Each source needs a nonempty {field}')
        if source['id'] in source_ids:
            raise ValueError(f"Duplicate source id: {source['id']}")
        source_ids.add(source['id'])
        if source.get('kind', 'method') not in ('method', 'figure', 'dataset', 'code', 'asset'):
            raise ValueError('Unknown source kind')
    linked, uncovered = {}, []
    for kind in ('nodes', 'edges', 'annotations', 'icons'):
        for index, item in enumerate(spec.get(kind, [])):
            identifier = f'{kind}:{item.get("id", index)}'
            refs = item.get('source_refs', [])
            if not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in source_ids for ref in refs):
                raise ValueError(f'{identifier}.source_refs must name sources in the specification')
            if refs:
                linked[identifier] = refs
            elif kind == 'edges' or (kind == 'nodes' and item.get('shape') not in ('header', 'group')):
                uncovered.append(identifier)
    figure_sources = [
        s for s in sources
        if s.get('kind') == 'figure'
        and isinstance(s.get('title'), str) and s['title'].strip()
        and isinstance(s.get('locator'), str) and s['locator'].strip()
        and any(isinstance(s.get(k), str) and s[k].strip() for k in ('doi', 'url', 'pdf_url'))
    ]
    return {'sources': sources, 'linked_elements': linked, 'unlinked_method_elements': uncovered,
            'paper_figures_inspected': len(figure_sources),
            'paper_figure_ids': [s['id'] for s in figure_sources],
            'review': 'Source references supplied by the author or agent; check claim support separately.'}


def validate_spec(spec):
    if not isinstance(spec, dict):
        raise ValueError("Specification must be a JSON object")
    canvas = spec.get("canvas", {})
    if not isinstance(canvas, dict):
        raise ValueError("canvas must be an object")
    width = number(canvas.get("width_pt"), "canvas.width_pt")
    height = number(canvas.get("height_pt"), "canvas.height_pt")
    minimum = number(canvas.get("min_font_pt", 8.5), "canvas.min_font_pt")
    font_size = number(canvas.get("font_pt", 9), "canvas.font_pt")
    if width <= 0 or height <= 0 or not 6 <= minimum <= font_size <= 36:
        raise ValueError("Positive canvas and 6 <= min_font_pt <= font_pt <= 36 required")
    if not isinstance(spec.get('title'), str) or not spec['title'].strip():
        raise ValueError("A descriptive title is required")
    if 'description' in spec and not isinstance(spec['description'], str):
        raise ValueError('description must be text')
    if 'font_family' in canvas and (not isinstance(canvas['font_family'], str) or not canvas['font_family'].strip()):
        raise ValueError('canvas.font_family must be a nonempty font family')
    if 'math' in canvas and not isinstance(canvas['math'], bool):
        raise ValueError('canvas.math must be true or false')
    style=spec.get('style',{})
    if not isinstance(style,dict):raise ValueError('style must be an object')
    for key, default in [('corner_radius_pt', 5), ('connector_radius_pt', 5)]:
        if number(style.get(key, default), f'style.{key}') < 0:
            raise ValueError(f'style.{key} must be nonnegative')
    for key in ('line_width_pt', 'connector_width_pt'):
        if number(style.get(key, .85), f'style.{key}') <= 0:
            raise ValueError(f'style.{key} must be positive')
    if style.get('connector_style','rounded') not in ('rounded','orthogonal'):
        raise ValueError('connector_style must be rounded or orthogonal')
    color(style.get('stroke_color', 'black'))
    color(style.get('connector_color', 'black'))
    gap=number(style.get('title_detail_gap_pt',3.5),'style.title_detail_gap_pt')
    if gap < 0:raise ValueError('title_detail_gap_pt must be nonnegative')
    if 'theme' in style:
        if not isinstance(style['theme'], str) or style['theme'] not in THEMES:
            raise ValueError(f"Unknown theme: {style['theme']}. Valid: {sorted(THEMES.keys())}")
    if 'arrow_scale' in style:
        if number(style['arrow_scale'], 'style.arrow_scale') <= 0:
            raise ValueError('style.arrow_scale must be positive')
    if 'shadow' in style and not isinstance(style['shadow'], bool):
        raise ValueError('style.shadow must be true or false')
    if 'crossing_jump' in style and not isinstance(style['crossing_jump'], bool):
        raise ValueError('style.crossing_jump must be true or false')
    if 'detail_color' in style:
        color(style['detail_color'])
    if 'detail_font_pt' in style:
        df_val = number(style['detail_font_pt'], 'style.detail_font_pt')
        if df_val <= 0 or df_val > 36:
            raise ValueError('style.detail_font_pt must be positive and at most 36 pt')
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("At least one node is required")
    ids = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]:
            raise ValueError("Each node needs a nonempty string id")
        if node["id"] in ids:
            raise ValueError(f"Duplicate node id: {node['id']}")
        ids.add(node["id"])
        x, y, w, h = box(node.get("box"), node["id"])
        if x < 0 or y < 0 or x+w > width or y+h > height:
            raise ValueError(f"Node {node['id']} lies outside the canvas")
        if node.get("shape", "process") not in ("process", "data", "input", "decision", "terminator", "header", "group"):
            raise ValueError(f"Unknown shape for {node['id']}")
        if not isinstance(node.get("label"), str) or not node["label"].strip():
            raise ValueError(f"Node {node['id']} needs a label")
        validate_label_style(node, f"Node {node['id']}", is_node=True)
        if 'detail' in node and (not isinstance(node['detail'],str) or not node['detail'].strip()):
            raise ValueError(f"Node {node['id']} detail must be nonempty text")
        if node.get('text_layout','stacked') not in ('stacked','bands'):
            raise ValueError('node.text_layout must be stacked or bands')
        if 'shadow' in node and not isinstance(node['shadow'], bool):
            raise ValueError(f"Node {node['id']} shadow must be true or false")
        if 'accent' in node:
            if node.get('shape') == 'group':
                raise ValueError(f"Node {node['id']} group frames do not support accent")
            if node['accent'] not in ('left', 'top'):
                raise ValueError(f"Node {node['id']} accent must be left or top")
        if 'accent_color' in node:
            color(node['accent_color'])
        if 'container_fill' in node:
            if node.get('shape') != 'group':
                raise ValueError(f"Node {node['id']} container_fill is only supported on group shapes")
            color(node['container_fill'])
        if 'border_style' in node:
            if node.get('shape') != 'group':
                raise ValueError(f"Node {node['id']} border_style is only supported on group shapes")
            if node['border_style'] not in ('solid', 'dashed'):
                raise ValueError(f"Node {node['id']} border_style must be solid or dashed")
        if 'badge' in node:
            if node.get('shape') == 'group':
                raise ValueError(f"Node {node['id']} group frames do not support badge")
            if not isinstance(node['badge'], str) or not node['badge'].strip():
                raise ValueError(f"Node {node['id']} badge must be nonempty text")
        if 'badge_fill' in node:
            color(node['badge_fill'])
        if 'badge_text_color' in node:
            color(node['badge_text_color'])
    edge_ids = set()
    edges=spec.get('edges',[])
    if not isinstance(edges,list):raise ValueError('edges must be a list')
    for i, edge in enumerate(edges):
        if not isinstance(edge,dict):raise ValueError('Each edge must be an object')
        if any(not isinstance(edge.get(key), str) or edge[key] not in ids for key in ('from', 'to')):
            raise ValueError(f"Edge {i} has an unknown endpoint")
        eid = edge.get("id", str(i))
        if isinstance(eid, bool) or not isinstance(eid, (str, int)) or not str(eid).strip():
            raise ValueError(f'Edge {i} needs a text or integer id')
        eid = str(eid)
        if eid in edge_ids:
            raise ValueError(f"Duplicate edge id: {eid}")
        edge_ids.add(eid)
        points = edge.get("points")
        if not isinstance(points, list) or len(points) < 2:
            raise ValueError(f"Edge {eid} requires at least two route points")
        parsed = []
        for pt in points:
            if not isinstance(pt, list) or len(pt) != 2:
                raise ValueError(f"Edge {eid} points must be [x,y]")
            x,y = [number(v, "edge point") for v in pt]
            if not 0 <= x <= width or not 0 <= y <= height:
                raise ValueError(f"Edge {eid} leaves the canvas")
            parsed.append((x,y))
        for a,b in zip(parsed, parsed[1:]):
            if a == b or (a[0] != b[0] and a[1] != b[1]):
                raise ValueError(f"Edge {eid} must use nonzero orthogonal segments")
        if edge.get("style", "solid") not in ("solid", "dashed"):
            raise ValueError(f"Edge {eid} style must be solid or dashed")
        if 'color' in edge:
            color(edge['color'])
        if edge.get('arrow','end') not in ('end','both','none'):
            raise ValueError(f'Edge {eid} arrow must be end, both or none')
        if 'label' in edge and (not isinstance(edge['label'], str) or not edge['label'].strip()):
            raise ValueError(f'Edge {eid} label must be nonempty text')
        if 'math' in edge and not isinstance(edge['math'], bool):
            raise ValueError(f'Edge {eid} math must be true or false')
        if edge.get("style") == "dashed" and (not isinstance(edge.get('meaning'), str) or not edge['meaning'].strip()):
            raise ValueError(f"Dashed edge {eid} needs an explicit meaning")
    accepted_crossings = spec.get('allowed_crossings', [])
    if not isinstance(accepted_crossings, list):
        raise ValueError('allowed_crossings must be a list')
    for entry in accepted_crossings:
        if (not isinstance(entry, dict) or not isinstance(entry.get('edges'), list)
                or len(entry['edges']) != 2 or not all(isinstance(e, str) and e in edge_ids for e in entry['edges'])
                or entry['edges'][0] == entry['edges'][1]
                or not isinstance(entry.get('reason'), str) or not entry['reason'].strip()):
            raise ValueError('Each allowed crossing needs two different edge ids and a reason')
    annotations=spec.get('annotations',[])
    if not isinstance(annotations,list):raise ValueError('annotations must be a list')
    for note in annotations:
        if not isinstance(note,dict):raise ValueError('Each annotation must be an object')
        x,y,w,h = box(note.get("box"), "annotation")
        if x < 0 or y < 0 or x+w > width or y+h > height:
            raise ValueError("Annotation lies outside the canvas")
        if not isinstance(note.get("label"), str) or not note["label"].strip():
            raise ValueError("Annotation label is required")
        validate_label_style(note, 'Annotation')
    icons = spec.get('icons', [])
    if not isinstance(icons, list):raise ValueError('icons must be a list')
    icon_ids = set()
    for icon in icons:
        if not isinstance(icon, dict) or not isinstance(icon.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', icon['id']):
            raise ValueError('Each icon needs a filename-safe id')
        if icon['id'] in icon_ids:raise ValueError('Duplicate icon id')
        icon_ids.add(icon['id'])
        if 'vector_icon' in icon:
            if not isinstance(icon['vector_icon'], str) or icon['vector_icon'] not in list_icons():
                raise ValueError(f"Unknown vector icon '{icon.get('vector_icon')}'; valid: {list_icons()}")
            if 'color' in icon:
                color(icon['color'])
            if 'stroke_color' in icon:
                color(icon['stroke_color'])
            if 'line_width_pt' in icon:
                if number(icon['line_width_pt'], 'icon.line_width_pt') <= 0:
                    raise ValueError('icon.line_width_pt must be positive')
        else:
            path = icon.get('path')
            if not isinstance(path, str) or not path or path.startswith('/') or '\\' in path or ':' in path or Path(path).is_absolute() or '..' in Path(path).parts or Path(path).suffix.lower() not in ('.png', '.svg'):
                raise ValueError('Icon path must be a relative local PNG or SVG within the specification directory')
        if not isinstance(icon.get('alt'), str) or not icon['alt'].strip():raise ValueError('Icon alt/meaning is required')
        placement=icon.get('placement','left' if 'node' in icon else 'fixed')
        if placement not in ('left','right','top','title','fixed'):raise ValueError('Unknown icon placement')
        if placement=='title':
            size=icon.get('size_pt')
            if not isinstance(size,list) or len(size)!=2 or min(number(v,'icon.size_pt') for v in size)<=0:
                raise ValueError('Title icons need size_pt: [width, height]')
            if 'box' in icon:raise ValueError('Title icon position is measured; use size_pt without box')
            if number(icon.get('gap_pt',4),'icon.gap_pt')<0:raise ValueError('Icon gap must be nonnegative')
        else:
            x,y,w,h = box(icon.get('box'), 'icon '+icon['id'])
            if x < 0 or y < 0 or x+w > width or y+h > height:raise ValueError('Icon lies outside the canvas')
        if 'node' not in icon and placement!='fixed':raise ValueError('Attached icon placement needs a node')
        if 'node' in icon:
            owner = next((n for n in nodes if n['id'] == icon['node']), None)
            if owner is None:raise ValueError('Icon has unknown node')
            if placement=='title':
                if owner.get('shape')=='group':raise ValueError('Title icons are not supported in group frames')
                if owner.get('text_layout','bands' if 'title_height_pt' in owner else 'stacked')!='stacked':
                    raise ValueError('Title icon requires stacked text; remove band height or set text_layout to stacked')
                if sum(isinstance(i, dict) and i.get('node')==icon['node'] for i in icons)!=1:raise ValueError('Use one attached icon per title cluster')
                continue
            if placement=='fixed':raise ValueError('For an attached icon choose left, right, top or title')
            reserve = number(owner.get('icon_space_pt', 0), 'node.icon_space_pt')
            nx,ny,nw,nh = owner['box']
            limit=nh if placement=='top' else nw
            if reserve <= 0 or reserve >= limit-10:raise ValueError('Icon owner must reserve label space with icon_space_pt')
            strips={'left':(nx,ny,reserve,nh),'right':(nx+nw-reserve,ny,reserve,nh),'top':(nx,ny,nw,reserve)}
            sx,sy,sw,sh=strips[placement]
            if not (sx+2<=x and x+w<=sx+sw-2 and sy+2<=y and y+h<=sy+sh-2):
                raise ValueError('Icon must fit in its reserved strip')
    if 'legend' in spec:
        leg = spec['legend']
        if not isinstance(leg, dict):
            raise ValueError('legend must be an object')
        lx, ly, lw, lh = box(leg.get('box'), 'legend')
        if lx < 0 or ly < 0 or lx + lw > width or ly + lh > height:
            raise ValueError('legend lies outside the canvas')
        items = leg.get('items')
        if not isinstance(items, list) or not items:
            raise ValueError('legend.items must be a nonempty list')
        for idx, it in enumerate(items):
            if not isinstance(it, dict) or not isinstance(it.get('label'), str) or not it['label'].strip():
                raise ValueError(f'legend item {idx} needs a nonempty label')
            color(it.get('color', it.get('fill', '#334E68')))
            if 'stroke_color' in it:
                color(it['stroke_color'])
        if 'fill' in leg:
            color(leg['fill'])
        if 'stroke_color' in leg:
            color(leg['stroke_color'])
        if 'text_color' in leg:
            color(leg['text_color'])
        if 'frame' in leg and not isinstance(leg['frame'], bool):
            raise ValueError('legend.frame must be true or false')
    provenance(spec)
    return spec


def intersects(a, b, gap=0):
    return min(a[2], b[2])-max(a[0], b[0]) > gap and min(a[3], b[3])-max(a[1], b[1]) > gap


def segment_hits(a, b, bounds):
    # Open-interior slab intersection works for straight and sampled curved paths.
    low,high=0.,1.
    for start,end,mn,mx in zip(a,b,bounds[:2],bounds[2:]):
        delta=end-start
        if abs(delta)<1e-10:
            if not mn < start < mx:return False
        else:
            enter,leave=sorted(((mn-start)/delta,(mx-start)/delta))
            low=max(low,enter);high=min(high,leave)
            if high-low<=1e-10:return False
    return high-low>1e-10


def rounded_route(points, radius):
    """Return SVG-like commands and samples for filleted orthogonal connections."""
    commands=[('M',tuple(points[0]))];samples=[tuple(points[0])]
    for i in range(1,len(points)-1):
        a,b,c=points[i-1],points[i],points[i+1]
        before=math.dist(a,b);after=math.dist(b,c)
        turn=(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
        r=min(radius,before/2,after/2)
        if r<=0 or abs(turn)<1e-10:
            commands.append(('L',tuple(b)));samples.append(tuple(b));continue
        enter=tuple(b[j]+(a[j]-b[j])*r/before for j in (0,1))
        leave=tuple(b[j]+(c[j]-b[j])*r/after for j in (0,1))
        commands.extend([('L',enter),('Q',tuple(b)),('Q',leave)])
        samples.append(enter)
        for step in range(1,17):
            t=step/16;samples.append(tuple((1-t)**2*enter[j]+2*(1-t)*t*b[j]+t*t*leave[j] for j in (0,1)))
    commands.append(('L',tuple(points[-1])));samples.append(tuple(points[-1]))
    return commands,samples


def rounded_polygon(points, radius):
    """Round a polygon's vertices without changing its semantic silhouette."""
    commands=[]
    for i,b in enumerate(points):
        a=points[i-1];c=points[(i+1)%len(points)]
        r=min(radius,math.dist(a,b)/3,math.dist(b,c)/3)
        enter=tuple(b[j]+(a[j]-b[j])*r/math.dist(a,b) for j in (0,1))
        leave=tuple(b[j]+(c[j]-b[j])*r/math.dist(b,c) for j in (0,1))
        commands.extend([('M' if i==0 else 'L',enter),('Q',tuple(b)),('Q',leave)])
    commands.append(('Z',commands[0][1]));return commands


def on_boundary(point, bounds, tolerance=1.5):
    x,y,w,h = bounds; px,py = point
    return ((abs(px-x) <= tolerance or abs(px-x-w) <= tolerance) and y-tolerance <= py <= y+h+tolerance
            or (abs(py-y) <= tolerance or abs(py-y-h) <= tolerance) and x-tolerance <= px <= x+w+tolerance)


def shape_port(point, neighbour, bounds, paths):
    """Intersect the outgoing corridor with the actual rounded/sloping silhouette."""
    x,y,w,h=bounds
    axis=0 if point[0]!=neighbour[0] else 1
    fixed=point[1-axis]
    # At either endpoint the adjacent route point lies outside the named shape.
    outward=neighbour[axis]-point[axis]
    side=1 if outward>0 else -1
    low=(x,y)[axis];span=(w,h)[axis]
    expected_side = low + span if side > 0 else low
    if abs(point[axis] - expected_side) > 1.5 or side * (neighbour[axis] - expected_side) <= 0:
        raise ValueError('Route points inward or runs along a boundary. Leave the named side of the node first.')
    def coord(value):return (value,fixed) if axis==0 else (fixed,value)
    def inside(value):return any(path.contains_point(coord(value)) for path in paths)
    # Find an interior point on this corridor, not the rectangle's corner.
    interior=low+span/2
    if not inside(interior):
        candidates=[low+span*i/128 for i in range(1,128)]
        found=next((v for v in candidates if inside(v)),None)
        if found is None:raise ValueError('Connection corridor misses its named shape; choose a central port')
        interior=found
    exterior=low+span+2 if side>0 else low-2
    for _ in range(36):
        midpoint=(interior+exterior)/2
        if inside(midpoint):interior=midpoint
        else:exterior=midpoint
    resolved = (interior+exterior)/2
    if side * (neighbour[axis] - resolved) <= 1e-6:
        raise ValueError('Route must continue away from the resolved node port.')
    return coord(resolved)


def segment_meeting(a, b, c, d):
    """Return a route intersection or collinear overlap, if present."""
    tolerance = 1e-7

    def cross(u, v):
        return u[0] * v[1] - u[1] * v[0]

    ab = tuple(y - x for x, y in zip(a, b))
    cd = tuple(y - x for x, y in zip(c, d))
    ac = tuple(y - x for x, y in zip(a, c))
    denominator = cross(ab, cd)
    if abs(denominator) > tolerance:
        t, u = cross(ac, cd) / denominator, cross(ac, ab) / denominator
        if -tolerance <= t <= 1 + tolerance and -tolerance <= u <= 1 + tolerance:
            return 'crossing', tuple(x + t * v for x, v in zip(a, ab))
        return None
    if abs(cross(ac, ab)) > tolerance or max(map(abs, ab)) <= tolerance or max(map(abs, cd)) <= tolerance:
        return None
    axis = 0 if abs(ab[0]) >= abs(ab[1]) else 1
    first, last = sorted(((c[axis] - a[axis]) / ab[axis], (d[axis] - a[axis]) / ab[axis]))
    lo, hi = max(0, first), min(1, last)
    if hi < lo - tolerance:
        return None
    midpoint = tuple(x + (lo + hi) / 2 * v for x, v in zip(a, ab))
    return ('overlap' if hi - lo > tolerance else 'crossing'), midpoint


def shared_join_prefix(first, second):
    """Find identical curve segments at a shared, same-role port."""
    segments = set()
    for a, b in zip(zip(first, first[1:]), zip(second, second[1:])):
        if a != b:
            break
        segments.add(frozenset(a))
    return segments


def connector_crossings(routes):
    """Flag independent routes and connections that cross outside a shared join."""
    for (i, (first, a)), (j, (second, b)) in combinations(enumerate(routes), 2):
        shared_segments = set()
        shared_ports = set()
        if first['from'] == second['from'] and a[0] == b[0]:
            shared_ports.add(a[0])
            shared_segments |= shared_join_prefix(a, b)
        if first['to'] == second['to'] and a[-1] == b[-1]:
            shared_ports.add(a[-1])
            shared_segments |= shared_join_prefix(a[::-1], b[::-1])
        shared_ports.update(p for segment in shared_segments for p in segment)
        for (p, q), (r, s) in ((x, y) for x in zip(a, a[1:]) for y in zip(b, b[1:])):
            if max(p[0], q[0]) < min(r[0], s[0]) or max(r[0], s[0]) < min(p[0], q[0]):
                continue
            if max(p[1], q[1]) < min(r[1], s[1]) or max(r[1], s[1]) < min(p[1], q[1]):
                continue
            meeting = segment_meeting(p, q, r, s)
            if not meeting:
                continue
            kind, point = meeting
            if kind == 'overlap' and frozenset((p, q)) == frozenset((r, s)) and frozenset((p, q)) in shared_segments:
                continue
            if kind == 'crossing' and any(math.dist(point, port) <= 1e-6 for port in shared_ports):
                continue
            yield {'edges': [str(first.get('id', i)), str(second.get('id', j))],
                   'kind': kind, 'point_pt': [round(v, 3) for v in point]}
            break


def contrast(fg, bg):
    def luminance(c):
        rgb=[int(c[i:i+2],16)/255 for i in (1,3,5)]
        rgb=[v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a,b in zip(rgb,[.2126,.7152,.0722]))
    a,b=sorted([luminance(fg),luminance(bg)])
    return (b+.05)/(a+.05)


def rectangle_union_area(rectangles):
    """Exact union of axis-aligned boxes, not coloured-pixel or ink coverage."""
    if not rectangles:return 0.
    xs=sorted({x for r in rectangles for x in (r[0],r[2])});area=0.
    for left,right in zip(xs,xs[1:]):
        spans=sorted((r[1],r[3]) for r in rectangles if r[0]<right and r[2]>left)
        covered=0.;bottom=None
        for top,end in spans:
            covered+=max(0.,end-max(top,bottom if bottom is not None else top))
            bottom=max(end,bottom if bottom is not None else end)
        area+=(right-left)*covered
    return area


def layout_metrics(spec, text_records=None, icon_records=None):
    """Advisory composition metrics; no universal fill target or layout rewrite."""
    width,height=spec['canvas']['width_pt'],spec['canvas']['height_pt']
    def bounds(box):
        x,y,w,h=box;return (x,y,x+w,y+h)
    def envelope(rects):
        return (min(r[0] for r in rects),min(r[1] for r in rects),max(r[2] for r in rects),max(r[3] for r in rects)) if rects else None
    def area(r):return (r[2]-r[0])*(r[3]-r[1]) if r else 0.
    nodes=[n for n in spec['nodes'] if n.get('shape') not in {'group','header'}]
    body=[bounds(n['box']) for n in nodes];body_envelope=envelope(body)
    all_rects=[bounds(n['box']) for n in spec['nodes']]+[bounds(n['box']) for n in spec.get('annotations',[])]+[bounds(n['box']) for n in spec.get('icons',[]) if 'box' in n]
    # Include routed feedback/interpretation corridors in outside margins.
    for edge in spec.get('edges',[]):
        xs,ys=zip(*edge['points']);all_rects.append((min(xs),min(ys),max(xs),max(ys)))
    outer=envelope(all_rects)
    union=rectangle_union_area(body)
    fill=union/area(body_envelope) if area(body_envelope) else None
    gaps=[];close=[]
    for i,a in enumerate(body):
        nearest=None
        for j,b in enumerate(body):
            if i==j:continue
            distance=math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
            nearest=distance if nearest is None else min(nearest,distance)
            if j>i and distance<6:close.append({'nodes':[nodes[i]['id'],nodes[j]['id']],'gap_pt':round(distance,2)})
        if nearest is not None:gaps.append(nearest)
    ordered=sorted(gaps)
    median_gap=(ordered[(len(ordered)-1)//2]+ordered[len(ordered)//2])/2 if ordered else None
    advisory=[]
    if fill is not None and len(body)>1 and fill<.42:
        advisory.append('Main node boxes occupy less than 42% of their envelope; review empty lanes/corridors. Branch/association diagrams may need this space.')
    if median_gap is not None and median_gap>24:
        advisory.append('Typical nearest-node gap exceeds 24 pt; review long connectors and row/column spacing.')
    if close:advisory.append('Some node gaps are below 6 pt; review crowding, arrowheads and label clearance.')
    margins={'left':outer[0],'top':outer[1],'right':width-outer[2],'bottom':height-outer[3]} if outer else {}
    if any(v>max(12,.08*(width if k in {'left','right'} else height)) for k,v in margins.items()):
        advisory.append('Outside margin is large relative to this canvas; review content-first sizing within venue dimensions.')
    content=[]
    if text_records is not None:
        for node,rect in zip(nodes,body):
            parts=[t['bounds_pt'] for t in text_records if t.get('node_id')==node['id']]
            parts += [i['bounds_pt'] for i in (icon_records or []) if i.get('node_id')==node['id']]
            env=envelope(parts);ratio=area(env)/area(rect) if env else 0.
            content.append({'node':node['id'],'shape':node.get('shape','process'),'content_envelope_fraction':round(ratio,4)})
        # A decision's wings are semantic geometry; a short question in a
        # readable inscribed rectangle does not make its diamond oversized.
        oversized=[r['node'] for r in content if r['shape']!='decision' and r['content_envelope_fraction']<.12]
        if oversized:advisory.append('Review oversized boxes around short labels: '+', '.join(oversized)+'. Preserve comparable widths and semantic-shape padding when useful.')
    return {'definition':'Box occupancy and spacing diagnostics, not ink coverage, aesthetic score or a universal target',
            'main_box_canvas_fraction':round(union/(width*height),4),
            'main_box_envelope_fraction':round(fill,4) if fill is not None else None,
            'content_bounds_pt':list(outer) if outer else None,'outside_margins_pt':margins,
            'median_nearest_node_gap_pt':round(median_gap,2) if median_gap is not None else None,
            'crowded_pairs':close,'node_content':content,'advisories':advisory,
            'automatic_layout_changes':'none; labels may use the compact stacked text default'}


def bleed_transparent_rgb(image):
    """Extend nearest edge RGB into zero-alpha pixels without changing alpha.

    Some raster backends filter straight RGB and alpha independently. Arbitrary
    black RGB under a transparent pixel otherwise creates a dark fringe. This
    temporary display copy keeps original prepared files and alpha untouched.
    """
    result=image.copy();pixels=result.load();width,height=result.size
    seen=bytearray(1 if a else 0 for a in image.getchannel('A').tobytes())
    queue=deque()
    for y in range(height):
        for x in range(width):
            if seen[y*width+x] and any(not seen[Y*width+X] for X,Y in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if 0<=X<width and 0<=Y<height):
                queue.append((x,y))
    while queue:
        x,y=queue.popleft();rgb=pixels[x,y][:3]
        for X,Y in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=X<width and 0<=Y<height and not seen[Y*width+X]:
                pixels[X,Y]=rgb+(0,);seen[Y*width+X]=1;queue.append((X,Y))
    return result


PROFILES = {
    'plos-one': {
        'reference': 'PLOS One guidelines (66.8–190.5 mm width, ≤222.3 mm height, 8–12 pt text, Arial/Times/Symbol, 300–600 DPI)',
    },
    'ieee-single': {
        'width_max': 252.0,
        'min_font': 8.0,
        'dpi_min': 300,
        'dpi_max': 600,
        'reference': 'IEEE single-column (3.5 in)',
    },
    'ieee-double': {
        'width_max': 515.52,
        'min_font': 8.0,
        'dpi_min': 300,
        'dpi_max': 600,
        'reference': 'IEEE double-column (7.16 in)',
    },
    'springer-lncs': {
        'width_max': 345.83,
        'height_max': 547.09,
        'min_font': 8.0,
        'dpi_min': 300,
        'dpi_max': 600,
        'reference': 'Springer LNCS (122 × 193 mm)',
    },
    'nature-single': {
        'width_max': 252.28,
        'min_font': 7.0,
        'dpi_min': 300,
        'dpi_max': 600,
        'reference': 'Nature single-column (89 mm)',
    },
    'nature-double': {
        'width_max': 518.74,
        'min_font': 7.0,
        'dpi_min': 300,
        'dpi_max': 600,
        'reference': 'Nature double-column (183 mm)',
    },
    'elsevier-double': {
        'width_max': 538.58,
        'min_font': 7.0,
        'dpi_min': 300,
        'dpi_max': 600,
        'reference': 'Elsevier double-column (190 mm)',
    },
}


def artifact_names(stem):
    extensions = ('.svg', '-outlined.svg', '.png', '.pdf', '.tiff', '.drawio', '.eps',
                  '-preview.png', '-print-size.png', '-diagnostic.png', '-source.json', '-attempt.json',
                  '-qa.json', '-assets')
    return {stem + extension for extension in extensions}


def artifact_hash(path):
    if path.is_symlink():
        raise ValueError(f'Generated artifacts cannot be symlinks: {path.name}')
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if path.is_dir():
        return {item.name: artifact_hash(item) for item in sorted(path.iterdir())}
    raise ValueError(f'Unexpected output file type: {path.name}')


def publish_run(staged, output_dir, stem, report):
    """Publish a complete run and archive the previous managed files."""
    names = artifact_names(stem)
    receipt = stem + '-qa.json'
    existing = {path.name: path for path in output_dir.iterdir() if path.name in names}
    previous = None
    if existing:
        if receipt not in existing:
            raise ValueError('Output stem already contains files without a renderer receipt. Use a new stem.')
        if existing[receipt].is_symlink():
            raise ValueError('Output receipt must be a regular file')
        previous = json.loads(existing[receipt].read_text(encoding='utf-8'))
        if (not isinstance(previous, dict) or 'passed_geometry_checks' not in previous
                or not isinstance(previous.get('exports'), list)):
            raise ValueError('Output stem already contains an unrecognised receipt. Use a new stem.')
        manifest = previous.get('artifacts')
        if manifest is not None:
            current = {name: artifact_hash(path) for name, path in existing.items() if name != receipt}
            if current != manifest:
                raise ValueError('Previous output files were edited, added or removed. Use a new stem to preserve them.')
        elif any(path.is_symlink() for path in existing.values()):
            raise ValueError('Legacy outputs containing symlinks cannot be archived')

    files = {path.name: path for path in staged.iterdir() if path.name in names and path.name != receipt}
    report['artifacts'] = {name: artifact_hash(path) for name, path in files.items()}
    (staged / receipt).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    archive = None
    moved, installed = [], []
    try:
        if previous is not None:
            history = output_dir / '.history'
            if history.is_symlink() or not history.resolve().is_relative_to(output_dir.resolve()):
                raise ValueError('The output history directory must be local to the output directory')
            archive = history / f'{stem}-{uuid4().hex}'
            archive.mkdir(parents=True)
            for name, path in existing.items():
                path.replace(archive / name)
                moved.append(name)
        for name, path in files.items():
            path.replace(output_dir / name)
            installed.append(name)
        (staged / receipt).replace(output_dir / receipt)
    except (OSError, ValueError):
        for name in reversed(installed):
            (output_dir / name).replace(staged / name)
        if archive is not None:
            for name in reversed(moved):
                (archive / name).replace(output_dir / name)
        raise


def render(spec, output_dir, stem="figure-01", dpi=600, asset_dir=None, *,
           preview_only=False, drawio=False, tiff=False, require_sources=False,
           require_paper_figures=False, profile=None, eps=False, theme=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", stem):
        raise ValueError("stem must be a filename without paths or extensions")
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    lock = destination / f'.{stem}.render.lock'
    try:
        handle = lock.open('x', encoding='utf-8')
    except FileExistsError:
        raise ValueError(f'Output stem {stem} is already in use. Choose a different stem.') from None
    try:
        handle.close()
        with TemporaryDirectory(dir=destination, prefix=f'.{stem}-') as tmp:
            staging = Path(tmp)
            try:
                if not 150 <= number(dpi, 'dpi') <= 1200:
                    raise ValueError('dpi must be between 150 and 1200')
                if profile not in (None, *PROFILES):
                    raise ValueError('Unknown figure export profile')
                if preview_only and (drawio or tiff or profile or eps):
                    raise ValueError('Preview mode only writes inspection images and QA')
                if callable(spec):
                    spec = spec()
                if theme and 'theme' not in spec.get('style', {}):
                    spec.setdefault('style', {})['theme'] = theme
                spec = apply_theme(spec)
                validate_spec(spec)
                sources = provenance(spec)
                if require_sources and sources['unlinked_method_elements']:
                    raise ValueError('Missing source references for ' + ', '.join(sources['unlinked_method_elements']))
                if require_paper_figures and sources.get('paper_figures_inspected', 0) < 2:
                    raise ValueError(
                        "Paper-grounded mode requires at least 2 inspected published figure sources "
                        "(kind: 'figure' with title, locator, and doi/url). "
                        "Fetch and inspect open-access papers via scripts/fetch_papers.py and scripts/extract_pdf_figures.py first."
                    )
                report = render_figure(spec, staging, stem, dpi, asset_dir,
                                       preview_only=preview_only, drawio=drawio, tiff=tiff or profile == 'plos-one',
                                       profile=profile, eps=eps)
            except (ValueError, OSError, ImportError) as error:
                failure_dir = staging / 'failure'
                failure_dir.mkdir()
                report = {'schema_version': 2, 'run_id': uuid4().hex, 'status': 'input-or-export-error',
                          'passed_geometry_checks': False, 'exports': [], 'errors': [str(error)]}
                publish_run(failure_dir, destination, stem, report)
                raise
            report['run_id'] = uuid4().hex
            report['spec_sha256'] = hashlib.sha256(
                json.dumps(spec, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
            publish_run(staging, destination, stem, report)
            return report
    finally:
        lock.unlink()


def render_figure(spec, output_dir, stem, dpi, asset_dir, *, preview_only, drawio, tiff, profile, eps=False):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams['ps.fonttype'] = 42
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.ft2font import FT2Font
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, PathPatch
    from matplotlib.path import Path as PlotPath
    import xml.etree.ElementTree as ET
    canvas=spec['canvas']; width=canvas['width_pt'];height=canvas['height_pt']
    design=spec.get('style',{});corner=design.get('corner_radius_pt',5)
    bend=design.get('connector_radius_pt',5) if design.get('connector_style','rounded')=='rounded' else 0
    line_width=design.get('line_width_pt',.85)
    connector_width = design.get('connector_width_pt', line_width)
    connector_color = design.get('connector_color', 'black')
    minimum=canvas.get('min_font_pt',8.5);base=canvas.get('font_pt',9)
    requested_font=canvas.get('font_family','DejaVu Sans')
    font, font_path = resolve_font(requested_font)
    supported_codepoints=set(FT2Font(font_path).get_charmap())
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    report={'schema_version':2,'scientific_review':'not performed by renderer',
            'visual_review':'pending human inspection','literature_review':'not performed by renderer',
            'font_requested':requested_font,'font_used':font,'matplotlib':matplotlib.__version__,
            'physical_inches':[width/72,height/72],'png_dpi':dpi,'errors':[],
            'warnings':[],'text':[],'icons':[],'exports':[],
            'style':{'corner_radius_pt':corner,'connector_radius_pt':bend,'line_width_pt':line_width,
                     'connector_width_pt':connector_width,
                     'title_detail_gap_pt':design.get('title_detail_gap_pt',3.5),
                     'theme':design.get('theme'),
                     'arrow_scale':design.get('arrow_scale', 6.0),
                     'shadow':design.get('shadow', False)},
            'edge_geometry_check':'16 samples per quadratic corner; visual review remains required',
            'provenance':provenance(spec)}
    if 'layout_plan' in spec:
        report['layout_plan'] = spec['layout_plan']
    if requested_font != 'auto' and font != requested_font:report['warnings'].append(f'Font unavailable; substituted {font}')
    rc={'font.family':font,'svg.fonttype':'none','pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white','svg.image_inline':True,'mathtext.fontset':'dejavusans'}
    with plt.rc_context(rc):
        fig=plt.figure(figsize=(width/72,height/72),dpi=144,facecolor='white')
        ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,width),ylim=(height,0));ax.set_axis_off()
        measurement_renderer = fig.canvas.get_renderer()
        nodes={n['id']:n for n in spec['nodes']}
        routes=[]
        edge_routes_by_id = {}
        badges = []
        def plot_path(commands):
            codes={'M':PlotPath.MOVETO,'L':PlotPath.LINETO,'Q':PlotPath.CURVE3,'Z':PlotPath.CLOSEPOLY}
            return PlotPath([p for cmd,p in commands],[codes[cmd] for cmd,p in commands])
        try:
            # Build semantic silhouettes first; z-order keeps connectors behind them.
            shape_paths={}
            for n in spec['nodes']:
                x,y,w,h=n['box'];shape=n.get('shape','process');fill=color(n.get('fill','white'))
                stroke = color(n.get('stroke_color', design.get('stroke_color', 'black')))
                rad=min(corner,h/2,w/2)
                has_shadow = (shape != 'group') and bool(n.get('shadow', design.get('shadow', False)))
                if has_shadow:
                    sdx, sdy = 1.2, 1.4
                    if shape in ('process', 'terminator', 'header'):
                        srad = min(h/2, 16) if shape == 'terminator' else rad
                        ax.add_patch(FancyBboxPatch((x+sdx, y+sdy), w, h, boxstyle=f'round,pad=0,rounding_size={srad}',
                                                    facecolor='#E8EEF2', edgecolor='none', zorder=1.5))
                    elif shape == 'data':
                        sey = 6
                        sverts = [(x+sdx, y+sdy+sey/2), (x+sdx, y+sdy), (x+w+sdx, y+sdy), (x+w+sdx, y+sdy+sey/2),
                                  (x+w+sdx, y+h+sdy-sey/2), (x+w+sdx, y+h+sdy), (x+sdx, y+h+sdy),
                                  (x+sdx, y+h+sdy-sey/2), (x+sdx, y+sdy+sey/2), (x+sdx, y+sdy+sey/2)]
                        scodes = [PlotPath.MOVETO] + [PlotPath.CURVE4]*3 + [PlotPath.LINETO] + [PlotPath.CURVE4]*3 + [PlotPath.LINETO, PlotPath.CLOSEPOLY]
                        ax.add_patch(PathPatch(PlotPath(sverts, scodes), facecolor='#E8EEF2', edgecolor='none', zorder=1.5))
                        ax.add_patch(Ellipse((x+w/2+sdx, y+sey/2+sdy), w, sey, facecolor='#E8EEF2', edgecolor='none', zorder=1.5))
                    elif shape == 'decision':
                        spts = [(x+w/2+sdx, y+sdy), (x+w+sdx, y+h/2+sdy), (x+w/2+sdx, y+h+sdy), (x+sdx, y+h/2+sdy)]
                        ax.add_patch(PathPatch(plot_path(rounded_polygon(spts, min(corner, 3))),
                                               facecolor='#E8EEF2', edgecolor='none', zorder=1.5, joinstyle='round'))
                    elif shape == 'input':
                        spts = [(x+7+sdx, y+sdy), (x+w+sdx, y+sdy), (x+w-7+sdx, y+h+sdy), (x+sdx, y+h+sdy)]
                        ax.add_patch(PathPatch(plot_path(rounded_polygon(spts, min(corner, 3))),
                                               facecolor='#E8EEF2', edgecolor='none', zorder=1.5, joinstyle='round'))

                if shape == 'group':
                    c_fill = n.get('container_fill')
                    g_face = color(c_fill) if c_fill else 'none'
                    g_border = n.get('border_style', 'dashed')
                    g_ls = (0, (3, 2)) if g_border == 'dashed' else 'solid'
                    patch = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={rad}',
                                           facecolor=g_face, edgecolor=stroke, lw=line_width,
                                           linestyle=g_ls, zorder=0.5)
                    ax.add_patch(patch)
                elif shape in {'process', 'terminator', 'header'}:
                    radius = min(h/2, 16) if shape == 'terminator' else rad
                    patch = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radius}',
                                           facecolor=fill, edgecolor=stroke, lw=line_width,
                                           linestyle='solid', zorder=2)
                    ax.add_patch(patch)
                elif shape == 'data':
                    ey = 6
                    verts = [(x, y+ey/2), (x, y), (x+w, y), (x+w, y+ey/2), (x+w, y+h-ey/2),
                             (x+w, y+h), (x, y+h), (x, y+h-ey/2), (x, y+ey/2), (x, y+ey/2)]
                    codes = [PlotPath.MOVETO] + [PlotPath.CURVE4]*3 + [PlotPath.LINETO] + [PlotPath.CURVE4]*3 + [PlotPath.LINETO, PlotPath.CLOSEPOLY]
                    patch = PathPatch(PlotPath(verts, codes), facecolor=fill, edgecolor=stroke, lw=line_width, zorder=2)
                    ax.add_patch(patch)
                    cap = Ellipse((x+w/2, y+ey/2), w, ey, facecolor=fill, edgecolor=stroke, lw=line_width, zorder=3)
                    ax.add_patch(cap)
                else:
                    pts = [(x+w/2, y), (x+w, y+h/2), (x+w/2, y+h), (x, y+h/2)] if shape == 'decision' else [(x+7, y), (x+w, y), (x+w-7, y+h), (x, y+h)]
                    patch = PathPatch(plot_path(rounded_polygon(pts, min(corner, 3))), facecolor=fill, edgecolor=stroke, lw=line_width, zorder=2, joinstyle='round')
                    ax.add_patch(patch)
                shape_paths[n['id']] = [patch.get_path()]
                if shape == 'data':
                    shape_paths[n['id']].append(cap.get_path().transformed(cap.get_patch_transform()))

                if shape != 'group' and n.get('accent') in ('left', 'top'):
                    from matplotlib.patches import Rectangle
                    accent_side = n['accent']
                    accent_c = color(n.get('accent_color', n.get('stroke_color', design.get('connector_color', '#334E68'))))
                    stripe_w = 3.0
                    if accent_side == 'left':
                        stripe_rect = Rectangle((x, y), stripe_w, h, facecolor=accent_c, edgecolor='none', zorder=2.3)
                    else:
                        stripe_rect = Rectangle((x, y), w, stripe_w, facecolor=accent_c, edgecolor='none', zorder=2.3)
                    ax.add_patch(stripe_rect)
                    stripe_rect.set_clip_path(patch)

                if shape != 'group' and n.get('badge'):
                    badge_str = str(n['badge']).strip()
                    badge_font = max(6.0, base - 2.5)
                    badge_fg = color(n.get('badge_text_color', '#FFFFFF'))
                    badge_bg = color(n.get('badge_fill', n.get('accent_color', design.get('connector_color', '#334E68'))))
                    if 'badge_fill' not in n and contrast(badge_fg, badge_bg) < 4.5:
                        badge_bg = color(design.get('connector_color', '#1E293B'))
                    t_badge = ax.text(0, 0, badge_str, fontsize=badge_font, fontweight='bold')
                    tb = t_badge.get_window_extent(measurement_renderer).transformed(ax.transData.inverted())
                    t_badge.remove()
                    tbw = max(tb.x1 - tb.x0 + 8.0, 18.0)
                    tbh = max(tb.y1 - tb.y0 + 3.0, 9.0)
                    bx_offset = 10.0 if shape in ('input', 'terminator') else 4.0
                    bx, by = x + bx_offset, y + 3.5
                    badge_pill = FancyBboxPatch((bx, by), tbw, tbh, boxstyle='round,pad=0,rounding_size=2.5',
                                               facecolor=badge_bg, edgecolor='none', zorder=3.5)
                    ax.add_patch(badge_pill)
                    ax.text(bx + tbw / 2, by + tbh / 2, badge_str, ha='center', va='center',
                            fontsize=badge_font, fontweight='bold', color=badge_fg, zorder=3.6)
                    b_ratio = contrast(badge_fg, badge_bg)
                    if b_ratio < 4.5:
                        report['errors'].append(f'Badge {n["id"]}:badge contrast is {b_ratio:.2f}, below 4.5')
                    badge_bounds = (bx, by, bx + tbw, by + tbh)
                    badges.append((f'{n["id"]}:badge', badge_bounds))
                    report['text'].append({
                        'id': f'{n["id"]}:badge',
                        'node_id': n['id'],
                        'text': badge_str,
                        'font_pt': badge_font,
                        'bounds_pt': list(badge_bounds),
                        'contrast': round(b_ratio, 3)
                    })

            placed_icons=[];icon_artists={}
            for icon in spec.get('icons', []):
                placement=icon.get('placement','left' if 'node' in icon else 'fixed')
                if 'vector_icon' in icon:
                    vname = icon['vector_icon']
                    vcol = color(icon.get('color', icon.get('stroke_color', design.get('connector_color', '#334E68'))))
                    vlw = number(icon.get('line_width_pt', 1.15), 'icon.line_width_pt')
                    if placement == 'title':
                        nx,ny,nw,nh=nodes[icon['node']]['box'];w,h=icon['size_pt']
                        x,y=nx+(nw-w)/2,ny+(nh-h)/2
                        iw,ih=w,h
                    else:
                        x,y,w,h=icon['box']
                        iw,ih=w,h
                    bounds=(x,y,x+iw,y+ih)
                    if placement != 'title':
                        artists = draw_vector_icon(ax, (x, y, iw, ih), vname, color=vcol, line_width=vlw, zorder=4.0)
                        icon_artists[icon['id']] = artists
                    else:
                        icon_artists[icon['id']] = None
                    placed_icons.append([icon, bounds, None, None])
                    report['icons'].append({
                        'id': icon['id'], 'alt': icon['alt'], 'vector_icon': vname,
                        'node_id': icon.get('node'), 'placement': placement,
                        'bounds_pt': list(bounds), 'format': 'vector'
                    })
                    continue
                root_dir=Path(asset_dir or '.').resolve()
                source=(root_dir/icon['path']).resolve()
                if not source.is_relative_to(root_dir):raise ValueError('Icon path escapes its asset directory')
                if icon['path'].lower().endswith('.svg'):
                    svg_info = load_local_svg(source)
                    vx, vy, vw, vh = svg_info['viewBox']
                    if vw <= 0 or vh <= 0:
                        vw, vh = 24.0, 24.0
                    if placement == 'title':
                        nx, ny, nw, nh = nodes[icon['node']]['box']; w, h = icon['size_pt']
                        x, y = nx + (nw - w) / 2, ny + (nh - h) / 2
                    else:
                        x, y, w, h = icon['box']
                    scale = min(w / vw, h / vh)
                    iw, ih = vw * scale, vh * scale
                    x += (w - iw) / 2; y += (h - ih) / 2
                    bounds = (x, y, x + iw, y + ih)
                    vcol = color(icon.get('color', icon.get('stroke_color', design.get('connector_color', '#334E68'))))
                    if placement != 'title':
                        artists = draw_svg_file(ax, (x, y, iw, ih), source, color_override=vcol, zorder=4.0)
                        icon_artists[icon['id']] = artists
                    else:
                        icon_artists[icon['id']] = None
                    placed_icons.append([icon, bounds, source, None])
                    report['icons'].append({
                        'id': icon['id'], 'alt': icon['alt'], 'path': icon['path'],
                        'node_id': icon.get('node'), 'placement': placement,
                        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'bounds_pt': list(bounds), 'format': 'vector-svg'
                    })
                    continue
                from PIL import Image
                with Image.open(source) as raw_icon:
                    if raw_icon.format != 'PNG' or raw_icon.width*raw_icon.height > 16_777_216 or getattr(raw_icon,'n_frames',1)!=1:
                        raise ValueError('Icons must be single-frame PNGs, maximum 16 megapixels')
                    image=raw_icon.convert('RGBA')
                alpha=image.getchannel('A')
                if alpha.getbbox() is None or alpha.getextrema()[0] == 255:
                    raise ValueError('Icon must have visible foreground and genuine transparency: '+icon['id'])
                if any(alpha.crop(b).getbbox() for b in [(0,0,image.width,1),(0,image.height-1,image.width,image.height),
                                                         (0,0,1,image.height),(image.width-1,0,image.width,image.height)]):
                    raise ValueError('Icon border must be transparent; prepare/crop with margin: '+icon['id'])
                if placement=='title':
                    nx,ny,nw,nh=nodes[icon['node']]['box'];w,h=icon['size_pt']
                    x,y=nx+(nw-w)/2,ny+(nh-h)/2  # resolved with measured title below
                else:x,y,w,h=icon['box']
                scale=min(w/image.width,h/image.height)
                iw,ih=image.width*scale,image.height*scale
                x+=(w-iw)/2;y+=(h-ih)/2
                bounds=(x,y,x+iw,y+ih)
                native_dpi=72/scale
                if native_dpi < 300:report['errors'].append(f'Icon {icon["id"]} has only {native_dpi:.0f} native DPI; use a larger source or smaller placement')
                if min(iw,ih)<12:report['warnings'].append(f'Icon {icon["id"]} is smaller than 12 pt; inspect at print size')
                artist=ax.imshow(bleed_transparent_rgb(image),extent=(x,x+iw,y+ih,y),origin='upper',aspect='auto',
                          interpolation='hanning',interpolation_stage='rgba',zorder=4)
                icon_artists[icon['id']]=artist
                placed_icons.append([icon,bounds,source,image])
                report['icons'].append({'id':icon['id'],'alt':icon['alt'],'path':icon['path'],
                    'node_id':icon.get('node'),'placement':placement,
                    'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_size_px':list(image.size),
                    'bounds_pt':list(bounds),'native_dpi':round(native_dpi,2),'background_review':'pending human inspection'})
            labels=[]
            report['resolved_ports']=[]
            for i,e in enumerate(spec.get('edges',[])):
                points=[tuple(p) for p in e['points']];eid=str(e.get('id',i))
                if not on_boundary(points[0],nodes[e['from']]['box']) or not on_boundary(points[-1],nodes[e['to']]['box']):
                    report['errors'].append(f'Edge {eid} does not meet its named node boundaries')
                else:
                    try:
                        start = shape_port(points[0],points[1],nodes[e['from']]['box'],shape_paths[e['from']])
                        end = shape_port(points[-1],points[-2],nodes[e['to']]['box'],shape_paths[e['to']])
                        points[0], points[-1] = start, end
                    except ValueError as exc:
                        report['errors'].append(f'Edge {eid}: {exc}')
                report['resolved_ports'].append({'id':eid,'start':list(points[0]),'end':list(points[-1])})
                style=(0,(3,2)) if e.get('style')=='dashed' else 'solid'
                commands,samples=rounded_route(points,bend);routes.append((e,samples))
                edge_routes_by_id[eid] = (e, commands, samples)
                arrow_scale = number(design.get('arrow_scale', 6.0), 'style.arrow_scale')
                ax.add_patch(FancyArrowPatch(path=plot_path(commands),arrowstyle={'end':'-|>,head_length=0.55,head_width=0.28','both':'<|-|>,head_length=0.55,head_width=0.28','none':'-'}[e.get('arrow','end')],mutation_scale=arrow_scale,
                    color=color(e.get('color', connector_color)),linewidth=connector_width,linestyle=style,
                    shrinkA=0,shrinkB=.4,zorder=1,joinstyle='round',capstyle='round'))
                if e.get('label') and e['label'].strip():
                    raw_edge_label = e['label'].strip()
                    edge_label_text, edge_use_math = _resolve_math(raw_edge_label, e, canvas.get('math') is True)
                    edge_label_size = max(minimum, base - 0.5)
                    seg_lengths = [math.dist(points[k], points[k+1]) for k in range(len(points)-1)]
                    longest_idx = seg_lengths.index(max(seg_lengths))
                    mid_a, mid_b = points[longest_idx], points[longest_idx+1]
                    mid_x = (mid_a[0] + mid_b[0]) / 2
                    mid_y = (mid_a[1] + mid_b[1]) / 2
                    edge_text_color = color(e.get('label_color', e.get('text_color', '#334155')))
                    if contrast(edge_text_color, '#FFFFFF') < 4.5:
                        edge_text_color = '#000000'
                    if not edge_use_math:
                        missing = sorted({ord(c) for c in raw_edge_label if not c.isspace() and ord(c) not in supported_codepoints})
                        if missing:
                            report['errors'].append(f'Edge {eid} label has missing glyphs in {font}: ' + ', '.join(f'U+{c:04X}' for c in missing))
                    else:
                        import re as _re
                        plain_parts = _re.split(r'\$[^$]*\$', edge_label_text)
                        missing = sorted({ord(c) for part in plain_parts for c in part if not c.isspace() and ord(c) not in supported_codepoints})
                        if missing:
                            report['errors'].append(f'Edge {eid} label has missing glyphs in {font}: ' + ', '.join(f'U+{c:04X}' for c in missing))
                    edge_text_artist = ax.text(mid_x, mid_y, edge_label_text, ha='center', va='center',
                                               fontsize=edge_label_size, color=edge_text_color, linespacing=1.13,
                                               zorder=6, parse_math=edge_use_math,
                                               bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='none', alpha=1.0))
                    try:
                        eb = edge_text_artist.get_window_extent(measurement_renderer).transformed(ax.transData.inverted())
                        edge_bounds = (min(eb.x0, eb.x1), min(eb.y0, eb.y1), max(eb.x0, eb.x1), max(eb.y0, eb.y1))
                    except ValueError as exc:
                        report['errors'].append(f'Edge {eid} label has invalid math syntax: {exc}')
                        edge_bounds = (mid_x, mid_y, mid_x, mid_y)
                    if edge_bounds[0] < 0 or edge_bounds[1] < 0 or edge_bounds[2] > width or edge_bounds[3] > height:
                        report['errors'].append(f'Edge label edge:{eid}:label lies outside the canvas')
                    report['text'].append({
                        'id': f'edge:{eid}:label',
                        'node_id': None,
                        'text': raw_edge_label,
                        'font_pt': edge_label_size,
                        'bounds_pt': list(edge_bounds),
                        'contrast': round(contrast(edge_text_color, '#FFFFFF'), 3)
                    })
                    labels.append((f'edge:{eid}:label', edge_bounds, edge_text_artist))
                    for node in spec['nodes']:
                        if node.get('shape') == 'group':
                            continue
                        nx, ny, nw, nh = node['box']
                        if intersects(edge_bounds, (nx, ny, nx+nw, ny+nh)):
                            report['errors'].append(f'Edge label edge:{eid}:label overlaps node {node["id"]}')

                for node in spec['nodes']:
                    if node['id'] in {e['from'],e['to']} or node.get('shape')=='group':continue
                    x,y,w,h=node['box']
                    nshape = node.get('shape', 'process')
                    if nshape in ('decision', 'input') and node['id'] in shape_paths:
                        node_paths = shape_paths[node['id']]
                        edge_hits_node = False
                        for a_pt, b_pt in zip(samples, samples[1:]):
                            if not segment_hits(a_pt, b_pt, (x+.5, y+.5, x+w-.5, y+h-.5)):
                                continue
                            for step in range(11):
                                t = step / 10.0
                                test_pt = (a_pt[0]*(1-t) + b_pt[0]*t, a_pt[1]*(1-t) + b_pt[1]*t)
                                if any(p.contains_point(test_pt) for p in node_paths):
                                    edge_hits_node = True
                                    break
                            if edge_hits_node:
                                break
                        if edge_hits_node:
                            report['errors'].append(f'Edge {eid} crosses unrelated node {node["id"]}')
                    else:
                        if any(segment_hits(a,b,(x+.5,y+.5,x+w-.5,y+h-.5)) for a,b in zip(samples,samples[1:])):
                            report['errors'].append(f'Edge {eid} crosses unrelated node {node["id"]}')
            allowed = {frozenset(item['edges']): item['reason'] for item in spec.get('allowed_crossings', [])}
            report['connector_crossings'] = list(connector_crossings(routes))
            for meeting in report['connector_crossings']:
                pair = meeting['edges']
                reason = allowed.get(frozenset(pair))
                if reason:
                    meeting['review_reason'] = reason
                    report['warnings'].append(f"Reviewed route {meeting['kind']} {pair[0]} / {pair[1]}: {reason}")
                    if design.get('crossing_jump', True):
                        cx, cy = meeting['point_pt']
                        ax.add_patch(Ellipse((cx, cy), connector_width + 4.0, connector_width + 4.0,
                                             facecolor='white', edgecolor='none', zorder=1.1))
                        route_info = edge_routes_by_id.get(str(pair[1]))
                        if route_info:
                            e2, e2_cmds, _ = route_info
                            ax.add_patch(FancyArrowPatch(path=plot_path(e2_cmds),
                                                         arrowstyle={'end':'-|>,head_length=0.55,head_width=0.28','both':'<|-|>,head_length=0.55,head_width=0.28','none':'-'}[e2.get('arrow','end')],
                                                         mutation_scale=arrow_scale,
                                                         color=color(e2.get('color', connector_color)),
                                                         linewidth=connector_width,
                                                         linestyle=(0,(3,2)) if e2.get('style')=='dashed' else 'solid',
                                                         shrinkA=0, shrinkB=.4, zorder=1.2, joinstyle='round', capstyle='round'))
                else:
                    report['errors'].append(f"Route {meeting['kind']} between edges {pair[0]} and {pair[1]} at {meeting['point_pt']}")
            def add_label(record, identifier, *, annotation=False):
                x,y,w,h=record['box'];shape=record.get('shape','process');padding=record.get('padding_pt',5)
                if shape != 'group' and not annotation and ('detail' not in record or identifier == record.get('id')):
                    if record.get('accent') == 'left':
                        x += 3.5
                        w -= 3.5
                    elif record.get('accent') == 'top':
                        y += 3.5
                        h -= 3.5
                    if record.get('badge'):
                        y += 12.0
                        h -= 12.0
                if shape=='data':padding=max(padding,7)
                if shape=='input':padding=max(padding,10)
                if shape=='decision':
                    # Inscribed rectangle, not the diamond's wider bounding rectangle.
                    x+=w/4;y+=h/4;w/=2;h/=2
                if shape=='group':
                    h=min(h,record.get('label_height_pt',34));padding=4
                size=record.get('font_pt',base)
                requested_size = size
                label_text, use_math = _resolve_math(record['label'], record, canvas.get('math') is True)
                if not use_math:
                    missing=sorted({ord(c) for c in record['label'] if not c.isspace() and ord(c) not in supported_codepoints})
                    if missing:
                        report['errors'].append(f'Label {identifier} has missing glyphs in {font}: '+', '.join(f'U+{c:04X}' for c in missing))
                else:
                    import re as _re
                    plain_parts = _re.split(r'\$[^$]*\$', label_text)
                    missing = sorted({ord(c) for part in plain_parts for c in part if not c.isspace() and ord(c) not in supported_codepoints})
                    if missing:
                        report['errors'].append(f'Label {identifier} has missing glyphs in {font}: '+', '.join(f'U+{c:04X}' for c in missing))
                if size < minimum:
                    report['errors'].append(f'Label {identifier} is below the minimum font size')
                alignment = record.get('align', 'center')
                label_x = x + padding if alignment == 'left' else x + w / 2
                text=ax.text(label_x,y+h/2,'',ha=alignment,va='center',fontweight='bold' if record.get('bold',False) else 'normal',
                    fontsize=size,color=color(record.get('text_color','black')),linespacing=1.13,zorder=5,parse_math=use_math)
                def bounds():
                    b=text.get_window_extent(measurement_renderer).transformed(ax.transData.inverted())
                    return min(b.x0,b.x1),min(b.y0,b.y1),max(b.x0,b.x1),max(b.y0,b.y1)
                def measure(value):
                    text.set_text(value)
                    left, _, right, _ = bounds()
                    return right - left
                while True:
                    text.set_fontsize(size)
                    try:
                        wrapped=wrap_label(label_text,w-2*padding,measure,math=use_math);text.set_text(wrapped);b=bounds()
                    except ValueError as exc:
                        report['errors'].append(f'Label {identifier} has invalid math syntax: {exc}')
                        b=(x,y,x+w,y+h);wrapped=label_text;break
                    epsilon = 1e-6
                    if b[0] >= x+padding-epsilon and b[2] <= x+w-padding+epsilon and b[1] >= y+padding-epsilon and b[3] <= y+h-padding+epsilon:break
                    if size <= minimum:
                        report['errors'].append(f'Label {identifier} overflows at {minimum:g} pt; enlarge/reflow the layout')
                        break
                    size=max(minimum,round(size-.25,2))
                if size < requested_size:
                    report['warnings'].append(f'Label {identifier} font shrunk from {requested_size:g} pt to {size:g} pt to fit')
                # Group frames and annotations have no background patch unless container_fill is specified.
                bg = (record.get('container_fill') or 'white') if shape == 'group' else ('white' if annotation else record.get('fill', 'white'))
                ratio=contrast(color(record.get('text_color','black')),color(bg))
                if ratio < 4.5:report['errors'].append(f'Label {identifier} contrast is {ratio:.2f}, below 4.5')
                labels.append((identifier,b,text))
                report['text'].append({'id':identifier,'node_id':record.get('id'),'text':wrapped,'font_pt':size,'bounds_pt':list(b),'contrast':round(ratio,3)})
            def content_box(n):
                x,y,w,h=n['box'];pad=n.get('padding_pt',5);shape=n.get('shape','process')
                if shape=='decision':x+=w/4;y+=h/4;w/=2;h/=2
                left=max(pad,10 if shape=='input' else 6 if shape=='data' else pad)
                top=max(pad,8 if shape=='data' else pad)
                inner=[x+left,y+top,w-2*left,h-top-pad]
                if n.get('accent') == 'left':
                    inner[0] += 3.5
                    inner[2] -= 3.5
                elif n.get('accent') == 'top':
                    inner[1] += 3.5
                    inner[3] -= 3.5
                if n.get('badge'):
                    inner[1] += 12.0
                    inner[3] -= 12.0
                if min(inner[2:])<=0:raise ValueError('Node too small for compact title/detail text')
                return inner
            def move_label(j,cx,cy):
                identifier,_,artist=labels[j];artist.set_position((cx,cy))
                b=artist.get_window_extent(measurement_renderer).transformed(ax.transData.inverted())
                measured=(min(b.x0,b.x1),min(b.y0,b.y1),max(b.x0,b.x1),max(b.y0,b.y1))
                labels[j]=(identifier,measured,artist)
                rec = next((t for t in report['text'] if t['id'] == identifier), None)
                if rec is not None:
                    rec['bounds_pt'] = list(measured)
            for n in spec['nodes']:
                attached=[(j,i) for j,i in enumerate(spec.get('icons',[])) if i.get('node')==n['id']]
                if attached and attached[0][1].get('placement')=='title':
                    j,icon=attached[0];inner=content_box(n)
                    _,bounds,_,_=placed_icons[j];iw,ih=bounds[2]-bounds[0],bounds[3]-bounds[1]
                    gap=icon.get('gap_pt',4);tw=inner[2]-iw-gap
                    if tw<=0:raise ValueError('No room for title beside icon; choose another placement')
                    start=len(labels)
                    title_record=dict(n,box=[inner[0],inner[1],tw,inner[3]],shape='process',align='center',
                                      bold=True if 'detail' in n else n.get('bold',False),padding_pt=0)
                    title_record.pop('accent', None)
                    title_record.pop('badge', None)
                    add_label(title_record,n['id']+':title' if 'detail' in n else n['id'])
                    tb=labels[start][1];title_w,title_h=tb[2]-tb[0],tb[3]-tb[1]
                    row_h=max(title_h,ih);detail_h=0.;stack_gap=design.get('title_detail_gap_pt',3.5) if 'detail' in n else 0.
                    if 'detail' in n:
                        detail_record=dict(n,box=inner,shape='process',label=n['detail'],bold=False,padding_pt=0,align='center',
                                           font_pt=n.get('detail_font_pt',design.get('detail_font_pt',base)),
                                           text_color=n.get('detail_color',design.get('detail_color',n.get('text_color','black'))))
                        detail_record.pop('accent', None)
                        detail_record.pop('badge', None)
                        add_label(detail_record,n['id']+':detail')
                        db=labels[start+1][1];detail_h=db[3]-db[1]
                    total=row_h+stack_gap+detail_h
                    if total>inner[3]+.01:report['errors'].append(f'Icon/title stack {n["id"]} overflows; compare side placement or reflow the node')
                    top=inner[1]+(inner[3]-total)/2;left=inner[0]+(inner[2]-iw-gap-title_w)/2
                    move_label(start,left+iw+gap+title_w/2,top+row_h/2)
                    if 'detail' in n:move_label(start+1,inner[0]+inner[2]/2,top+row_h+stack_gap+detail_h/2)
                    image_top=top+(row_h-ih)/2;resolved=(left,image_top,left+iw,image_top+ih)
                    placed_icons[j][1]=resolved;report['icons'][j]['bounds_pt']=list(resolved)
                    if icon.get('vector_icon'):
                        vname = icon['vector_icon']
                        vcol = color(icon.get('color', icon.get('stroke_color', design.get('connector_color', '#334E68'))))
                        vlw = number(icon.get('line_width_pt', 1.15), 'icon.line_width_pt')
                        artists = draw_vector_icon(ax, (left, image_top, iw, ih), vname, color=vcol, line_width=vlw, zorder=4.0)
                        icon_artists[icon['id']] = artists
                    elif str(icon.get('path', '')).lower().endswith('.svg'):
                        vcol = color(icon.get('color', icon.get('stroke_color', design.get('connector_color', '#334E68'))))
                        artists = draw_svg_file(ax, (left, image_top, iw, ih), placed_icons[j][2], color_override=vcol, zorder=4.0)
                        icon_artists[icon['id']] = artists
                    else:
                        icon_artists[icon['id']].set_extent((left,left+iw,image_top+ih,image_top))
                    continue
                if attached:
                    mode=attached[0][1].get('placement','left');n=copy.deepcopy(n);x,y,w,h=n['box'];reserve=n['icon_space_pt']
                    n['box']={'left':[x+reserve,y,w-reserve,h],'right':[x,y,w-reserve,h],'top':[x,y+reserve,w,h-reserve]}[mode]
                if 'detail' not in n or n.get('shape')=='group':
                    add_label(n,n['id']);continue
                # Keep title and explanation together as one centred content stack,
                # rather than centring them in arbitrarily tall separate bands.
                # Existing explicit band heights retain their older behaviour.
                if n.get('text_layout','bands' if 'title_height_pt' in n else 'stacked')=='stacked':
                    inner=content_box(n)
                    start=len(labels)
                    add_label(dict(n,box=inner,shape='process',bold=True,padding_pt=0),n['id']+':title')
                    add_label(dict(n,box=inner,shape='process',label=n['detail'],bold=False,padding_pt=0,
                                   font_pt=n.get('detail_font_pt',design.get('detail_font_pt',base)),
                                   text_color=n.get('detail_color',design.get('detail_color',n.get('text_color','black')))),n['id']+':detail')
                    heights=[labels[j][1][3]-labels[j][1][1] for j in (start,start+1)]
                    gap=design.get('title_detail_gap_pt',3.5);total=sum(heights)+gap
                    if total>inner[3]+.01:
                        report['errors'].append(f'Combined title/detail {n["id"]} overflows; enlarge/reflow the node')
                    cursor=inner[1]+(inner[3]-total)/2
                    for j,lh in zip((start,start+1),heights):
                        label_x = inner[0] if n.get('align') == 'left' else inner[0] + inner[2] / 2
                        move_label(j,label_x,cursor+lh/2)
                        cursor+=lh+gap
                    continue
                x,y,w,h=n['box'];split=n.get('title_height_pt',22 if n.get('shape')=='data' else 18)
                if not 0 < split < h:
                    raise ValueError(f"Node {n['id']} title_height_pt must lie within its box")
                # Measure title and body separately: local bold hierarchy without mathtext
                # escaping or rasterising the editable labels.
                title=dict(n,box=[x,y,w,split],shape='process',bold=True,padding_pt=3)
                detail=dict(n,box=[x,y+split,w,h-split],shape='process',label=n['detail'],bold=False,padding_pt=3,
                            font_pt=n.get('detail_font_pt',design.get('detail_font_pt',base)),
                            text_color=n.get('detail_color',design.get('detail_color',n.get('text_color','black'))))
                if n.get('shape')=='data':
                    # Clear the entire six-point cylinder cap, including its stroke.
                    if split <= 9:raise ValueError('Data-node title band must clear the cylinder cap')
                    title['box']=[x+6,y+7,w-12,split-7];title['padding_pt']=2
                    detail['box']=[x+6,y+split,w-12,h-split-2]
                elif n.get('shape')=='input':
                    title['box']=[x+6,y+2,w-12,split-2]
                    detail['box']=[x+6,y+split,w-12,h-split-2]
                add_label(title,n['id']+':title');add_label(detail,n['id']+':detail')
            for i,n in enumerate(spec.get('annotations',[])):add_label(n,f'annotation-{i}',annotation=True)
            for ann_idx, note in enumerate(spec.get('annotations', [])):
                ann_rec = next((t for t in report['text'] if t['id'] == f'annotation-{ann_idx}'), None)
                if ann_rec:
                    ann_bounds = tuple(ann_rec['bounds_pt'])
                else:
                    ax_a, ay_a, aw_a, ah_a = note['box']
                    ann_bounds = (ax_a, ay_a, ax_a+aw_a, ay_a+ah_a)
                for node in spec['nodes']:
                    if node.get('shape') == 'group':
                        continue
                    nx, ny, nw, nh = node['box']
                    if intersects(ann_bounds, (nx, ny, nx+nw, ny+nh)):
                        report['errors'].append(f'Annotation annotation-{ann_idx} overlaps node {node["id"]}')

            for grp in spec['nodes']:
                if grp.get('shape') != 'group':
                    continue
                grp_rec = next((t for t in report['text'] if t['id'] == grp['id']), None)
                if grp_rec is None:
                    continue
                glb = tuple(grp_rec['bounds_pt'])
                for child in spec['nodes']:
                    if child.get('shape') == 'group' or child['id'] == grp['id']:
                        continue
                    cx, cy, cw, ch = child['box']
                    if intersects(glb, (cx, cy, cx+cw, cy+ch)):
                        report['errors'].append(f'Group label {grp["id"]} overlaps child node {child["id"]}')

            if 'legend' in spec:
                leg = spec['legend']
                lx, ly, lw, lh = leg['box']
                has_frame = leg.get('frame') is True
                leg_fill = color(leg.get('fill', '#FFFFFF'))
                leg_stroke = color(leg.get('stroke_color', '#CBD5E1'))
                leg_text_color = color(leg.get('text_color', '#334155'))
                if has_frame:
                    leg_patch = FancyBboxPatch((lx, ly), lw, lh, boxstyle='round,pad=0,rounding_size=3',
                                               facecolor=leg_fill, edgecolor=leg_stroke, lw=line_width, zorder=2.0)
                    ax.add_patch(leg_patch)
                items = leg.get('items', [])
                if items:
                    p_min = PROFILES[profile].get('min_font', 8.0 if profile == 'plos-one' else 0.0) if (profile and profile in PROFILES) else 0.0
                    leg_font_size = max(p_min, 7.5 if minimum <= 8.5 else max(7.5, min(8.0, minimum - 0.5)))
                    line_swatch_w = 22.0
                    node_swatch_w = 11.0
                    node_swatch_h = 6.5
                    text_gap = 5.0
                    item_widths = []
                    for it in items:
                        is_line = it.get('kind') == 'edge' or it.get('shape') == 'line'
                        sw = line_swatch_w if is_line else node_swatch_w
                        tmp_txt = ax.text(0, 0, it['label'], fontsize=leg_font_size, linespacing=1.13)
                        tb_tmp = tmp_txt.get_window_extent(measurement_renderer).transformed(ax.transData.inverted())
                        tw = abs(tb_tmp.x1 - tb_tmp.x0)
                        tmp_txt.remove()
                        item_widths.append(sw + text_gap + tw)

                    use_cols = 'columns' in leg
                    num_cols = leg.get('columns', len(items))
                    if not use_cols:
                        desired_gap = 14.0
                        total_items_w = sum(item_widths) + max(0, len(items) - 1) * desired_gap
                        if total_items_w <= lw - 12:
                            start_x = lx + (lw - total_items_w) / 2
                            item_xs = []
                            cur_x = start_x
                            for w in item_widths:
                                item_xs.append(cur_x)
                                cur_x += w + desired_gap
                            slot_widths = [w + desired_gap for w in item_widths]
                        else:
                            slot_w = (lw - 12) / len(items)
                            item_xs = [lx + 6 + idx * slot_w for idx in range(len(items))]
                            slot_widths = [slot_w] * len(items)
                    else:
                        slot_w = (lw - 12) / num_cols
                        item_xs = [lx + 6 + idx * slot_w for idx in range(len(items))]
                        slot_widths = [slot_w] * len(items)

                    for idx, it in enumerate(items):
                        ix = item_xs[idx]
                        iy = ly + lh / 2
                        slot_w = slot_widths[idx]
                        scol = color(it.get('color', it.get('fill', '#334E68')))
                        s_stroke = color(it.get('stroke_color', scol))
                        is_line = it.get('kind') == 'edge' or it.get('shape') == 'line'
                        swatch_w = line_swatch_w if is_line else node_swatch_w
                        if is_line:
                            is_dashed = it.get('style') == 'dashed' or it.get('border_style') == 'dashed'
                            l_style = (0, (3.2, 2.0)) if is_dashed else 'solid'
                            if it.get('arrow', 'end') != 'none':
                                ax.add_patch(FancyArrowPatch((ix, iy), (ix + swatch_w, iy),
                                                             arrowstyle='-|>,head_length=0.5,head_width=0.25', mutation_scale=6.0,
                                                             color=scol, linewidth=1.15,
                                                             linestyle=l_style, zorder=2.2))
                            else:
                                ax.plot([ix, ix + swatch_w], [iy, iy], color=scol,
                                        lw=1.15, ls=l_style, zorder=2.2)
                        else:
                            ax.add_patch(FancyBboxPatch((ix, iy - node_swatch_h / 2), swatch_w, node_swatch_h,
                                                        boxstyle='round,pad=0,rounding_size=1.0',
                                                        facecolor=scol, edgecolor=s_stroke, lw=0.6, zorder=2.2))
                        lt = ax.text(ix + swatch_w + text_gap, iy, it['label'], ha='left', va='center',
                                     fontsize=leg_font_size, color=leg_text_color, zorder=2.2)
                        tb = lt.get_window_extent(measurement_renderer).transformed(ax.transData.inverted())
                        leg_bounds = (min(tb.x0, tb.x1), min(tb.y0, tb.y1), max(tb.x0, tb.x1), max(tb.y0, tb.y1))
                        if leg_bounds[2] > min(ix + slot_w, lx + lw - 1.0) + 0.05 or leg_bounds[2] > lx + lw:
                            report['errors'].append(f'Legend item {idx} label overflows allocated slot')
                        effective_bg = leg_fill if has_frame else color(spec.get('canvas', {}).get('fill', '#FFFFFF'))
                        l_contrast = contrast(leg_text_color, effective_bg)
                        if l_contrast < 4.5:
                            report['errors'].append(f'Legend item {idx} contrast is {l_contrast:.2f}, below 4.5')
                        report['text'].append({
                            'id': f'legend:item-{idx}',
                            'node_id': None,
                            'text': it['label'],
                            'font_pt': leg_font_size,
                            'bounds_pt': list(leg_bounds),
                            'contrast': round(l_contrast, 3)
                        })
                for node in spec['nodes']:
                    if node.get('shape') == 'group': continue
                    nx, ny, nw, nh = node['box']
                    if intersects((lx, ly, lx + lw, ly + lh), (nx, ny, nx + nw, ny + nh)):
                        report['errors'].append(f'Legend overlaps node {node["id"]}')
                for ann_idx, ann in enumerate(spec.get('annotations', [])):
                    ax_a, ay_a, aw_a, ah_a = ann['box']
                    if intersects((lx, ly, lx + lw, ly + lh), (ax_a, ay_a, ax_a + aw_a, ay_a + ah_a)):
                        report['errors'].append(f'Legend overlaps annotation annotation-{ann_idx}')
                for ei, (e, samples) in enumerate(routes):
                    if any(segment_hits(a, b, (lx, ly, lx + lw, ly + lh)) for a, b in zip(samples, samples[1:])):
                        report['errors'].append(f'Edge {e.get("id", ei)} crosses legend')

            for i,(aid,ab,_) in enumerate(labels):
                for bid,bb,_ in labels[i+1:]:
                    if intersects(ab,bb):report['errors'].append(f'Labels overlap: {aid} / {bid}')
            for i,(e,samples) in enumerate(routes):
                eid = str(e.get('id', i))
                for label,b,_ in labels:
                    if label == f'edge:{eid}:label':
                        continue
                    if any(segment_hits(a,z,b) for a,z in zip(samples,samples[1:])):
                        report['errors'].append(f'Edge {eid} crosses label {label}')
            for i,(icon,bounds,_,_) in enumerate(placed_icons):
                x,y,X,Y=bounds
                for n in spec['nodes']:
                    if n.get('shape')=='group':continue
                    nx,ny,nw,nh=n['box']
                    if n['id']==icon.get('node'):
                        if not all(any(p.contains_point(pt) for p in shape_paths[n['id']]) for pt in [(x,y),(X,y),(x,Y),(X,Y)]):
                            report['errors'].append(f'Icon {icon["id"]} leaves its actual node silhouette')
                    elif intersects(bounds,(nx,ny,nx+nw,ny+nh)):
                        report['errors'].append(f'Icon {icon["id"]} overlaps unrelated node {n["id"]}')
                for other,ob,_,_ in placed_icons[i+1:]:
                    if intersects(bounds,ob):report['errors'].append(f'Icons overlap: {other["id"]} / {icon["id"]}')
                for label,b,_ in labels:
                    if intersects(bounds,b):report['errors'].append(f'Icon {icon["id"]} overlaps label {label}')
                for ei,(e,samples) in enumerate(routes):
                    if any(segment_hits(a,b,bounds) for a,b in zip(samples,samples[1:])):
                        report['errors'].append(f'Edge {e.get("id",ei)} crosses icon {icon["id"]}')
            for bid, bb in badges:
                for lid, lb, _ in labels:
                    if intersects(bb, lb):
                        report['errors'].append(f'Badge {bid} overlaps label {lid}')
                for icon, ibounds, _, _ in placed_icons:
                    if intersects(bb, ibounds):
                        report['errors'].append(f'Badge {bid} overlaps icon {icon["id"]}')
                for ei, (e, samples) in enumerate(routes):
                    if any(segment_hits(a, b, bb) for a, b in zip(samples, samples[1:])):
                        report['errors'].append(f'Edge {e.get("id", ei)} crosses badge {bid}')
            for i,a in enumerate(spec['nodes']):
                if a.get('shape')=='group':continue
                x,y,w,h=a['box']
                for b in spec['nodes'][i+1:]:
                    if b.get('shape')=='group':continue
                    X,Y,W,H=b['box']
                    if intersects((x,y,x+w,y+h),(X,Y,X+W,Y+H),gap=.25):
                        report['errors'].append(f'Nodes overlap: {a["id"]} / {b["id"]}')
            report['layout']=layout_metrics(spec,report['text'],report['icons'])
            report['warnings']+=report['layout']['advisories']
            if profile == 'plos-one':
                report['export_profile'] = {
                    'name': 'plos-one', 'reference': 'https://journals.plos.org/plosone/s/figures',
                    'scope': 'Canvas dimensions, resolution, actual font, text sizes and TIFF size'
                }
                if not 189.36 - 1e-6 <= width <= 540 or height > 630:
                    report['errors'].append('PLOS One profile expects 66.8–190.5 mm width and at most 222.3 mm height')
                if not 300 <= dpi <= 600:
                    report['errors'].append('PLOS One profile expects 300–600 DPI')
                if font not in ('Arial', 'Times New Roman', 'Symbol'):
                    report['errors'].append('PLOS One profile needs an installed Arial, Times New Roman or Symbol font. Set canvas.font_family.')
                if any(not 8 <= text['font_pt'] <= 12 for text in report['text']):
                    report['errors'].append('PLOS One profile expects 8–12 pt text')
            elif profile in PROFILES:
                p_info = PROFILES[profile]
                report['export_profile'] = {
                    'name': profile,
                    'reference': p_info['reference'],
                    'scope': 'Canvas dimensions, resolution and minimum font size'
                }
                if width > p_info['width_max'] + 1e-6:
                    report['errors'].append(f'{profile} profile expects width at most {p_info["width_max"]:.2f} pt')
                if 'height_max' in p_info and height > p_info['height_max'] + 1e-6:
                    report['errors'].append(f'{profile} profile expects height at most {p_info["height_max"]:.2f} pt')
                if not p_info['dpi_min'] <= dpi <= p_info['dpi_max']:
                    report['errors'].append(f'{profile} profile expects {p_info["dpi_min"]}–{p_info["dpi_max"]} DPI')
                if any(text['font_pt'] < p_info['min_font'] - 1e-6 for text in report['text']):
                    report['errors'].append(f'{profile} profile expects minimum {p_info["min_font"]:g} pt text')
            report['errors']=list(dict.fromkeys(report['errors']))
            report['passed_geometry_checks']=not report['errors']
            if not report['errors'] and preview_only:
                report['exports'] = [f'{stem}-preview.png', f'{stem}-print-size.png']
                fig.savefig(output_dir / report['exports'][0], dpi=150)
                fig.savefig(output_dir / report['exports'][1], dpi=96)
                report['status'] = 'preview'
            elif not report['errors']:
                svg=output_dir/f'{stem}.svg';fig.savefig(svg)
                # Standalone editable SVG: no external DTD; local glyphs, no remote resources.
                raw=re.sub(r'<!DOCTYPE[^>]*>','',svg.read_text(encoding='utf-8'),flags=re.S)
                root=ET.fromstring(raw);ns='{http://www.w3.org/2000/svg}'
                # A local plotting font may not exist on the reader's machine. Do not
                # let a single-family declaration silently fall back to Times/serif.
                for e in root.iter():
                    if 'font-family:' in e.get('style',''):
                        e.set('style',re.sub(r'font-family:([^;]+)',r"font-family:\1, 'Liberation Sans', Arial, sans-serif",e.get('style')))
                root.set('role','img');root.set('aria-labelledby','diagram-title diagram-description')
                title=ET.Element(ns+'title',{'id':'diagram-title'});title.text=spec['title'];root.insert(0,title)
                desc=ET.Element(ns+'desc',{'id':'diagram-description'});desc.text=spec.get('description',spec['title'])
                if report['icons']:desc.text+=' Icons: '+'; '.join(i['alt'] for i in report['icons'])
                root.insert(1,desc)
                ET.register_namespace('',ns[1:-1]);svg.write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
                with plt.rc_context({'svg.fonttype':'path'}):
                    fig.savefig(output_dir/f'{stem}-outlined.svg')
                for ext,res in [('pdf',dpi),('png',dpi)]:fig.savefig(output_dir/f'{stem}.{ext}',dpi=res)
                fig.savefig(output_dir/f'{stem}-preview.png',dpi=150)
                fig.savefig(output_dir/f'{stem}-print-size.png',dpi=96)
                report['exports']=[f'{stem}.{ext}' for ext in ['svg','pdf','png']]+[f'{stem}-outlined.svg']
                report['outlined_svg_label_text_editable']=False
                source_spec = copy.deepcopy(spec)
                svg_placed = [p for p in placed_icons if p[2] is not None and str(p[2]).lower().endswith('.svg')]
                raster_placed = [p for p in placed_icons if p[3] is not None]
                if raster_placed or svg_placed:
                    asset_output = output_dir / f'{stem}-assets'
                    asset_output.mkdir(exist_ok=True)
                    for item, (_, _, source_path, image) in zip(source_spec.get('icons', []), placed_icons):
                        if image is not None:
                            image.save(asset_output / f'{item["id"]}.png')
                            item['path'] = f'{stem}-assets/{item["id"]}.png'
                        elif source_path is not None and str(source_path).lower().endswith('.svg'):
                            (asset_output / f'{item["id"]}.svg').write_bytes(source_path.read_bytes())
                            item['path'] = f'{stem}-assets/{item["id"]}.svg'
                if raster_placed:
                    report['raster_icons_in_vector_exports'] = True
                    report['warnings'].append('Icons are embedded raster assets; SVG/PDF labels and shapes remain vector')
                (output_dir/f'{stem}-source.json').write_text(json.dumps(source_spec,indent=2,ensure_ascii=False),encoding='utf-8')
                report['text_editable_in_svg']=True
                if tiff:
                    from PIL import Image
                    tiff_path = output_dir / f'{stem}.tiff'
                    with Image.open(output_dir / f'{stem}.png') as rendered:
                        rendered.convert('RGB').save(tiff_path, compression='tiff_lzw', dpi=(dpi, dpi))
                    if profile == 'plos-one' and tiff_path.stat().st_size >= 10_000_000:
                        raise ValueError('PLOS One profile expects a TIFF smaller than 10 MB')
                    report['exports'].append(tiff_path.name)
                if eps:
                    eps_path = output_dir / f'{stem}.eps'
                    fig.savefig(eps_path, format='eps')
                    report['exports'].append(eps_path.name)
                if drawio:
                    try:
                        from export_drawio import write_drawio
                    except ModuleNotFoundError as exc:
                        if exc.name != 'export_drawio':
                            raise
                        from scripts.export_drawio import write_drawio
                    target = output_dir / f'{stem}.drawio'
                    write_drawio(spec, report, target, {entry[0]['id']: entry[2] for entry in placed_icons if entry[2] is not None}, color)
                    report['exports'].append(target.name)
                report['status'] = 'complete'
            else:
                fig.savefig(output_dir/f'{stem}-diagnostic.png',dpi=150)
                (output_dir/f'{stem}-attempt.json').write_text(
                    json.dumps(spec, indent=2, ensure_ascii=False), encoding='utf-8')
                report['status'] = 'geometry-or-profile-error'
        finally:
            plt.close(fig)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec',type=Path,nargs='?');p.add_argument('--output-dir',type=Path,default=Path('diagram-output'))
    p.add_argument('--stem',default='figure-01');p.add_argument('--dpi',type=int,default=600)
    p.add_argument('--check-only',action='store_true',help='Validate the specification without Matplotlib or exports')
    p.add_argument('--layout-only',action='store_true',help='Report box occupancy/spacing without packages, rendering or changing the source')
    p.add_argument('--preview-only', action='store_true', help='Render inspection PNGs and QA without final formats')
    p.add_argument('--drawio', action='store_true', help='Also export native editable diagrams.net XML')
    p.add_argument('--tiff', action='store_true', help='Also export lossless LZW TIFF at the requested DPI')
    p.add_argument('--eps', action='store_true', help='Also export vector EPS via Matplotlib')
    p.add_argument('--profile', choices=list(PROFILES.keys()), help='Check a target journal export profile')
    p.add_argument('--theme', choices=list(THEMES.keys()), help='Apply a publication theme')
    p.add_argument('--list-icons', action='store_true', help='List all available vector icons')
    p.add_argument('--require-sources', action='store_true', help='Require supplied source locators on each method node and edge')
    p.add_argument('--require-paper-figures', action='store_true', help='Require at least 2 inspected published paper figures in sources')
    args=p.parse_args()
    if args.list_icons:
        for name in list_icons():
            print(name)
        return 0
    if not args.spec:
        p.error('the following arguments are required: spec')
    try:
        def load():
            return json.loads(args.spec.read_text(encoding='utf-8-sig'))
        if args.layout_only or args.check_only:
            spec = load()
            if args.theme and 'theme' not in spec.get('style', {}):
                spec.setdefault('style', {})['theme'] = args.theme
            spec = apply_theme(spec)
            validate_spec(spec)
            prov = provenance(spec)
            if args.require_sources and prov['unlinked_method_elements']:
                raise ValueError('Source references are missing from method nodes or edges.')
            if args.require_paper_figures and prov.get('paper_figures_inspected', 0) < 2:
                raise ValueError(
                    "Paper-grounded mode requires at least 2 inspected published figure sources "
                    "(kind: 'figure' with title, locator, and doi/url). "
                    "Fetch and inspect open-access papers via scripts/fetch_papers.py and scripts/extract_pdf_figures.py first."
                )
            if args.layout_only:print(json.dumps(layout_metrics(spec),indent=2));return 0
            print('Specification valid. Rendering and visual review have not run.');return 0
        report=render(load,args.output_dir,args.stem,args.dpi,asset_dir=args.spec.parent, preview_only=args.preview_only,
                      drawio=args.drawio, tiff=args.tiff, profile=args.profile, require_sources=args.require_sources,
                      require_paper_figures=args.require_paper_figures, eps=args.eps, theme=args.theme)
        print(json.dumps({'passed_geometry_checks':report['passed_geometry_checks'],'errors':report['errors'],
                          'layout_advisories':report['layout']['advisories'],
                          'status':report['status'],'visual_review':report['visual_review'],'exports':report['exports']},indent=2))
        return 0 if report['passed_geometry_checks'] else 1
    except (ValueError,OSError,ImportError) as exc:
        print(f'Cannot render diagram: {exc}',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())

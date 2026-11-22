#!/usr/bin/env python3
"""Draw a supplied, explicitly laid-out research schematic locally from JSON.

Geometry is in points (72 points/inch), origin top left. This renderer does not
infer methods, select papers or certify scientific correctness. Matplotlib is
loaded only when rendering; schema validation needs the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

PALETTE = {"blue": "#0072B2", "sky_blue": "#56B4E9", "orange": "#E69F00",
           "green": "#009E73", "purple": "#CC79A7", "black": "#000000",
           "yellow": "#F0E442", "vermillion": "#D55E00", "white": "#FFFFFF"}


def color(value):
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
    if not str(spec.get("title", "")).strip():
        raise ValueError("A descriptive title is required")
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
        if node.get("shape", "process") not in {"process", "data", "input", "decision", "terminator", "header", "group"}:
            raise ValueError(f"Unknown shape for {node['id']}")
        if not isinstance(node.get("label"), str) or not node["label"].strip():
            raise ValueError(f"Node {node['id']} needs a label")
        color(node.get("fill", "white")); color(node.get("text_color", "black"))
        number(node.get("font_pt", font_size), "node.font_pt")
        if 'detail' in node and (not isinstance(node['detail'],str) or not node['detail'].strip()):
            raise ValueError(f"Node {node['id']} detail must be nonempty text")
    edge_ids = set()
    edges=spec.get('edges',[])
    if not isinstance(edges,list):raise ValueError('edges must be a list')
    for i, edge in enumerate(edges):
        if not isinstance(edge,dict):raise ValueError('Each edge must be an object')
        if edge.get("from") not in ids or edge.get("to") not in ids:
            raise ValueError(f"Edge {i} has an unknown endpoint")
        eid = edge.get("id", str(i))
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
        if edge.get("style", "solid") not in {"solid", "dashed"}:
            raise ValueError(f"Edge {eid} style must be solid or dashed")
        if edge.get("style") == "dashed" and not edge.get("meaning"):
            raise ValueError(f"Dashed edge {eid} needs an explicit meaning")
    annotations=spec.get('annotations',[])
    if not isinstance(annotations,list):raise ValueError('annotations must be a list')
    for note in annotations:
        if not isinstance(note,dict):raise ValueError('Each annotation must be an object')
        x,y,w,h = box(note.get("box"), "annotation")
        if x < 0 or y < 0 or x+w > width or y+h > height:
            raise ValueError("Annotation lies outside the canvas")
        if not isinstance(note.get("label"), str) or not note["label"].strip():
            raise ValueError("Annotation label is required")
    return spec


def intersects(a, b, gap=0):
    return min(a[2], b[2])-max(a[0], b[0]) > gap and min(a[3], b[3])-max(a[1], b[1]) > gap


def segment_hits(a, b, bounds):
    x0,y0,x1,y1 = bounds
    if a[0] == b[0]:
        return x0 < a[0] < x1 and min(a[1],b[1]) < y1 and max(a[1],b[1]) > y0
    return y0 < a[1] < y1 and min(a[0],b[0]) < x1 and max(a[0],b[0]) > x0


def on_boundary(point, bounds, tolerance=1.5):
    x,y,w,h = bounds; px,py = point
    return ((abs(px-x) <= tolerance or abs(px-x-w) <= tolerance) and y-tolerance <= py <= y+h+tolerance
            or (abs(py-y) <= tolerance or abs(py-y-h) <= tolerance) and x-tolerance <= px <= x+w+tolerance)


def contrast(fg, bg):
    def luminance(c):
        rgb=[int(c[i:i+2],16)/255 for i in (1,3,5)]
        rgb=[v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a,b in zip(rgb,[.2126,.7152,.0722]))
    a,b=sorted([luminance(fg),luminance(bg)])
    return (b+.05)/(a+.05)


def render(spec, output_dir, stem="figure-01", dpi=600):
    validate_spec(spec)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", stem):
        raise ValueError("stem must be a filename without paths or extensions")
    if not 150 <= dpi <= 1200:
        raise ValueError("dpi must be between 150 and 1200")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.ft2font import FT2Font
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Ellipse, PathPatch
    from matplotlib.path import Path as PlotPath
    import xml.etree.ElementTree as ET
    canvas=spec['canvas']; width=canvas['width_pt'];height=canvas['height_pt']
    minimum=canvas.get('min_font_pt',8.5);base=canvas.get('font_pt',9)
    requested_font=canvas.get('font_family','DejaVu Sans')
    try:
        font_path=font_manager.findfont(requested_font, fallback_to_default=False)
        font=font_manager.FontProperties(fname=font_path).get_name()
    except ValueError:
        font='DejaVu Sans'
        font_path=font_manager.findfont(font)
    supported_codepoints=set(FT2Font(font_path).get_charmap())
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    report={'schema_version':1,'scientific_review':'not performed by renderer',
            'visual_review':'pending human inspection','literature_review':'not performed by renderer',
            'font_requested':requested_font,'font_used':font,'matplotlib':matplotlib.__version__,
            'physical_inches':[width/72,height/72],'png_dpi':dpi,'errors':[],
            'warnings':[],'text':[],'exports':[]}
    if font != requested_font:report['warnings'].append(f'Font unavailable; substituted {font}')
    rc={'font.family':font,'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white'}
    with plt.rc_context(rc):
        fig=plt.figure(figsize=(width/72,height/72),dpi=144,facecolor='white')
        ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,width),ylim=(height,0));ax.set_axis_off()
        nodes={n['id']:n for n in spec['nodes']}
        try:
            # Draw paths before shapes/text. Explicit routes preserve semantic intent.
            for i,e in enumerate(spec.get('edges',[])):
                points=e['points']; eid=e.get('id',str(i))
                if not on_boundary(points[0],nodes[e['from']]['box']) or not on_boundary(points[-1],nodes[e['to']]['box']):
                    report['errors'].append(f'Edge {eid} does not meet its named node boundaries')
                style=(0,(3,2)) if e.get('style')=='dashed' else 'solid'
                if len(points)>2:ax.plot(*zip(*points[:-1]),color='black',lw=.85,linestyle=style,zorder=1)
                ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=6,
                    color='black',linewidth=.85,linestyle=style,shrinkA=0,shrinkB=.4,zorder=1))
                for node in spec['nodes']:
                    if node['id'] in {e['from'],e['to']} or node.get('shape')=='group':continue
                    x,y,w,h=node['box']
                    if any(segment_hits(a,b,(x+.5,y+.5,x+w-.5,y+h-.5)) for a,b in zip(points,points[1:])):
                        report['errors'].append(f'Edge {eid} crosses unrelated node {node["id"]}')
            for n in spec['nodes']:
                x,y,w,h=n['box'];shape=n.get('shape','process');fill=color(n.get('fill','white'))
                if shape in {'process','terminator','header','group'}:
                    radius=min(h/2,16) if shape=='terminator' else 5
                    patch=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={radius}',
                        facecolor='none' if shape=='group' else fill,edgecolor='black',lw=.85,
                        linestyle=(0,(3,2)) if shape=='group' else 'solid',zorder=0 if shape=='group' else 2)
                    ax.add_patch(patch)
                elif shape=='data':
                    ey=6
                    verts=[(x,y+ey/2),(x,y),(x+w,y),(x+w,y+ey/2),(x+w,y+h-ey/2),
                           (x+w,y+h),(x,y+h),(x,y+h-ey/2),(x,y+ey/2),(x,y+ey/2)]
                    codes=[PlotPath.MOVETO]+[PlotPath.CURVE4]*3+[PlotPath.LINETO]+[PlotPath.CURVE4]*3+[PlotPath.LINETO,PlotPath.CLOSEPOLY]
                    ax.add_patch(PathPatch(PlotPath(verts,codes),facecolor=fill,edgecolor='black',lw=.85,zorder=2))
                    ax.add_patch(Ellipse((x+w/2,y+ey/2),w,ey,facecolor=fill,edgecolor='black',lw=.85,zorder=3))
                else:
                    pts=[(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)] if shape=='decision' else [(x+7,y),(x+w,y),(x+w-7,y+h),(x,y+h)]
                    ax.add_patch(Polygon(pts,closed=True,facecolor=fill,edgecolor='black',lw=.85,zorder=2))
            labels=[]
            def add_label(record, identifier):
                x,y,w,h=record['box'];shape=record.get('shape','process');padding=record.get('padding_pt',5)
                if shape=='data':padding=max(padding,7)
                if shape=='input':padding=max(padding,10)
                if shape=='decision':
                    # Inscribed rectangle, not the diamond's wider bounding rectangle.
                    x+=w/4;y+=h/4;w/=2;h/=2
                if shape=='group':
                    h=min(h,record.get('label_height_pt',34));padding=4
                size=record.get('font_pt',base)
                missing=sorted({ord(c) for c in record['label'] if not c.isspace() and ord(c) not in supported_codepoints})
                if missing:
                    report['errors'].append(f'Label {identifier} has missing glyphs in {font}: '+', '.join(f'U+{c:04X}' for c in missing))
                if size < minimum:
                    report['errors'].append(f'Label {identifier} is below the minimum font size')
                text=ax.text(x+w/2,y+h/2,'',ha='center',va='center',fontweight='bold' if record.get('bold',False) else 'normal',
                    fontsize=size,color=color(record.get('text_color','black')),linespacing=1.13,zorder=5,parse_math=False)
                def bounds():
                    fig.canvas.draw(); b=text.get_window_extent(fig.canvas.get_renderer()).transformed(ax.transData.inverted())
                    return min(b.x0,b.x1),min(b.y0,b.y1),max(b.x0,b.x1),max(b.y0,b.y1)
                def wrap(raw, available):
                    lines=[]
                    for para in raw.split('\n'):
                        line=''
                        for word in para.split():
                            candidate=(line+' '+word).strip();text.set_text(candidate)
                            a,_,b,_=bounds()
                            if b-a > available and line:lines.append(line);line=word
                            else:line=candidate
                        lines.append(line)
                    return '\n'.join(lines)
                while True:
                    text.set_fontsize(size);wrapped=wrap(record['label'],w-2*padding);text.set_text(wrapped);b=bounds()
                    if b[0] >= x+padding and b[2] <= x+w-padding and b[1] >= y+padding and b[3] <= y+h-padding:break
                    if size <= minimum:
                        report['errors'].append(f'Label {identifier} overflows at {minimum:g} pt; enlarge/reflow the layout')
                        break
                    size=max(minimum,round(size-.25,2))
                ratio=contrast(color(record.get('text_color','black')),color(record.get('fill','white')))
                if ratio < 4.5:report['errors'].append(f'Label {identifier} contrast is {ratio:.2f}, below 4.5')
                labels.append((identifier,b,text))
                report['text'].append({'id':identifier,'text':wrapped,'font_pt':size,'bounds_pt':list(b),'contrast':round(ratio,3)})
            for n in spec['nodes']:
                if 'detail' not in n or n.get('shape')=='group':
                    add_label(n,n['id']);continue
                x,y,w,h=n['box'];split=n.get('title_height_pt',22 if n.get('shape')=='data' else 18)
                if not 0 < split < h:
                    raise ValueError(f"Node {n['id']} title_height_pt must lie within its box")
                # Measure title and body separately: local bold hierarchy without mathtext
                # escaping or rasterising the editable labels.
                title=dict(n,box=[x,y,w,split],shape='process',bold=True,padding_pt=3)
                detail=dict(n,box=[x,y+split,w,h-split],shape='process',label=n['detail'],bold=False,padding_pt=3,
                            font_pt=n.get('detail_font_pt',base))
                if n.get('shape')=='data':
                    # Clear the entire six-point cylinder cap, including its stroke.
                    if split <= 9:raise ValueError('Data-node title band must clear the cylinder cap')
                    title['box']=[x+6,y+7,w-12,split-7];title['padding_pt']=2
                    detail['box']=[x+6,y+split,w-12,h-split-2]
                elif n.get('shape')=='input':
                    title['box']=[x+6,y+2,w-12,split-2]
                    detail['box']=[x+6,y+split,w-12,h-split-2]
                add_label(title,n['id']+':title');add_label(detail,n['id']+':detail')
            for i,n in enumerate(spec.get('annotations',[])):add_label(n,f'annotation-{i}')
            for i,(aid,ab,_) in enumerate(labels):
                for bid,bb,_ in labels[i+1:]:
                    if intersects(ab,bb):report['errors'].append(f'Labels overlap: {aid} / {bid}')
            for i,e in enumerate(spec.get('edges',[])):
                for label,b,_ in labels:
                    if any(segment_hits(a,z,b) for a,z in zip(e['points'],e['points'][1:])):
                        report['errors'].append(f'Edge {e.get("id",i)} crosses label {label}')
            for i,a in enumerate(spec['nodes']):
                if a.get('shape')=='group':continue
                x,y,w,h=a['box']
                for b in spec['nodes'][i+1:]:
                    if b.get('shape')=='group':continue
                    X,Y,W,H=b['box']
                    if intersects((x,y,x+w,y+h),(X,Y,X+W,Y+H),gap=.25):
                        report['errors'].append(f'Nodes overlap: {a["id"]} / {b["id"]}')
            report['errors']=list(dict.fromkeys(report['errors']))
            report['passed_geometry_checks']=not report['errors']
            if not report['errors']:
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
                desc=ET.Element(ns+'desc',{'id':'diagram-description'});desc.text=spec.get('description',spec['title']);root.insert(1,desc)
                ET.register_namespace('',ns[1:-1]);svg.write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
                with plt.rc_context({'svg.fonttype':'path'}):
                    fig.savefig(output_dir/f'{stem}-outlined.svg')
                for ext,res in [('pdf',dpi),('png',dpi)]:fig.savefig(output_dir/f'{stem}.{ext}',dpi=res)
                fig.savefig(output_dir/f'{stem}-preview.png',dpi=150)
                fig.savefig(output_dir/f'{stem}-print-size.png',dpi=96)
                report['exports']=[f'{stem}.{ext}' for ext in ['svg','pdf','png']]+[f'{stem}-outlined.svg']
                report['outlined_svg_label_text_editable']=False
                (output_dir/f'{stem}-source.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
                report['text_editable_in_svg']=True
            else:
                fig.savefig(output_dir/f'{stem}-diagnostic.png',dpi=150)
        finally:
            plt.close(fig)
    (output_dir/f'{stem}-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec',type=Path);p.add_argument('--output-dir',type=Path,default=Path('diagram-output'))
    p.add_argument('--stem',default='figure-01');p.add_argument('--dpi',type=int,default=600)
    p.add_argument('--check-only',action='store_true',help='Validate the specification without Matplotlib or exports')
    args=p.parse_args()
    try:
        spec=json.loads(args.spec.read_text(encoding='utf-8-sig'));validate_spec(spec)
        if args.check_only:print('Specification valid; rendering and visual review have not run.');return 0
        report=render(spec,args.output_dir,args.stem,args.dpi)
        print(json.dumps({'passed_geometry_checks':report['passed_geometry_checks'],'errors':report['errors'],
                          'visual_review':report['visual_review'],'exports':report['exports']},indent=2))
        return 0 if report['passed_geometry_checks'] else 1
    except (ValueError,OSError,ImportError) as exc:
        print(f'Cannot render diagram: {exc}',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())

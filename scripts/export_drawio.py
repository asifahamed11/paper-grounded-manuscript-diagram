"""Write native diagrams.net vertices and edges for a checked local specification."""

from __future__ import annotations

import base64
from html import escape
import xml.etree.ElementTree as ET

try:
    from .node_shapes import SHAPES as SCIENTIFIC_SHAPES, drawio_stencil, shape_swatch_size
except ImportError:
    try:
        from scripts.node_shapes import SHAPES as SCIENTIFIC_SHAPES, drawio_stencil, shape_swatch_size
    except ImportError:
        from node_shapes import SHAPES as SCIENTIFIC_SHAPES, drawio_stencil, shape_swatch_size


PT_TO_PX = 4 / 3
SHAPES = {
    'process': 'rounded=1;',
    'terminator': 'rounded=1;arcSize=45;',
    'data': 'shape=cylinder3;size=8;',
    'decision': 'rhombus;rounded=1;',
    'input': 'shape=parallelogram;perimeter=parallelogramPerimeter;size=0.08;rounded=1;',
    'header': 'rounded=1;',
    'group': 'container=1;collapsible=0;pointerEvents=0;rounded=1;dashed=1;verticalAlign=top;',
}


def pixels(length):
    return f'{length * PT_TO_PX:.5f}'


def vertex(root, identifier, value, style, bounds, *, parent='1'):
    cell = ET.SubElement(root, 'mxCell', id=identifier, value=value, style=style, vertex='1', parent=parent)
    ET.SubElement(cell, 'mxGeometry', dict(zip(('x', 'y', 'width', 'height'), map(pixels, bounds)), **{'as': 'geometry'}))
    return cell


def write_drawio(spec, report, destination, icon_paths, color):
    """Create editable objects. The native editor can rewrap labels and reroute edges."""
    canvas = spec['canvas']
    design = spec.get('style', {})
    file = ET.Element('mxfile', host='drawio')
    page = ET.SubElement(file, 'diagram', name='Figure')
    model = ET.SubElement(page, 'mxGraphModel', page='1', pageScale='1', grid='0',
                          pageWidth=pixels(canvas['width_pt']), pageHeight=pixels(canvas['height_pt']),
                          background='#FFFFFF')
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')
    nodes = {node['id']: node for node in spec['nodes']}
    native_ids = {identifier: f'node-{i}' for i, identifier in enumerate(nodes)}
    fonts = {record['id']: record for record in report['text']}
    connector_color = design.get('connector_color', 'black')
    line_width = pixels(design.get('line_width_pt', .85))
    connector_width = pixels(design.get('connector_width_pt', design.get('line_width_pt', .85)))
    family = report['font_used'].replace(';', '').replace('=', '').replace('"', '').replace("'", '')
    font_stack = escape(f"'{family}',Arial,Helvetica,sans-serif", quote=True)
    round_style = '1' if design.get('connector_style','rounded') == 'rounded' else '0'
    ports = {str(record['id']): record for record in report['resolved_ports']}
    arc_size_px = pixels(design.get('corner_radius_pt', 5))

    def label_html(text_id, *, bold=False):
        record = fonts[text_id]
        label = escape(record['text']).replace('\n', '<br>')
        font_size = pixels(record['font_pt'])
        weight = 'bold' if bold else 'normal'
        color_attr = ''
        if text_id.endswith(':detail'):
            node_id = text_id[:-7]
            n = nodes.get(node_id, {})
            detail_col = n.get('detail_color', design.get('detail_color'))
            if detail_col:
                color_attr = f'color:{color(detail_col)};'
        return f'<div style="font-family:{font_stack};font-size:{font_size}px;font-weight:{weight};{color_attr}">{label}</div>'

    # Map each non-group node to its enclosing group container (if any)
    group_nodes = [node for node in spec['nodes'] if node.get('shape') == 'group']
    enclosing_group = {}
    for identifier, node in nodes.items():
        if node.get('shape') == 'group':
            continue
        nx, ny, nw, nh = node['box']
        candidates = []
        for grp in group_nodes:
            gx, gy, gw, gh = grp['box']
            if (nx >= gx - 1e-4 and ny >= gy - 1e-4 and
                nx + nw <= gx + gw + 1e-4 and ny + nh <= gy + gh + 1e-4):
                candidates.append(grp)
        if candidates:
            chosen = min(candidates, key=lambda g: g['box'][2] * g['box'][3])
            enclosing_group[identifier] = chosen

    # Draw containers first. Independently editable nodes retain their own labels.
    for identifier, node in sorted(nodes.items(), key=lambda pair: pair[1].get('shape') != 'group'):
        shape = node.get('shape', 'process')
        fg = color(node.get('text_color', 'black'))
        stroke = color(node.get('stroke_color', design.get('stroke_color', 'black')))
        if shape == 'group':
            c_fill = node.get('container_fill')
            bg = color(c_fill) if c_fill else 'none'
            dash_override = 'dashed=0;' if node.get('border_style') == 'solid' else 'dashed=1;'
        else:
            bg = color(node.get('fill', 'white'))
            dash_override = ''
        has_shadow = (shape != 'group') and bool(node.get('shadow', design.get('shadow', False)))
        shadow_style = 'shadow=1;' if has_shadow else ''
        arc_style = f'absoluteArcSize=1;arcSize={arc_size_px};' if shape in ('process', 'header', 'group') else ''
        base_shape = drawio_stencil(shape) if shape in SCIENTIFIC_SHAPES else SHAPES[shape]
        if shape == 'group' and dash_override:
            base_shape = base_shape.replace('dashed=1;', dash_override)
        style = (base_shape + arc_style + shadow_style + f'fillColor={bg};strokeColor={stroke};strokeWidth={line_width};'
                 f'fontFamily={family};fontColor={fg};html=1;whiteSpace=wrap;'
                 f'align={node.get("align", "center")};spacing=3;')
        if identifier+':title' in fonts:
            label = label_html(identifier+':title', bold=True) + label_html(identifier+':detail')
        else:
            label = label_html(identifier, bold=node.get('bold', False))

        parent_group = enclosing_group.get(identifier)
        if parent_group:
            parent_id = native_ids[parent_group['id']]
            gx, gy, _, _ = parent_group['box']
            nx, ny, nw, nh = node['box']
            node_bounds = (nx - gx, ny - gy, nw, nh)
        else:
            parent_id = '1'
            node_bounds = node['box']

        # Preserve the measured label positions for shapes with a reserved
        # text area or attached icon. Each label remains an editable text cell.
        separate_text = (shape in SCIENTIFIC_SHAPES
                         or any(icon.get('node_id') == identifier for icon in report['icons']))
        vertex(root, native_ids[identifier], '' if separate_text else label, style, node_bounds, parent=parent_id)
        if separate_text:
            x, y, _, _ = node['box']
            text_ids = ([identifier+':title', identifier+':detail']
                        if identifier+':title' in fonts else [identifier])
            for j, text_id in enumerate(text_ids):
                a, b, c, d = fonts[text_id]['bounds_pt']
                col = fg
                if text_id.endswith(':detail'):
                    d_col = node.get('detail_color', design.get('detail_color'))
                    if d_col:
                        col = color(d_col)
                child_text_style = (f'text;strokeColor=none;fillColor=none;html=1;whiteSpace=nowrap;align={node.get("align", "center")};'
                                    f'verticalAlign=middle;spacing=0;fontFamily={family};fontColor={col};')
                bold = text_id.endswith(':title') or (text_id == identifier and node.get('bold', False))
                vertex(root, native_ids[identifier]+f'-text-{j}', label_html(text_id, bold=bold),
                       child_text_style, (a-x-1, b-y, c-a+2, d-b), parent=native_ids[identifier])

    for i, edge in enumerate(spec.get('edges', [])):
        identifier = str(edge.get('id', i))
        resolved = ports[identifier]
        stroke = color(edge.get('color', connector_color))
        style = (f'edgeStyle=segmentEdgeStyle;rounded={round_style};strokeColor={stroke};'
                 f'strokeWidth={connector_width};html=1;')
        arrow = edge.get('arrow', 'end')
        style += f'endArrow={"none" if arrow == "none" else "blockThin"};'
        style += f'startArrow={"blockThin" if arrow == "both" else "none"};'
        if edge.get('style') == 'dashed':
            style += 'dashed=1;'
        for port_name, side, node_key in [('exit', 'start', 'from'), ('entry', 'end', 'to')]:
            x, y, w, h = nodes[edge[node_key]]['box']
            px, py = resolved[side]
            style += f'{port_name}X={(px-x)/w:.5f};{port_name}Y={(py-y)/h:.5f};{port_name}Perimeter=0;'
        
        edge_value = ''
        if edge.get('label'):
            edge_text_id = f'edge:{identifier}:label'
            if edge_text_id in fonts:
                edge_value = label_html(edge_text_id)
            else:
                edge_font_size = pixels(max(canvas.get('min_font_pt', 8.5), canvas.get('font_pt', 9) - 0.5))
                edge_label_escaped = escape(edge['label']).replace('\n', '<br>')
                edge_value = f'<div style="font-family:{font_stack};font-size:{edge_font_size}px;font-weight:normal">{edge_label_escaped}</div>'
            style += 'labelBackgroundColor=#FFFFFF;'

        cell = ET.SubElement(root, 'mxCell', id=f'edge-{i}', value=edge_value, edge='1', parent='1',
                             source=native_ids[edge['from']], target=native_ids[edge['to']], style=style)
        geometry = ET.SubElement(cell, 'mxGeometry', relative='1', **{'as': 'geometry'})
        if edge['points'][1:-1]:
            waypoints = ET.SubElement(geometry, 'Array', **{'as': 'points'})
            for x, y in edge['points'][1:-1]:
                ET.SubElement(waypoints, 'mxPoint', x=pixels(x), y=pixels(y))

    for i, note in enumerate(spec.get('annotations', [])):
        style = ('text;strokeColor=none;fillColor=none;html=1;whiteSpace=wrap;'
                 f'align={note.get("align", "center")};fontFamily={family};fontColor={color(note.get("text_color","black"))};')
        vertex(root, f'note-{i}', label_html(f'annotation-{i}', bold=note.get('bold', False)), style, note['box'])

    for i, icon in enumerate(report['icons']):
        x, y, right, bottom = icon['bounds_pt']
        owner = icon.get('node_id')
        nx, ny = nodes[owner]['box'][:2] if owner else (0, 0)
        orig_icon = next((ic for ic in spec.get('icons', []) if ic.get('id') == icon.get('id')), icon)
        if icon.get('vector_icon'):
            try:
                from .vector_icons import as_data_uri
            except ImportError:
                try:
                    from scripts.vector_icons import as_data_uri
                except ImportError:
                    from vector_icons import as_data_uri
            vcol = color(orig_icon.get('color', orig_icon.get('stroke_color', connector_color)))
            payload = as_data_uri(icon['vector_icon'], stroke=vcol)
            style = f'shape=image;imageAspect=1;image={payload};'
        elif icon.get('format') == 'vector-svg' or str(orig_icon.get('path', '')).lower().endswith('.svg'):
            svg_bytes = icon_paths[icon['id']].read_bytes()
            b64_svg = base64.b64encode(svg_bytes).decode('ascii')
            payload = f'data:image/svg+xml;base64,{b64_svg}'
            style = f'shape=image;imageAspect=1;image={payload};'
        else:
            payload = base64.b64encode(icon_paths[icon['id']].read_bytes()).decode('ascii')
            style = f'shape=image;imageAspect=1;image=data:image/png;base64,{payload};'
        vertex(root, f'icon-{i}', '', style, (x-nx, y-ny, right-x, bottom-y), parent=native_ids.get(owner, '1'))

    if 'legend' in spec:
        leg = spec['legend']
        lx, ly, lw, lh = leg['box']
        has_frame = leg.get('frame') is True
        if has_frame:
            leg_fill = color(leg.get('fill', '#FFFFFF'))
            leg_stroke = color(leg.get('stroke_color', '#CBD5E1'))
            vertex(root, 'legend-frame', '', f'rounded=1;fillColor={leg_fill};strokeColor={leg_stroke};strokeWidth={line_width};', (lx, ly, lw, lh))
        else:
            vertex(root, 'legend-frame', '', 'rounded=1;fillColor=none;strokeColor=none;', (lx, ly, lw, lh))
        leg_items = leg.get('items', [])
        if leg_items:
            text_gap = 5.0
            for idx, it in enumerate(leg_items):
                record = fonts[f'legend:item-{idx}']
                tx, ty, end_x, end_y = record['bounds_pt']
                scol = color(it.get('color', it.get('fill', '#334E68')))
                s_stroke = color(it.get('stroke_color', scol))
                shape = it.get('shape')
                is_line = it.get('kind') == 'edge' or shape == 'line'
                has_stencil = not is_line and isinstance(shape, str) and shape in SCIENTIFIC_SHAPES
                swatch_w, swatch_h = shape_swatch_size(shape) if has_stencil else (22.0 if is_line else 11.0, 6.5)
                ix = tx - swatch_w - text_gap
                iy = ly + lh / 2
                if is_line:
                    arrow = it.get('arrow', 'end')
                    end_arr = 'classic' if arrow in ('end', 'both') else 'none'
                    start_arr = 'classic' if arrow in ('start', 'both') else 'none'
                    dash_str = 'dashed=1;' if it.get('style') == 'dashed' or it.get('border_style') == 'dashed' else ''
                    l_style = f'edgeStyle=none;endArrow={end_arr};startArrow={start_arr};strokeColor={scol};strokeWidth=1.5;{dash_str}'
                    cell = ET.SubElement(root, 'mxCell', id=f'legend-swatch-{idx}', value='', edge='1', parent='1', style=l_style)
                    geom = ET.SubElement(cell, 'mxGeometry', relative='1', **{'as': 'geometry'})
                    ET.SubElement(geom, 'mxPoint', x=pixels(ix), y=pixels(iy), **{'as': 'sourcePoint'})
                    ET.SubElement(geom, 'mxPoint', x=pixels(ix + swatch_w), y=pixels(iy), **{'as': 'targetPoint'})
                else:
                    swatch_shape = drawio_stencil(shape) if has_stencil else 'rounded=1;'
                    swatch_style = f'{swatch_shape}fillColor={scol};strokeColor={s_stroke};strokeWidth=0.8;'
                    vertex(root, f'legend-swatch-{idx}', '', swatch_style, (ix, iy - swatch_h / 2, swatch_w, swatch_h))
                leg_color = color(leg.get('text_color', '#334155'))
                text_style = (f'text;strokeColor=none;fillColor=none;html=1;whiteSpace=nowrap;align=left;'
                              f'verticalAlign=middle;spacing=0;fontFamily={family};fontColor={leg_color};')
                vertex(root, f'legend-text-{idx}', label_html(record['id']), text_style,
                       (tx, ty, end_x - tx + 2, end_y - ty))

    ET.indent(file, space='  ')
    ET.ElementTree(file).write(destination, encoding='utf-8', xml_declaration=True)

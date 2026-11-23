"""Write native diagrams.net vertices and edges for a checked local specification."""

from __future__ import annotations

import base64
from html import escape
import xml.etree.ElementTree as ET


PT_TO_PX = 4 / 3
SHAPES = {
    'process': 'rounded=1;',
    'terminator': 'rounded=1;arcSize=45;',
    'data': 'shape=cylinder3;size=8;',
    'decision': 'rhombus;rounded=1;',
    'input': 'shape=parallelogram;perimeter=parallelogramPerimeter;size=0.08;rounded=1;',
    'header': 'rounded=1;',
    'group': 'rounded=1;dashed=1;verticalAlign=top;',
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
    connector_color = color(design.get('connector_color', 'black'))
    line_width = pixels(design.get('line_width_pt', .85))
    family = report['font_used'].replace(';', '').replace('=', '').replace('"', '').replace("'", '')
    font_stack = escape(f"'{family}',Arial,Helvetica,sans-serif", quote=True)
    round_style = '1' if design.get('connector_style','rounded') == 'rounded' else '0'
    ports = {str(record['id']): record for record in report['resolved_ports']}

    def label_html(text_id, *, bold=False):
        record = fonts[text_id]
        label = escape(record['text']).replace('\n', '<br>')
        font_size = pixels(record['font_pt'])
        weight = 'bold' if bold else 'normal'
        return f'<div style="font-family:{font_stack};font-size:{font_size}px;font-weight:{weight}">{label}</div>'

    # Draw containers first. Independently editable nodes retain their own labels.
    for identifier, node in sorted(nodes.items(), key=lambda pair: pair[1].get('shape') != 'group'):
        shape = node.get('shape', 'process')
        fg = color(node.get('text_color', 'black'))
        stroke = color(node.get('stroke_color', design.get('stroke_color', 'black')))
        bg = 'none' if shape == 'group' else color(node.get('fill', 'white'))
        style = (SHAPES[shape] + f'fillColor={bg};strokeColor={stroke};strokeWidth={line_width};'
                 f'fontFamily={family};fontColor={fg};html=1;whiteSpace=wrap;'
                 f'align={node.get("align", "center")};spacing=3;')
        if identifier+':title' in fonts:
            label = label_html(identifier+':title', bold=True) + label_html(identifier+':detail')
        else:
            label = label_html(identifier, bold=node.get('bold', False))
        # Copy the actual text positions into editable child cells when an icon
        # reserves part of the node, so native editing starts without collisions.
        attached = any(icon.get('node_id') == identifier for icon in report['icons'])
        vertex(root, native_ids[identifier], '' if attached else label, style, node['box'])
        if attached:
            x, y, _, _ = node['box']
            text_ids = ([identifier+':title', identifier+':detail']
                        if identifier+':title' in fonts else [identifier])
            text_style = (f'text;strokeColor=none;fillColor=none;html=1;whiteSpace=nowrap;align=center;'
                          f'verticalAlign=middle;spacing=0;fontFamily={family};fontColor={fg};')
            for j, text_id in enumerate(text_ids):
                a, b, c, d = fonts[text_id]['bounds_pt']
                vertex(root, native_ids[identifier]+f'-text-{j}', label_html(text_id, bold=text_id.endswith(':title')),
                       text_style, (a-x-1, b-y, c-a+2, d-b), parent=native_ids[identifier])

    for i, edge in enumerate(spec.get('edges', [])):
        identifier = str(edge.get('id', i))
        resolved = ports[identifier]
        style = (f'edgeStyle=segmentEdgeStyle;rounded={round_style};strokeColor={connector_color};'
                 f'strokeWidth={line_width};html=1;')
        arrow = edge.get('arrow', 'end')
        style += f'endArrow={"none" if arrow == "none" else "blockThin"};'
        style += f'startArrow={"blockThin" if arrow == "both" else "none"};'
        if edge.get('style') == 'dashed':
            style += 'dashed=1;'
        for port_name, side, node_key in [('exit', 'start', 'from'), ('entry', 'end', 'to')]:
            x, y, w, h = nodes[edge[node_key]]['box']
            px, py = resolved[side]
            style += f'{port_name}X={(px-x)/w:.5f};{port_name}Y={(py-y)/h:.5f};{port_name}Perimeter=0;'
        cell = ET.SubElement(root, 'mxCell', id=f'edge-{i}', edge='1', parent='1',
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
        payload = base64.b64encode(icon_paths[icon['id']].read_bytes()).decode('ascii')
        style = f'shape=image;imageAspect=1;image=data:image/png,{payload};'
        vertex(root, f'icon-{i}', '', style, (x-nx, y-ny, right-x, bottom-y), parent=native_ids.get(owner, '1'))

    ET.indent(file, space='  ')
    ET.ElementTree(file).write(destination, encoding='utf-8', xml_declaration=True)

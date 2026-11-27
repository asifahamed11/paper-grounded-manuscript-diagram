"""Shared scientific node geometry for the renderer, planner and Draw.io exporter."""
from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from urllib.parse import quote
from xml.etree import ElementTree as ET
import zlib


# Body parts and strokes use fractions of the node box. The separate text
# rectangle leaves space for schematic features without constraining label size.
SHAPES = {
    'tensor': {
        'meaning': 'Feature tensor, image stack or feature pyramid level',
        'palette': 'data',
        'body': (('rect', (.16, 0, .84, .78)), ('rect', (.08, .11, .84, .78)),
                 ('rect', (0, .22, .84, .78))),
        'lines': (),
        'text': (0, .22, .84, .78),
    },
    'grid': {
        'meaning': 'Token or patch grid, matrix, or schematic spatial mask',
        'palette': 'data',
        'body': (('rect', (0, 0, 1, 1)),),
        'lines': (
            ((.05, .23), (.29, .23), (.29, .77), (.05, .77), (.05, .23)),
            ((.13, .23), (.13, .77)), ((.21, .23), (.21, .77)),
            ((.05, .41), (.29, .41)), ((.05, .59), (.29, .59)),
        ),
        'text': (.32, 0, .68, 1),
    },
    'operator': {
        'meaning': 'Explicit merge, sum, subtraction or comparison operation',
        'palette': 'process',
        'body': (('ellipse', (0, 0, 1, 1)),),
        'lines': (),
        'text': (.15, .15, .70, .70),
    },
    'document': {
        'meaning': 'Protocol, annotation sheet, manifest or other named document',
        'palette': 'input',
        'body': (('polygon', ((0, 0), (.82, 0), (1, .23), (1, 1), (0, 1))),),
        'lines': (((.82, 0), (.82, .23), (1, .23)),),
        'text': (0, .23, 1, .77),
    },
    'external': {
        'meaning': 'Actor, service or source outside the system boundary',
        'palette': 'input',
        'body': (('polygon', ((.13, 0), (.87, 0), (1, .5), (.87, 1), (.13, 1), (0, .5))),),
        'lines': (),
        'text': (.13, 0, .74, 1),
    },
    'state': {
        'meaning': 'Observed condition, conceptual construct or named state',
        'palette': 'process',
        'body': (('ellipse', (0, 0, 1, 1)),),
        'lines': (),
        'text': (.15, .15, .70, .70),
    },
    'event': {
        'meaning': 'Dated milestone or discrete trigger on a timeline or flow',
        'palette': 'terminator',
        'body': (('polygon', ((0, 0), (1, 0), (1, .76), (.62, .76),
                              (.5, 1), (.38, .76), (0, .76))),),
        'lines': (),
        'text': (0, 0, 1, .76),
    },
}

STANDARD_SHAPES = {
    'process': 'Ordinary step or component',
    'data': 'Dataset, store or archive',
    'input': 'Data input or output',
    'decision': 'Condition with alternate routes',
    'terminator': 'Start, end or final output',
    'header': 'Section title',
    'group': 'Container for related elements',
}
NODE_SHAPES = (*STANDARD_SHAPES, *SHAPES)
AUTOMATIC_SHAPES = tuple(shape for shape in NODE_SHAPES if shape not in ('header', 'group'))


def shape_swatch_size(shape):
    return (12.0, 12.0) if shape == 'operator' else (18.0, 12.0)


def palette_role(shape):
    return SHAPES[shape]['palette'] if shape in SHAPES else shape


def text_fractions(shape):
    return SHAPES[shape]['text'] if shape in SHAPES else (0, 0, 1, 1)


def transform_box(bounds, fractions):
    x, y, width, height = bounds
    left, top, w, h = fractions
    return x + left * width, y + top * height, w * width, h * height


def text_box(shape, bounds):
    return transform_box(bounds, text_fractions(shape))


def list_shapes():
    return {**STANDARD_SHAPES, **{name: shape['meaning'] for name, shape in SHAPES.items()}}


def _path(parent, points, close=False):
    path = ET.SubElement(parent, 'path')
    for index, (x, y) in enumerate(points):
        ET.SubElement(path, 'move' if index == 0 else 'line', x=f'{x*100:g}', y=f'{y*100:g}')
    if close:
        ET.SubElement(path, 'close')


def _stencil_body(parent, part):
    kind, points = part
    if kind == 'polygon':
        _path(parent, points, close=True)
    else:
        ET.SubElement(parent, kind, **{key: f'{value*100:g}' for key, value in zip('xywh', points)})


@lru_cache(maxsize=len(SHAPES))
def drawio_stencil(shape):
    """Encode an inline diagrams.net stencil with its standard file encoding."""
    design = SHAPES[shape]
    root = ET.Element('shape', name=shape, w='100', h='100', aspect='variable', strokewidth='inherit')
    background = ET.SubElement(root, 'background')
    _stencil_body(background, design['body'][0])
    foreground = ET.SubElement(root, 'foreground')
    ET.SubElement(foreground, 'fillstroke')
    for part in design['body'][1:]:
        _stencil_body(foreground, part)
        ET.SubElement(foreground, 'fillstroke')
    for points in design['lines']:
        _path(foreground, points)
        ET.SubElement(foreground, 'stroke')
    data = quote(ET.tostring(root, encoding='unicode'), safe="!~*'()-_.").encode('ascii')
    compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    encoded = b64encode(compressor.compress(data) + compressor.flush()).decode('ascii')
    return f'shape=stencil({encoded});'
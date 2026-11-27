"""Validate local figure-review records and the elements they describe."""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit


METHOD_KINDS = {'method', 'code', 'dataset'}
DOI = re.compile(r'10\.[0-9]{4,9}/[^\s<>]+', re.IGNORECASE)
ARXIV = re.compile(r'(?:[0-9]{4}\.[0-9]{4,5}|[a-z.-]+/[0-9]{7})(?:v[0-9]+)?', re.IGNORECASE)


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def doi_identity(value):
    value = re.sub(r'^doi:\s*', '', unquote(value.strip()), flags=re.IGNORECASE).lower()
    if not DOI.fullmatch(value):
        return None
    if value.startswith('10.48550/arxiv.'):
        return arxiv_identity(value.removeprefix('10.48550/arxiv.'))
    return 'doi:' + value


def arxiv_identity(value):
    value = value.lower()
    if ARXIV.fullmatch(value):
        return 'arxiv:' + re.sub(r'v[0-9]+$', '', value)
    return None


def public_identity(value):
    if not has_text(value):
        return None
    value = value.strip()
    if doi := doi_identity(value):
        return doi
    try:
        url = urlsplit(value)
        host = url.hostname
        port = url.port
    except ValueError:
        return None
    if (url.scheme not in ('http', 'https') or not host or '.' not in host
            or url.username is not None or any(c.isspace() for c in value)):
        return None
    path = unquote(url.path).rstrip('/')
    if host in ('doi.org', 'dx.doi.org'):
        return doi_identity(path.lstrip('/'))
    if host in ('arxiv.org', 'www.arxiv.org', 'export.arxiv.org'):
        match = re.fullmatch(r'/(?:abs|pdf|html)/(.+)', path)
        return arxiv_identity(match[1].removesuffix('.pdf')) if match else None
    query = urlencode(sorted((key, item) for key, item in parse_qsl(url.query)
                      if not key.lower().startswith('utm_')))
    if not (path or query):
        return None
    authority = host if port in (None, 80, 443) else f'{host}:{port}'
    return f'url:{authority}{path}' + (f'?{query}' if query else '')


def paper_records(sources):
    """Group supplied figure records by their offline-normalized paper identities."""
    groups = []
    incomplete = []
    for source in sources:
        if source.get('kind') != 'figure':
            continue
        sid = source['id']
        identities = {public_identity(source.get(field)) for field in ('doi', 'url', 'pdf_url')}
        identities.discard(None)
        if not identities or not any(has_text(source.get(field)) for field in ('takeaway', 'notes')):
            incomplete.append(sid)
            continue
        matches = [group for group in groups if group['identities'] & identities]
        if matches:
            target = matches[0]
            target['ids'].append(sid)
            target['identities'].update(identities)
            for group in matches[1:]:
                target['ids'].extend(group['ids'])
                target['identities'].update(group['identities'])
                groups.remove(group)
        else:
            groups.append({'ids': [sid], 'identities': identities})
    return [group['ids'] for group in groups], incomplete


def _elements(row, known, where):
    ids = row.get('elements', [])
    if not isinstance(ids, list) or any(not isinstance(key, str) or key not in known for key in ids):
        raise ValueError(f'{where}.elements must name existing diagram elements')
    return ids


def shape_inventory(row, source_id):
    shapes = row['shapes']
    if not isinstance(shapes, list) or (not shapes and not has_text(row.get('shape_inventory_note'))):
        raise ValueError(f'{source_id}.shapes needs observed forms or an empty-inventory note')
    seen = set()
    for item in shapes:
        fields = ('id', 'form', 'role', 'location')
        if not isinstance(item, dict) or not all(has_text(item.get(key)) for key in fields):
            raise ValueError(f'Each shape observed in {source_id} needs an id, form, role and location')
        if item['id'] in seen:
            raise ValueError(f'Duplicate shape observation in {source_id}: {item["id"]}')
        seen.add(item['id'])
    return seen


def validate_shape_choices(choices, inventories, paper_ids, node_shapes, supported):
    if not isinstance(choices, list):
        raise ValueError('design_review.shape_choices must be a list')
    mapped = set()
    adapted = set()
    for row in choices:
        if not isinstance(row, dict) or not all(has_text(row.get(key)) for key in ('shape', 'reason')):
            raise ValueError('Each shape choice needs a rendering shape and a reason')
        targets = row.get('nodes')
        if not isinstance(targets, list) or not targets or not all(has_text(node) for node in targets):
            raise ValueError('Each shape choice needs a nonempty nodes list')
        refs = row.get('from_shapes', [])
        if not isinstance(refs, list):
            raise ValueError('Shape choice from_shapes must be a list')
        seen_refs = set()
        for ref in refs:
            if not isinstance(ref, dict) or not all(has_text(ref.get(key)) for key in ('source', 'shape')):
                raise ValueError('Each shape reference needs a figure source and a shape observation ID')
            source_id, shape_id = ref['source'], ref['shape']
            if shape_id not in inventories.get(source_id, ()):
                raise ValueError(f'Shape choice references an unrecorded observation: {source_id}/{shape_id}')
            if (source_id, shape_id) in seen_refs:
                raise ValueError(f'Duplicate shape reference: {source_id}/{shape_id}')
            seen_refs.add((source_id, shape_id))
        for target in targets:
            if target not in node_shapes:
                raise ValueError(f'Shape choice must name existing nodes: {target}')
            if target in mapped:
                raise ValueError(f'Duplicate shape choice for node: {target}')
            if node_shapes[target] != row['shape']:
                raise ValueError(f'Shape choice for {target} must match its rendered shape: {node_shapes[target]}')
            if f'nodes:{target}' not in supported:
                raise ValueError(f'Shape choice for {target} needs method, code, or dataset evidence')
            mapped.add(target)
            if refs:
                adapted.add(target)
    substantive = {node for node, shape in node_shapes.items() if shape not in ('header', 'group')}
    return {
        'inventoried_figures': len(inventories),
        'shape_observations': sum(map(len, inventories.values())),
        'mapped_nodes': len(mapped),
        'nodes_using_paper_conventions': len(adapted),
        'missing_figure_inventories': sorted(paper_ids - inventories.keys()),
        'nodes_without_shape_choice': sorted(substantive - mapped),
    }


def validate_design_review(review, elements, supported, sources, papers, node_shapes):
    """Check review mappings. Visual inspection and claim support remain human judgments."""
    if not isinstance(review, dict) or not has_text(review.get('reader_question')):
        raise ValueError('design_review needs a reader_question')
    checks = review.get('checks')
    if not isinstance(checks, list) or not checks:
        raise ValueError('design_review.checks must contain at least one reader check')
    for row in checks:
        where = 'Each design review check'
        if not isinstance(row, dict) or not has_text(row.get('question')):
            raise ValueError(f'{where} needs a question')
        ids = _elements(row, elements, where)
        if not ids or any(key not in supported for key in ids):
            raise ValueError(f'{where} needs elements backed by method, code, or dataset references')
        if 'relationship' in row and not isinstance(row['relationship'], bool):
            raise ValueError(f'{where}.relationship must be a boolean')
        if row.get('relationship') and not any(key.startswith('edges:') for key in ids):
            raise ValueError(f'{where} for a relationship must identify a drawn edge')

    paper_ids = {sid for group in papers for sid in group}
    precedents = review.get('precedents', [])
    if not isinstance(precedents, list):
        raise ValueError('design_review.precedents must be a list')
    seen = set()
    published = set()
    inventories = {}
    for row in precedents:
        where = 'Each design precedent'
        if not isinstance(row, dict) or not all(has_text(row.get(k)) for k in ('source', 'observation', 'decision')):
            raise ValueError(f'{where} needs a source, an observation and a design decision')
        sid = row['source']
        if sid not in paper_ids or sid in seen:
            raise ValueError(f'{where} needs a distinct figure source ID with a DOI or stable URL: {sid}')
        ids = _elements(row, elements, where)
        reason = has_text(row.get('omission_reason'))
        if bool(ids) == reason:
            raise ValueError(f'{where} must map to elements or explain its omission: {sid}')
        inspection = sources[sid].get('inspection')
        if (not isinstance(inspection, dict) or not has_text(inspection.get('location'))
                or inspection.get('publication') not in ('published', 'preprint', 'unverified')):
            raise ValueError(f'{where} needs a reported inspection location and publication status: {sid}')
        seen.add(sid)
        if inspection['publication'] == 'published':
            published.add(sid)
        if 'shapes' in row:
            inventories[sid] = shape_inventory(row, sid)

    shape_review = None
    if inventories or 'shape_choices' in review:
        shape_review = validate_shape_choices(review.get('shape_choices', []), inventories, paper_ids,
                                              node_shapes, supported)
    return {
        'reader_checks': len(checks),
        'mapped_precedents': len(seen),
        'reported_published_papers': sum(bool(published.intersection(group)) for group in papers),
        'unmapped_figure_sources': sorted(paper_ids - seen),
        'shape_review': shape_review,
        'status': 'records_valid',
    }

#!/usr/bin/env python3
"""100% Free Automated Scholarly Paper Fetcher.

Fetches open-access papers and metadata from OpenAlex and arXiv using Python standard library only.
Outputs CSV matching the templates/paper-matrix.csv schema for scripts/score_papers.py.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from itertools import zip_longest
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

try:
    from .score_papers import metadata_topic_match
except ImportError:
    try:
        from scripts.score_papers import metadata_topic_match
    except ImportError:
        from score_papers import metadata_topic_match


FIELDNAMES = [
    'title', 'authors', 'year', 'venue', 'doi', 'url',
    'citations', 'citation_source', 'citation_checked_on',
    'relevance', 'figure_relevance', 'metadata_match', 'oa_status', 'pdf_url', 'oa_url',
    'downloaded_full_text', 'figure_inspected', 'figure_locator', 'notes',
    'target_diagram_type'
]

DIAGRAM_TYPE_TERMS: dict[str, str] = {
    'workflow': '"methodology workflow" OR "experimental pipeline" OR "study workflow"',
    'architecture': '"model architecture" OR "network architecture" OR "framework overview"',
    'system': '"system architecture" OR "system overview" OR "pipeline architecture"',
    'flowchart': '"flowchart" OR "decision workflow" OR "algorithm flow"',
    'prisma': '"PRISMA" OR "systematic review" OR "study selection flow diagram"',
    'conceptual': '"conceptual framework" OR "theoretical model" OR "causal diagram"',
    'taxonomy': '"taxonomy" OR "survey" OR "classification hierarchy"',
    'timeline': '"timeline" OR "longitudinal study" OR "chronological workflow"',
    'multi-panel': '"multi-panel" OR "translational workflow" OR "pipeline overview"',
    'graphical-abstract': '"graphical abstract" OR "overview schematic"',
}

USER_AGENT = 'paper-grounded-manuscript-diagram'


def _validate_diagram_type(diagram_type: str | None) -> str | None:
    """Validate and normalize optional diagram type against DIAGRAM_TYPE_TERMS."""
    if diagram_type is None:
        return None
    normalized = diagram_type.strip().lower()
    if normalized not in DIAGRAM_TYPE_TERMS:
        valid = ', '.join(sorted(DIAGRAM_TYPE_TERMS))
        raise ValueError(f"Unknown diagram type '{diagram_type}'. Valid types: {valid}")
    return normalized


def build_targeted_query(query: str, diagram_type: str | None = None, source: str = 'openalex') -> str:
    """Append concise diagram-type keywords tailored to OpenAlex or arXiv search syntax."""
    cleaned = query.strip()
    dt = _validate_diagram_type(diagram_type)
    if not dt:
        return cleaned
    terms = DIAGRAM_TYPE_TERMS[dt]
    if source == 'arxiv':
        phrases = [p.strip() for p in terms.split(' OR ') if p.strip()]
        tokens = [t for t in re.findall(r'"[^"]+"|\S+', cleaned) if t.upper() not in ('AND', 'OR')]
        topic_clause = ' AND '.join(f'all:{tok}' for tok in tokens)
        or_clause = ' OR '.join(f'all:{p}' for p in phrases)
        return f'({topic_clause}) AND ({or_clause})' if topic_clause else f'({or_clause})'
    return f'{cleaned} ({terms})' if cleaned else f'({terms})'


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy deduplication."""
    return re.sub(r'\W+', '', title.lower())


def normalize_doi(doi: str) -> str:
    """Clean and normalize DOI string."""
    if not doi:
        return ''
    doi = doi.strip()
    doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', doi, flags=re.IGNORECASE)
    doi = re.sub(r'^doi:\s*', '', doi, flags=re.IGNORECASE)
    return doi.lower()


def fetch_openalex(query: str, limit: int = 10) -> list[dict]:
    """Fetch scholarly metadata from OpenAlex API."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={encoded}&per-page={min(limit, 50)}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        raise RuntimeError(f"OpenAlex request failed: {exc}") from exc

    results = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for work in data.get('results', []):
        title = (work.get('title') or work.get('display_name') or '').strip()
        if not title:
            continue
        authors_list = [
            a.get('author', {}).get('display_name', '').strip()
            for a in work.get('authorships', [])
            if a.get('author', {}).get('display_name')
        ]
        authors = ', '.join(filter(None, authors_list))
        year = str(work.get('publication_year') or '')
        primary_loc = work.get('primary_location') or {}
        venue = (primary_loc.get('source') or {}).get('display_name') or ''
        raw_doi = work.get('doi') or ''
        clean_doi = normalize_doi(raw_doi) if raw_doi else ''
        landing_url = raw_doi if raw_doi else (work.get('id') or '')
        citations = str(work.get('cited_by_count') if work.get('cited_by_count') is not None else '')
        oa_info = work.get('open_access') or {}
        oa_status = oa_info.get('oa_status') or ''
        best_oa = work.get('best_oa_location') or {}
        pdf_url = best_oa.get('pdf_url') or ''
        oa_url = best_oa.get('landing_page_url') or oa_info.get('oa_url') or ''

        results.append({
            'title': title,
            'authors': authors,
            'year': year,
            'venue': venue,
            'doi': clean_doi,
            'url': landing_url,
            'citations': citations,
            'citation_source': 'OpenAlex',
            'citation_checked_on': today,
            'relevance': '',
            'figure_relevance': '',
            'oa_status': oa_status,
            'pdf_url': pdf_url,
            'oa_url': oa_url,
            'downloaded_full_text': 'no',
            'figure_inspected': 'no',
            'figure_locator': '',
            'notes': '',
            'target_diagram_type': ''
        })
    return results


def fetch_arxiv(query: str, limit: int = 10) -> list[dict]:
    """Fetch preprints from arXiv Atom API."""
    search_expr = query if 'all:' in query else f"all:{query}"
    encoded = urllib.parse.quote(search_expr)
    url = f"https://export.arxiv.org/api/query?search_query={encoded}&max_results={min(limit, 50)}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_text = resp.read().decode('utf-8')
    except Exception as exc:
        raise RuntimeError(f"arXiv request failed: {exc}") from exc

    ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        raise RuntimeError(f"arXiv XML parsing failed: {exc}") from exc

    results = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for entry in root.findall('atom:entry', namespaces=ns):
        title = (entry.findtext('atom:title', default='', namespaces=ns)).replace('\n', ' ').strip()
        title = re.sub(r'\s+', ' ', title)
        if not title:
            continue
        authors_list = [
            a.findtext('atom:name', default='', namespaces=ns).strip()
            for a in entry.findall('atom:author', namespaces=ns)
        ]
        authors = ', '.join(filter(None, authors_list))
        published = entry.findtext('atom:published', default='', namespaces=ns)
        year = published[:4] if len(published) >= 4 else ''
        venue = 'arXiv preprint'
        id_url = entry.findtext('atom:id', default='', namespaces=ns).strip()
        doi = entry.findtext('arxiv:doi', default='', namespaces=ns).strip()
        if doi:
            doi = normalize_doi(doi)

        pdf_url = ''
        for link in entry.findall('atom:link', namespaces=ns):
            if link.attrib.get('title') == 'pdf':
                pdf_url = link.attrib.get('href', '').strip()
                break
        if not pdf_url and id_url:
            match = re.search(r'arxiv\.org/abs/([^/]+)', id_url)
            if match:
                pdf_url = f"https://arxiv.org/pdf/{match.group(1)}.pdf"

        results.append({
            'title': title,
            'authors': authors,
            'year': year,
            'venue': venue,
            'doi': doi,
            'url': id_url,
            'citations': '',
            'citation_source': 'arXiv',
            'citation_checked_on': today,
            'relevance': '',
            'figure_relevance': '',
            'oa_status': 'green-preprint',
            'pdf_url': pdf_url,
            'downloaded_full_text': 'no',
            'figure_inspected': 'no',
            'figure_locator': '',
            'notes': '',
            'target_diagram_type': ''
        })
    return results


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """Deduplicate DOI/title aliases and keep access links supplied by another provider."""
    known = {}
    unique = []
    for paper in papers:
        keys = [key for key in (
            ('doi', normalize_doi(paper.get('doi') or '')),
            ('title', normalize_title(paper.get('title') or ''))
        ) if key[1]]
        matches = [known[key] for key in keys if key in known]
        if matches:
            first = matches[0]
            for field in ('doi', 'pdf_url', 'oa_url'):
                if not first.get(field) and paper.get(field):
                    first[field] = paper[field]
        else:
            first = dict(paper)
            unique.append(first)
        for key in keys:
            known[key] = first
    return unique


def _priority(paper):
    return (paper['metadata_match'], bool(paper.get('pdf_url')))


def search_papers(query: str, limit: int = 20, sources: list[str] | None = None,
                  oa_only: bool = False, diagram_type: str | None = None) -> list[dict]:
    """Make a provider-balanced, metadata-only candidate shortlist."""
    if limit < 1:
        raise ValueError('limit must be positive')
    dt = _validate_diagram_type(diagram_type)
    if sources is None:
        sources = ['openalex', 'arxiv']
    providers = {'openalex': fetch_openalex, 'arxiv': fetch_arxiv}
    streams = []
    errors = []
    fetch_limit = min(50, max(limit * 3, 25)) if oa_only else limit

    for src in dict.fromkeys(s.strip().lower() for s in sources):
        if src not in providers:
            sys.stderr.write(f"Warning: Unknown source '{src}', skipping.\\n")
            continue
        try:
            candidates = providers[src](build_targeted_query(query, dt, source=src), limit=fetch_limit)
        except (RuntimeError, OSError) as exc:
            errors.append(f'{src}: {exc}')
            continue
        ranked = []
        for paper in candidates:
            is_open = paper.get('oa_status') not in (None, '', 'closed', 'none')
            if oa_only and not (is_open or paper.get('pdf_url')):
                continue
            ranked.append({**paper, 'target_diagram_type': dt or '',
                           'metadata_match': metadata_topic_match(query, paper.get('title') or '')})
        if ranked:
            streams.append(sorted(ranked, key=_priority, reverse=True))

    if not streams and errors:
        raise RuntimeError('No candidates available. Provider failures:\\n' + '\\n'.join(errors))
    for error in errors:
        sys.stderr.write(f'Warning: Partial paper search: {error}\\n')

    streams.sort(key=lambda stream: _priority(stream[0]), reverse=True)
    combined = [paper for batch in zip_longest(*streams) for paper in batch if paper is not None]
    selected = deduplicate_papers(combined)[:limit]
    return sorted(selected, key=_priority, reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', help='Search query for papers (e.g. "hybrid retrieval BM25 dense fusion")')
    parser.add_argument('--limit', type=int, default=20, help='Maximum number of papers to retrieve (default: 20)')
    parser.add_argument('--sources', default='openalex,arxiv',
                        help='Comma-separated sources: openalex, arxiv (default: openalex,arxiv)')
    parser.add_argument('--diagram-type', choices=sorted(DIAGRAM_TYPE_TERMS.keys()), default=None,
                        help='Bias search toward papers containing a matching published diagram type')
    parser.add_argument('--oa-only', action='store_true', help='Only shortlist records with reported open access or a PDF link; verify access separately')
    parser.add_argument('--output', type=Path, default=None,
                        help='Destination CSV file path (prints to stdout if omitted)')
    args = parser.parse_args()

    source_list = [s.strip() for s in args.sources.split(',') if s.strip()]
    try:
        papers = search_papers(args.query, limit=args.limit, sources=source_list,
                               oa_only=args.oa_only, diagram_type=args.diagram_type)
    except Exception as exc:
        sys.stderr.write(f"Error fetching papers: {exc}\n")
        sys.exit(1)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(papers)
        print(f"Wrote {len(papers)} candidate papers to {args.output}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=FIELDNAMES, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(papers)


if __name__ == '__main__':
    main()

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
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

FIELDNAMES = [
    'title', 'authors', 'year', 'venue', 'doi', 'url',
    'citations', 'citation_source', 'citation_checked_on',
    'relevance', 'figure_relevance', 'oa_status', 'pdf_url',
    'downloaded_full_text', 'figure_inspected', 'figure_locator', 'notes'
]

USER_AGENT = 'paper-grounded-manuscript-diagram (mailto:scholar@example.org)'


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
        pdf_url = best_oa.get('pdf_url') or oa_info.get('oa_url') or ''

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
            'downloaded_full_text': 'no',
            'figure_inspected': 'no',
            'figure_locator': '',
            'notes': ''
        })
    return results


def fetch_arxiv(query: str, limit: int = 10) -> list[dict]:
    """Fetch preprints from arXiv Atom API."""
    encoded = urllib.parse.quote(f"all:{query}")
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
            'notes': ''
        })
    return results


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """Deduplicate records by DOI or normalized title."""
    seen_dois = set()
    seen_titles = set()
    unique = []
    for paper in papers:
        doi = paper.get('doi', '').strip().lower()
        title_key = normalize_title(paper.get('title', ''))
        if doi and doi in seen_dois:
            continue
        if title_key and title_key in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        if title_key:
            seen_titles.add(title_key)
        unique.append(paper)
    return unique


def search_papers(query: str, limit: int = 10, sources: list[str] | None = None,
                  oa_only: bool = False) -> list[dict]:
    """Search scholarly repositories and return structured paper matrix records."""
    if sources is None:
        sources = ['openalex', 'arxiv']
    combined = []
    errors = []

    for src in sources:
        src = src.strip().lower()
        try:
            if src == 'openalex':
                combined.extend(fetch_openalex(query, limit=limit))
            elif src == 'arxiv':
                combined.extend(fetch_arxiv(query, limit=limit))
            else:
                sys.stderr.write(f"Warning: Unknown source '{src}', skipping.\n")
        except Exception as exc:
            errors.append(f"{src}: {exc}")

    if not combined and errors:
        raise RuntimeError("All sources failed:\n" + "\n".join(errors))

    unique = deduplicate_papers(combined)
    if oa_only:
        unique = [
            p for p in unique
            if (p.get('oa_status') and p['oa_status'] not in ('closed', 'none')) or p.get('pdf_url')
        ]
    return unique[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', help='Search query for papers (e.g. "hybrid retrieval BM25 dense fusion")')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of papers to retrieve (default: 10)')
    parser.add_argument('--sources', default='openalex,arxiv',
                        help='Comma-separated sources: openalex, arxiv (default: openalex,arxiv)')
    parser.add_argument('--oa-only', action='store_true', help='Only return open-access papers with accessible PDFs')
    parser.add_argument('--output', type=Path, default=None,
                        help='Destination CSV file path (prints to stdout if omitted)')
    args = parser.parse_args()

    source_list = [s.strip() for s in args.sources.split(',') if s.strip()]
    try:
        papers = search_papers(args.query, limit=args.limit, sources=source_list, oa_only=args.oa_only)
    except Exception as exc:
        sys.stderr.write(f"Error fetching papers: {exc}\n")
        sys.exit(1)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(papers)
        print(f"Wrote {len(papers)} candidate papers to {args.output}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(papers)


if __name__ == '__main__':
    main()

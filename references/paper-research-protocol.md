# Paper Research and Download Protocol

## Objective

Build a defensible reference set for the requested figure. The goal is not simply to collect papers with large citation counts; it is to find papers that explain the research method and contain figures relevant to the requested visual task.

## 1. Search strategy

Use multiple query patterns:

- exact research topic + requested figure type;
- core method/model + workflow or architecture;
- dataset/domain + methodology;
- review/survey + method;
- seminal method + recent improvements.

Search suitable scholarly indexes available in the current environment. Examples include OpenAlex, Crossref, Semantic Scholar, PubMed/PMC, arXiv, ACL Anthology, publisher sites, and university repositories. Verify important metadata against a DOI landing page or publisher record when possible.

Do not scrape services in ways that violate their terms. Do not treat ordinary web search snippets as full-text access.

## 2. Candidate selection

For a deep research request, a larger candidate set can help. For a focused drawing task, stop once the specific design questions are answered. Include as relevant:

- recent, directly relevant work;
- highly influential work when it defines a method or convention;
- papers with figures close to the requested figure type;
- reliable primary research or authoritative reviews.

Prefer methodological and visual diversity over meeting an arbitrary count. Existing locally reviewed references can be reused.

### Recommended scoring

Use `scripts/score_papers.py` with these input fields:

- `relevance`: 0–100, based on topic and method fit;
- `figure_relevance`: 0–100, based on whether the paper has a useful comparable figure;
- `citations`: reported citation count from a named source;
- `year`: publication year.

Default weights:

| Factor | Weight |
|---|---:|
| Topic/method relevance | 40% |
| Figure relevance | 25% |
| Citation influence | 20% |
| Recency | 15% |

Citation influence is log-normalized within the candidate set to reduce domination by a single extremely cited paper. Recency uses a five-year half-life. This is a ranking aid, not an objective measure of scientific quality. Adjust weights if the field or task requires it.

## 3. Access and inspection scope

For every new diagram, grounding the visual layout, grouping conventions, and notation in peer-reviewed domain literature is the **mandatory default**. Inspect 3–5 relevant open-access paper full texts and visually analyze 2–4 directly useful figures and captions (with a minimum of 2 verified figure sources recorded in `spec["sources"]` having `kind: "figure"`, title, exact figure/page locator, and a verifiable DOI or URL). A styling correction or typo fix to an existing verified diagram does not require a fresh literature search. If the user explicitly requests no literature search, honor that exemption and disclose it.

A paper counts as **downloaded and inspected** only if:
- a full-text PDF or equivalent full text was actually obtained;
- the document was opened/read;
- relevant figures and captions were inspected.

The following do not count as downloaded full text:
- title/abstract pages;
- search-result snippets;
- citation records;
- a figure thumbnail without the paper context;
- a DOI landing page.

If the desired reference set cannot be legally accessed:
1. try alternate legitimate sources (publisher open-access page, author manuscript, institutional repository, PMC, arXiv, ACL Anthology, or another recognized repository);
2. record which papers were inaccessible and why;
3. report the actual number downloaded and inspected;
4. do not bypass paywalls or access controls;
5. continue a useful diagram from the user's verified method with the evidence limitations stated; ask for a missing source only when it materially affects scientific content or an explicit requirement;
6. never claim a requested paper count or inspection stage was met if it was not. Never fabricate paper records or fake DOIs.

Do not send private manuscript text, unpublished diagrams or research data to external search/generation services. Public subject/DOI queries and lawful public-paper downloads are sufficient for style research. Link every adopted convention to an actual inspected page/figure and a concrete new-design choice; a bibliography alone is not a design analysis.

## 4. Legal access and rights

Use:
- publisher-provided open-access PDFs;
- author-accepted manuscripts made available by the author or institution;
- recognized preprint servers;
- institutional repositories;
- public repositories such as PubMed Central when applicable;
- other downloads explicitly authorized by the rights holder.

Do not:
- bypass a paywall;
- defeat DRM or access controls;
- use stolen credentials;
- execute macros, scripts, or embedded content from downloaded documents;
- redistribute full papers in the skill's output unless the license permits it.

The skill should normally deliver citations and links, not bundle copyrighted papers into the user's figure package.

## 5. Citation metadata

For each paper, record:

- title;
- all authors or first author et al.;
- year;
- journal/conference/preprint venue;
- DOI;
- stable landing-page URL;
- PDF URL if legally accessible;
- scholarly index used;
- citation count;
- citation-count provider;
- date citation count was checked;
- open-access status;
- download status;
- figure inspection status;
- relevance notes.

Citation counts differ across databases and change over time. Phrase claims carefully, e.g. "OpenAlex reported N citations on YYYY-MM-DD." Do not say "the most cited paper" unless the comparison scope and source are explicit.

Use the scorer's usual mode for discovery. After opening comparable figures, set `figure_inspected` and give the actual `figure_locator`. Run `python scripts/score_papers.py candidates.csv --reviewed-only` to order that inspected subset by figure fit. Record which convention each selected figure informed.

## 6. Figure relevance

Do not inspect every figure indiscriminately. Prioritize:
- methodology and workflow figures;
- system architecture diagrams;
- conceptual frameworks;
- data collection/preprocessing pipelines;
- study-area maps;
- experimental setup figures;
- graphical abstracts, when the requested output is a graphical abstract.

Read captions and nearby text. A figure's meaning cannot always be inferred from its image alone.

## 7. Reference integrity

Before delivery:
- verify titles and author/year details;
- verify DOI format and landing page;
- remove duplicate records;
- distinguish peer-reviewed articles from preprints;
- state any uncertain metadata;
- cite the papers that materially informed the diagram's conventions or scientific content.

Never invent missing metadata. A blank DOI is better than a fabricated DOI.

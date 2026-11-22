# Paper-Grounded Manuscript Diagram

A portable Agent Skill for creating original, scientifically accurate, publication-ready research diagrams grounded in the user's manuscript and relevant academic literature.

It helps an AI agent research the topic, find and inspect relevant papers, analyze published figure conventions, plan a new figure, create editable diagram source, and perform scientific and visual quality checks.

## Agent Skills format

This package follows the open [Agent Skills specification](https://agentskills.io/specification): a skill folder with a required `SKILL.md`, portable `name` and `description` frontmatter, and optional scripts and reference resources. The format supports progressive disclosure, but each host agent must implement skill loading and provide the tools needed for research and diagram creation.

## What it does

- Understands the user's research, code, experiments, and manuscript context.
- Searches for recent and influential papers relevant to the topic and requested figure type.
- Makes a best-effort attempt to download and inspect **at least five legally accessible full-text papers**.
- Analyzes relevant paper figures for structure, hierarchy, layout, typography, color, spacing, labels, and scientific conventions.
- Synthesizes an original diagram instead of copying a published figure.
- Uses the Okabe-Ito palette and rounded process shapes by default.
- Applies the correct conventions for flowcharts, methodology diagrams, conceptual frameworks, architectures, graphical abstracts, and study-area maps.
- Checks scientific accuracy, readability, alignment, exports, and remaining limitations.
- Provides the final figure, editable source, reference list, and QA summary when the host agent has the necessary tools.

## Important portability note

This repository follows the open Agent Skills folder format: a `SKILL.md` file with YAML frontmatter (`name` and `description`) plus optional scripts, references, and assets.

The folder is portable across compatible agent clients. **It is not a universal executable plugin.** Each AI platform must support Agent Skills or provide a way to load the `SKILL.md` instructions and bundled resources. Browser access, academic-paper search, PDF reading, image inspection, diagram rendering, and file export depend on the tools available in that platform.

## Repository structure

```text
paper-grounded-manuscript-diagram/
├── SKILL.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── requirements-optional.txt
├── references/
│   ├── paper-research-protocol.md
│   ├── figure-analysis-template.md
│   ├── diagram-conventions.md
│   ├── design-system.md
│   ├── quality-assurance.md
│   ├── platform-compatibility.md
│   └── output-specification.md
├── scripts/
│   ├── score_papers.py
│   ├── extract_pdf_figures.py
│   ├── build_contact_sheet.py
│   └── validate_svg.py
├── templates/
│   ├── paper-matrix.csv
│   ├── figure-analysis.md
│   ├── diagram-spec.yaml
│   └── methodology-flow.mmd
├── tests/
│   └── test_helpers.py
└── .github/
    └── workflows/
        └── validate.yml
```

## Quick start

1. Download or clone this repository.
2. Place the whole `paper-grounded-manuscript-diagram` folder in a skills directory recognized by your agent.
3. Make sure the agent can read `SKILL.md` and the files under `references/`.
4. Give the agent a request such as:

   > Read my research manuscript, code, and experiment notes. Create a publication-ready methodology diagram. Follow the Paper-Grounded Manuscript Diagram skill. Search for and inspect at least five legally accessible relevant full-text papers where available, analyze their related figures, and create an original diagram. Deliver SVG, PDF, PNG, editable source, references, and a QA report.

5. If the platform does not auto-discover skills, explicitly ask the agent to read this folder's `SKILL.md`.

## Optional helper scripts

The helper scripts are offline utilities. They do not call academic APIs or download papers automatically.

### 1. Rank a paper candidate list

Prepare a CSV with these columns:

`title,year,citations,relevance,figure_relevance,doi,url,venue`

`relevance` and `figure_relevance` are scores from 0 to 100. The script calculates a weighted score:

- topic relevance: 40%
- relevance of the paper's figures: 25%
- normalized citation influence: 20%
- recency: 15%

Example:

```bash
python scripts/score_papers.py candidates.csv --output ranked-papers.csv
```

Citation counts should come from a named scholarly source and be recorded with a date. Scores help organize a candidate set; they do not prove paper quality.

### 2. Extract images and render PDF pages

Install the optional PDF dependency:

```bash
python -m pip install -r requirements-optional.txt
```

Then run:

```bash
python scripts/extract_pdf_figures.py paper.pdf --output-dir extracted_figures
```

The script extracts embedded raster images and renders PDF pages for inspection. It may not perfectly isolate vector figures or multi-panel figures. Inspect page renders and captions as well.

### 3. Build a contact sheet

```bash
python scripts/build_contact_sheet.py extracted_figures --output contact-sheet.png
```

Requires Pillow. Review the contact sheet and open individual images at full resolution.

### 4. Validate an SVG

```bash
python scripts/validate_svg.py final-figure.svg
```

This checks basic XML/SVG structure, dimensions, viewBox, and text presence. It cannot determine scientific correctness, visual balance, or whether labels are clipped.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Research integrity and legal access

- Do not fabricate references, DOIs, citation counts, or download status.
- Do not bypass paywalls or access controls.
- Prefer legally available full texts and record the source URL.
- Never copy or trace a published figure. Create a new visual composition based on verified research content and general design conventions.
- If five full-text papers cannot be accessed, state the exact number actually inspected and why.

## Default visual style

The default palette is Okabe-Ito:

| Color | Hex |
|---|---|
| Black | `#000000` |
| Orange | `#E69F00` |
| Sky blue | `#56B4E9` |
| Bluish green | `#009E73` |
| Yellow | `#F0E442` |
| Blue | `#0072B2` |
| Vermillion | `#D55E00` |
| Reddish purple | `#CC79A7` |

Rounded rectangles are the default for ordinary process blocks. Use semantic shapes when a diagram convention requires them. Avoid low-contrast yellow text on white.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

# Paper-Grounded Manuscript Diagram

A portable Agent Skill for creating editable research diagrams from the user's method, manuscript or existing figure, with optional paper-figure review and a local drawing engine.

It helps an agent choose a composition, draw it with measured typography and geometry, inspect the actual export and preserve the underlying research. It does not infer missing methodology or certify journal acceptance.

## Agent Skills format

This package follows the open [Agent Skills specification](https://agentskills.io/specification): a skill folder with a required `SKILL.md`, portable `name` and `description` frontmatter, and optional scripts and reference resources. The format supports progressive disclosure, but each host agent must implement skill loading and provide the tools needed for research and diagram creation.

## What it does

- Understands the user's research, code, experiments, and manuscript context.
- Searches for recent and influential papers relevant to the topic and requested figure type.
- Uses relevant paper figures when they answer a design question. A simple redesign does not require a fresh paper search; an explicit user-requested reference count is respected.
- Analyzes relevant paper figures for structure, hierarchy, layout, typography, color, spacing, labels, and scientific conventions.
- Synthesizes an original diagram instead of copying a published figure.
- Uses the Okabe-Ito palette and rounded process shapes by default.
- Applies the correct conventions for flowcharts, methodology diagrams, conceptual frameworks, architectures, graphical abstracts, and study-area maps.
- Checks scientific accuracy, readability, alignment, exports, and remaining limitations.
- Includes a Python/Matplotlib renderer, illustrative sequential, parallel, decision and noncausal conceptual layouts, editable SVG, vector PDF, 600-DPI PNG, and measured geometry reports.
- Applies rounded outlines and smooth connector bends consistently across layouts, with explicit overrides for venue-specific rules.
- Supports optional context/palette-matched icons when useful: capability-aware generation guidance, local white-background removal/cropping, embedded assets and measured placement checks.

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
│   ├── rendering.md
│   ├── icon-workflow.md
│   └── output-specification.md
├── scripts/
│   ├── score_papers.py
│   ├── extract_pdf_figures.py
│   ├── build_contact_sheet.py
│   ├── render_diagram.py
│   ├── prepare_icon.py
│   └── validate_svg.py
├── templates/
│   ├── paper-matrix.csv
│   ├── figure-analysis.md
│   ├── diagram-spec.yaml
│   ├── linear-workflow.json
│   ├── decision-workflow.json
│   ├── conceptual-framework.json
│   ├── parallel-study.json
│   ├── icon-workflow/          # runnable example and local illustrative assets
│   └── methodology-flow.mmd
├── tests/
│   ├── test_helpers.py
│   ├── test_renderer.py
│   └── test_icons.py
└── .github/
    └── workflows/
        └── validate.yml
```

## Quick start

1. Download or clone this repository.
2. Place the whole `paper-grounded-manuscript-diagram` folder in a skills directory recognized by your agent.
3. Make sure the agent can read `SKILL.md` and the files under `references/`.
4. Give the agent a request such as:

   > Use $paper-grounded-manuscript-diagram to draw my supplied method. Preserve every supported stage and relationship. Choose a layout that fits the research, use Okabe-Ito colours and rounded process shapes, and deliver editable SVG, vector PDF, a 600-DPI PNG and source. Inspect the full preview and actual print-size output. Review comparable paper figures only where they add useful design evidence.

5. If the platform does not auto-discover skills, explicitly ask the agent to read this folder's `SKILL.md`.

## Optional helper scripts

The helper scripts are offline utilities. They do not call academic APIs or download papers automatically.

### Draw a workflow locally

Use an existing Python environment with Matplotlib and Pillow. Adapt a template's labels, routes and size from the verified method; the example contents are illustrative, not a study protocol:

```bash
python scripts/render_diagram.py templates/parallel-study.json --check-only
python scripts/render_diagram.py templates/parallel-study.json --output-dir diagram-output --stem methodology
python scripts/validate_svg.py diagram-output/methodology.svg --json diagram-output/svg-check.json
```

Read [the drawing contract](references/rendering.md). Coordinates use points at the actual manuscript size. The renderer measures label overflow, node overlap, contrast, arrow endpoints and paths through unrelated content, returning a nonzero exit code on failure. Open `methodology-preview.png` and `methodology-print-size.png` yourself: automated geometry does not establish scientific accuracy or visual polish. On failure, do not mistake older files in a reused output directory for a new successful export.

SVG retains text for a vector editor and includes a local sans-serif fallback stack; PDF embeds local fonts where supported. The additional `-outlined.svg` keeps label appearance stable for Word embedding, but its letters are not editable text. Neither is a native Word, PowerPoint or draw.io diagram. No remote fonts, hosted image generator or paid API is needed. Use other local authoring tools for unsupported diagram types.

The default `style` rounds shape corners and connector elbows across all examples. Choose `connector_style: "orthogonal"` only when a user or venue requests hard elbows. Use `arrow: "none"` for undirected associations and `arrow: "both"` only when justified. Do not treat the parallel example as a universal layout: choose and recompose a structure from the method.

### Optional clean icons

Read [the icon workflow](references/icon-workflow.md) when paper figures and the supplied method support useful icons. Generate only the required distinct assets if the host supports authorised image generation; use one restrained rounded style and exact palette on pure white backgrounds. The bundled helper prepares existing local images, preserving native alpha or removing connected white exterior, cropping with safe margin and producing white/dark/checkerboard QA previews:

```sh
python scripts/prepare_icon.py raw/icon.png --output assets/icon.png
```

For a single-colour glyph, `--foreground '#0072B2'` recovers antialiased transparency. For complex artwork use a reviewed local segmentation mask. A mask quality check is still needed: the helper does not claim perfect general-purpose background removal. The renderer accepts optional `icons`, reserves node text space and embeds PNGs in the SVG/PDF. See [rendering](references/rendering.md). Core rendering needs no generator, model download or cloud service, and icons remain raster inside vector exports.

Run the bundled synthetic example with `python scripts/render_diagram.py templates/icon-workflow/diagram.json --output-dir diagram-output --stem icons`. Its three symbols were drawn locally, not generated by AI; their source is `templates/icon-workflow/make_example_assets.py`. These fixtures demonstrate asset handling, not image-generator quality or research evidence.

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

If the relevant packages are missing and installation is authorised, install the optional dependencies in a project environment (not globally):

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

This checks positive physical dimensions/viewBox, editable-text presence, and rejects active content and nonlocal resource references. It cannot determine scientific correctness, visual balance, or whether labels are clipped. Use the renderer's geometry report plus visual review for those concerns.

## Run tests

```bash
python -m unittest discover -s tests -v
```

Without optional dependencies, renderer/PDF/image tests explicitly skip. The CI rendering job installs its pinned test dependencies and exercises real exports; a standard-library-only test run is not equivalent to a rendering pass.

## Research integrity and legal access

- Do not fabricate references, DOIs, citation counts, or download status.
- Do not bypass paywalls or access controls.
- Prefer legally available full texts and record the source URL.
- Never copy or trace a published figure. Create a new visual composition based on verified research content and general design conventions.
- State the actual reference set inspected and its page/figure locators. Never count a search snippet as full-text or figure review.
- Keep private manuscripts and extracted research content local. External scholarly queries should use public topic/DOI terms.

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

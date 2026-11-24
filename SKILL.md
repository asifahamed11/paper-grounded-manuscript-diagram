---
name: paper-grounded-manuscript-diagram
description: Create or refine editable research workflows, method schematics and conceptual diagrams from a manuscript, method or existing figure. Use for academic diagram design, with relevant paper-figure review when it adds value; route numerical plots and geographic maps to their own tools.
---

# Paper-Grounded Manuscript Diagram

Design publication-grade, reproducible scientific workflows, method schematics, and conceptual diagrams grounded in actual manuscript text and inspected peer-reviewed literature. All operations use 100% free, local Python tools (matplotlib, Pillow, numpy, PyMuPDF) with zero paid APIs, cloud services, or external model downloads.

**Privacy & Legal Compliance**: Keep unpublished manuscripts, experimental protocols, and extracted figure data strictly local. Use only legal, open-access sources for visual convention research. Record figure inspection precedents and design decisions in the project's review/QA notes, never by modifying skill reference files.

## 1. Select the Workflow Scope & Core Philosophy

> [!IMPORTANT]
> **Perfection Over Speed:** Never rush or settle for "good enough". Take as many planning, inspection, and refinement iterations as necessary so the final diagram is publication-perfect, scientifically exact, balanced, clean, and indistinguishable from a human-crafted Illustrator/Figma/TikZ figure.

### Mandatory Grounding & Workflow Modes

| Scope | Pipeline & Actions | Enforcement |
|---|---|---|
| **New Figure (MANDATORY DEFAULT)** | Even when complete manuscript text or code is provided, **FIRST** run the paper-figure research pipeline (`fetch_papers.py` → `score_papers.py` → download 3–5 legal OA PDFs → `extract_pdf_figures.py` → `build_contact_sheet.py` → visually inspect at least 2–4 relevant published figures & captions) to ground layout, visual conventions, grouping, and notation in real peer-reviewed domain literature BEFORE drafting the diagram. Include inspected figures in `spec["sources"]` (`"kind": "figure"` with `doi`/`url` and exact `locator`, e.g., `"Fig. 2, p. 4"`). | Execute with `--require-sources --require-paper-figures` (enforces $\ge 2$ inspected figure sources with verifiable links). |
| **Figure Polish / Refactoring** | Improve spacing, colors, hierarchy, or alignment of an already-verified existing spec. Re-running paper search is not required for minor typo/color/spacing adjustments on existing diagrams. | Run with `--require-sources`. |
| **Multi-Format Export** | Render vector PDF, editable SVG, 600-DPI PNG, TIFF, EPS, and native Draw.io diagram. | Full format suite generated automatically. |

### Autonomous Defaults (For Short, Simple User Prompts)

When a user gives a brief request without mentioning themes, dimensions, flags, or paper research (e.g., *"Draw a methodology figure from my paper/code"*), automatically apply all defaults without asking unnecessary technical questions:
- **Mandatory Literature Grounding:** Always run `fetch_papers.py` → `score_papers.py` → download 3–5 legal OA PDFs → `extract_pdf_figures.py` → inspect 2–4 real published figures → record $\ge 2$ verified `kind: "figure"` sources and render with `--require-sources --require-paper-figures --drawio`.
- **Smart Domain Auto-Selection:**
  - **ML / DL / NLP / AI**: `"theme": "neurips-soft"`, prefer horizontal double-column (`width_pt: 515.0`, `--profile ieee-double`).
  - **Biomedical / Clinical / PRISMA**: `"theme": "biomed-prisma"`, vertical or two-lane (`width_pt: 360–468`).
  - **Engineering / Systems**: `"theme": "ieee-crisp"`, `--profile ieee-double` (or `ieee-single`).
  - **General Science / Multi-Panel**: `"theme": "nature-clean"`, `--profile nature-double` (or `nature-single`).
- **Human-Crafted Print Defaults:** `"font_family": "auto"`, flat vector (`shadow: false`), clean pastel rounded rectangles (use consistent `process` boxes for tall blocks rather than over-rounded tall `terminator` squircles), bold titles + muted slate subtitles, sans-serif inline math `\( ... \)`, at most 0–2 understated vector icons, and borderless (`"frame": false`) legend ONLY when encoding non-obvious line styles or shared roles.

**Only Allowed Exemptions to Paper Search:**
Skip literature search **ONLY** when:
1. The user explicitly requests no literature search, or
2. The task is a minor typo, color, or spacing fix on an already-verified existing diagram.

If network or OA full-text access genuinely fails after trying both OpenAlex and arXiv, **never fabricate paper records**—disclose the exact shortfall in the QA report and proceed honestly with evidence limitations clearly documented.

## 2. Paper Grounding Pipeline

When visual conventions or domain precedents are needed:

1. **Query & Retrieve**: Search OpenAlex and arXiv using stdlib (zero API keys):
   ```bash
   python scripts/fetch_papers.py "single-cell RNA-seq clustering workflow" --limit 10 --oa-only --output papers.csv
   ```
2. **Score & Filter**: Score candidate papers by relevance and figure density:
   ```bash
   python scripts/score_papers.py papers.csv --output scored.csv
   ```
3. **Extract & Inspect**: Extract figures from open-access PDFs into an inspection contact sheet:
   ```bash
   python scripts/extract_pdf_figures.py paper.pdf --output-dir extracted/
   python scripts/build_contact_sheet.py extracted/ --output contact.png
   ```
4. **Record Precedents**: Log figure locator, convention, and design decision in your design notes.

## 3. Diagram Planning & Composition

For standard methods, parallel lanes, skip-rank DAGs, or cyclic feedback loops, author or generate a method JSON specification and run the deterministic layout planner:

```bash
python scripts/plan_diagram.py method.json --output-dir output --stem figure-01 --theme nature-clean --profile nature-single --require-sources --require-paper-figures
```

- **Relationships**: Planner resolves row ranking (`rank`), parallel lane assignment (`col`), skip-rank corridor routing, feedback loops (outer return corridors), and horizontal left-to-right pipelines (`"direction": "horizontal"`).
- **Grounding Evidence**: Declare top-level `"sources": [{"id": "method-sec2", "kind": "method", "title": "Author Manuscript", "locator": "Section 2.1"}]` and attach per-node or per-edge `"source_refs": ["method-sec2"]`. Enforce source coverage via `--require-sources`.

## 4. Visual Masterpiece Engine & Styling

The core renderer (`scripts/render_diagram.py`) applies publication aesthetics:

- **Curated Themes (`--theme`)**: `nature-clean` (slate `#0F172A`, teal accents, hairline borders), `ieee-crisp` (navy `#0F172A`, steel borders, bold connectors), `neurips-soft` (modern pastel cards, indigo/green tints), `biomed-prisma` (warm clinical palette), `print-mono` (black & white publication standard). Custom node colors override theme defaults. All themes default to flat, crisp print vector (`shadow: false`).
- **Journal Profiles (`--profile`)**: Calibrated column widths: `ieee-single` (88 mm), `ieee-double` (181 mm), `nature-single` (89 mm), `nature-double` (183 mm), `springer-lncs` (122 mm), `elsevier-double` (190 mm), `plos-one` (171.45 mm).
- **Modern Typography**: Set `"font_family": "auto"` to automatically select the cleanest installed sans-serif (`Inter`, `Arial`, `Helvetica`, `Segoe UI`, fallback `DejaVu Sans`).
- **Accents & Badges**: Add distinct visual cues via `"accent": "left"` / `"top"` (with optional `"accent_color"`) and `"badge": "Phase 1"` (with `"badge_fill"` / `"badge_text_color"`).
- **Containers & Groups**: Structural containers use `"container_fill"` (solid tint or transparent) with dashed or solid borders and collision-free headers.
- **Legends**: Compact horizontal `"legend"` with swatches (`kind: "node"` with `fill`/`stroke_color`, or `kind: "edge"` / `shape: "line"` with arrow and dashed options).
- **Crisp Math Expressions**: `\( ... \)` syntax renders math automatically (e.g. `\( \alpha + \beta \)`). Embedded `$...$` syntax is rendered as math when `"math": true` (default `parse_math=False` preserves literal `$100`).

### Human-Crafted Academic Aesthetic (Avoid the AI-Generated Look)

Real top-journal figures (Nature, IEEE, NeurIPS, *Attention Is All You Need*) look human-crafted in Adobe Illustrator, Figma, or LaTeX TikZ. Avoid "AI-generated SaaS card" over-styling:
1. **Flat, restrained, print-first:** Top-tier figures are flat vector schematics with clean pastel fills, crisp 0.8–1.0 pt borders, and generous alignment — **NEVER** stack drop shadows + SaaS corner badges + side accent stripes + UI icons all at once on every card.
2. **Typography carries the hierarchy:** Use bold dark titles (`9.0–10.0 pt`) + smaller muted-slate subtitles (`detail_color: "#475569"`, `detail_font_pt: 8.0`) inside tight, well-proportioned boxes (typical height 34–44 pt, not bloated 65 pt cards).
3. **Prefer clean flat rounded rectangles:** Use `process` rectangles with soft role-based pastel fills (like TikZ/Illustrator) for most pipeline stages; use 3D `data` cylinders or `decision` diamonds only when classical flowchart notation genuinely enhances clarity.
4. **Restraint with icons & badges:** An icon-free, typography-led schematic is often the cleanest, most authoritative choice. If icons help, use at most 2–4 purposeful domain symbols (or custom domain `.svg` / AI art) — do **NOT** stamp a wireframe UI icon onto every single box. Reserve `badge` only for multi-panel labels like `(a)` / `(b)` or numbered stages, never SaaS status tags like `INPUT` / `EVAL`.
5. **Clean geometry & compact legends:** Align boxes on a strict grid with consistent vertical/horizontal gaps (12–18 pt), use crisp orthogonal rounded connectors without unnecessary zigzags, and ensure every legend swatch matches the exact fill/stroke/line style actually drawn in the diagram.
6. **Legend restraint & borderless framing:** Only include a legend when it explains a non-obvious visual encoding (such as dashed vs. solid arrows or shared color roles across multi-panel stages). Never waste a legend repeating single-box titles, and keep legends borderless (`"frame": false`) by default.

## 5. Three-Tier Icon System

In diagram specifications, icons are declared in the top-level `"icons": [...]` array with `"id"`, `"node"`, `"alt"`, and `"box"` or `"placement"`:

1. **Tier 1 (Host Native AI Image Generation)**: When authorized and rich domain illustration helps, generate isolated objects on white backgrounds and run `python scripts/prepare_icon.py input.png --output assets/icon.png` for alpha cutout and transparent PNG embedding.
2. **Tier 2 (Custom AI-Authored Local SVG)**: Unlimited pure-vector symbols authored locally (`"path": "assets/icon.svg"`). Rendered directly as vector path patches across all outputs without rasterization warnings.
3. **Tier 3 (30 Built-in Instant Vector Icons)**: Zero external files; specify `"vector_icon": "<name>"` directly (`python scripts/render_diagram.py --list-icons`):
   - *Data & Storage*: `database`, `table`, `document`, `documents`, `folder`, `cloud`, `globe`, `satellite`, `sensor`, `waveform`
   - *AI & Compute*: `brain`, `neural_net`, `cpu`, `code`, `layers`, `filter`, `merge`, `split`, `sliders`, `gear`
   - *Science & Analysis*: `microscope`, `dna`, `flask`, `chart_bar`, `chart_line`, `search`, `check`, `alert`, `shield`, `users`

## 6. Rendering & Multi-Format Delivery

Generate publication-ready artifacts:

```bash
python scripts/render_diagram.py diagram.json --output-dir output --stem figure-01 --drawio --eps --tiff
python scripts/validate_svg.py output/figure-01.svg --json output/svg-check.json
```

- **Outputs**: Editable SVG, vector PDF, 600-DPI PNG, print-size PNG, native Draw.io XML (`--drawio`), EPS (`--eps`), lossless TIFF (`--tiff`).
- **Asset Portability**: Local icons copied to `<output-dir>/<stem>-assets/` for self-contained handoff.

## 7. Mandatory Multi-Pass Visual Self-Critique Loop

Always inspect **BOTH** `<stem>-print-size.png` (at 100% physical print scale) **AND** `<stem>.png` (high-res rendering) after rendering. Verify all 6 strict criteria:

1. **Scientific Fidelity Against Manuscript/Code**: Every node, branch condition, mathematical objective, and output faithfully reflects the underlying scientific methodology without omitted stages or invented connections.
2. **Paper-Grounded Conventions**: Visual structure, grouping boundaries, and notation reflect real peer-reviewed domain conventions learned from inspected literature figures (never copied, but authentically grounded).
3. **Human-Editorial Aesthetic (Anti-AI-Slop)**: Restrained flat pastel fills, crisp 0.8–1.0 pt hairline borders, no drop shadows, no SaaS status badges, no Jira-like accent stripes, and no arbitrary UI icons cluttering boxes.
4. **Typography & Sans-Serif Math Clarity**: Clear hierarchy (bold dark title 9–10 pt + muted slate subtitle 8 pt); math formulas render cleanly in upright sans-serif mathtext (`\mathbf{h} \in \mathbb{R}^d`) without clipping or serif clashes.
5. **Grid Alignment, Breathing Room & Orthogonal Routing**: Main pipeline stages align along a strict grid spine; vertical/horizontal gaps are consistent (12–18 pt); orthogonal connectors feature crisp TikZ arrowheads (`head_length=0.55,head_width=0.28`) without unnecessary kinks or diagonal crossings.
6. **Matching Legend & WCAG AA Contrast**: Legend swatches exactly match the fills, borders, and line styles actually drawn in the diagram; all text exceeds 4.5:1 contrast against container and node fills.

### Strict Anti-Hallucination & Visual Micro-QA Rules

- **Zero Fabricated Specifics:** NEVER invent unreported model names (e.g., XLM-RoBERTa), split ratios (e.g., 80/10/10), vector dimensions (e.g., $\mathbb{R}^{300}$), or domain counts not explicitly present in the user's manuscript or code.
- **Exact Legend Swatch Parity:** Every node swatch in `legend` MUST specify BOTH the exact `"fill"` and `"stroke_color"` of the actual boxes it represents (never use a solid dark swatch for a pale-tinted box).
- **Edge Label & Corridor Clearance:** Never place an edge label on a connector segment shorter than `label_height + 10 pt` (otherwise the pill hides the arrow and touches node borders). Leave at least `16–20 pt` corridor clearance between adjacent shaded group containers so parallel routed arrows never hug dashed borders.

> [!CAUTION]
> **Iterative Refinement Mandate:** If **ANY** visual, alignment, typographic, or scientific imperfection is noticed during inspection, revise the JSON specification, re-render, and re-inspect in a loop until all 6 criteria are spotless.

# Default Figure Design System

## 1. Palette

Follow the user or journal palette when specified. Otherwise, choose the palette that suits the figure.

| Palette | Use |
|---|---|
| Paul Tol Muted | Research frameworks, methodology diagrams, and conceptual models with several categories. |
| Okabe–Ito | General default for scientific figures, especially statistical comparisons, experimental results, and labelled categories. |
| Paul Tol Pale | Light fills for text-heavy PRISMA diagrams, research workflows, and methodology flowcharts. Keep labels and connectors dark. |

### Paul Tol Muted

`#CC6677` · `#332288` · `#DDCC77` · `#117733` · `#88CCEE` · `#882255` · `#44AA99` · `#999933` · `#AA4499`

### Okabe–Ito

| Role | Color | Hex |
|---|---|---|
| Neutral / text | Black | `#000000` |
| Primary accent | Blue | `#0072B2` |
| Secondary accent | Bluish green | `#009E73` |
| Supporting accent | Sky blue | `#56B4E9` |
| Highlight | Orange | `#E69F00` |
| Alert / emphasis | Vermillion | `#D55E00` |
| Secondary category | Reddish purple | `#CC79A7` |
| Caution accent | Yellow | `#F0E442` |

### Paul Tol Pale

`#AACCEE` · `#CCEEFF` · `#BBDDBB` · `#EEEEBB` · `#FFBBCC` · `#EEBBDD` · `#DDDDDD`

Use these hex values in the renderer's colour fields.

### Publication Themes

The system provides 5 ready-to-publish themes configured for specific academic venue requirements and visual standards:

| Theme | Best For | Role Fills (`process`, `data`, `input`, `decision`) | Text / Detail / Connectors | Card Polish (All `shadow: false`, `arrow_scale: 7.0`) |
|---|---|---|---|---|
| `nature-clean` | Nature, Springer, Cell | `#FFFFFF`, `#EBF5F7`, `#F1F5F9`, `#FEF7E6` | `#0F172A` / `#475569` / `#334155` | Flat vector, 0.85 pt hairline borders, 4.5 pt corners |
| `ieee-crisp` | IEEE Transactions, ACM | `#FFFFFF`, `#E8F1FA`, `#F1F5F9`, `#FEF7E0` | `#0F172A` / `#334155` / `#1E293B` | Flat vector, 0.85 pt structural borders, 3.5 pt corners |
| `neurips-soft` | NeurIPS, ICML, ICLR | `#FFFFFF`, `#EEF2FF`, `#F0F9FF`, `#FEF3C7` | `#111827` / `#4B5563` / `#374151` | Flat vector, 0.85 pt borders, 4.5 pt corners, indigo/green tints |
| `biomed-prisma` | PLOS ONE, Lancet, BMJ | `#FFFFFF`, `#EBF5FB`, `#F4F6F7`, `#FEF5E7` | `#1E293B` / `#475569` / `#475569` | Flat vector, calm clinical tints, 0.85 pt borders, 4.0 pt corners |
| `print-mono` | B&W Print Proceedings | `#FFFFFF`, `#F3F4F6`, `#E5E7EB`, `#F9FAFB` | `#111827` / `#4B5563` / `#111827` | Grayscale-only, flat vector, 0.85 pt borders, 3.5 pt corners |

### Palette rules

- Use two to four colors in most figures; use more only when categories require them.
- Keep text dark and high contrast.
- Avoid yellow text or thin yellow lines on white.
- Do not rely on color alone to distinguish categories.
- Use the same semantic color consistently across related panels.
- Carry a branch accent along its route when doing so helps readers trace a distinct input, comparison, feedback or contextual link. Keep its source, destination and other meaning cues visible in grayscale.
- Check the figure in grayscale when practical.

## 2. Shapes and semantics

- Rounded rectangles are the default for ordinary process and information blocks.
- Use standard decision diamonds, terminators, input/output shapes, and map symbols when the diagram convention calls for them.
- Keep corner radii consistent across ordinary boxes and headers. Give decision/input silhouettes gently rounded vertices too; retain their role rather than replacing all shapes with circles.
- Avoid excessive nested containers and decorative shapes.
- Use borders sparingly and consistently.
- **Accent stripes**: Use `node.accent: "left"` or `"top"` with `node.accent_color` to visually highlight stage entry points or distinct data modalities without overwhelming the card fill.
- **Stage pill badges**: Use `node.badge` (e.g., `STAGE 1`, `STEP 2`, `INPUT`) anchored at the top-left to structure sequential multi-panel methods. Ensure `badge_fill` provides >= 4.5:1 contrast against white badge text.
- **Group containers**: Use `shape: "group"` with `container_fill` (e.g. `#F8FAFC`) and `border_style: "dashed"` to demarcate sub-systems, pipelines, or logical clusters.
- **Vector icons**: Use the built-in 24x24 vector icon library for semantic clarity (e.g. `database` for inputs, `cpu` for model layers, `shield` for verification, `dna` or `flask` for wet-lab assays). Avoid decorative clip-art.

## 3. Typography

- Use one sans-serif family unless the journal requires otherwise.
- Choose fonts likely to be available in the host environment; embed fonts in final exports when permitted and supported.
- Keep a clear hierarchy among panel titles, node labels, annotations, and footnotes.
- Avoid tiny text. Review the figure at its actual intended print size.
- Follow journal specifications first; there is no single font size suitable for every journal and figure dimension.
- Use proper subscripts, superscripts, Greek letters, symbols, and units. Do not approximate scientific notation with awkward plain-text substitutes when proper typography is available.

## 4. Spacing and alignment

Use a compact, balanced layout by default. Fit the canvas to the organised content within the venue's dimensions; size boxes around readable text and group title/detail tightly. Reduce oversized boxes, excess outer margins and empty inter-panel corridors before adding more elements. Follow [density and whitespace](layout-density.md) for composition and measured review; a fill percentage is an advisory, not a reason to crowd the figure.

- Use a consistent grid and equal gaps between comparable nodes.
- Align edges and centers deliberately.
- Keep enough whitespace around groups and between labels and connectors.
- Maintain consistent inner padding.
- Avoid crowding nodes against the canvas edge.
- Keep margins balanced.
- Do not let connectors pass through text or unrelated blocks.

## 5. Lines and arrows

- Use consistent connector thickness and arrowhead style. Let arrows carry the visual weight of the reading path when thinner box borders improve the hierarchy.
- Default to rounded caps/joins and smooth filleted connector bends. Use orthogonal control corridors to keep routing clear, and curve the elbows consistently across every diagram type. Hard elbows require an explicit user/venue choice.
- Use solid arrows for the primary flow unless another convention is required.
- Use dashed or dotted lines only when their meaning is explained.
- Route connectors around nodes and labels.
- Avoid unnecessary bidirectional arrows.
- Label feedback loops and conditional branches.

## 6. Canvas and export

- Follow journal dimensions and file requirements when known.
- Prefer vector output (SVG or PDF) for diagrams with text and geometry.
- Also provide a high-resolution PNG when requested or useful.
- For raster-only submission, follow the journal's resolution requirements; 300 dpi is a common baseline for many figure types but is not a universal rule.
- Check final physical size, page bounds, font embedding, transparency, and clipping.
- Use a consistent background.
- Keep editable source alongside exports.

## 7. Visual tone

Draw the reading order before deciding the shapes. Keep consecutive stages on an aligned spine where the relationships allow it. Give peer branches the same level of emphasis. Keep supporting paths to one side when their roles support it, and show exactly where each enters the main path. Use an edge label where two choices would otherwise be ambiguous.

For a small print figure, start with a white page, dark text and clear accents from the chosen palette. Use solid accents or tints according to the role, importance and legibility of each element. Keep important panel colours visible at print size. Give every frame, icon and colour a specific job. Keep comparable gaps consistent, preserve enough space for branches and let typography lead the reading order. Use the source's terminology and read the final lines at the intended width.

At that width, compare an alternative if the first layout looks flat, the arrows are faint or the main stages drift out of alignment. Compare layouts with the same labels and relationships. A slightly taller layout can give annotations and arrowheads the clearance they need.

Aim for:
- precise;
- restrained;
- balanced;
- modern;
- readable;
- scientific.

Avoid:
- childish clip-art;
- excessive gradients;
- glossy 3D effects;
- thick cartoon outlines;
- unnecessary shadows;
- over-saturated backgrounds;
- decorative icons with no informational purpose.

## 8. Human-Crafted Academic Aesthetic (Avoid the AI-Generated Look)

Real top-journal figures (Nature, IEEE, NeurIPS, *Attention Is All You Need*) look human-crafted in Adobe Illustrator, Figma, or LaTeX TikZ. Avoid "AI-generated SaaS card" over-styling:
1. **Flat, restrained, print-first:** Top-tier figures are flat vector schematics with clean pastel fills, crisp 0.8–1.0 pt borders, and generous alignment — **NEVER** stack drop shadows + SaaS corner badges + side accent stripes + UI icons all at once on every card.
2. **Typography carries the hierarchy:** Use bold dark titles (`9.0–10.0 pt`) + smaller muted-slate subtitles (`detail_color: "#475569"`, `detail_font_pt: 8.0`) inside tight, well-proportioned boxes (typical height 34–44 pt, not bloated 65 pt cards).
3. **Prefer clean flat rounded rectangles:** Use `process` rectangles with soft role-based pastel fills (like TikZ/Illustrator) for most pipeline stages; use 3D `data` cylinders or `decision` diamonds only when classical flowchart notation genuinely enhances clarity.
4. **Restraint with icons & badges:** An icon-free, typography-led schematic is often the cleanest, most authoritative choice. If icons help, use at most 2–4 purposeful domain symbols (or custom domain `.svg` / AI art) — do **NOT** stamp a wireframe UI icon onto every single box. Reserve `badge` only for multi-panel labels like `(a)` / `(b)` or numbered stages, never SaaS status tags like `INPUT` / `EVAL`.
5. **Clean geometry & compact legends:** Align boxes on a strict grid with consistent vertical/horizontal gaps (12–18 pt), use crisp orthogonal rounded connectors without unnecessary zigzags, and ensure every legend swatch matches the exact fill/stroke/line style actually drawn in the diagram.

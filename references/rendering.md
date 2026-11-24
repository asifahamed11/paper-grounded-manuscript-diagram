# Local drawing contract

`scripts/render_diagram.py` renders an explicit JSON layout. For a standard sequence, parallel workflow or decision branch, start with [method to figure](method-to-figure.md) and use the exported JSON to refine positions. Read this contract for custom and existing layouts.

## Shared rounded style

The whole renderer defaults to soft corners and smooth connector bends. Process boxes, headers and group frames share a five-point corner radius; semantic input/decision silhouettes retain their meaning with gently rounded vertices. Data sources have curved caps and outputs use rounded terminators. This is a visual system applied to all layouts, not a special case for one figure.

```json
"style": {
  "corner_radius_pt": 5,
  "connector_style": "rounded",
  "connector_radius_pt": 5,
  "line_width_pt": 0.85,
  "connector_width_pt": 1.15
}
```

Connectors follow the supplied orthogonal corridors but replace each bend with a quadratic fillet. Short segments automatically limit the radius to half the adjacent segment lengths. Caps and joins are rounded. If a venue explicitly requires hard elbows, set `connector_style` to `orthogonal`; set `corner_radius_pt` to zero only for a deliberate square-shape override. Do not mix arbitrary per-node styles.

Use `style.connector_width_pt` to adjust connector weight independently of box borders. Omit it to use `style.line_width_pt` for both. Use `style.connector_color` for the main paths and set optional `edge.color` to a palette name or `#RRGGBB` when an accent clarifies a route. Pair colour with visible labels, route geometry or line style. The native draw.io export carries both overrides.

Specify ports on the named bounding-box edges. The renderer intersects that corridor with the **actual** rounded/sloping outline, preserving the horizontal/vertical direction. This prevents visible gaps at parallelograms, softened diamond tips and cylinder caps. The resolved ports are recorded in QA. A corridor that misses the shape fails instead of silently inventing a connection.

## Coordinates and size

- All coordinates and font sizes are **points**, 72 points per inch, with the origin at the top left.
- `canvas.width_pt` and `height_pt` determine SVG/PDF physical size and raster pixel dimensions. For example, 464.4 points is 6.45 inches. At 600 DPI that width is 3870 pixels.
- Choose the actual manuscript width before laying out. Defaults: 9-point labels and 8.5-point minimum. Follow a supplied journal requirement instead. Do not force a dense two-lane figure into a single column.
- JSON `box: [x, y, width, height]` always uses positive width/height. `label` is required. Explicit newlines are honoured and each line may wrap at word boundaries. Long unbreakable identifiers need wider boxes or an author-approved abbreviation.

## Nodes

```json
{"id":"source", "shape":"data", "box":[12,40,150,52],
 "label":"Observed records\nDates and source definitions", "fill":"sky_blue"}
```

Shapes: `process` (default), `data`, `input`, `decision`, `terminator`, `header`, `group`. Groups are transparent dashed containers; their label occupies the top 34 points (customisable using `label_height_pt`). Other nodes may sit inside that container without triggering overlap errors. This exemption does not excuse crossing group labels or unrelated child nodes.

Optional node fields: `fill`, `text_color` (palette name or `#RRGGBB`), `font_pt`, `bold`, `padding_pt`. Supported colours: black, white, blue, sky_blue, orange, green, purple, yellow, vermillion. Palette names are convenient, not scientific meaning. Contrast is checked at 4.5:1 as a conservative local default; this is not a journal compliance certificate.

Use `style.stroke_color` and `style.connector_color` for a coherent outline and connector palette. `node.stroke_color` overrides the shared stroke. Set `align` to `left` for a left-aligned heading or stack and `center` for centered text. Transparent group headings and annotations use white-canvas contrast.

For a bold title over a regular-weight explanation, supply `label` and `detail` separately. By default they form a centred, measured **stack**, separated by `style.title_detail_gap_pt` (3.5 pt); a tall node no longer pushes its title and explanation far apart. `detail_font_pt` controls the explanation size. The combined stack must fit; if not, enlarge/reflow the node rather than hiding overflow. Cylinders clear the six-point cap and decisions use their inscribed text area.

For compatibility, an existing explicit `title_height_pt` retains separate band layout unless `text_layout: "stacked"` is set. `text_layout: "bands"` deliberately uses the old bands (default title band 18 pt, or 22 for data). Use a reserved band only when the intended layout needs it. It is not the compact default.

## Density diagnostics

Read [density and whitespace](layout-density.md) for content-first composition. `--layout-only` returns standard-library box occupancy, margins and gap diagnostics without moving content or measuring fonts. A full render adds actual text/icon content envelopes in `layout` inside the QA report. Headers/group frames cannot inflate the main-node union. Sparse/crowded layout warnings are also printed by the CLI. They prompt visual review and do not change the geometry pass/fail result. The renderer never moves nodes or changes the physical canvas automatically.

## Connections and notes

```json
{"id":"records-to-audit", "from":"source", "to":"audit",
 "points":[[87,92],[87,110]], "style":"solid", "label":"Verified"}
```

Give every edge named source/target nodes and an explicit route with at least two points. Edges may include an optional `label` string, which is rendered natively along the longest segment of the route, verified against collisions, and exported to Draw.io edges. Route control points consist of nonzero horizontal/vertical segments; the renderer rounds their bends by default. First and last points must meet their named boxes. Make corridors for connectors; do not route through unrelated nodes or text. Obstacle/label checks use the drawn curves sampled at 16 points per bend, rather than checking only the unrounded controls. A merge can use two routes ending on the same target boundary. A dedicated junction may be represented by a small process node only when scientifically meaningful; avoid adding empty dummy methods.

The initial and final corridors must approach their named sides from outside each shape. An unexpected route crossing or overlap is an error, with its location recorded in QA. Shared fan-out or fan-in paths from the same port are allowed. If a crossing is deliberate, use `allowed_crossings` with `{"edges":["first-id","second-id"],"reason":"Explanation of the intended crossing"}` and clarify it in the figure. Review route readability at print size.

`arrow` defaults to `end`. Use `none` for undirected associations and `both` only for a genuinely two-way relationship. An arrowless edge still needs `from`/`to` for geometry; those names do not assert causal direction. The conceptual-framework example shows association lines and an explicit noncausal note.

For `style: "dashed"`, include `meaning`, and explain that meaning in a visible note or caption. The string is audit metadata, not an automatically drawn legend. Put footer/legend text in `annotations`, with its own `box`, `label`, optional font size and padding. These bounds and collisions are measured too.

## Optional local icons

Read [the icon workflow](icon-workflow.md) before choosing/generating assets and comparing placement candidates. The renderer does not generate or remove backgrounds. Optional top-level `icons` records have `id`, `path`, `alt`, plus the chosen placement fields below. IDs use letters/digits/hyphens/underscores. Paths accept both local `.png` raster files and local `.svg` vector files under the specification directory (SVG icons must contain valid, safe vector path data); URLs, absolute paths, parent traversal and symlink escapes are rejected. Raster PNG assets must be single-frame PNGs with actual transparency and a clear transparent border, at most 16 megapixels. Native DPI must be at least 300 at the fitted physical placement. Scaling preserves aspect ratio.

For an icon/title cluster use `node`, `placement: "title"`, `size_pt: [width,height]`, and optionally `gap_pt` (default 4). Omit `box` and `icon_space_pt`. Measured title width sets the cluster position; detail text uses the full inner width. The cluster and detail are centred together vertically. The selected node must use stacked text and one attached icon; an oversized cluster fails rather than adding height or shrinking content silently. This can avoid the wasted column and extra detail wrapping of a side strip.

For side/top placement use `node`, `placement: "left"`, `"right"` or `"top"`, a fixed `box`, and `icon_space_pt` on the node. The value reserves width for left/right or height for top; the text uses the remainder. The assigned icon box must fit that strip with at least two points of margin. Old attached icons without a placement remain left-strip icons. A standalone icon omits `node` and uses an explicit `box` (fixed placement). All fitted rectangles must respect semantic silhouettes. Image-image, image-label, unrelated-node and image-connector overlaps fail geometry checks. Raster contrast, optical alignment and the best placement choice still require visual review, including against a coloured node. The renderer records the selected mode and resolved bounds, not an automatic best-position claim.

The CLI resolves assets relative to the input JSON. Python callers pass `asset_dir=spec_path.parent` to `render(...)`. Successful source export copies prepared icons into `<stem>-assets/` and rewrites `<stem>-source.json` to refer to those copies, so the complete output folder is reproducible elsewhere. SVGs embed PNG data; no external links are required. PDF/SVG labels and geometry stay vector, but the icons remain raster. QA records native pixel size, fitted bounds, DPI, meaning and SHA-256. Keep original generation prompts/terms separately; the renderer cannot verify them.

## Mathematical notation

Mathematical formulas use Matplotlib mathtext (100% free, zero external LaTeX install required). By default `parse_math=False` is active so literal currency strings such as `Cost $100 and $200` pass through unchanged. Math rendering is opt-in:
- Set `"math": true` on a node, edge or annotation (or `canvas.math: true` across the figure).
- Or use explicit inline delimiters: `\( \alpha + \beta \)`. The renderer safely translates `\( ... \)` to `$...$` while preserving literal `$` outside formulas.

## Publication themes and typography

The renderer includes 5 curated, publication-grade academic themes:
- `nature-clean`: Deep ink (`#0F172A`), muted slate detail (`#475569`, `8.0 pt`), fills (`process`: `#FFFFFF`, `data`: `#EBF5F7`, `input`: `#F1F5F9`, `decision`: `#FEF7E6`, `terminator`: `#EAF6EE`), strokes (`#94A3B8`, `#2B7A8B`, `#64748B`, `#C27803`, `#1E7E5C`), connectors `#334155` (`1.15 pt`), `arrow_scale: 7.0`, flat print vector (`shadow: false`), `corner_radius_pt: 4.5`.
- `ieee-crisp`: High-contrast navy ink (`#0F172A`), steel detail (`#334155`, `8.0 pt`), fills (`#FFFFFF`, `#E8F1FA`, `#F1F5F9`, `#FEF7E0`, `#E8F5E9`), strokes (`#334155`, `#1D4ED8`, `#4A6572`, `#B45309`, `#15803D`), connectors `#1E293B` (`1.15 pt`), `arrow_scale: 7.0`, flat print vector (`shadow: false`), `corner_radius_pt: 3.5`.
- `neurips-soft`: Modern ML/AI aesthetic with charcoal ink (`#111827`), muted detail (`#4B5563`, `8.0 pt`), pastel fills (`#FFFFFF`, `#EEF2FF`, `#F0F9FF`, `#FEF3C7`, `#ECFDF5`), strokes (`#94A3B8`, `#4F46E5`, `#0284C7`, `#B45309`, `#047857`), connectors `#374151` (`1.15 pt`), `arrow_scale: 7.0`, flat print vector (`shadow: false`), `corner_radius_pt: 4.5`.
- `biomed-prisma`: Clinical slate ink (`#1E293B`), detail (`#475569`, `8.0 pt`), soft tints (`#FFFFFF`, `#EBF5FB`, `#F4F6F7`, `#FEF5E7`, `#EAFAF1`), strokes (`#94A3B8`, `#0284C7`, `#0D9488`, `#EA580C`, `#16A34A`), connectors `#475569` (`1.15 pt`), `arrow_scale: 7.0`, flat print vector (`shadow: false`), `corner_radius_pt: 4.0`.
- `print-mono`: 100% grayscale publication theme with ink (`#111827`), detail (`#4B5563`, `8.0 pt`), fills (`#FFFFFF`, `#F3F4F6`, `#E5E7EB`, `#F9FAFB`), strokes (`#374151`, `#111827`), connectors `#111827` (`1.15 pt`), `arrow_scale: 7.0`, flat print vector (`shadow: false`), `corner_radius_pt: 3.5`.

Specify a theme in the spec via `"style": {"theme": "nature-clean"}` or on the CLI via `--theme <name>`. Theme colors provide defaults; any explicit node or style attributes in the JSON specification always take precedence. The renderer also supports `style.detail_color` and `style.detail_font_pt` (default `8.0 pt` across all 5 themes) to tune subtitle typography independently.

Set `"canvas": {"font_family": "auto"}` to automatically detect and select the best installed sans-serif font from `['Inter', 'IBM Plex Sans', 'Liberation Sans', 'Arial', 'Helvetica', 'Segoe UI', 'DejaVu Sans']`.

## Visual polish: cards, containers, and badges

- **Card Elevation (`style.shadow` or `node.shadow: true`)**: Draws a restrained vector shadow patch (+1.2 pt x, +1.4 pt y) in solid cool gray `#E8EEF2` (zorder 1.5) behind non-group nodes. 100% vector, zero transparency warnings in EPS/PDF.
- **Role Accent Stripes (`node.accent: "left" | "top"`, `node.accent_color`)**: Renders a crisp 3.0 pt saturated indicator stripe along the node edge, shifting content padding +3.5 pt to avoid text crowding.
- **Tinted Group Containers (`node.container_fill`, `node.border_style: "solid" | "dashed"`)**: Allows group nodes to have a soft tinted background (e.g. `#F8FAFC`). When `container_fill` is omitted, group containers remain completely transparent.
- **Stage Pill Badges (`node.badge`, `node.badge_fill`, `node.badge_text_color`)**: Displays a compact metadata pill badge (e.g. `STAGE 1`, `INPUT`) anchored at the top-left of the node. Contrast is strictly verified against 4.5:1 ratio and logged in the QA report as `<node_id>:badge`.

## Connectors and crossing jumps

- **Arrowhead Scale (`style.arrow_scale`)**: Configurable arrowhead size (default 6.0, themes use 7.5–8.0).
- **Crossing Jump Halos (`style.crossing_jump: true`)**: For allowed crossings (`allowed_crossings`), renders a clean 5 pt white halo behind the foreground connector to produce a clean visual gap over the background connector.

## Compact horizontal legends

Specify a top-level `legend` object to render a clean horizontal legend:
```json
"legend": {
  "box": [40, 220, 300, 24],
  "frame": false,
  "items": [
    {"label": "Input Data", "fill": "#F0F9FF", "stroke_color": "#0284C7", "kind": "node"},
    {"label": "Evaluation Flow", "color": "#0F62FE", "kind": "edge", "shape": "line", "dashes": [3, 2]}
  ]
}
```
Legends default to borderless (`"frame": false`) for an editorial, non-boxy look; set `"frame": true` to render an outer rounded frame. Swatches support both node fills/strokes and line/arrow edges. The renderer verifies swatch contrast, text legibility, and ensures the legend does not collide with nodes or annotations. Native Draw.io exports also receive matching styled legend cells.

## Pure-vector scientific icon library

In addition to raster PNG icons, the renderer includes a built-in library of 30 pure-vector 24x24 scientific icons spanning Data, AI/Compute, and Science:
- **Data & Storage**: `database`, `table`, `document`, `documents`, `folder`, `cloud`, `globe`, `satellite`, `sensor`, `waveform`
- **AI & Compute**: `brain`, `neural_net`, `cpu`, `code`, `layers`, `filter`, `merge`, `split`, `sliders`, `gear`
- **Science & Analysis**: `microscope`, `dna`, `flask`, `chart_bar`, `chart_line`, `search`, `check`, `alert`, `shield`, `users`

Attach a vector icon to any node using:
```json
{"id": "icon-1", "vector_icon": "cpu", "node": "encoder", "placement": "title", "size_pt": [12, 12], "alt": "CPU"}
```
Vector icons scale losslessly in SVG/PDF/EPS exports without triggering raster warnings, and export to Draw.io as embedded SVG data URIs. List all available icons using `python scripts/render_diagram.py --list-icons`.

## Exports and failure behaviour

Successful geometry emits `figure-01.svg` (text retained, local sans-serif fallback stack), `figure-01-outlined.svg` (stable glyph paths), `.pdf` (vector, local font embedded where supported), `.png` (600 DPI by default), `-preview.png`, `-print-size.png` (96 DPI), `-source.json`, and `-qa.json`. `--preview-only` exports the inspection PNGs and receipt for quick comparisons. Pass `--eps` to additionally export vector EPS (`figure-01.eps`).

The outlined SVG keeps exact label geometry when Word or another machine lacks the plotting font. Its letters are paths, not editable text; keep the editable SVG and JSON alongside it. A fallback font can change text metrics, so inspect the editable SVG in the target viewer or use the outlined export for embedding. No remote font download is used.

Use `--drawio` for native diagrams.net objects. Group nodes are exported as containers with child relative coordinates and matching corner radius. Use `--tiff` for an RGB LZW TIFF at the chosen resolution. Use `--profile` to validate journal figure constraints:
- `plos-one`: 66.8–190.5 mm width, <=222.3 mm height, 300–600 DPI, 8–12 pt font, required font family, TIFF < 10 MB.
- `ieee-single`: width <= 252.0 pt (3.5 in), min font >= 8.0 pt, 300–600 DPI.
- `ieee-double`: width <= 515.52 pt (7.16 in), min font >= 8.0 pt, 300–600 DPI.
- `springer-lncs`: width <= 345.83 pt (122 mm), height <= 547.09 pt (193 mm), min font >= 8.0 pt, 300–600 DPI.
- `nature-single`: width <= 252.28 pt (89 mm), min font >= 7.0 pt, 300–600 DPI.
- `nature-double`: width <= 518.74 pt (183 mm), min font >= 7.0 pt, 300–600 DPI.
- `elsevier-double`: width <= 538.58 pt (190 mm), min font >= 7.0 pt, 300–600 DPI.

Geometry failure writes a diagnostic PNG, the attempted JSON and a failed QA receipt and returns exit status 1. Input and export errors publish a failed receipt and return 2. Each run stages its files before publishing the current receipt. When reusing a stem, the renderer keeps previous generated files inside `.history/`. If a previous generated file was edited, removed or supplemented, choose a new stem. Unrelated files stay in place. Check the current receipt's status, spec hash and artifact hashes before delivery.

`--check-only` validates schema/geometry inputs without importing Matplotlib; it does not measure rendered labels. `validate_svg.py` checks standalone SVG structure and active/external resources; it cannot measure fonts or certify the figure's science.
`--require-sources` enforces that substantive nodes and edges have valid `source_refs` pointing to records in `spec["sources"]`.
`--require-paper-figures` enforces that `spec["sources"]` contains at least 2 inspected published figure sources (`kind: "figure"` with nonempty `title`, exact `locator`, and verifiable `doi`/`url`/`pdf_url`), ensuring that new diagrams are grounded in peer-reviewed domain literature.

## Choosing another authoring method

Use custom local SVG/Matplotlib for visual relationships this helper cannot express. Use GIS for maps, a scientific plotting library for measured results, and native draw.io/PPTX tooling if the user requires those editable formats. Preserve local fonts and source evidence. Do not install or call hosted tools just to make this template work.

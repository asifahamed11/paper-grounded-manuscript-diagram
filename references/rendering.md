# Local drawing contract

`scripts/render_diagram.py` renders a human/agent-designed JSON specification. It supplies drawing and measurement mechanics; it does not infer a method or automatically lay out a graph.

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

For a bold title over a regular-weight explanation, supply `label` and `detail` separately. Optional `title_height_pt` (default 18, or 22 for a data cylinder) reserves space for the title; `detail_font_pt` controls the explanation size. Cylinder titles clear the six-point cap. Enlarge the box or title band for long titles instead of making all text bold or shrinking below the minimum.

## Connections and notes

```json
{"id":"records-to-audit", "from":"source", "to":"audit",
 "points":[[87,92],[87,110]], "style":"solid"}
```

Give every edge named source/target nodes and an explicit route with at least two points. Routes consist of nonzero horizontal/vertical segments. First and last points must meet their named boxes. Make corridors for connectors; do not route through unrelated nodes or text. A merge can use two routes ending on the same target boundary. A dedicated junction may be represented by a small process node only when scientifically meaningful; avoid adding empty dummy methods.

For `style: "dashed"`, include `meaning`, and explain that meaning in a visible note or caption. The string is audit metadata, not an automatically drawn legend. Put footer/legend text in `annotations`, with its own `box`, `label`, optional font size and padding. These bounds and collisions are measured too.

## Exports and failure behaviour

Successful geometry emits `figure-01.svg` (text retained, local sans-serif fallback stack), `figure-01-outlined.svg` (stable glyph paths), `.pdf` (vector, local font embedded where supported), `.png` (600 DPI by default), `-preview.png`, `-print-size.png` (96 DPI), `-source.json`, and `-qa.json`.

The outlined SVG keeps exact label geometry when Word or another machine lacks the plotting font. Its letters are paths, not editable text; keep the editable SVG and JSON alongside it. A fallback font can change text metrics, so inspect the editable SVG in the target viewer or use the outlined export for embedding. No remote font download is used.

On a measured geometry failure, only `-diagnostic.png` and `-qa.json` are produced for that run; exit status is 1. Input/dependency errors return 2. Existing files from a previous successful run are not a fresh success: use an empty revision directory while iterating and check the current QA report's `exports` and `passed_geometry_checks`.

`--check-only` validates schema/geometry inputs without importing Matplotlib; it does not measure rendered labels. `validate_svg.py` checks standalone SVG structure and active/external resources; it cannot measure fonts or certify the figure's science.

## Choosing another authoring method

Use custom local SVG/Matplotlib for visual relationships this helper cannot express. Use GIS for maps, a scientific plotting library for measured results, and native draw.io/PPTX tooling if the user requires those editable formats. Preserve local fonts and source evidence. Do not install or call hosted tools just to make this template work.

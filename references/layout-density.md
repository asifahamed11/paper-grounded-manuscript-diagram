# Compact composition with useful breathing room

The default is a diagram that feels cohesive and makes good use of its footprint. Keep enough separation to distinguish steps, labels, icons and routes. Do not scatter short labels across a large page or compress a complex method into illegible clusters.

## Compose from content

1. Fix the intended print width, supported labels/relationships and readable font sizes. If the venue leaves aspect ratio open, choose the height after arranging content; do not start with a large square or slide canvas and spread content to its edges.
2. Estimate each node from its wrapped title/detail and optional icon. Use a small number of comparable widths/heights, rather than identical oversized boxes for everything or arbitrary sizes for every label. Centre title/detail as one closely spaced stack. The renderer's default gap between their measured bounds is 3.5 pt; explicit legacy band heights remain supported when deliberately needed.
3. Arrange meaningful rows, columns, branches or lanes. Bring related stages together; align shared baselines and evaluations when scientifically appropriate. Balance a short lane against a long one by useful grouping/alignment, not a huge empty frame or invented stages. An association is not a sequence merely because a chain packs more tightly.
4. Shorten long empty corridors and remove redundant bend detours, preserving named connections and arrow direction. Reserve channels for branch labels, feedback and dashed interpretation links. Keep those legitimate spaces even when a fill metric is low.
5. Remove excess outer canvas space within the venue's size constraints. Include curved strokes, arrowheads, side loops, captions and legends when checking bounds. If width is fixed, adjust height or recompose; do not crop and stretch the figure to pretend it is denser.
6. Inspect at actual print size. If tight, first redistribute/reflow rows or labels, revise optional wording with the author's permission, or split panels. Do not shrink below the chosen minimum, overlap components or add decorative content to hit a percentage.

For ordinary 9-point workflow labels, useful **starting ranges** are about 4–6 pt inside rectangular boxes, 10–18 pt between sequential rows, 14–24 pt for simple lane/branch corridors, and 6–12 pt outside content. These are local composition heuristics, not journal rules or fixed limits. A decision diamond, long label, cylinder cap or multi-route channel can need more. Comparable items should share a rhythm; every gap need not be identical.

## Read fill rate as several diagnostics

There is no single universal fill target for all research diagrams. Ink coverage would count white boxes as empty and colour blocks as full; neither measures clarity. The renderer therefore reports transparent, box-based quantities:

| Diagnostic | Meaning | Useful response |
|---|---|---|
| `main_box_canvas_fraction` | Union area of substantive node bounding boxes / whole canvas | A small value can indicate wasted canvas, but can also reflect an inherently sparse network. |
| `main_box_envelope_fraction` | The same node area / the bounding envelope of those nodes | Separates inner scattering from outside margins. It excludes headers and group frames; nested frames cannot inflate it. |
| `outside_margins_pt` | Distances from all assigned node/icon/note bounds and routed control points to canvas edges | Review large margins, including below a footer. These are coordinate estimates; allow stroke/arrowhead safety space during visual review. |
| `median_nearest_node_gap_pt` | Median of each substantive node's nearest box separation | Review overlong gaps, alongside the topology and actual connector corridors. |
| `node_content` | Measured text/icon envelope relative to each node box | Helps spot a short label floating in a tall/wide box. It is not glyph ink coverage. Preserve semantic silhouette and comparable widths when useful. |
| `crowded_pairs` | Box separations below the local 6 pt review threshold | Check arrowheads and breathing room; geometry may still be technically valid. |

The local compactness review flags box-envelope occupancy below 42%, typical nearest gaps above 24 pt, unusually large outside margins, or small content envelopes. The thresholds prompt inspection; they do not fail rendering, rank quality or override the method. A branch/association diagram may intentionally stay below that occupancy threshold. If a warning is justified by topology or venue dimensions, keep the space and briefly record why.

Measure before/after with the **same definitions** and keep labels, relationships and font sizes comparable. Prefer increased useful occupancy accompanied by shorter routing and clearer grouping. Increasing box size, removing a legend, shrinking letters or adding a solid background to improve a number is not a compactness improvement.

```sh
python scripts/render_diagram.py diagram.json --layout-only
python scripts/render_diagram.py diagram.json --output-dir revision --stem method
```

`--layout-only` uses no optional packages and does not edit the JSON or measure text. Full rendering adds actual label/icon envelopes and records the diagnostics in `-qa.json`. The helper does not automatically move nodes, crop the canvas or route a graph; the agent must recompose the source and inspect it. These rules also apply when using another authoring tool.

## Acceptance

- The figure reads as one organised composition; no unexplained isolated islands or empty bands dominate it.
- Related steps are close, comparable gaps follow a consistent rhythm, and rows/columns align where meaningful.
- Titles and explanations sit together, with enough but not excessive inner padding.
- Text, icons, arrowheads and branch/feedback labels remain distinct at the intended print width.
- Semantic shape, content, numbers, relationships, palette and rounded visual language remain correct.
- Automated density/clearance advisories have been reviewed, with any intentional whitespace explained. A high fill metric cannot waive the visual checks.

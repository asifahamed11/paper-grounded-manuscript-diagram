# Choose shapes from inspected figures

Start with the objects and operations in the user's method. Give each a role
that a reader needs to distinguish. Read the relevant papers' figures, captions,
and adjacent text for the visual conventions used to represent those roles.

## From observed shapes to placements

1. **Inventory each inspected figure.** List distinct forms, their role in that
   figure, and a precise panel or location. Include relevant outlines, symbol
   nodes and image tiles. Group repeats with the same form and role. Record a
   second observation when the same form means something different. Describe
   an unfamiliar form in plain language. Mark a role as unclear when the
   visible evidence cannot resolve it.
2. **Compare by meaning.** Across the inventories, find shapes that represent a
   similar role to an object or operation in the user's method. Check that the
   form stays recognizable at the target print size, works in grayscale, and
   fits the actual routes. Select the shape for each corresponding node. Reuse
   one convention wherever the role repeats. Explain a locally chosen shape
   when none of the observed forms fit the method.
3. **Record the placement.** In the editable JSON, store the inventory in each
   `design_review.precedents[*].shapes` and map your choices in
   `design_review.shape_choices`. The node's `source_refs` support its study role
   and its `from_shapes` entries identify the borrowed visual conventions.
   For a figure without discrete shapes, record `shapes: []` and a
   `shape_inventory_note` describing its visual structure.
4. **Compare at print size.** Ask the reader checks against the rendered figure.
   If a grid, stack or symbol makes adjacent routes hard to trace, revise its
   placement or use a labeled detail panel that preserves the relationships.
   Deliver a short per-figure inventory and explain the important placements.
   The editable JSON carries the full observations and reasons.

Use `--require-shape-review` with either CLI to check that each reviewed figure
has an inventory and that each method node has a shape choice. References must
resolve to an inventoried form and the choice must match the node's actual shape.
Include supplied paper figures you can inspect locally. When the analysis uses
only method evidence and you inspect zero paper figures, use an empty
precedent list and explain the choices from the method. The check validates
the record. The figure and its caption establish what the source shows.

## Native shapes by role

| Shape | Intended role and placement |
| --- | --- |
| `process` | Named stage, model block, or action in a workflow. |
| `data` | Dataset, repository, or persistent store. |
| `input` | Input or output crossing a stage boundary. |
| `decision` | Condition with explicitly labeled exits. |
| `terminator` | Start, end, or final handoff. |
| `header`, `group` | Section label or frame for a responsibility, panel, or scope. Set their positions in an explicit layout. |
| `tensor` | A tensor, feature stack, or pyramid level emitted by a stage. Offset planes leave space for a label or a level name. |
| `grid` | A schematic token/patch grid, matrix, or spatial mask. Give the label the actual role. The small repeated cells are a symbol with illustrative dimensions. |
| `operator` | A compact sum, concatenation, subtraction, or other specified operation. Use a short label or glyph, name the operation nearby when needed, and draw the actual inputs and outputs. Use equal width and height for an explicit circle. |
| `document` | A named protocol, annotation sheet, manifest, or report. Use it where the document enters or leaves the process. |
| `external` | Actor, source, or service outside a system. Put it outside the labeled boundary when the crossing matters. |
| `state` | A persistent condition, construct, or state. Choose the line and arrow semantics from the evidence. |
| `event` | A discrete trigger or milestone. Place a dated event on a scaled axis only when time spacing is supported. |

Use native swatches for the seven additional shapes when readers need help
interpreting a form. Set the legend item's `shape`, `color` and `stroke_color` to match the
corresponding node. Keep any sign inside an operator in the actual node or
explain it with a nearby annotation.

Match the drawing method to the source geometry. Use grids and stacks for
schematic data objects. Use measured heatmaps, maps, imagery, and plots as
local figure assets with their proper units, legends, or scale. Use labeled
group boundaries for nested components and connectors for fan-in, fan-out, and
feedback. For a field-specific symbol with its own meaning, compose a local
vector asset and explain the symbol in the review. These choices keep the
shape vocabulary usable across studies.

```sh
python scripts/render_diagram.py --list-shapes
python scripts/plan_diagram.py --list-shapes
python scripts/render_diagram.py templates/multiscale-architecture.json --output-dir demo --stem multiscale --drawio --profile ieee-double --require-sources --require-paper-figures --require-shape-review
python scripts/render_diagram.py templates/scientific-shapes.json --output-dir demo --stem shape-roles --drawio --profile ieee-double --require-sources --require-shape-review
```

The [multiscale source](../templates/multiscale-architecture.json) contains
five published-figure inventories and the node choices. The [handoff
source](../templates/scientific-shapes.json) shows the seven additional shapes
with choices grounded in a local method. View the `*-print-size.png` and
editable `*.drawio` files. New shape outlines are embedded as native
diagrams.net stencils. [diagrams.net stencil format](https://www.drawio.com/docs/tutorials/custom-shapes/)

## Method for the example

In this synthetic example, a shared encoder processes the token grid at
each of two epochs. The two output tensors hold aligned token features
`A` and `B`. Their element-wise absolute difference yields the token
contrasts. The little grids represent data structure schematically. In the
separate review handoff, a data steward outside the internal review system
submits a QA checklist. Opening the review marks the transition of that
checklist into the in-review state.

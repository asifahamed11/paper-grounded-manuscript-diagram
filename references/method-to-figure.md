# From method to editable figure

Use this path for a sequence, parallel workflow or decision branch with explicit relationships. Keep a manuscript caption separate from labels inside the figure. Set the final physical width first so that typography is measured for the size the reader sees.

## Run the example

Use a local Python environment with Matplotlib and Pillow. The same environment can install the optional PDF helper from `requirements-optional.txt`.

```sh
python scripts/plan_diagram.py --doctor
python scripts/plan_diagram.py templates/review-selection-method.json --output-dir demo --drawio --require-sources
```

Open `demo/method-print-size.png`, `demo/method.drawio` and `demo/method-qa.json`. The screening example is an excerpt of study selection in the database and register path in [Page et al. (2021), Fig. 1](https://www.bmj.com/content/372/bmj.n71), with reporting details from [item 16a](https://www.bmj.com/content/372/bmj.n160). The layout is an original adaptation for teaching. A completed review supplies its own counts, reasons and identification stages. For an official PRISMA form use the [PRISMA flow-diagram templates](https://www.prisma-statement.org/prisma-2020-flow-diagram).

## Describe your method

| Input | What to supply |
|---|---|
| `title`, optional `description` | Identify the figure and describe its reading order or links. |
| `canvas.width_pt` | Intended figure width in points. At 72 points per inch, 252 points equals 3.5 inches. The planner calculates height. |
| `nodes` | Stable `id`, visible `label`, optional `detail`, and meaningful `shape`. |
| `edges` | Links with `from` and `to` ids. Add `label` for an explicit branch choice. Preserve `arrow`, `style` and `meaning` from the method. Optional `color` helps a reader follow a distinct route. |
| Optional `lanes` | Name lanes in left-to-right order and set each node's `lane`. This keeps a method track aligned over several ranks. |
| Optional `direction` | Use `vertical`, `horizontal` or `auto`. Auto uses a horizontal layout only when short ranks and measured labels fit. |
| Optional `icons` | One prepared local PNG with `id`, `path`, `node` and `alt` per destination. Candidate size is `size_pt` with optional explicit `placement`. |
| Optional `math` | Set `"math": true` (on canvas, node or edge) or use inline `\( ... \)` to render mathematical formulas without external LaTeX dependencies. |
| Optional `sources`, `source_refs` | Put the document or code identity and locator beside the stages and links they support. |

The planner measures wrapping and sizes nodes for the requested font. It lays out adjacent tiers of an acyclic workflow, skip-rank DAG corridors, and cyclic feedback loops with outer return routes. Ranks can hold branches, aligned lanes, or horizontal left-to-right pipelines with vector icons and labels. Branch labels are dynamically spaced to prevent overlap with connector lines and nodes. Use `--drawio`, `--tiff`, `--eps`, or `--profile` (e.g. `ieee-single`, `springer-lncs`, `plos-one`) to generate matching manuscript exports. A geometry error includes the attempted specification for revision. Move nodes or change routes there while preserving the method and caption.

If a draft already has `box` for each node and `points` for each edge, use `render_diagram.py` directly to retain the layout.

## Trace content and design choices

Each `sources` record needs an `id`, `title` and `locator`. Optional `kind` distinguishes `method`, `figure`, `dataset`, `code` and `asset`. Use `source_refs` on a node or edge to name the records that support it. Record a paper's DOI or public URL when applicable. For style references add the actual figure locator and the specific convention adopted.

`--require-sources` checks that named references exist and cover substantive nodes and edges. The QA report lists all links and missing references. Verify that the specified location supports the claim, numbers, role and arrow direction. A bibliography entry alone cannot establish that support. Keep unpublished evidence in the local project.

`--require-paper-figures` enforces that deeply analyzed published figure sources (`kind: "figure"` with nonempty `title`, exact `locator`, verifiable `doi`/`url`/`pdf_url`, and nonempty `takeaway` or `notes`) are present in `spec["sources"]` (default minimum: **5**, configurable via `--min-paper-figures`). Use it alongside `--require-sources` for every new manuscript diagram to ensure thorough visual and methodological peer-reviewed literature grounding.

## Prefer a clean starting composition

Choose a flat, colorblind-safe scientific theme (`okabe-ito` for general workflows/ML pipelines, `paul-tol-muted` for conceptual/framework models, `paul-tol-pale` for text-heavy PRISMA/flowcharts, or `print-mono` for B&W print) via `"style": {"theme": "..."}` or `--theme`. Keep the primary path recognisable in grayscale, pair strong accents with readable dark ink, and reserve ordinary steps for quiet backgrounds. Review the visual order of branches and use a borderless horizontal `legend` or annotation when explaining line styles or shared roles. Use `--preview-only` for comparing alternatives. Give each candidate its own stem.

Compare the full composition at the intended width. Keep room between parallel branches, around arrowheads and near branch labels. Choose the layout that reads most naturally, even if another candidate has a higher occupancy fraction.

For prepared icons the planner compares title, side and top arrangements using measured title and detail lines and the required height. The QA receipt records the options and the chosen placement. Inspect optical spacing and recognisability at print size. Use the existing manual positions for an intentional override.

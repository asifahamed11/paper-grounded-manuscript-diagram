# Paper-Grounded Manuscript Diagram

**Turn research methods into clear, editable diagrams.**

A portable Agent Skill for research workflows, method schematics and conceptual frameworks. Learn from relevant paper figures, preserve the actual method, and deliver a compact composition with readable labels and reproducible source.

![A compact parallel research workflow with rounded shapes and two coordinated study lanes](assets/readme/research-workflow.png)

*An illustrative [parallel-study example](templates/parallel-study.json), rendered with the bundled local engine. This is a layout demonstration, not a research result.*

## Why use it?

- **Research stays intact.** Preserve supported stages, numbers and relationships; inspect paper figures when they help answer a design question.
- **Space works harder.** Compact layouts, close title/detail stacks, rounded connectors and a restrained Okabe–Ito palette.
- **Checks accompany the figure.** Measured text, overlap, contrast, ports and spacing, followed by full and print-size visual review.
- **Source stays editable.** SVG text, vector geometry, PDF, 600-DPI PNG and a reproducible JSON specification. Optional PNG icons remain raster assets.

## Get started

Copy this whole repository folder into your agent's supported skills directory, then use:

```text
Use $paper-grounded-manuscript-diagram to draw my method.
Preserve its scientific meaning. Choose a compact, clean layout with rounded
shapes and connectors. Review relevant paper figures where useful.
Deliver SVG, PDF, 600-DPI PNG and source; inspect the actual print-size output.
```

Your agent must support skill loading and provide the necessary file, image and research tools. See [platform setup](references/platform-compatibility.md).

To try the local renderer with an existing Matplotlib/Pillow environment:

```sh
python scripts/render_diagram.py templates/parallel-study.json --output-dir diagram-output --stem method
```

Open `method-preview.png` and `method-print-size.png`. The renderer checks your explicit layout; it does not infer missing methods or automatically arrange every graph.

## Icons that fit the content

When useful, the agent compares title-inline, side or top positions, keeping labels readable and avoiding an empty icon column. Image generation is optional: available tools can create a matching set on white, then local preparation removes the exterior and checks the cutouts.

![Three compact workflow nodes with small icons beside their titles and full-width details](assets/readme/icon-workflow.png)

*The [icon example](templates/icon-workflow/diagram.json) uses locally authored artwork, not AI-generated assets. Generation and background-removal model inference depend on the host.*

## Go deeper

[Skill instructions](SKILL.md) · [Drawing contract](references/rendering.md) · [Density and whitespace](references/layout-density.md) · [Icon workflow](references/icon-workflow.md)

Keep unpublished materials local, use legally accessible sources and record the figures actually inspected. Automated checks support review; they do not certify scientific validity or journal acceptance.

## Contribute

Useful examples, layout bug reports, clearer conventions and focused fixes are welcome. Share a small public or synthetic case and before/after images. See [the contribution guide](CONTRIBUTING.md).

[MIT licence](LICENSE)

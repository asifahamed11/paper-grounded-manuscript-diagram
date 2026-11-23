# Paper-Grounded Manuscript Diagram

Create editable manuscript diagrams from a research method. Start with the stages and relationships, choose the intended print width, and review a measured layout before export.

This local workflow runs with Python and free libraries. The final files include SVG, PDF, PNG and a reproducible specification. Native draw.io and TIFF are available as options.

![A compact parallel research workflow with rounded shapes and two coordinated study lanes](assets/readme/research-workflow.png)

*An illustrative [parallel-study example](templates/parallel-study.json), rendered with the bundled local engine. This is a layout demonstration, not a research result.*

## Same prompt, two agent runs

[![Two workflows from the same prompt, made without the skill on the left and with the revised skill on the right.](assets/readme/same-prompt-comparison.png)](assets/readme/same-prompt-comparison.png)

Both panels used the same model and prompt. The left is the original baseline and the right was generated after updating the skill. Open the image for the full-size comparison. [Read the shared prompt](assets/readme/comparison-prompt.txt).

## Why use it?

- Start from stages and relationships or bring an existing layout.
- Link substantive stages and arrows to manuscript sections or other source locations.
- Check text size, contrast, ports, crossings and spacing at the intended print width.
- Edit the source in JSON, SVG or native draw.io. Use TIFF when the venue calls for it.

## Get started

Copy the `paper-grounded-manuscript-diagram` folder into your agent's skill directory and ask it to use the skill with your method. See the [platform setup guide](references/platform-compatibility.md).

```text
Use $paper-grounded-manuscript-diagram to draw my method.
Preserve its scientific meaning. Choose a compact, clean layout with rounded
shapes and connectors. Review relevant paper figures where useful.
Deliver SVG, PDF, 600-DPI PNG and source; inspect the actual print-size output.
```

Try the example locally in a Python environment. Install the optional libraries once if they are missing.

```sh
python -m pip install -r requirements-render.txt
python scripts/plan_diagram.py --doctor
python scripts/plan_diagram.py templates/review-selection-method.json --output-dir demo --drawio --require-sources
```

Open `demo/method-print-size.png` and `demo/method.drawio`. The example builds a screening workflow excerpt from a [public source](https://www.bmj.com/content/372/bmj.n71), and the QA receipt links nodes and arrows to specific source locations. [Input and figure walkthrough](references/method-to-figure.md).

![Study selection with a main path, explicit branches and the recorded exclusions beside it](assets/readme/review-selection.png)

## Icons that fit the content

Use an icon when it clarifies the stage. The planner compares title, side and top placement using the amount of wrapping and space each needs. The example uses locally drawn symbols.

![Three compact workflow nodes with small icons beside their titles and full-width details](assets/readme/icon-workflow.png)

See the [icon example and source](templates/icon-workflow/diagram.json).

## Go deeper

[Skill instructions](SKILL.md) · [Method and source fields](references/method-to-figure.md) · [Drawing contract](references/rendering.md) · [Icon workflow](references/icon-workflow.md)

Keep unpublished materials local, use legally accessible sources and record the figures actually inspected. Automated checks support review; they do not certify scientific validity or journal acceptance.

## Contribute

Useful examples, layout bug reports, clearer conventions and focused fixes are welcome. Share a small public or synthetic case and before/after images. See [the contribution guide](CONTRIBUTING.md).

[MIT licence](LICENSE)

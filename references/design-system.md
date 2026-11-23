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

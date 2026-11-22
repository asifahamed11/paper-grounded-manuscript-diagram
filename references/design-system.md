# Default Figure Design System

## 1. Palette

Use the Okabe-Ito palette by default unless the user or target journal specifies another palette.

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

### Palette rules

- Use two to four colors in most figures; use more only when categories require them.
- Keep text dark and high contrast.
- Avoid yellow text or thin yellow lines on white.
- Do not rely on color alone to distinguish categories.
- Use the same semantic color consistently across related panels.
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

- Use a consistent grid and equal gaps between comparable nodes.
- Align edges and centers deliberately.
- Keep enough whitespace around groups and between labels and connectors.
- Maintain consistent inner padding.
- Avoid crowding nodes against the canvas edge.
- Keep margins balanced.
- Do not let connectors pass through text or unrelated blocks.

## 5. Lines and arrows

- Use consistent connector thickness and arrowhead style.
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

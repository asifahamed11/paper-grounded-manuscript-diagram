---
name: paper-grounded-manuscript-diagram
description: Create or refine editable research diagrams from a manuscript, method, code, or existing figure. Covers scientific workflows, model and system architecture, conceptual diagrams, and multi-panel compositions. Use comparable published figures for design decisions when applicable. Route map and quantitative plot creation to their dedicated tools.
---

# Paper-Grounded Manuscript Diagram

Deliver an original, readable figure at its intended print size. The study's
manuscript, code, and data support the scientific content. Published figures
inform how to communicate that content. Keep unpublished material local and
send only public topic or bibliographic queries to external services.

## Decide what the figure must explain

- Determine the reader's question, what has to be visible to answer it, the
  target width, and the required output formats. Choose overview, mechanism
  detail, or both. Use more than one panel when separate views help the reader
  follow the study at the target size.
- Choose a recipe in [figure planning](references/figure-planning.md).
  Architecture, decision flow, association, and chronology use different
  relations. A multi-panel figure can combine several kinds of view.
- Record the important components and relationships with local manuscript or
  code locators before styling. A connection the reader must trace needs a
  drawn edge or an explicit handoff between panels. Keep supported operations,
  units, counts, and data roles intact. Ask about missing facts only when the
  answer materially affects the figure.

## Select and use comparable figures

- For a new complex figure or a requested deep design review, aim for at least
  five distinct, inspected published papers. Respect any source set or count
  specified by the user. For a focused drawing or a style revision, reuse
  supplied or previously inspected references when they answer the design
  question. Read the [paper protocol](references/paper-research-protocol.md).
- Search with public terms for the topic **and the relationship the figure
  needs to communicate**. Check the actual figure, caption, and surrounding
  text. Distinguish publication from preprint and report any access shortfall.
  Use candidate rankings for discovery and verify figure inspection against
  the opened paper.
- In the [review record](references/figure-analysis-template.md), connect each
  precedent's observation to a specific design decision and to the panel,
  nodes, or edges where it appears. Explain precedents you omit. Draw original
  artwork and use the user's method to resolve each relationship.

## Build and review the layout

- For layerable workflows, start with [the planner](references/method-to-figure.md).
  For closely coupled feature levels, nested system boundaries, conceptual
  networks, and mixed panels, choose an appropriate template and use the
  [explicit renderer](references/rendering.md) when the planner cannot produce
  the intended composition.
- When a layout is crowded or routing fails, keep the evidence-backed
  connections. Check the diagnostic and attempt JSON, then choose a different
  arrangement, draw explicit routes, or split the explanation into linked
  panels. For a dense diagram, compare the plausible alternatives at the same
  physical width before selecting one.
- Use [design conventions](references/diagram-conventions.md) and
  [print styling](references/design-system.md) for the chosen figure. Use
  shape, grouping, annotation, or line style when it conveys information.
  Keep illustrations and icons limited to those that help identify a real
  component. [Icon preparation](references/icon-workflow.md) is optional.

## Verify and deliver

- For a new figure with supplied study evidence, include `design_review` and
  run `--require-sources --require-design-review`. When an applicable
  minimum of inspected published examples is met, add
  `--require-paper-figures --min-paper-figures N`. If access falls short,
  preserve the real records, report the shortfall and use the applicable checks.
- Inspect the full render and the print-size view. Answer the reader checks
  using the drawing, then verify each important relationship against the
  study. Report scientific, paper-inspection, and geometry checks as separate
  results. See the [QA guide](references/quality-assurance.md).
- Deliver the editable source and the formats the user or venue requires.
  The local tools produce SVG, PDF and PNG, with optional Draw.io, EPS or TIFF.
  Check any separately requested editable export in its intended viewer if
  available. See the [output guide](references/output-specification.md).

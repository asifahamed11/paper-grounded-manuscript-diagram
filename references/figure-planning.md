# Plan the figure at its intended size

Choose the main question a reader should be able to answer from the visual.
Decide whether the figure explains an overview, a mechanism in detail, or both.
Set the physical width and the smallest readable text before placing groups.
Mark the actual study stages and relationships with manuscript, code, or data
locators. Capture unresolved details separately and avoid filling them in from
a published precedent.

## Choose the figure's visual structure

| Purpose | What the reader must be able to trace | Starting point |
| --- | --- | --- |
| Model architecture | Modalities and tensor roles, parameter sharing, levels, merges, skip paths, output and training/inference where relevant | [Separated training and evaluation](../templates/ml-architecture.json), [multiscale overview and detail](../templates/multiscale-architecture.json) |
| System architecture | Components, boundary crossings, external dependencies, and the difference between control, data and feedback | Group components by responsibility and mark edge roles |
| Study workflow | Inputs, sequence, branch and merge, feedback, and evaluation isolation | [Parallel study](../templates/parallel-study.json) or [linear workflow](../templates/linear-workflow.json) |
| Flowchart or PRISMA | Criteria and both decision exits; screening units and any counts supported by the protocol | [Decision workflow](../templates/decision-workflow.json), [selection example](../templates/review-selection-method.json) |
| Conceptual framework | Constructs, association versus directional claims, and any uncertainty or moderation the study supports | [Explicit association layout](../templates/conceptual-framework.json) |
| Taxonomy | Parent–child membership and cross-classification if reported | Group or tree with hierarchy labels |
| Timeline | Time order, overlapping intervals, units and the meaning of spacing | Time axis for measured spacing; mark an ordered schematic when spacing is illustrative |
| Graphical abstract | A single supported takeaway and enough evidence to interpret it | Choose one main visual narrative and verify any venue format requirements |
| Multi-panel composition | A question for each panel, reading order, consistent units and shared references between related panels | [Panel groups](../templates/multi-panel-method.json). Compose existing map or plot assets where appropriate |

The planner builds a ranked directed graph. Use an explicit layout when an
undirected or spatial structure would acquire an unintended reading order in
ranks. For a hybrid figure, select the appropriate visual grammar per panel.
An overview can refer to a detail panel by a repeated named component, scale or
tensor. Make that correspondence visible and check its sources.

## Compare and refine a dense layout

1. Try the simplest arrangement that retains the reader checks. Keep importance
   visible through group hierarchy, shape and connections as well as color.
2. When the main panel is crowded, compare a compact overview with an overview
   plus detail using the same target width and text minimum. Choose the draft
   that communicates more of the supported relationships without clipping.
3. Inspect the planner's geometry report and failed route if available. A
   reroute, different arrangement, or explicit panel handoff preserves the
   design intent. A real crossing may use the renderer's documented crossing
   exception only when the reader can still distinguish the paths.
4. Reserve dedicated figures or another plotting/GIS tool for panels whose
   native form needs a quantitative axis, geographic projection, or scientific
   image processing.

## Store the reader and precedent checks

Use the [method specification](method-to-figure.md) and the
[figure review template](figure-analysis-template.md). A check should describe
a task a reader can perform from the rendered figure. For a relationship, name
an edge or edges that make the path visible. Record whether a source convention
is adopted and where, or why it was left out. Paper artwork and scientific
claims from prior studies do not supply facts about the user's implementation.

### Synthetic method for the multiscale template

Two epoch inputs use one encoder with shared weights. It returns four paired
feature levels. At each level the diagram receives the pair and computes an
element-wise absolute difference. In the detail panel the deepest difference
seeds decoding. Each following decoder level receives the preceding stage and
the corresponding shallower difference. The final stage produces change logits.
These invented-for-testing stages establish the geometry example and contain
no measured performance, dataset or parameter claims.

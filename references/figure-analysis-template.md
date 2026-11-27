# Figure Analysis Template

Use one record per figure actually inspected. Follow the
[paper protocol](paper-research-protocol.md) for the applicable scope.
After reading the caption and nearby text, record the visible convention and
how it applies to the user's figure.

## Paper identity

- **Paper title:**
- **Authors:**
- **Year:**
- **Venue:**
- **DOI / stable URL:**
- **PDF obtained from:**
- **Full text actually inspected:** Yes / No
- **Citation count source and check date:**

## Figure identity

- **Figure number:**
- **Caption:**
- **Pages:**
- **Why this figure is relevant to the user's request:**

## Scientific structure

- Main purpose:
- Main components:
- Sequence or relationship:
- Inputs and outputs:
- Grouping / hierarchy:
- Domain-specific notation:
- Important labels or abbreviations:

## Visual design observations

- Layout topology & reading direction:
- Grouping & containers:
- Domain symbols and their role in this figure:
- Information density:
- Typography & approximate hierarchy:
- Color roles:
- Arrow & connector styling:
- Line weights:
- Spacing and alignment:
- Legend / annotations:
- Density and readability:

## Shape inventory

Record one row per distinct form and role. Add rows as needed and group repeats.
Use the caption, nearby text and legend to confirm what each form represents.

| Observation ID | Visible form | Role in the source figure | Exact panel or location |
| --- | --- | --- | --- |
| | | | |

## Strengths to adopt & takeaways

List general domain conventions or communication patterns that can inform the new figure (do not copy any source artwork), and summarize one crisp insight for `spec["sources"][i]["takeaway"]`:

1.
2.
3.
- **Recorded `takeaway` (for `spec["sources"]`):**

## What to avoid

- Clutter or ambiguity:
- Poor contrast or tiny text:
- Unclear arrows:
- Nonstandard symbols:
- Other weaknesses:

## How this informs the new original figure

Explain which general conventions will be adopted, which will be changed, and why. The new diagram must represent the user's own research and must not be a trace or close replica of the source figure.

## Transfer to the figure specification

- In `sources`, store `kind: "figure"`, the figure locator, a DOI or stable URL,
  and the specific takeaway. Add `inspection.location` and
  `inspection.publication` (`published`, `preprint`, or `unverified`).
- In `design_review.precedents`, record the source ID, observation, decision,
  and final element IDs (e.g. `edges:scale-to-decoder`). For an omitted
  convention, use `omission_reason`. Store the inventory as `shapes` on the
  same record. Each item has `id`, `form`, `role`, and `location`.
- In `design_review.shape_choices`, name the target nodes, chosen shape,
  evidence-backed reason, and any inventory references in `from_shapes`.
  Use the [shape workflow](scientific-shapes.md) to compare and select forms.
- In `design_review.checks`, map the intended reader checks to study-backed
  elements. Inspect the render to verify that each mapping is visible.

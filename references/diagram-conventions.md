# Scientific Diagram Conventions

Choose conventions according to the diagram's purpose. Do not force a diagram into a flowchart if it is actually a conceptual model, map, or quantitative plot.

## 1. Flowcharts

- Use a consistent top-to-bottom or left-to-right reading direction.
- Use terminators for start/end where appropriate.
- Use process rectangles (rounded by default).
- Keep all supported shape corners softly rounded, including input and decision outlines; keep the data/decision semantics recognisable. Use curved connector bends with consistent caps and line widths.
- Use decision diamonds for actual branching decisions.
- Use input/output parallelograms when that distinction helps.
- Label decision branches clearly, such as Yes/No or condition names.
- Use arrowheads consistently and connect lines to intended nodes.
- Minimize crossing connectors; use line jumps or routing only when necessary.
- Do not use a diamond for an ordinary processing step.
- Keep node labels short and action-oriented.

## 2. Methodology and experimental workflow

A common structure is:

1. research input or data source;
2. data collection or acquisition;
3. preprocessing / quality control;
4. method, model, or intervention;
5. evaluation / validation;
6. outputs or findings.

This is only a planning pattern. Include only stages that the user's research actually performs. Show feedback loops only if the method genuinely includes iteration. Separate training, validation, and test data when relevant. Make leakage prevention visible when it is central to the method.

## 3. Machine-learning and AI pipelines

- Distinguish raw data, preprocessing, feature construction, model components, training, inference, and evaluation.
- Label datasets and splits precisely.
- Show model inputs and outputs with correct names and dimensions when important.
- Distinguish retrieval, reranking, generation, and verification in RAG systems if those stages actually exist.
- Show baselines and ablation branches only when they were part of the study.
- Do not imply causal or sequential relationships that the implementation does not have.
- Keep evaluation metrics grouped and label them accurately.

## 4. System architecture diagrams

- Separate components by responsibility or layer.
- Label data/control flows.
- Use a legend for line styles if multiple relationship types exist.
- Distinguish external services from the system under study.
- Show trust boundaries or network boundaries when relevant.
- Avoid decorative icons that make the architecture harder to read.
- Do not add technologies that the user's implementation does not use.

## 5. Conceptual frameworks

- Establish a clear hierarchy: central construct, dimensions, factors, outcomes, or hypotheses.
- Use arrows only when they indicate a defined relationship.
- Distinguish association, influence, mediation, moderation, and causation. Do not use a causal arrow for a mere correlation.
- Use an arrowless association line when direction is not supported; the local renderer supports `arrow: "none"`. Show a legend for dashed associations.
- Label relationship types when the line alone is ambiguous.
- Keep the framework balanced and avoid excessive cross-links.

## 6. Graphical abstracts

- Communicate one main takeaway at a glance.
- Prefer a small number of visual stages and short labels.
- Use a clear visual narrative and generous whitespace.
- Avoid turning the graphical abstract into a miniature full paper.
- Follow the target journal's exact graphical-abstract dimensions and restrictions.

## 7. Study-area maps

A map must be based on verifiable geographic information. Do not invent a study location, boundary, coordinates, administrative divisions, rivers, roads, or sampling sites.

Use the following elements when appropriate:
- locator inset showing country/region context;
- study-area boundary or highlighted region;
- scale bar;
- north arrow, if orientation is meaningful and not obvious;
- coordinate graticule or coordinate labels when useful;
- legend for mapped features;
- CRS/projection information;
- data source and map date;
- clear labels and a restrained basemap.

Check:
- coordinate reference system and units;
- geographic extent and scale;
- geometry validity;
- source and license of boundary data;
- whether the map projection is appropriate;
- whether labels and symbols remain readable at print size.

Ask the user for coordinates, a shapefile, GeoJSON, geocoded points, or an unambiguous study-area description if necessary. If the map requires precise study boundaries, do not substitute a generic map screenshot.

## 8. Quantitative plots

A chart based on numerical results is not a schematic diagram. Use the real data, correct statistical encoding, suitable axes, units, uncertainty intervals, sample sizes, and captions. Do not invent datapoints or smooth a series in a misleading way. Use a charting workflow rather than a decorative diagram.

## 9. Captions and labels

- Define abbreviations at first use or in the caption.
- Use consistent terminology with the manuscript.
- Include units where quantities appear.
- Avoid sentence-length text inside nodes.
- Ensure figure labels match the manuscript and code.
- Add a concise caption that explains the figure without repeating the entire methods section.

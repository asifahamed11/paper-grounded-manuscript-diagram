# Final Quality Assurance Protocol

A figure is complete only after both scientific and visual checks have been performed.

## 1. Scientific correctness

- [ ] Figure purpose matches the user's request.
- [ ] Figure content matches the manuscript, code, data, and experiment records.
- [ ] Every process block is real and correctly named.
- [ ] Every arrow or relationship is logically correct.
- [ ] Inputs and outputs are not reversed.
- [ ] Dataset names, split names, model names, parameters, metrics, and units are exact.
- [ ] No unreported model, dataset, result, or experimental stage was added.
- [ ] The figure does not imply causation when only association is supported.
- [ ] Map location, boundary, CRS, coordinates, and mapped features are verified.
- [ ] Abbreviations and terminology match the manuscript.

## 2. Visual quality

- [ ] One clear reading path or hierarchy is visible.
- [ ] Text is readable at intended final size.
- [ ] No text is clipped, overlapped, or hidden.
- [ ] Nodes are aligned and spacing is consistent.
- [ ] Connectors reach the correct nodes.
- [ ] Arrowheads are visible and consistent.
- [ ] No avoidable connector crossings.
- [ ] Colors have adequate contrast.
- [ ] Meaning is not encoded by color alone.
- [ ] Legend, scale bar, north arrow, and notes are present where required.
- [ ] Figure is balanced and not unnecessarily dense.
- [ ] Figure is understandable without relying on surrounding paragraphs.

## 3. Export checks

- [ ] SVG/PDF/PNG opens successfully.
- [ ] Canvas size and aspect ratio are correct.
- [ ] No unexpected blank page or clipping.
- [ ] Fonts and special characters render correctly.
- [ ] Raster resolution meets the target journal's instructions.
- [ ] Editable source is saved.
- [ ] Final render has been visually inspected.

## 4. Literature-grounding checks

- [ ] Paper titles and metadata are verified.
- [ ] DOI or stable URLs are provided when available.
- [ ] Citation count source and date are stated.
- [ ] Downloaded full texts are distinguished from metadata-only records.
- [ ] Figure-inspected status is truthful.
- [ ] At least five full texts were inspected, or the limitation is explicitly reported.
- [ ] The new figure is not a copy or trace of a published figure.

## 5. Iteration rule

If any material check fails:
1. identify the specific defect;
2. revise the source;
3. re-export;
4. inspect the new render;
5. repeat until all critical issues pass or explain the remaining limitation.

Do not mark a check as passed merely because a script ran without an error. Script checks are only partial automation.

# Output Specification

Deliver as much of this package as the current host can genuinely create.

## 1. Figure files

Preferred:
- `figure-01.svg` — editable vector source;
- `figure-01.pdf` — publication-oriented vector export;
- `figure-01.png` — high-resolution preview or submission file.

If another format is more editable for the user, include it:
- `.drawio`
- `.mmd` / `.mermaid`
- `.dot`
- `.pptx`
- source project from the selected editor.

Do not claim a file is editable unless the format and contents support editing.

Use the native draw.io option for editable connections, and lossless TIFF when required by the venue. Keep the original JSON and inspect the native layout before sharing it. Include the current QA receipt and method source locators with the author's local editable package.

With optional raster icons, SVG/PDF text and shapes remain vector while embedded icons are bitmap assets. Include the prepared icons, portable source paths and [asset provenance](icon-workflow.md). Do not call the entire figure wholly vector or claim that a generated PNG became an editable vector symbol.

## 2. Research evidence

Provide a reference table with:

| Field | Description |
|---|---|
| Paper | Verified title |
| Authors/year | Bibliographic identity |
| DOI/URL | Stable identifier or landing page |
| Citation data | Count, source, and check date when available |
| Access status | PDF downloaded, OA full text, metadata only, or abstract only |
| Figure inspected | Yes/No, with figure number if known |
| Relevance | Why it informed the requested figure |

## 3. Design rationale

Briefly state:
- why the selected diagram type and layout fit the research;
- which scientific conventions were used;
- how the default palette and shapes were applied or adapted;
- what was deliberately omitted to preserve clarity.

## 4. QA report

Summarize:
- scientific checks;
- visual checks;
- export checks;
- number of full-text papers actually downloaded and inspected;
- any unresolved issue or unavailable capability.

## 5. Naming

Use simple, stable filenames:
- `figure-01-methodology.svg`
- `figure-01-methodology.pdf`
- `figure-01-methodology.png`
- `figure-01-source.mmd`
- `figure-01-qa.md`
- `reference-papers.csv`

Avoid filenames that claim "perfect", "100-percent", or "journal-approved".

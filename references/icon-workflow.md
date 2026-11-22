# Optional icons grounded in the figure's meaning

Use this mode when icons make an actual research entity or activity easier to recognise at the intended print size. Decoration alone is a weak reason. A clear icon-free diagram remains a valid outcome.

## Decide before generating

Inspect the relevant paper figures, not just their abstracts. If the task requests five or six papers, review that many where legally accessible and disclose shortfalls; an example count is not a new universal minimum. Record paper/figure/page, what the icon communicates, and which choice it informs. Do not copy a paper's artwork or assume its objects, devices, methods or participants exist in the supplied study.

Make a small asset plan: unique semantic ID, meaning, destination nodes, final size, palette, visual style and evidence/rationale. Reuse one asset for repeated identical meanings. Generate exactly the distinct assets needed; do not generate a decorative sheet of unrelated symbols. A manuscript about weather might need a weather-record symbol; it does not automatically need a mosquito, patient, map or laboratory icon. The same principle applies to engineering, education, ecology and other fields.

Check the host's available tools and permissions. Prefer its native image-generation capability when generation is authorised. This workflow does not imply permission for paid APIs, new accounts, model installs or private uploads. Send a minimal generic icon description; keep unpublished text, figures, data and proprietary device details local. If generation is unavailable, use an existing permitted asset, a simple locally authored vector symbol, or omit icons, and report the choice. Do not pretend that a fixture or local vector was AI-generated.

## Generate a coherent set

One unique icon per file/call is the reliable default. Use a common art direction across all calls, and a supplied style reference when the host supports it. Do not rely on a multi-icon collage that later requires guessed cuts.

Reusable prompt structure (replace fields from the asset plan):

> Create one professional, clean scientific diagram icon representing [entity/activity], for [generic context]. Flat vector-like artwork with rounded stroke ends and joins, restrained detail, consistent [stroke/filled style], front-facing or [chosen perspective]. Use only [exact foreground palette hex values] and [outline colour]. Centred on a uniform pure white #FFFFFF background with generous empty margin on every side. No text, letters, numbers, logo, watermark, border tile, gradient, texture, glow, drop shadow, 3D rendering or additional objects. The silhouette must remain recognisable at [final size] points. Preserve [scientifically necessary feature]. Match [set's style reference] if provided.

Generate on white as requested. If the host returns genuine transparency, keep the alpha rather than flattening it and removing it again. Inspect each raw icon: correct meaning, no invented anatomy/equipment detail, exact family/perspective, consistent stroke/visual weight, useful detail at print size. Reject confusing or cluttered assets. Use a bounded targeted revision when needed; do not keep spending on cosmetic retries indefinitely.

## Remove white without destroying white details

Keep originals. Never globally delete every white pixel: white interiors can belong to the subject. No automatic method guarantees a perfect cutout for every icon.

The bundled `scripts/prepare_icon.py` uses Pillow only and never downloads anything:

```sh
python scripts/prepare_icon.py raw/weather.png --output assets/weather.png
```

`auto` preserves existing transparency; otherwise it removes **border-connected** near-white exterior (default tolerance 8/255), trims by the alpha bounds and adds eight transparent pixels of margin. A nonuniform border, clipped foreground, blank result or opaque output fails. White enclosed details remain. Enclosed background holes and antialias halos may need a mask, a targeted regeneration, or vector replacement; do not silently raise tolerance until pale features vanish.

For an actually single-colour glyph composited on white, declare its exact foreground colour to recover antialiased alpha and remove white edge contamination analytically:

```sh
python scripts/prepare_icon.py raw/weather.png --output assets/weather.png --foreground '#0072B2'
```

This mode treats white holes as transparent. It rejects inconsistent multi-colour pixels and is inappropriate for white-filled objects. For a reviewed segmentation matte, supply a local grayscale mask (white = keep; black = remove; gray = partial alpha), with the same oriented dimensions:

```sh
python scripts/prepare_icon.py raw/icon.png --mask work/icon-mask.png --output assets/icon.png
```

An RGBA mask uses its alpha channel. `--unmatte-white` additionally removes white colour contamination using that mask; use it only when the source really was composited on white. Native alpha is preserved without this flag. The helper never upscales the asset or stretches its proportions. It writes the cutout PNG, a white/dark/checkerboard preview and a JSON record with input/output hashes and the actual operation.

### GitHub tools for harder cutouts

Official sources inspected 2026-11-23; re-check the installed version and exact checkpoint before use:

| Option | Useful role | Selection constraint |
|---|---|---|
| [rembg](https://github.com/danielgatis/rembg) | Local model inference and mask/edge workflows for more complex artwork | MIT software; checkpoint licences differ. Current upstream also includes cloud backends and a BRIA default: explicitly select an allowed **local** model, rather than calling an unspecified default. Session reuse helps a batch. Review first-run weight download, size, checksum and licence; never hide it inside diagram rendering. |
| [BiRefNet official implementation](https://github.com/ZhengPeng7/BiRefNet) | A candidate when fine foreground boundaries defeat simple exterior removal | More inference/dependency work; inspect the exact official weights, terms and hardware needs. Natural-image benchmarks do not prove superiority for small scientific icons. No automatic `trust_remote_code` execution. |
| [BRIA RMBG-2.0 model card](https://huggingface.co/briaai/RMBG-2.0) | An alternative only when the intended use is permitted | Its model terms and gated access differ from rembg's software licence; do not assume unrestricted commercial use. |

These are candidate tools, not a benchmark ranking. Compare the actual icon on white, dark and checkerboard backgrounds before accepting a mask. Do not upload private assets to a hosted removal service by default. No model-specific wrapper is bundled: the deterministic helper accepts a reviewed local matte from any suitable tool, avoiding version-dependent downloads or licensing surprises.

## Place and verify

Use transparent PNG assets, or retain a native vector original when available. Crop only exterior empty space; keep all meaningful strokes, soft alpha and a small safety margin. Match **optical** size and visual weight across the set; equal file dimensions alone do not do that. Keep icon colours consistent with lane/role colours and do not use colour alone to carry meaning. Labels remain authoritative; an icon must not replace a required methodological label.

### Find the position, not a compulsory icon column

Start with the readable icon-free layout. Do not widen every node or reserve a tall left strip simply because an icon exists. Consider:

| Candidate | Works well when | Watch for |
|---|---|---|
| Beside the title | A small recognisable symbol and short title can form one compact row | Long titles or tall symbols may need a side position. Details should retain the full width. |
| Left or right of the content stack | The icon is portrait-shaped, the title is long, or several text lines share one symbol | A wide empty strip, extra line wrapping or inconsistent optical alignment. |
| Above the text | The symbol is an important visual anchor and the node has a deliberate vertical composition | Unnecessary height and a sparse poster-like tile. |
| No icon | The symbol adds little or every candidate weakens the method diagram | Do not add decoration to fill a numerical target. Honour an explicit user requirement for icons by reflowing instead. |

If the position is uncertain or the icon reduces useful fill, render two or three plausible candidates with the same labels, font sizes and icon family. Discard clipping, overlap or minimum-font failures. Compare extra wraps, required box/canvas growth, unused icon-strip space and optical balance at print size. Prefer the compact readable candidate, not the one with the largest icon or a colour-filled box. Use consistent placement for comparable nodes unless their content justifies a difference. Save a short candidate/choice note with the QA files. The agent makes this design choice; the renderer checks a chosen layout and does not claim a universal aesthetic optimiser.

The bundled renderer accepts an optional top-level `icons` list:

```json
"icons": [
  {"id":"records-symbol", "path":"assets/records.png", "node":"records",
   "placement":"title", "size_pt":[18,18], "gap_pt":4, "alt":"Stored records"}
]
```

Paths are relative to the JSON specification directory and must stay inside it. `placement: "title"` measures and centres an icon/title cluster, with full-width detail underneath; it requires `size_pt` instead of a fixed `box`, one attached icon for that node and stacked text. It does not reserve an empty column across the detail lines. For `left`, `right` or `top`, give an explicit `box` and `icon_space_pt` on the node to reserve the corresponding strip. Old in-node records without a placement retain left-strip behaviour. Standalone fixed icons omit `node` and retain an explicit box. The renderer fits without stretching, checks native resolution (at least 300 DPI at final placement), node/label/connector collisions, and embeds the PNG in SVG/PDF. It records resolved positions and the selected mode in QA. See [rendering](rendering.md) for the full contract. Its vector exports contain **raster icons**, not magically vectorised artwork. A venue demanding wholly vector artwork needs native vector symbols instead.

Inspect raw image, prepared cutout, a coloured-node composite, full figure and actual print-size figure. Check halos, white rectangles, jagged edges, missing interior features, unintended detached marks, recognisability and palette/weight consistency. A successful mask/geometry check does not prove semantic correctness or visual quality.

Deliver the figure, prepared assets, reproducible source and an asset ledger: semantic ID, prompt or local source, generator/model when known, source terms when relevant, output hashes, background operation and actual visual review. Note any required AI-use disclosure for the target venue. State separately what was generated, locally authored, model-processed, automatically checked and visually inspected.

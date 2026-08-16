# PuppyBench mini-site / slide deck

**One file, zero dependencies.** `index.html` is fully self-contained (fonts embedded,
all CSS and SVG inline, no network requests). Open it in any browser, from any folder,
offline. 152KB.

## What it is

The graphical About for PuppyBench: the question, the founding case, the instrument
(with architecture diagrams), the design and governance pipeline, the model matrix,
the deontic frame, results slots, and The Real Cat AI Labs / digital-literacy context.
IMRAD-shaped, written for a scientifically literate reader who has never seen the repo.

## Turning it into the submission deck

Each section is print-formatted as one landscape page:

1. Open `index.html` in Chrome or Edge
2. Ctrl+P → Destination: Save as PDF → Layout: **Landscape**
3. Margins: Default · Background graphics: **ON** (the ink slides need it)
4. Save. Each section is one slide; import the PDF into PowerPoint/Slides if a
   .pptx is required (PowerPoint: Insert → Screenshot/pictures from PDF pages, or
   any PDF-to-PPTX converter — the pages are already 11×8.5 slide geometry).

## Editing

Results slots in the Results section (`#results`) are honestly empty until collection
completes; fill them from `analysis/` rendered figures + their manifests only.
Numbers in the hero chips came from the authorized cell manifest at build time —
re-check against the frozen manifest before submission.

Style system: TW-derived (Archivo display / Inter body, ink + paper + lime marker,
solid blocks). Diagram accent pair fox `#ea580c` / teal `#0d9488` — validated
colorblind-safe against the paper surface (dataviz skill six-checks, 15AUG2026).
Every diagram element is direct-labeled; color never carries meaning alone.

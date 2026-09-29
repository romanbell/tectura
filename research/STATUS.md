# Research status — COMPLETE (2026-09-11)

All 13 batches researched and merged: 127 architects, 1,270 project entries.
Build: `python3 tools/build.py` — merges research/batch-*.json (applying
research/title-overrides.json), resolves images via Wikipedia pageimages →
media-list fallback → search rescue (logo/map/junk filenames rejected),
downloads to assets/img/, regenerates js/data.js.

Image coverage: 108 portraits, 646 project images (the rest render as
placeholders — no free/correct image exists on Wikipedia for them).
Quality: two full multi-agent visual QA passes over every downloaded image;
~90 wrong images (logos, maps, wrong buildings, misattributed portraits)
were removed or corrected via title-overrides.json.

Links: all 93 studio/foundation links curl-checked; richardmeier.com →
meierpartners.com, rsh-p.com → rshp.com, mk27.com confirmed. Null links are
deliberate (Zumthor, Siza, Souto de Moura etc. have no websites).

Fact updates caught during research: Frank Gehry died 2025-12-05;
Marina Tabassum born 1969; Escobedo's Met wing opening 2030.

## Next-phase ideas (not started)
- Higher-quality image curation for the ~624 placeholder projects
  (Flickr/Commons deep search, or licensed sources)
- Image credits page (sources are in each entry's wikiUrl fields)
- Styles/movement cross-linking or filtering

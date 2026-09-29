# TECTURA research brief

You are researching architects for TECTURA, a black-and-white editorial web index
(project root: /Users/romanbellisari/Documents/gsd/fun/tectura). Your job: produce
one JSON file covering the architects assigned to you, at the exact path given in
your task prompt.

## Output schema

The file is a JSON array. One object per architect, in the order assigned:

```json
{
  "id": "given-id",
  "name": "Display Name",
  "born": 1887,
  "died": 1965,
  "yearsLabel": "b. 1950 / 1952",
  "country": "Country / Country",
  "link": "https://official-site.example",
  "linkLabel": "Short label",
  "firm": "Firm or studio name",
  "styles": ["Movement", "Movement"],
  "wikipedia": "Exact English Wikipedia article title for the architect",
  "bio": "4–6 sentence editorial paragraph.",
  "projects": [
    {
      "title": "Project Name",
      "year": "1959",
      "location": "City, CC",
      "blurb": "1–2 sentence editorial description.",
      "wikipedia": "Exact English Wikipedia article title for the building, or null"
    }
  ]
}
```

Field rules:
- `died`: null if living. `yearsLabel`: ONLY for partnerships/collectives where a
  single born–died string misleads (e.g. "1925–2018 / 1931–", "b. 1950", "est. 2010");
  omit the key otherwise. For collectives with an "est." label still set `born` to the
  founding year (used for chronological sort) and `died` to null.
- `link`: the official studio / foundation / archive / estate website. Verify with
  ONE WebSearch per architect where you are unsure; do not WebFetch every site.
  If the architect famously has no website, or you cannot confirm one, use null
  (the site renders a — dash; that is a feature, not a failure). A separate build
  step curl-checks every link afterward, so flag guesses in your reply rather than
  burning tool calls.
- `linkLabel`: 1–2 words, how the office is actually called: "OMA", "Fondation",
  "ZHA", "Studio". null when link is null.
- `country`: origin / main country of practice, slash-separated when they differ.
- `projects`: EXACTLY 10, their most significant built works (unbuilt/theoretical
  allowed only when it is genuinely among their most influential output, e.g.
  Archigram). Order by significance, not date.
- `wikipedia` (both levels): the exact English Wikipedia article title from your
  knowledge. Do NOT fetch every title to verify it — a downstream build step
  resolves all titles through the Wikipedia API (redirects included) and reports
  misses, so a good-faith title is enough. Be careful only with generically-named
  works ("Water Temple", "Church on the Water") where the plain title may point
  elsewhere — qualify those the way Wikipedia does. When choosing between two works
  of roughly equal significance, prefer the one likely to have an article; never
  include a minor work just because it has one. Use null when no article exists.

## Facts

Rely on your knowledge for well-established facts. Use WebSearch only for the
things that can genuinely have changed or that you are unsure of — above all,
whether older "living" architects have died through 2026 (one batched search like
"<name> death" per uncertain architect is enough). Do not guess, but also do not
re-verify textbook facts.

## Tool discipline

Keep total web tool calls modest (roughly 10–20 for your whole batch). If a web
tool call errors or hangs twice in a row, STOP using that tool and finish the job
from knowledge, noting what went unverified in your reply. Delivering the file is
the priority; a missing verification is fixable later, an unwritten file is not.
Write the JSON file EARLY and incrementally if that helps — the file on disk is
the deliverable.

## Tone

Read the featured entries in js/data.js first (le-corbusier, zaha-hadid, louis-kahn,
peter-zumthor) — match that voice: editorial, precise, specific, a little wry, zero
marketing fluff, no "iconic"/"stunning"/"masterpiece" filler. Bios are 4–6 sentences
with real biographical texture (facts, dates, turning points, one memorable detail).
Blurbs are 1–2 sentences that say what the thing IS and why it matters.

Never use em-dash-free listicle prose; never use superlatives without content.
No all-caps anywhere.

## Existing entries

Some architects assigned to you may already have full entries in js/data.js
(bio + 10 projects). For those: keep the existing project selection and blurbs
(light edits allowed), keep or lightly improve the bio, verify the facts and link,
and ADD the wikipedia titles. Do not discard good existing copy.

## Delivery

Write the JSON file (valid JSON, UTF-8, no trailing commas), then reply with ONE
short paragraph: confirmation + list of any projects/architects where wikipedia is
null or the link could not be verified. Do not paste the JSON into your reply.

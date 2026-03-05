---
name: vc-essay-archive
description: Build and maintain a local, token-efficient archive of Paul Graham and Fred Wilson essays/posts. Use when collecting essay text, refreshing indexes, compiling selected essays into markdown bundles, or answering questions grounded in these writings.
---

# VC Essay Archive

Maintain a **lean prompt footprint** while keeping full essay text available on disk.

## Workflow

1. Refresh indexes (do not load full essay text into context):
   - `python scripts/fetch_paul_graham_index.py`
   - `python scripts/fetch_fred_wilson_index.py --max-pages 120`
2. Fetch full text only for needed essays:
   - `python scripts/fetch_essay_text.py --url <essay-url> --author <paul|fred>`
3. Build a bundle for specific needs:
   - `python scripts/build_bundle.py --author paul --limit 20 --out references/paul_bundle.md`
   - `python scripts/build_bundle.py --author fred --limit 20 --out references/fred_bundle.md`

## Efficiency rules

- Keep `SKILL.md` small; never paste massive corpora here.
- Keep essay bodies in `cache/` and generated bundles in `references/`.
- Read only targeted files needed for the user’s current request.
- Prefer smaller themed bundles over one giant file.

## Archive layout

- `references/paul_graham_index.md` — title/url index
- `references/fred_wilson_index.md` — title/url/date index
- `cache/paul/*.md` — full text per essay
- `cache/fred/*.md` — full text per post

If data is missing or blocked by a site, state that explicitly and continue with available sources.

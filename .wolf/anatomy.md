# Project Anatomy

## Layout Templates (created 2026-05-17)
- `layouts/index.html` — Homepage with category grid (27 category cards) + recent articles section
- `layouts/_default/single.html` — Article detail with TOC, tags, breadcrumbs, related articles
- `layouts/_default/list.html` — Category/tag term listing with 20/page pagination, breadcrumbs
- `layouts/_default/terms.html` — Tag cloud page with font-size based on article count
- `layouts/categories/terms.html` — Category listing with hardcoded descriptions
- `layouts/partials/nav.html` — Standalone nav component (not actively used, PaperMod handles nav)
- `layouts/partials/related.html` — Related articles partial (same category, up to 5 items)

## Configuration
- `hugo.toml` — Updated: paginate=20, added 首页 menu item

## Existing Data
- `content/website/*.md` — 1783 articles in 14 categories, 4452 total pages after build

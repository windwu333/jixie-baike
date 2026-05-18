#!/usr/bin/env python3
"""EngineersEdge scraper — batch-collect engineering reference pages.

Source ID: "engineers-edge"
Target: 100-500 pages from key engineering sections.
"""

import logging, re, sys, time, traceback, urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scrapers.framework import cached_get, extract_links, save_raw, session, sanitize

log = logging.getLogger("engineers-edge")

BASE = "https://www.engineersedge.com"

# ── curated topic menu pages (sitemaps) ──────────────────────────────
TOPIC_MENUS: dict[str, list[str]] = {
    "materials": [
        "/manufacturing_menu.shtml",
        "/properties_of_metals.htm",
        "/heat_treat.htm",
        "/tool_steel.htm",
    ],
    "strength-of-materials": [
        "/mechanics_material_menu.shtml",
        "/beam_calc_menu.shtml",
        "/section_properties_menu.shtml",
        "/structural_shapes_menu.shtml",
        "/friction_menu.shtml",
    ],
    "fasteners-hardware": [
        "/fastener_thread_menu.shtml",
        "/ansi_hardware_menu.shtml",
        "/iso_hardware_menu.shtml",
    ],
    "bearings": [
        "/bearing_menu.shtml",
    ],
    "gears": [
        "/gear_menu.shtml",
    ],
    "gdt-drafting": [
        "/gdt.htm",
        "/drafting/",
    ],
    "engineering-analysis": [
        "/engineering-analysis.htm",
        "/dfm-dfma.htm",
    ],
    "civil-engineering": [
        "/civil_engineering/civil_engineering_menu.shtml",
    ],
}

# Path prefixes that are EXCLUDED (auth, store, forum, non-content pages)
EXCLUDE_PREFIXES = (
    "/secure/", "/engineerstore/", "/engineering-forum/", "/membership",
    "/feedback", "/advertise", "/privacy", "/contact", "/disclaimer",
    "/imager2", "/pop_up_window",
)

# Root-level .htm pages that are navigation hubs, not articles
ROOT_NAV_PAGES = {
    "/engineering-basics.htm", "/calculators.htm", "/applications-design.htm",
    "/engineering-analysis.htm", "/feedback.htm", "/definitions.htm",
    "/design_data.shtml", "/gauge.htm", "/drill_sizes.htm",
    "/pipe_schedules.htm", "/screw_threads_chart.htm", "/nail_size_chart.htm",
    "/lumber.htm", "/commercial_lumber_sizes.htm",
    "/construction-span-tables.htm", "/beam_calc_menu.shtml",
    "/beam-deflection-menu.htm", "/flat_plates_equations_calculators.htm",
    "/section_properties_menu.shtml", "/structural_shapes_menu.shtml",
    "/friction_menu.shtml", "/fluid_flow/fluid_flow_table_content.htm",
    "/heat_transfer/heat_transfer_table_content.htm",
    "/manufacturing_design.shtml", "/bearing_application.htm",
    "/hardware/", "/GDT_Training.htm", "/gdt.htm",
    "/dfm-dfma.htm", "/heat_treat.htm", "/heat_treat2.htm",
    "/tool_steel.htm", "/steel_terms.htm", "/properties_of_metals.htm",
    "/aluminum_tempers.htm", "/basic_conversions.htm",
    "/material_manufacturing.htm", "/engineering/",
    "/technology_news/", "/video/",
    "/excel_calculators/index.htm", "/advertise.htm",
    "/contact.htm", "/privacy.htm", "/disclaimer.htm",
}
# Also any root-level URL that is just a single .htm in the root
ROOT_HTM_BLOCK = re.compile(r"^/[a-z0-9_-]+\.(htm|shtml)$")


def _is_article_url(url: str) -> bool:
    """Return True if *url* looks like a real article page (not nav/auth/store)."""
    path = urllib.parse.urlparse(url).path.lower()
    if not path.endswith((".htm", ".html", ".shtml")):
        return False
    if path.endswith(("_menu.shtml", "index.htm", "index.html", "/")):
        return False
    for prefix in EXCLUDE_PREFIXES:
        if path.startswith(prefix):
            return False
    # Exclude known nav hub pages
    if path in ROOT_NAV_PAGES:
        return False
    # Exclude root-level .htm files (they are nav pages, not content articles)
    if ROOT_HTM_BLOCK.match(path):
        return False
    return True


class EngineersEdgeScraper:
    """Scrape engineering reference content from Engineers Edge."""

    def __init__(self) -> None:
        self.sess = session()
        self._last_request = 0.0
        self._min_interval = 1.5  # seconds between requests
        self.discovered: dict[str, list[dict[str, str]]] = {}  # topic -> [article]

    def _throttle(self) -> None:
        """Enforce minimum interval between HTTP requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _fetch(self, url: str, **kwargs: Any) -> str:
        """Throttled wrapper around cached_get."""
        self._throttle()
        return cached_get(url, sess=self.sess, **kwargs)

    # ── discovery ────────────────────────────────────────────────────

    def discover_topics(self) -> list[str]:
        """Return list of available topic names (keys from TOPIC_MENUS)."""
        return list(TOPIC_MENUS.keys())

    # Content subdirectory prefixes per topic (for root-level menu pages)
    TOPIC_CONTENT_PREFIXES: dict[str, set[str]] = {
        "materials": {
            "/calculators/", "/manufacturing_spec/", "/manufacturing/",
            "/material_science/", "/materials/", "/Engineering_White_Papers/",
            "/heat_transfer/",
        },
        "strength-of-materials": {
            "/material_science/", "/mechanics_machines/",
            "/calculators/", "/beam_bending/",
            "/materials/", "/analysis/",
            "/Engineering_White_Papers/",
        },
        "fasteners-hardware": {
            "/hardware/", "/calculators/", "/excel_calculators/",
            "/material_science/",
        },
        "bearings": {
            "/bearing/", "/calculators/", "/motors/",
        },
        "gears": {
            "/gears/", "/calculators/", "/excel_calculators/",
            "/gearanimator/",
        },
        "gdt-drafting": {
            "/drafting/", "/calculators/gdt_", "/gdt",
        },
        "engineering-analysis": {
            "/analysis/", "/calculators/", "/Engineering_White_Papers/",
            "/manufacturing/", "/heat_transfer/", "/fluid_flow/",
        },
        "civil-engineering": {
            "/civil_engineering/", "/calculators/", "/excel_calculators/",
        },
    }

    def _extract_links_from_menu(self, url: str, topic: str) -> list[dict[str, str]]:
        """Fetch menu/sitemap page and extract article links belonging to *topic*."""
        html = self._fetch(url, ttl=86400)
        all_links = extract_links(html, url)
        seen: set[str] = set()
        articles: list[dict[str, str]] = []

        # Determine allowed content prefixes for this topic
        allowed_prefixes = self.TOPIC_CONTENT_PREFIXES.get(topic, set())

        for link in all_links:
            href = link["url"]
            if not _is_article_url(href):
                continue
            if href in seen:
                continue
            seen.add(href)

            link_path = urllib.parse.urlparse(href).path.lower()

            # Accept if link path starts with any allowed prefix
            if any(link_path.startswith(p) for p in allowed_prefixes):
                articles.append({
                    "url": href,
                    "title": link["text"] or Path(urllib.parse.urlparse(href).path).stem.replace("_", " ").title(),
                })

        return articles

    def discover_articles(self, topic: str | None = None) -> dict[str, list[dict[str, str]]]:
        """Discover article URLs for one or all topics.

        Returns dict[topic_name, list[article_dict]].
        """
        topics = [topic] if topic else list(TOPIC_MENUS.keys())

        for t in topics:
            if t in self.discovered:
                continue
            menus = TOPIC_MENUS[t]
            all_articles: list[dict[str, str]] = []
            seen_urls: set[str] = set()
            for menu_url in menus:
                full_url = urllib.parse.urljoin(BASE, menu_url)
                try:
                    articles = self._extract_links_from_menu(full_url, t)
                    for a in articles:
                        if a["url"] not in seen_urls:
                            seen_urls.add(a["url"])
                            all_articles.append(a)
                except Exception as exc:
                    log.warning("Failed to scan %s: %s", menu_url, exc)
            self.discovered[t] = all_articles
            log.info("Topic %s: discovered %d articles from %d menu pages",
                      t, len(all_articles), len(menus))

        return {t: self.discovered[t] for t in topics}

    # ── scraping ─────────────────────────────────────────────────────

    def _extract_content(self, url: str) -> dict[str, Any]:
        """Scrape content from a single article page.

        Returns dict with keys: url, title, text, tables, error (or None).
        """
        result: dict[str, Any] = {"url": url, "error": None}
        try:
            html = self._fetch(url, ttl=86400)
        except Exception as exc:
            log.warning("HTTP error %s: %s", url, exc)
            return {"url": url, "error": str(exc)[:200]}

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # title
        title_tag = soup.title
        result["title"] = sanitize(title_tag.string) if title_tag else Path(
            urllib.parse.urlparse(url).path).stem.replace("_", " ").title()

        # --- main content extraction ---
        # Strategy: collect all <p> and <li> text in the <body>,
        # then remove known boilerplate patterns.
        body = soup.body
        if body:
            # Remove script/style/nav elements
            for tag in body.select("script, style, nav, header, footer, form, noscript, iframe"):
                tag.decompose()

            # Get all text from remaining body
            full_text = body.get_text(separator="\n", strip=True)
            lines = [s.strip() for s in full_text.split("\n") if s.strip()]

            # Filter out boilerplate lines
            boilerplate_keywords = [
                "membership services", "scientific calculator", "popup",
                "related resources:", "advertise", "privacy policy",
                "all rights reserved", "copyright", "disclaimer",
                "feedback", "engineering book store", "engineering forum",
                "applications and design", "engineering calculators",
                "engineering terms", "excel app. downloads",
                "flat plate stress calcs", "fluids flow engineering",
                "home", "membership",
            ]
            content_lines = []
            for line in lines:
                lower = line.lower()
                # Skip short lines and boilerplate
                if len(line) < 15:
                    continue
                if any(bp in lower for bp in boilerplate_keywords):
                    continue
                content_lines.append(line)

            result["text"] = "\n".join(content_lines[:200])  # cap at 200 lines
        else:
            result["text"] = ""

        # --- extract tables as structured data ---
        table_data: list[list[list[str]]] = []
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            parsed_rows: list[list[str]] = []
            for row in rows:
                cells = row.find_all(["td", "th"])
                cell_texts = [sanitize(c.get_text(separator=" ", strip=True)) for c in cells]
                if any(c for c in cell_texts):
                    parsed_rows.append(cell_texts)
            if len(parsed_rows) >= 2:  # at least header + 1 data row
                table_data.append(parsed_rows)
        result["tables"] = table_data

        # summary
        result["text_length"] = len(result["text"])
        result["table_count"] = len(table_data)

        return result

    def scrape_topic(self, topic: str, limit: int = 0) -> list[dict[str, Any]]:
        """Scrape all articles for a single topic.

        If *limit* > 0, only scrape that many articles.
        """
        if topic not in self.discovered:
            self.discover_articles(topic)
        articles = self.discovered.get(topic, [])
        if limit:
            articles = articles[:limit]

        results: list[dict[str, Any]] = []
        for i, article in enumerate(articles):
            url = article["url"]
            content = self._extract_content(url)
            content["topic"] = topic
            content["discovered_title"] = article["title"]
            results.append(content)
            log.info("  [%d/%d] %s — %s (%d chars)",
                      i + 1, len(articles), topic,
                      content.get("title", "?")[:50],
                      content.get("text_length", 0))
        return results

    def scrape_all(self, limit_per_topic: int = 0) -> list[dict[str, Any]]:
        """Scrape articles from all topics.

        Returns a flat list of all scraped page dicts.
        """
        self.discover_articles()
        all_results: list[dict[str, Any]] = []
        for topic in self.discovered:
            all_results.extend(self.scrape_topic(topic, limit=limit_per_topic))
        return all_results


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # parse --limit and --topic
    import argparse
    parser = argparse.ArgumentParser(description="Engineers Edge scraper")
    parser.add_argument("--topic", help="Scrape only this topic")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max articles per topic (0 = all)")
    args = parser.parse_args()

    scraper = EngineersEdgeScraper()

    if args.topic:
        log.info("Scraping topic: %s (limit=%s)", args.topic, args.limit or "all")
        scraper.discover_articles(args.topic)
        results = scraper.scrape_topic(args.topic, limit=args.limit)
    else:
        log.info("Scraping all topics (limit per topic=%s)", args.limit or "all")
        results = scraper.scrape_all(limit_per_topic=args.limit)

    log.info("Done scraping. Total pages: %d", len(results))

    if results:
        path = save_raw("engineers-edge", results)
        print(f"\nSaved {len(results)} pages to {path}")

        # report per-topic counts
        from collections import Counter
        topic_counts = Counter(r["topic"] for r in results if "topic" in r)
        print("\nPer-topic counts:")
        for t, c in sorted(topic_counts.items()):
            print(f"  {t}: {c}")
        errors = [r for r in results if r.get("error")]
        if errors:
            print(f"\nErrors: {len(errors)} / {len(results)}")
            for e in errors[:5]:
                print(f"  {e['url']}: {e['error'][:80]}")

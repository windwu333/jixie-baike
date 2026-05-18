#!/usr/bin/env python3
"""NIST Engineering Resources scraper for 机械师大百科.

Discover and scrape engineering-related content from www.nist.gov.
Source: https://www.nist.gov/engineering
Target: 100-300 pages of technical engineering content.
"""

import json
import logging
import random
import re
import sys
import time
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

# Add project root so framework import works when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))
from framework import cached_get, extract_links, extract_text, log, sanitize, save_raw, session

log = logging.getLogger("nist-engineering")
BASE_URL = "https://www.nist.gov"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

# Topics / sub-directories under engineering that hold technical content.
# Ordered by estimated value for a mechanical engineering encyclopedia.
ENGINEERING_TOPICS = [
    "advanced-manufacturing",
    "biomanufacturing",
    "cyber-physical-systems",
    "disaster-resilience",
    "energy",
    "engineering-design",
    "environmental",
    "fire",
    "infrastructure",
    "intelligent-systems",
    "manufacturing",
    "materials",
    "mechanical",
    "nanotechnology",
    "robotics",
    "semiconductors",
    "smart-manufacturing",
    "standards",
    "sustainable-manufacturing",
    "systems-engineering",
    "engineering-laboratories",
    "engineering-research",
    "engineering-programs",
]

# Subdirectories under /mep/ that hold useful content
MEP_TOPICS = [
    "manufacturing",
    "quality-management",
    "supply-chain",
    "technology-acceleration",
    "workforce-development",
]

# URL patterns to skip (low-value pages)
SKIP_PATTERNS = re.compile(
    r"/(news|events|people|contact|about|pressroom|calendar|"
    r"blogs|social|careers|forms|policies|alerts|directories)/",
    re.I,
)


class NistScraper:
    """Scraper for NIST Engineering Resources."""

    def __init__(self, target: int = 200, shuffle: bool = True):
        self.target = target
        self.shuffle = shuffle
        self.discovered_urls: list[dict[str, str]] = []
        self.sess = session(retries=3, backoff=1.0, timeout=30)
        self._last_call = 0.0

    # ------------------------------------------------------------------ #
    #  Rate-limit helper
    # ------------------------------------------------------------------ #
    def _throttle(self, interval: float = 1.0) -> None:
        """Ensure at least `interval` seconds since last network request."""
        elapsed = time.time() - self._last_call
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_call = time.time()

    # ------------------------------------------------------------------ #
    #  Sitemap discovery
    # ------------------------------------------------------------------ #
    def _parse_sitemap(self, xml_text: str) -> list[str]:
        """Parse an XML sitemap into a flat list of URLs.

        Handles both sitemap indexes (containing <sitemap><loc>) and
        regular sitemaps (containing <url><loc>).
        """
        root = ElementTree.fromstring(xml_text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Detect: sitemap index has <sitemap> children
        sitemap_nodes = root.findall(".//sm:sitemap", ns)
        url_nodes = root.findall(".//sm:url", ns)

        if sitemap_nodes and not url_nodes:
            # This is a sitemap index -- return the sub-sitemap URLs
            return [
                loc.text.strip()
                for loc in root.iterfind(".//sm:sitemap/sm:loc", ns)
            ]

        # Regular sitemap -- return page URLs
        return [
            loc.text.strip()
            for loc in root.iterfind(".//sm:url/sm:loc", ns)
        ]

    def _resolve_sitemap(self, xml_text: str) -> list[str]:
        """Resolve a sitemap (index or regular) into a flat list of page URLs.

        If ``xml_text`` is a sitemap index, fetch each sub-sitemap and
        collect all page URLs.
        """
        urls = self._parse_sitemap(xml_text)

        # If any of the returned values look like sub-sitemaps, recurse
        sample = urls[:5]
        if sample and all(u.endswith(".xml") or "sitemap" in u for u in sample):
            log.info("Sitemap index detected with %d sub-sitemaps", len(urls))
            all_pages: list[str] = []
            for i, sub_url in enumerate(urls):
                log.info("[sitemap %d/%d] %s", i + 1, len(urls), sub_url)
                self._throttle(0.5)
                try:
                    sub_xml = cached_get(sub_url, ttl=43200, sess=self.sess)
                    pages = self._parse_sitemap(sub_xml)
                    all_pages.extend(pages)
                    log.info("  -> %d URLs", len(pages))
                except Exception as exc:
                    log.warning("  -> Failed: %s", exc)
            log.info(
                "Resolved all sub-sitemaps: %d total page URLs", len(all_pages)
            )
            return all_pages

        return urls

    def _is_useful(self, url: str) -> bool:
        """Return True if the URL is engineering content worth scraping."""
        path = url.replace(BASE_URL, "")
        # Must be under /engineering/ or /mep/
        if "/engineering/" not in path and "/mep/" not in path:
            return False
        # Skip low-value sections
        if SKIP_PATTERNS.search(path):
            return False
        # Skip homepage fragments
        if path.strip("/") in ("engineering", "mep"):
            return False
        # Skip print/PDF views
        if "print" in path or "pdf" in path:
            return False
        return True

    def discover_topics(self) -> list[dict[str, str]]:
        """Discover engineering-related URLs from the NIST sitemap.

        Returns list of {url, title} dicts.
        """
        log.info("Fetching sitemap from %s ...", SITEMAP_URL)

        self._throttle(0.5)
        xml_text = cached_get(SITEMAP_URL, ttl=43200, sess=self.sess)

        all_urls = self._resolve_sitemap(xml_text)
        log.info("Sitemap resolved to %d total URLs", len(all_urls))

        useful = []
        for url in all_urls:
            if self._is_useful(url):
                # Derive a human-readable title from the URL path
                path = url.replace(BASE_URL, "").strip("/")
                segments = path.split("/")
                # Last meaningful segment, de-slugified
                title = segments[-1].replace("-", " ").title()
                useful.append({"url": url, "title": title})

        log.info("Discovered %d useful engineering URLs", len(useful))
        self.discovered_urls = useful
        return useful

    # ------------------------------------------------------------------ #
    #  Individual page scrape
    # ------------------------------------------------------------------ #
    def scrape_topic(self, url: str) -> dict[str, Any] | None:
        """Scrape a single NIST engineering page.

        Returns dict with keys: url, title, content, headings, links, topics.
        Returns None on failure.
        """
        self._throttle(1.0)  # Be polite to .gov
        try:
            html = cached_get(url, ttl=86400, sess=self.sess)
        except Exception as exc:
            log.warning("Failed to fetch %s: %s", url, exc)
            return None

        # Extract page title from <title>
        title_parts = extract_text(html, "title")
        page_title = title_parts[0] if title_parts else url

        # Main content region varies by NIST page type; target the most common containers
        content_parts = extract_text(html, "article .field--item, .node__content, .content, main")
        # If those yielded nothing, fall back to body text
        if not content_parts:
            content_parts = extract_text(html, "body p, body li")

        # Headings for structure
        headings = extract_text(html, "h1, h2, h3, h4")

        # Extract internal and external links from the main region
        links = extract_links(html, BASE_URL, selector="main a[href], article a[href]")

        # Determine topic(s) from URL path
        path = url.replace(BASE_URL, "").strip("/")
        segments = path.split("/")
        # The second segment is the main topic (e.g. /engineering/manufacturing/...)
        in_topic = segments[1] if len(segments) > 1 else ""
        # Map /mep/ to a label
        if in_topic == "mep" and len(segments) > 2:
            in_topic = f"mep-{segments[2]}"

        return {
            "url": url,
            "title": sanitize(page_title),
            "content": "\n\n".join(content_parts) if content_parts else "",
            "headings": [sanitize(h) for h in headings],
            "internal_links": [
                l for l in links if l["url"].startswith(BASE_URL)
            ],
            "topic": in_topic,
            "source": "nist-engineering",
        }

    # ------------------------------------------------------------------ #
    #  Batch scrape
    # ------------------------------------------------------------------ #
    def scrape_all(self) -> list[dict[str, Any]]:
        """Discover topics then scrape up to ``self.target`` pages.

        Returns list of scraped-page dicts.
        """
        if not self.discovered_urls:
            self.discover_topics()

        # Shuffle for topic diversity so first N pages span engineering sub-areas
        if self.shuffle:
            random.shuffle(self.discovered_urls)
            log.info("Shuffled %d discovered URLs for topic diversity", len(self.discovered_urls))

        results: list[dict[str, Any]] = []
        errors = 0

        for i, entry in enumerate(self.discovered_urls):
            if i >= self.target:
                log.info("Reached target of %d pages, stopping.", self.target)
                break

            log.info("[%d/%d] %s", i + 1, min(self.target, len(self.discovered_urls)), entry["url"])
            page = self.scrape_topic(entry["url"])
            if page:
                results.append(page)
            else:
                errors += 1

            # Progress log every 20 pages
            if (i + 1) % 20 == 0:
                log.info("Progress: %d saved, %d errors so far", len(results), errors)

        log.info(
            "Scrape complete: %d pages saved, %d errors (target %d)",
            len(results),
            errors,
            self.target,
        )
        return results


# ------------------------------------------------------------------ #
#  CLI entry point
# ------------------------------------------------------------------ #
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NIST Engineering Resources")
    parser.add_argument(
        "--target",
        type=int,
        default=200,
        help="Number of pages to scrape (default: 200)",
    )
    parser.add_argument(
        "--save",
        type=str,
        default="nist-engineering.json",
        help="Output filename under raw/nist-engineering/ (default: nist-engineering.json)",
    )
    parser.add_argument(
        "--no-shuffle",
        action="store_true",
        help="Disable URL shuffling (scrape in sitemap order instead)",
    )
    args = parser.parse_args()

    scraper = NistScraper(target=args.target, shuffle=not args.no_shuffle)

    log.info("Starting NIST Engineering scraper, target=%d pages", args.target)
    log.info("Rate limit: 1s between requests. Be polite to .gov.")

    results = scraper.scrape_all()

    out_path = save_raw("nist-engineering", results, filename=args.save)
    print(f"\nDone. {len(results)} pages saved to {out_path}")

    # Brief summary
    topics = {}
    for r in results:
        t = r.get("topic", "unknown")
        topics[t] = topics.get(t, 0) + 1
    print("\nTopics breakdown:")
    for t, c in sorted(topics.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c} pages")


if __name__ == "__main__":
    main()

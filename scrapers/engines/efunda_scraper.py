#!/usr/bin/env python3
"""机械师大百科 — eFunda (www.efunda.com) 采集引擎

Engineering Reference: materials, formulas, design standards, calculators, processes.

Uses Chrome-era UA directly (NOT framework default). eFunda blocks bots/spiders.
Rate limit 1.5s between requests. Target 200-400 records.
"""

import logging
import re
import sys
import time
import json
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from framework import save_raw, log

log = logging.getLogger("efunda")

BASE = "https://www.efunda.com"
CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Section entry points (confirmed accessible)
# ---------------------------------------------------------------------------
SECTIONS = {
    "materials": f"{BASE}/materials/index.cfm",
    "design_standards": f"{BASE}/designstandards/index.cfm",
    "processes": f"{BASE}/processes/index.cfm",
    "mathematics": f"{BASE}/math/math_home/index.cfm",
}

SKIP_PREFIXES = (
    "/cgi-bin/", "/login", "/register", "/feedback",
    "/about", "/privacy", "/sitemap", "/search",
    "/advertise", "/contact",
)
SKIP_SUFFIXES = (".pdf", ".jpg", ".png", ".gif", ".zip", ".exe", ".js", ".css")


def get(url: str) -> str:
    """Fetch URL with Chrome UA. Raises on HTTP error."""
    resp = requests.get(url, headers={"User-Agent": CHROME_UA}, timeout=30)
    resp.raise_for_status()
    return resp.text


def is_scrapable(url: str) -> bool:
    """Return True if url points to a scrapable eFunda content page."""
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc and "efunda.com" not in parsed.netloc:
        return False
    path = parsed.path.lower()
    if not (path.endswith(".cfm") or path.endswith(".html") or path.endswith(".htm")):
        return False
    for prefix in SKIP_PREFIXES:
        if path.startswith(prefix):
            return False
    for suffix in SKIP_SUFFIXES:
        if path.endswith(suffix):
            return False
    return True


def extract_title(soup: BeautifulSoup) -> str:
    """Extract page title from <title> or first <h1>."""
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    return ""


def extract_content(html: str) -> str:
    """Extract readable article body from eFunda HTML.

    Strategy:
    1. #mainContent or #content or .mainBody area
    2. <pre> tags (formulas, specs, code blocks)
    3. Wide <td> cells (table-based layout body)
    4. Fallback: <body> minus nav elements
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles
    for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Strategy 1: ID/class selectors
    for sel in ("#mainContent", "#content", ".content", ".mainBody", "#main", ".mainContent"):
        container = soup.select_one(sel)
        if container:
            text = _sanitize(container.get_text(separator="\n", strip=True))
            if len(text) > 80:
                return text

    # Strategy 2: <pre> blocks (formulas, data tables)
    pre_texts = []
    for pre in soup.find_all("pre"):
        t = _sanitize(pre.get_text(strip=True))
        if t:
            pre_texts.append(t)
    if pre_texts:
        return "\n\n".join(pre_texts)

    # Strategy 3: wide <td> cells (table-based layouts)
    wide_texts = []
    for td in soup.find_all("td"):
        w = td.get("width", "")
        try:
            pct = int(w.rstrip("%"))
        except (ValueError, AttributeError):
            pct = 0
        if pct >= 50:
            t = _sanitize(td.get_text(separator="\n", strip=True))
            if len(t) > 100:
                wide_texts.append(t)
    if wide_texts:
        return "\n\n".join(wide_texts)

    # Strategy 4: <body> minus nav-like elements
    body = soup.find("body")
    if body:
        for nav_class in ("leftNav", "leftnav", "nav", "navigation", "sidebar"):
            for tag in body.select(f".{nav_class}"):
                tag.decompose()
        for tag in body.find_all("table"):
            w = tag.get("width", "")
            try:
                pct = int(w.rstrip("%"))
            except (ValueError, AttributeError):
                pct = 100
            if pct and pct < 30:
                tag.decompose()
        text = _sanitize(body.get_text(separator="\n", strip=True))
        if len(text) > 100:
            return text

    return ""


def _sanitize(text: str) -> str:
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def discover_links(url: str) -> list[dict[str, str]]:
    """Extract all scrapable .cfm links from a section index page."""
    log.info("  Discovering links from: %s", url)
    html = get(url)
    soup = BeautifulSoup(html, "html.parser")
    links: list[dict[str, str]] = []
    seen: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urllib.parse.urljoin(url, href)
        if not is_scrapable(full_url):
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        text = _sanitize(a_tag.get_text(strip=True)) or ""
        links.append({"url": full_url, "text": text})

    log.info("    Found %d links", len(links))
    return links


def scrape_page(url: str, section: str) -> dict[str, Any] | None:
    """Scrape a single eFunda content page.

    Returns dict with url, title, content, section, or None on failure/empty.
    """
    try:
        html = get(url)
    except requests.RequestException as exc:
        log.warning("  FAIL %s — %s", url, exc)
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Try to follow frames
    for frame in soup.find_all(["frame", "iframe"]):
        src = frame.get("src", "")
        if src and not src.startswith("#") and not src.startswith("javascript"):
            frame_url = urllib.parse.urljoin(url, src)
            log.debug("  Following frame: %s", frame_url)
            try:
                html = get(frame_url)
            except requests.RequestException as exc:
                log.warning("  Frame FAIL %s — %s", frame_url, exc)
                continue
            break

    title = extract_title(BeautifulSoup(html, "html.parser"))
    content = extract_content(html)

    if not content or len(content) < 50:
        return None

    return {
        "url": url,
        "title": title,
        "content": content,
        "section": section,
    }


def run(max_pages: int = 400, rate: float = 1.5) -> list[dict[str, Any]]:
    """Full discovery + scrape pipeline.

    1. Fetch each section index page.
    2. Extract all content links.
    3. Visit each content page and extract title/content.
    4. Rate limit between requests.
    """
    # -- Phase 1: Discover all content links across sections --
    all_links: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for section_name, section_url in SECTIONS.items():
        links = discover_links(section_url)
        for link in links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                link["section"] = section_name
                all_links.append(link)

    log.info("Discovered %d unique links across %d sections", len(all_links), len(SECTIONS))

    if not all_links:
        log.warning("No links discovered! Something may be wrong with the site or connection.")
        return []

    # -- Phase 2: Scrape each page --
    if len(all_links) > max_pages:
        log.info("Limiting to %d pages (discovered %d)", max_pages, len(all_links))
        all_links = all_links[:max_pages]

    results: list[dict[str, Any]] = []
    for i, link in enumerate(all_links):
        log.info("[%d/%d] [%s] %s", i + 1, len(all_links), link["section"], link["url"])
        page = scrape_page(link["url"], link["section"])
        if page:
            results.append(page)
        time.sleep(rate)

    log.info(
        "Scrape complete: %d / %d pages yielded content",
        len(results), len(all_links),
    )
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="eFunda scraper")
    parser.add_argument("--max-pages", type=int, default=400, help="Max pages to scrape (default 400)")
    parser.add_argument("--rate", type=float, default=1.5, help="Seconds between requests (default 1.5)")
    parser.add_argument("--discover-only", action="store_true", help="Only discover links, don't scrape")
    parser.add_argument("--no-save", action="store_true", help="Print results instead of saving")
    args = parser.parse_args()

    logging.getLogger("efunda").setLevel(logging.INFO)

    # Discover links from all sections
    all_links: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for section_name, section_url in SECTIONS.items():
        links = discover_links(section_url)
        for link in links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                link["section"] = section_name
                all_links.append(link)

    log.info("Discovered %d unique links across %d sections", len(all_links), len(SECTIONS))

    if not all_links:
        log.warning("No links discovered! Check connection or site structure.")
        sys.exit(1)

    if args.discover_only:
        print(f"\nDiscovered {len(all_links)} pages:")
        for link in sorted(all_links, key=lambda x: (x["section"], x["url"])):
            print(f"  [{link['section']:20s}] {link['text'][:60]:60s} {link['url']}")
        return

    # Limit
    if len(all_links) > args.max_pages:
        log.info("Limiting to %d pages (discovered %d)", args.max_pages, len(all_links))
        all_links = all_links[: args.max_pages]

    # Scrape
    results: list[dict[str, Any]] = []
    for i, link in enumerate(all_links):
        log.info("[%d/%d] [%s] %s", i + 1, len(all_links), link["section"], link["url"])
        page = scrape_page(link["url"], link["section"])
        if page:
            results.append(page)

        # Periodic progress
        if (i + 1) % 50 == 0:
            log.info("Progress: %d/%d scraped, %d with content", i + 1, len(all_links), len(results))
            # Intermediate save every 50 for safety
            from framework import save_raw as _save
            _save("efunda", results, filename=f"checkpoint_{i+1}.json")

        time.sleep(args.rate)

    if args.no_save:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        path = save_raw("efunda", results)
        print(f"\nSaved {len(results)} pages -> {path}")

    # Summary
    from collections import Counter

    cat_counts = Counter(r.get("section", "unknown") for r in results)
    print("\nSection breakdown:")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s} {cnt} pages")

    sizes = [len(r.get("content", "")) for r in results]
    if sizes:
        print(
            f"\nContent: avg {sum(sizes) // len(sizes):,} chars  |  "
            f"min {min(sizes):,}  |  max {max(sizes):,}  |  "
            f"total {sum(sizes):,} chars"
        )


if __name__ == "__main__":
    main()

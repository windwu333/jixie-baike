#!/usr/bin/env python3
"""机械师大百科 — Engineering ToolBox sitemap-based scraper (site restructured 2026)."""

import json, logging, re, sys, time, urllib.parse
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
from framework import sanitize, save_raw, log

log = logging.getLogger("engineeringtoolbox")

SOURCE_ID = "engineering-toolbox"
BASE_URL = "https://www.engineeringtoolbox.com"
CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

SKIP_PATTERNS = (
    r"/amp/", r"/static/", r"\.pdf$", r"\.png$", r"\.jpg$",
    r"index\.html$", r"^https://www\.engineeringtoolbox\.com/$",
)


def get(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": CHROME_UA}, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_content(html: str) -> dict:
    """Extract title + text body from ETB HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = sanitize(h1.get_text(strip=True))
    if not title:
        t = soup.find("title")
        if t:
            title = sanitize(t.get_text(strip=True))

    # Try multiple content area selectors
    content_text = ""
    for sel in ("article", "[role=main]", ".content", "#content", ".main", "#main", ".entry", "body"):
        el = soup.select_one(sel)
        if el:
            text = sanitize(el.get_text(separator=" ", strip=True))
            if len(text) > 200:
                content_text = text
                break

    if not content_text:
        body = soup.find("body")
        if body:
            content_text = sanitize(body.get_text(separator=" ", strip=True))

    return {"title": title, "content": content_text}


def run(max_pages: int = 800, rate: float = 1.0) -> list[dict[str, Any]]:
    """Fetch sitemap, filter content URLs, scrape each."""
    log.info("Fetching sitemap from %s/sitemap.xml ...", BASE_URL)
    html = get(f"{BASE_URL}/sitemap.xml")
    soup = BeautifulSoup(html, "xml")
    all_urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text(strip=True)
        skip = False
        for pat in SKIP_PATTERNS:
            if re.search(pat, url):
                skip = True
                break
        if not skip:
            all_urls.append(url)

    log.info("Found %d content URLs in sitemap", len(all_urls))

    if len(all_urls) > max_pages:
        log.info("Limiting to %d pages", max_pages)
        all_urls = all_urls[:max_pages]

    results: list[dict] = []
    for i, url in enumerate(all_urls):
        if (i + 1) % 50 == 0:
            log.info("[%d/%d] %d valid so far", i + 1, len(all_urls), len(results))
        try:
            html = get(url)
        except Exception as exc:
            log.warning("FAIL %s — %s", url, exc)
            time.sleep(rate)
            continue

        parsed = extract_content(html)
        if parsed["content"] and len(parsed["content"]) >= 200:
            results.append({
                "url": url,
                "title": parsed["title"],
                "content": parsed["content"],
                "source": SOURCE_ID,
            })

        time.sleep(rate)

    log.info("Scrape complete: %d/%d pages yielded content", len(results), len(all_urls))
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ETB sitemap scraper")
    parser.add_argument("--max", type=int, default=800, help="Max pages (default 800)")
    parser.add_argument("--rate", type=float, default=1.0, help="Seconds between requests")
    args = parser.parse_args()

    results = run(max_pages=args.max, rate=args.rate)
    path = save_raw(SOURCE_ID, results)
    print(f"\nSaved {len(results)} pages -> {path}")
    sizes = [len(r.get("content", "")) for r in results]
    if sizes:
        print(f"Avg content: {sum(sizes)//len(sizes):,} chars, total: {sum(sizes):,} chars")


if __name__ == "__main__":
    main()

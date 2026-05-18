#!/usr/bin/env python3
"""机械师大百科 — ExplainThatStuff scraper from A-Z index."""

import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from framework import cached_get, sanitize, save_raw, log
from bs4 import BeautifulSoup

BASE = "https://www.explainthatstuff.com"
CHROME_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def _get(url):
    import requests
    resp = requests.get(url, headers={"User-Agent": CHROME_UA}, timeout=30)
    resp.raise_for_status()
    return resp.text

class ExplainThatStuffScraper:
    TARGET_CATS = ["Engineering", "Energy", "Materials", "Tools, instruments, and measurement",
                   "Transportation", "Science", "Electricity and electronics"]

    def __init__(self):
        self._last = 0.0

    def _rlimit(self):
        elapsed = time.time() - self._last
        if elapsed < 2.0:
            time.sleep(2.0 - elapsed)
        self._last = time.time()

    def discover_articles(self) -> list[dict]:
        html = _get(f"{BASE}/azindex.html")
        articles = []
        in_target = False
        for m in re.finditer(r'<a\s+href=\"([^\"]+\.html)\"[^>]*>([^<]+)</a>', html, re.I):
            url = m.group(1)
            title = m.group(2).strip()
            if title in self.TARGET_CATS:
                in_target = True
                continue
            if title in ["A-Z index", "Timeline", "Teaching guide", "About us", "Privacy &amp; cookies"]:
                in_target = False
                continue
            if in_target and title:
                full_url = url if url.startswith("http") else BASE + "/" + url.lstrip("/")
                articles.append({"url": full_url, "title": title})
        return articles

    def scrape_article(self, url: str, title: str) -> dict | None:
        self._rlimit()
        try:
            html = _get(url)
        except:
            return None
        soup = BeautifulSoup(html, "html.parser")
        # Remove unwanted elements
        for tag in soup.select("script, style, nav, header, footer, aside, .ad, .sidebar, #comments, .related"):
            tag.decompose()
        # Get main content from article, main, or column divs
        main = soup.select_one("article, [role=main], .main, .content, #main, #content, .column, .entry-content")
        if main:
            text = sanitize(main.get_text(separator=" ", strip=True))
        else:
            text = sanitize(soup.get_text(separator=" ", strip=True))
        if len(text) < 200:
            return None
        return {
            "title": title,
            "url": url,
            "content": text[:5000],
            "source": "explainthatstuff",
        }

    def scrape_all(self) -> list[dict]:
        articles = self.discover_articles()
        log.info("Discovered %d articles in target categories", len(articles))
        results = []
        for i, a in enumerate(articles):
            rec = self.scrape_article(a["url"], a["title"])
            if rec:
                results.append(rec)
            if (i + 1) % 30 == 0:
                log.info("  %d/%d collected, %d valid", i + 1, len(articles), len(results))
        return results

if __name__ == "__main__":
    s = ExplainThatStuffScraper()
    data = s.scrape_all()
    path = save_raw("explainthatstuff", data)
    log.info("ExplainThatStuff: %d articles -> %s", len(data), path)

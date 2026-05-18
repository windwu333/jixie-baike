#!/usr/bin/env python3
"""机械师大百科 — IntechOpen Engineering open-access book chapter scraper."""

import sys, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from framework import cached_get, sanitize, extract_text, extract_links, save_raw, log, rate_limit

BASE = "https://www.intechopen.com"

class IntechOpenScraper:
    def __init__(self):
        self.seen_urls = set()

    def discover_subcategories(self) -> list[dict]:
        html = cached_get(f"{BASE}/subjects/engineering", ttl=86400)
        cats = []
        for link in extract_links(html, BASE, selector="a[href*='/subjects/']"):
            url = link["url"]
            if url not in [c["url"] for c in cats] and url != f"{BASE}/subjects/engineering":
                cats.append({"url": url, "name": link["text"]})
        return cats

    def discover_books(self, cat_url: str, max_pages: int = 5) -> list[dict]:
        books = []
        for page in range(1, max_pages + 1):
            url = f"{cat_url}?page={page}"
            try:
                html = cached_get(url, ttl=86400)
            except:
                break
            for link in extract_links(html, BASE, selector="a[href*='/books/']"):
                url = link["url"]
                if url not in [b["url"] for b in books] and url != cat_url:
                    books.append({"url": url, "title": link["text"], "category_url": cat_url})
            time.sleep(1)
        return books

    def discover_chapters(self, book_url: str) -> list[dict]:
        try:
            html = cached_get(book_url, ttl=86400)
        except:
            return []
        chapters = []
        for link in extract_links(html, BASE, selector="a[href*='/chapters/']"):
            url = link["url"]
            if url not in self.seen_urls:
                self.seen_urls.add(url)
                chapters.append({"url": url, "title": link["text"]})
        return chapters

    @rate_limit(2.0)
    def scrape_chapter(self, chapter_url: str, book_title: str = "") -> dict | None:
        try:
            html = cached_get(chapter_url, ttl=86400)
        except:
            return None
        title = ""
        titles = extract_text(html, "h1, h2.chapter-title")
        if titles:
            title = titles[0]
        paragraphs = extract_text(html, "div.chapter-content p, div.Abstract p, section p")
        content = " ".join(paragraphs)
        authors = extract_text(html, "div.authors a, span.author-name")
        doi_links = extract_links(html, BASE, selector="a[href*='doi.org']")
        doi = doi_links[0]["url"] if doi_links else ""
        if not content:
            return None
        return {
            "title": title or chapter_url.split("/")[-1],
            "book_title": book_title,
            "url": chapter_url,
            "doi": doi,
            "authors": authors,
            "content": content[:3000],
            "source": "intechopen-engineering",
        }

    def scrape_all(self, max_cats: int = 5, max_books_per_cat: int = 5) -> list[dict]:
        results = []
        cats = self.discover_subcategories()[:max_cats]
        for cat in cats:
            log.info("Category: %s", cat["name"])
            books = self.discover_books(cat["url"], max_pages=3)[:max_books_per_cat]
            for book in books:
                log.info("  Book: %s", book["title"][:60])
                chapters = self.discover_chapters(book["url"])[:20]
                for ch in chapters:
                    rec = self.scrape_chapter(ch["url"], book["title"])
                    if rec:
                        results.append(rec)
                    if len(results) % 10 == 0:
                        log.info("  Collected %d chapters so far", len(results))
        return results


if __name__ == "__main__":
    s = IntechOpenScraper()
    data = s.scrape_all(max_cats=5, max_books_per_cat=5)
    path = save_raw("intechopen-engineering", data)
    log.info("IntechOpen: %d chapters -> %s", len(data), path)

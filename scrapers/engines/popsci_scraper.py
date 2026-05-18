#!/usr/bin/env python3
"""机械师大百科 — Popular science site scrapers (Britannica + ExplainThatStuff + HowStuffWorks)."""

import sys, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from framework import cached_get, sanitize, extract_text, extract_links, save_raw, log, rate_limit


class BritannicaScraper:
    BASE = "https://www.britannica.com"

    def discover_topics(self) -> list[dict]:
        urls_seen = set()
        topics = []
        start_urls = [
            f"{self.BASE}/engineering",
            f"{self.BASE}/science/mechanical-engineering",
            f"{self.BASE}/technology/materials-processing",
            f"{self.BASE}/technology/manufacturing",
        ]
        for start in start_urls:
            try:
                html = cached_get(start, ttl=86400)
            except:
                continue
            links = extract_links(html, self.BASE, selector="a[href*='/technology/'], a[href*='/science/'], a[href*='/engineering']")
            for link in links:
                url = link["url"]
                if url not in urls_seen and "britannica.com" in url:
                    urls_seen.add(url)
                    topics.append({"url": url, "title": link["text"]})
            time.sleep(1)
        return topics

    @rate_limit(2.0)
    def scrape_topic(self, url: str) -> dict | None:
        try:
            html = cached_get(url, ttl=86400)
        except:
            return None
        title = extract_text(html, "h1")
        content = extract_text(html, "div.article-content p, div.mdp-page p, section.article-body p")
        if not title or not content:
            return None
        categories = extract_text(html, "nav.breadcrumb a, div.breadcrumb a")
        return {
            "url": url,
            "title": title[0],
            "content": " ".join(content),
            "categories": categories,
            "source": "britannica-engineering",
        }

    def scrape_all(self) -> list[dict]:
        topics = self.discover_topics()
        log.info("Britannica: discovered %d topics", len(topics))
        results = []
        for t in topics[:100]:
            rec = self.scrape_topic(t["url"])
            if rec:
                results.append(rec)
        return results


class ExplainThatStuffScraper:
    BASE = "https://www.explainthatstuff.com"

    def discover_topics(self) -> list[dict]:
        urls_seen = set()
        topics = []
        html = cached_get(f"{self.BASE}/engineering.html", ttl=86400)
        links = extract_links(html, self.BASE, selector="a[href]")
        for link in links:
            url = link["url"]
            if url not in urls_seen and url.endswith(".html") and "explainthatstuff.com" in url and "sitemap" not in url:
                urls_seen.add(url)
                topics.append({"url": url, "title": link["text"]})
        return topics

    @rate_limit(2.0)
    def scrape_topic(self, url: str) -> dict | None:
        try:
            html = cached_get(url, ttl=86400)
        except:
            return None
        title = extract_text(html, "h1")
        content = extract_text(html, "div.article p, main p, div#content p")
        if not content:
            return None
        return {
            "url": url,
            "title": title[0] if title else url.split("/")[-1].replace(".html", ""),
            "content": " ".join(content),
            "source": "explainthatstuff",
        }

    def scrape_all(self) -> list[dict]:
        topics = self.discover_topics()
        log.info("ExplainThatStuff: discovered %d topics", len(topics))
        results = []
        for t in topics[:80]:
            rec = self.scrape_topic(t["url"])
            if rec:
                results.append(rec)
        return results


class HowStuffWorksScraper:
    BASE = "https://www.howstuffworks.com"

    def discover_topics(self) -> list[dict]:
        urls_seen = set()
        topics = []
        start_urls = [
            f"{self.BASE}/engineering.htm",
            f"{self.BASE}/engineering/",
        ]
        for start in start_urls:
            try:
                html = cached_get(start, ttl=86400)
            except:
                continue
            links = extract_links(html, self.BASE, selector="a[href*='/engineering/']")
            for link in links:
                url = link["url"]
                if url not in urls_seen and "howstuffworks.com" in url and not any(x in url for x in ["/category/", "/about"]):
                    urls_seen.add(url)
                    topics.append({"url": url, "title": link["text"]})
            time.sleep(1)
        return topics

    @rate_limit(2.0)
    def scrape_topic(self, url: str) -> dict | None:
        try:
            html = cached_get(url, ttl=86400)
        except:
            return None
        title = extract_text(html, "h1")
        content = extract_text(html, "article p, div.article-content p, main p")
        if not content:
            return None
        cats = extract_text(html, "nav.breadcrumb a, ul.breadcrumbs a")
        return {
            "url": url,
            "title": title[0] if title else "",
            "content": " ".join(content),
            "categories": cats,
            "source": "howstuffworks-eng",
        }

    def scrape_all(self) -> list[dict]:
        topics = self.discover_topics()
        log.info("HowStuffWorks: discovered %d topics", len(topics))
        results = []
        for t in topics[:80]:
            rec = self.scrape_topic(t["url"])
            if rec:
                results.append(rec)
        return results


if __name__ == "__main__":
    all_data = {}
    for name, cls in [("britannica-engineering", BritannicaScraper),
                       ("explainthatstuff", ExplainThatStuffScraper),
                       ("howstuffworks-eng", HowStuffWorksScraper)]:
        try:
            s = cls()
            data = s.scrape_all()
            path = save_raw(name, data)
            all_data[name] = len(data)
            log.info("%s: saved %d items -> %s", name, len(data), path)
        except Exception as e:
            log.error("%s scraper failed: %s", name, e)
    log.info("Popsci collection complete: %s", all_data)

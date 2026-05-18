#!/usr/bin/env python3
"""机械师大百科 — 海外内容批量采集框架

通用采集基础设施：HTTP 缓存、速率限制、HTML 解析、JSON 存储。
"""

import hashlib, json, logging, os, pickle, re, sys, textwrap, time, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = Path(__file__).parent.parent
RAW = BASE / "raw"
CACHE_DIR = BASE / "raw" / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("scraper")


def session(retries: int = 3, backoff: float = 1.0, timeout: int = 30) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; JixieBaike/1.0; +https://github.com/windwu333/jixie-baike)",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    })
    retry = Retry(total=retries, backoff_factor=backoff, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.timeout = timeout
    return s


def cache_key(url: str, params: dict | None = None) -> str:
    raw = url + (json.dumps(params, sort_keys=True) if params else "")
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def cached_get(url: str, params: dict | None = None, ttl: int = 86400, sess: requests.Session | None = None) -> str:
    key = cache_key(url, params)
    cache_file = CACHE_DIR / key
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < ttl:
        return pickle.loads(cache_file.read_bytes())

    s = sess or session()
    resp = s.get(url, params=params)
    resp.raise_for_status()
    text = resp.text

    cache_file.write_bytes(pickle.dumps(text))
    return text


def sanitize(text: str) -> str:
    """Remove excessive whitespace, normalize unicode."""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_text(html: str, selector: str) -> list[str]:
    """Extract text from HTML using a CSS-like selector path."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for tag in soup.select(selector):
        t = sanitize(tag.get_text(separator=" ", strip=True))
        if t:
            results.append(t)
    return results


def extract_links(html: str, base_url: str, selector: str = "a[href]") -> list[dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select(selector):
        href = a.get("href", "")
        if href and not href.startswith("#"):
            full = urllib.parse.urljoin(base_url, href)
            text = sanitize(a.get_text(strip=True))
            links.append({"url": full, "text": text})
    return links


def save_raw(source_id: str, data: list[dict], filename: str | None = None) -> Path:
    """Save scraped data as JSON to raw/<source_id>/<filename>."""
    out_dir = RAW / source_id
    out_dir.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    out_path = out_dir / filename
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    log.info("Saved %d items → %s", len(data), out_path)
    return out_path


def load_raw(source_id: str) -> list[dict]:
    """Load all JSON files from raw/<source_id>/."""
    out_dir = RAW / source_id
    if not out_dir.exists():
        return []
    data = []
    for f in sorted(out_dir.glob("*.json")):
        data.extend(json.loads(f.read_text()))
    return data


def rate_limit(min_interval: float = 1.0):
    """Decorator: ensure minimum interval between calls."""
    last_call = [0.0]

    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    print(f"✅ Scraper framework loaded")
    print(f"   Raw data: {RAW}")
    print(f"   Cache:    {CACHE_DIR}")

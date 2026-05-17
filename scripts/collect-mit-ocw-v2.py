#!/usr/bin/env python3
"""MIT OCW 机械工程课程采集 v2 — 基于 sitemap 解析"""
import json, urllib.request, time, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse, unquote

OUTPUT = Path(__file__).parent.parent / "knowledge-base" / "mit-ocw-courses.json"
UA = "JixieBaikeBot/1.0"

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode()
        except Exception as e:
            if i < retries - 1:
                time.sleep(2 ** i)
            else:
                return None

# Step 1: Get main sitemap to find course listing
print("Fetching sitemap index...", file=sys.stderr)
sitemap = fetch("https://ocw.mit.edu/sitemap.xml")
if not sitemap:
    print("Failed to fetch sitemap", file=sys.stderr)
    sys.exit(1)

# Extract all course sitemap URLs
course_sitemaps = re.findall(r'https://ocw\.mit\.edu/courses/[^<]+/sitemap\.xml', sitemap)
print(f"Course sitemaps: {len(course_sitemaps)}", file=sys.stderr)

# Step 2: Filter for 2.xxx (Mechanical Engineering) and related course numbers
mech_patterns = [
    r'/2-\d{3}',       # 2.xxx Mechanical Engineering
    r'/3-\d{3}',       # 3.xxx Materials Science
]

filtered_sitemaps = [s for s in course_sitemaps if any(re.search(p, s) for p in mech_patterns)]
print(f"ME-related sitemaps: {len(filtered_sitemaps)}", file=sys.stderr)

# Step 3: Parse each sitemap to get course info
courses = []
seen_ids = set()
for i, sm_url in enumerate(filtered_sitemaps):
    sm_content = fetch(sm_url)
    if not sm_content:
        continue
    try:
        root = ET.fromstring(sm_content)
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = root.findall(".//ns:url/ns:loc", ns)
        if not urls:
            urls = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    except:
        urls = re.findall(r'<loc>(.*?)</loc>', sm_content)

    # First URL is the course page
    course_urls = [u if isinstance(u, str) else u.text for u in urls]
    if not course_urls:
        continue

    # Parse course info from URL
    course_path = urlparse(course_urls[0]).path
    # Extract course number and name from path
    # e.g., /courses/2-72-elements-of-mechanical-design-spring-2009/
    match = re.match(r'/courses/([\d-]+)-(.+?)(?:/|$)', course_path)
    if match:
        cid = match.group(1)  # 2-72
        slug = match.group(2)
        # Build title from slug
        title_words = slug.replace("-", " ").split()
        season_years = [w for w in title_words if w.lower() in ("spring", "fall", "summer", "january", "iap")]
        year_words = [w for w in title_words if re.match(r'^\d{4}$', w)]
        season = " ".join(season_years) if season_years else ""
        year = year_words[0] if year_words else ""

        title = " ".join(w for w in title_words
                        if w.lower() not in ("spring", "fall", "summer", "january", "iap")
                        and not re.match(r'^\d{4}$', w))
        title = title.title()

        if cid not in seen_ids:
            seen_ids.add(cid)
            courses.append({
                "course_id": f"{cid.replace('-', '.')}",
                "title": title,
                "url": f"https://ocw.mit.edu{course_path}",
                "slug": slug,
                "season": season,
                "year": year,
            })

    if i % 20 == 0:
        print(f"  [{i}/{len(filtered_sitemaps)}] parsed, {len(courses)} unique courses", file=sys.stderr)
    time.sleep(0.1)

# Step 4: Fetch page descriptions
print(f"\nFetching descriptions for {len(courses)} courses...", file=sys.stderr)
for i, c in enumerate(courses):
    page = fetch(c["url"])
    if page:
        # Try to extract meta description
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', page)
        if desc_match:
            c["description"] = desc_match.group(1)[:600]
        else:
            c["description"] = ""
        # Extract topics/keywords
        topic_match = re.search(r'<meta[^>]*name="keywords"[^>]*content="([^"]*)"', page)
        if topic_match:
            topics = [t.strip() for t in topic_match.group(1).split(",")]
            c["topics"] = topics[:10]
    if i % 10 == 0:
        print(f"  [{i}/{len(courses)}] descriptions fetched", file=sys.stderr)
    time.sleep(0.3)

# Sort by course number
courses.sort(key=lambda c: c["course_id"])

output = {
    "meta": {
        "source": "MIT OpenCourseWare",
        "source_url": "https://ocw.mit.edu/courses/mechanical-engineering/",
        "method": "sitemap parsing",
        "collected": "2026-05-18",
        "total": len(courses),
        "filter": "Mechanical Engineering (2.xxx) + Materials Science (3.xxx)"
    },
    "courses": courses,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
print(f"\n✅ MIT OCW: {len(courses)} 门课程，保存到 {OUTPUT}", file=sys.stderr)
for c in courses[:5]:
    print(f"  {c['course_id']} - {c['title']}", file=sys.stderr)
if len(courses) > 5:
    print(f"  ... 及另外 {len(courses)-5} 门", file=sys.stderr)

#!/usr/bin/env python3
"""MIT OpenCourseWare 机械工程课程采集"""
import json, urllib.request, urllib.parse, time, sys, re
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "knowledge-base" / "mit-ocw-courses.json"
API = "https://ocw.mit.edu/api/courses/"
USER_AGENT = "JixieBaikeBot/1.0"

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode()
        except Exception as e:
            if i < retries-1: time.sleep(2**i)
            else: print(f"  [FAIL] {e}", file=sys.stderr); return None

# Step 1: fetch course listing from API
print("Fetching MIT OCW course list...", file=sys.stderr)
data = fetch(API)
if not data:
    print("FAILED: could not fetch course list", file=sys.stderr)
    sys.exit(1)

courses_raw = json.loads(data)
print(f"Total courses from API: {len(courses_raw)}", file=sys.stderr)

# Step 2: filter to mechanical engineering courses
# MIT Mechanical Engineering course numbers: 2.xxx
mech_courses = []
for c in courses_raw:
    cid = c.get("id", "")
    title = c.get("title", "")
    # Filter by course number prefix 2.xxx (Mechanical Engineering)
    # Also include related: 3.xxx (Materials), 10.xxx (ChemE)
    is_mech = False
    if re.match(r'^2\.', cid):
        is_mech = True
    elif re.match(r'^3\.', cid):  # Materials Science
        is_mech = True
    elif any(kw in title.lower() for kw in ['mechanical', 'manufacturing', 'thermodynamics',
               'fluid mechanics', 'heat transfer', 'materials science', 'design',
               'robotics', 'automation', 'solid mechanics', 'dynamics']):
        is_mech = True

    if is_mech:
        mech_courses.append({
            "course_id": cid,
            "title": title,
            "url": f"https://ocw.mit.edu/courses/{cid}/",
            "description": (c.get("description", "") or "")[:500],
            "department": c.get("department", ""),
            "topics": c.get("topics", []),
            "levels": c.get("levels", []),
            "instructors": c.get("instructors", []),
        })

print(f"Mechanical engineering courses: {len(mech_courses)}", file=sys.stderr)

# Step 3: get details for each course
for i, course in enumerate(mech_courses):
    detail_url = f"{API}{course['course_id']}/"
    detail = fetch(detail_url)
    if detail:
        try:
            d = json.loads(detail)
            course["description"] = (d.get("description", "") or "")[:800]
            extra = d.get("extra_course_numbers", [])
            if extra: course["extra_numbers"] = extra
            feature_tags = d.get("feature_tags", [])
            if feature_tags: course["resource_types"] = feature_tags
        except: pass
    if i % 10 == 0:
        print(f"  [{i}/{len(mech_courses)}] detailed", file=sys.stderr)
    time.sleep(0.3)

# Output
output = {
    "meta": {
        "source": "MIT OpenCourseWare API",
        "url": API,
        "collected": "2026-05-18",
        "total": len(mech_courses),
        "filter": "Mechanical Engineering (course numbers 2.xxx) + related"
    },
    "courses": mech_courses,
    "course_numbers": sorted(set(c["course_id"] for c in mech_courses))
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
print(f"\n✅ MIT OCW: {len(mech_courses)} 门课程，保存到 {OUTPUT}", file=sys.stderr)
print(f"   课程编号: {', '.join(sorted(set(c['course_id'] for c in mech_courses))[:10])}...", file=sys.stderr)

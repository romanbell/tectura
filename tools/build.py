#!/usr/bin/env python3
"""
TECTURA build — merge research/batch-*.json, fetch images from Wikipedia,
download them to assets/img/, and generate js/data.js.

Idempotent: already-downloaded images are skipped, so it can be re-run
after fixing individual batches.

Usage: python3 tools/build.py [--skip-images]
"""

import glob
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(ROOT, "research")
IMG_DIR = os.path.join(ROOT, "assets", "img")
DATA_JS = os.path.join(ROOT, "js", "data.js")

API = "https://en.wikipedia.org/w/api.php"
UA = "TECTURA-local-index/1.0 (personal project; contact: romanbellisari@gmail.com)"
THUMB_WIDTH = 800


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "untitled"


def load_entries():
    entries = []
    seen = set()
    for path in sorted(glob.glob(os.path.join(RESEARCH, "batch-*.json"))):
        with open(path) as f:
            batch = json.load(f)
        for e in batch:
            if e["id"] in seen:
                print(f"  ! duplicate id {e['id']} in {os.path.basename(path)}, skipping")
                continue
            seen.add(e["id"])
            entries.append(e)
    entries.sort(key=lambda e: (e.get("born") or 9999, e["name"]))

    # curated corrections: replace wrong titles, null titles with no real article
    ov_path = os.path.join(RESEARCH, "title-overrides.json")
    if os.path.exists(ov_path):
        with open(ov_path) as f:
            ov = json.load(f)
        replace, nulled = ov.get("replace", {}), set(ov.get("null", []))
        fix = lambda t: None if t in nulled else replace.get(t, t)
        for e in entries:
            e["wikipedia"] = fix(e.get("wikipedia"))
            for p in e["projects"]:
                p["wikipedia"] = fix(p.get("wikipedia"))
    return entries


def api_get(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(8 * (attempt + 1))
                continue
            raise


def fetch_thumbs(titles):
    """title -> thumbnail URL (follows redirects/normalization)."""
    out = {}
    titles = [t for t in dict.fromkeys(titles) if t]
    for i in range(0, len(titles), 50):
        chunk = titles[i : i + 50]
        params = {
            "action": "query",
            "redirects": "1",
            "prop": "pageimages",
            "piprop": "thumbnail",
            "pilicense": "any",
            "pilimit": "max",
            "pithumbsize": str(THUMB_WIDTH),
            "titles": "|".join(chunk),
        }
        forward = {t: t for t in chunk}
        by_title = {}
        cont = {}
        while True:
            data = api_get({**params, **cont})
            q = data.get("query", {})
            # map requested title -> final title through normalization + redirects
            for step in ("normalized", "redirects"):
                for m in q.get(step, []):
                    for req_t, cur in list(forward.items()):
                        if cur == m["from"]:
                            forward[req_t] = m["to"]
            for p in q.get("pages", []):
                if "thumbnail" in p and p["title"] not in by_title:
                    by_title[p["title"]] = p
            if "continue" in data:
                cont = data["continue"]
                time.sleep(0.3)
            else:
                break
        for req_t, final_t in forward.items():
            page = by_title.get(final_t)
            if page:
                url = page["thumbnail"]["source"]
                # institution articles often use their LOGO as the page image —
                # reject those here so the media-list fallback finds a real photo
                if is_bad_file(urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])):
                    continue
                out[req_t] = url
        time.sleep(0.5)
    return out


BAD_FILE = re.compile(
    r"(?i)\b(logo|logotype|icon|icons|map|maps|flag|flags|coat of arms|stub|question|speaker|"
    r"padlock|wiki|commons|disambig|montage|collage|signature|wordmark|emblem|seal|crest|banner|7132)\b"
    r"|\.(svg|ogg|ogv|webm|tif|tiff|pdf|gif)(\.[a-z0-9]+)?$"
)


def is_bad_file(title):
    return bool(BAD_FILE.search(title.replace("_", " ")))


def rest_get(path):
    url = "https://en.wikipedia.org/api/rest_v1/" + path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(8 * (attempt + 1))
                continue
            return None
        except Exception:
            return None


def media_list_file(title):
    """Best image File: title for an article via the ordered media-list."""
    data = rest_get("page/media-list/" + urllib.parse.quote(title.replace(" ", "_"), safe=""))
    if not data:
        return None
    items = [i for i in data.get("items", [])
             if i.get("type") == "image" and i.get("title") and not is_bad_file(i["title"])]
    if not items:
        return None
    lead = [i for i in items if i.get("leadImage")]
    return (lead or items)[0]["title"]


def search_title(query):
    try:
        data = api_get({"action": "query", "list": "search", "srsearch": query, "srlimit": "1"})
        hits = data.get("query", {}).get("search", [])
        return hits[0]["title"] if hits else None
    except Exception:
        return None


def fallback_thumbs(misses):
    """title -> thumbnail URL via media-list (+ search rescue). Returns (map, substitutions)."""
    file_for = {}
    subs = []
    for t in misses:
        f = media_list_file(t)
        if not f:
            alt = search_title(t)
            if alt and alt != t:
                f = media_list_file(alt)
                if f:
                    subs.append((t, alt))
        if f:
            file_for[t] = f
        time.sleep(0.6)
    # resolve File: titles to scaled URLs in batches
    out = {}
    files = sorted(set(file_for.values()))
    url_for_file = {}
    for i in range(0, len(files), 50):
        chunk = files[i : i + 50]
        try:
            data = api_get({
                "action": "query",
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": str(THUMB_WIDTH),
                "titles": "|".join(chunk),
            })
            for p in data.get("query", {}).get("pages", []):
                ii = p.get("imageinfo")
                if ii:
                    url_for_file[p["title"]] = ii[0].get("thumburl") or ii[0].get("url")
        except Exception as e:
            print(f"  ! imageinfo batch failed: {e}")
        time.sleep(0.5)
    for t, f in file_for.items():
        # imageinfo normalizes underscores; try both forms
        u = url_for_file.get(f) or url_for_file.get(f.replace("_", " "))
        if u:
            out[t] = u
    return out, subs


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "cached"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        time.sleep(0.15)
        return "ok"
    except Exception as e:
        if os.path.exists(dest):
            os.remove(dest)
        print(f"  ! download failed {url}: {e}")
        return "fail"


def ext_for(url):
    path = urllib.parse.urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def main():
    skip_images = "--skip-images" in sys.argv
    entries = load_entries()
    print(f"Loaded {len(entries)} architects from {len(glob.glob(os.path.join(RESEARCH, 'batch-*.json')))} batches")

    # collect every wikipedia title we need an image for
    wanted = []
    for e in entries:
        wanted.append(e.get("wikipedia"))
        for p in e["projects"]:
            wanted.append(p.get("wikipedia"))

    thumbs = {}
    if not skip_images:
        print("Fetching thumbnail URLs from Wikipedia…")
        thumbs = fetch_thumbs(wanted)
        print(f"  {len(thumbs)} thumbnails found for {len([t for t in set(wanted) if t])} titles")
        misses = sorted(set(t for t in wanted if t and t not in thumbs))
        if misses:
            print(f"  {len(misses)} titles without pageimage — trying media-list fallback…")
            extra, subs = fallback_thumbs(misses)
            thumbs.update(extra)
            print(f"  fallback recovered {len(extra)}")
            still = sorted(set(t for t in wanted if t and t not in thumbs))
            with open(os.path.join(RESEARCH, "unresolved-titles.txt"), "w") as f:
                f.write("\n".join(still))
            with open(os.path.join(RESEARCH, "search-substitutions.txt"), "w") as f:
                f.write("\n".join(f"{a}  ->  {b}" for a, b in subs))
            print(f"  {len(still)} still unresolved; {len(subs)} search substitutions logged")

    os.makedirs(IMG_DIR, exist_ok=True)
    stats = {"portrait_ok": 0, "portrait_missing": 0, "img_ok": 0, "img_missing": 0}

    for e in entries:
        # portrait
        e["portrait"] = None
        t = e.get("wikipedia")
        if t and t in thumbs:
            dest_name = f"{e['id']}--portrait{ext_for(thumbs[t])}"
            if download(thumbs[t], os.path.join(IMG_DIR, dest_name)) != "fail":
                e["portrait"] = f"assets/img/{dest_name}"
        if e["portrait"]:
            stats["portrait_ok"] += 1
        else:
            stats["portrait_missing"] += 1
            print(f"  – no portrait: {e['name']}")
        if t:
            e["wikiUrl"] = "https://en.wikipedia.org/wiki/" + t.replace(" ", "_")

        # projects
        for p in e["projects"]:
            p["image"] = None
            pt = p.get("wikipedia")
            if pt and pt in thumbs:
                dest_name = f"{e['id']}--{slugify(p['title'])}{ext_for(thumbs[pt])}"
                if download(thumbs[pt], os.path.join(IMG_DIR, dest_name)) != "fail":
                    p["image"] = f"assets/img/{dest_name}"
            if pt:
                p["wikiUrl"] = "https://en.wikipedia.org/wiki/" + pt.replace(" ", "_")
            stats["img_ok" if p["image"] else "img_missing"] += 1
            p.pop("wikipedia", None)
        e.pop("wikipedia", None)

    header = (
        "/* ------------------------------------------------------------------\n"
        "   TECTURA — data (generated by tools/build.py — do not hand-edit;\n"
        "   edit research/batch-*.json and re-run the build instead)\n"
        f"   {len(entries)} architects, images via Wikipedia/Wikimedia (see wikiUrl\n"
        "   fields for sources). CSS renders all images grayscale.\n"
        "------------------------------------------------------------------ */\n\n"
    )
    with open(DATA_JS, "w") as f:
        f.write(header + "const ARCHITECTS = " + json.dumps(entries, ensure_ascii=False, indent=2) + ";\n")

    print(f"\nWrote js/data.js with {len(entries)} architects")
    print(f"Portraits: {stats['portrait_ok']} ok, {stats['portrait_missing']} missing (placeholder)")
    print(f"Project images: {stats['img_ok']} ok, {stats['img_missing']} missing (placeholder)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch the Laws of Bangladesh (http://bdlaws.minlaw.gov.bd) chronological index, the
full-text page (act-details-<id>.html) of every law not marked [Repealed], and its summary page
(act-<id>.html), which links schedules/appendices published as separate PDF files.

Pages are served as UTF-16; they are cached as-is under RAW (default ../../_raw/bd).
Output: RAW/index.json.
"""
import json, os, re, sys, time, html
import requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "http://bdlaws.minlaw.gov.bd"
RAW = os.environ.get("RAW", os.path.join(os.path.dirname(__file__), "..", "..", "_raw", "bd"))
DELAY = 1.0
S = requests.Session()
S.headers["User-Agent"] = UA


def decode(b):
    if b[:2] in (b"\xfe\xff", b"\xff\xfe"):
        return b.decode("utf-16")
    return b.decode("utf-8", "replace")


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return open(path, "rb").read()
    for attempt in range(6):
        try:
            r = S.get(url, timeout=180)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path + ".part", "wb") as f:
                f.write(r.content)
            os.replace(path + ".part", path)
            time.sleep(DELAY)
            return r.content
        except Exception as e:
            print("retry", attempt, url, e, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    return None


def clean(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("‌", "").replace("‍", "").split())


def main():
    s = decode(get(BASE + "/laws-of-bangladesh-chronological-index.html", f"{RAW}/index/chrono.html"))
    recs = []
    for r in re.findall(r"<tr>(.*?)</tr>", s, re.S):
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        links = re.findall(r'href="/act-(\d+)\.html"', r)
        if not links or len(cells) < 3:
            continue
        rep = "text-style-repealed" in r or "[Repealed]" in cells[0]
        recs.append({"id": int(links[0]), "title": cells[0], "number": cells[1], "year": cells[2], "repealed": rep})
    print(len(recs), "laws;", sum(r["repealed"] for r in recs), "repealed", file=sys.stderr)
    json.dump(recs, open(f"{RAW}/index.json", "w"), ensure_ascii=False, indent=1)
    todo = [r for r in recs if not r["repealed"]]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(3) as ex:
        for i, _ in enumerate(ex.map(lambda r: get(f"{BASE}/act-details-{r['id']}.html", f"{RAW}/act/{r['id']}.html"), todo)):
            if i % 50 == 0:
                print(i, len(todo), file=sys.stderr)
        # summary pages (table of contents) carry the links to schedule/appendix PDFs
        for i, _ in enumerate(ex.map(lambda r: get(f"{BASE}/act-{r['id']}.html", f"{RAW}/summary/{r['id']}.html"), todo)):
            if i % 50 == 0:
                print("summary", i, len(todo), file=sys.stderr)


if __name__ == "__main__":
    main()

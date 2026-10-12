#!/usr/bin/env python3
"""Convert cached bdlaws.minlaw.gov.bd act-details pages (see bd_fetch.py) into Markdown.

Usage: bd_convert.py [REPO_DIR]
"""
import json, os, re, sys, datetime, unicodedata, html
from bs4 import BeautifulSoup, NavigableString, Tag

RAW = os.environ.get("RAW", os.path.join(os.path.dirname(__file__), "..", "..", "_raw", "bd"))
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
RETRIEVED = os.environ.get("RETRIEVED", datetime.date.today().isoformat())
BASE = "http://bdlaws.minlaw.gov.bd"
BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
BN_MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
BN_MONTHS_ALT = {"জানুয়ারী": 1, "ফেব্রুয়ারী": 2, "আগষ্ট": 8, "অক্টোবর": 10, "জানুআরি": 1}


def decode(b):
    if b[:2] in (b"\xfe\xff", b"\xff\xfe"):
        return b.decode("utf-16")
    return b.decode("utf-8", "replace")


def slug(s, n=70):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    if len(s) > n:
        s = s[:n].rsplit("-", 1)[0]
    return s


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def norm(s):
    return " ".join(s.replace("‌", "").replace("‍", "").replace("\xa0", " ").split())


def parse_date(s):
    s = norm(s).strip("[] ").translate(BN_DIGITS)
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+),?\s+(\d{4})", s)
    mon = None
    if m and m.group(2).lower() in MONTHS:
        mon = MONTHS.index(m.group(2).lower()) + 1
    if not m or not mon:
        m = re.search(r"(\d{1,2})\s+(\S+?),?\s+(\d{4})", s)
        if m:
            w = m.group(2).rstrip(",")
            mon = BN_MONTHS.index(w) + 1 if w in BN_MONTHS else BN_MONTHS_ALT.get(w)
    if m and mon:
        try:
            return datetime.date(int(m.group(3)), mon, int(m.group(1))).isoformat()
        except ValueError:
            return None
    return None


def esc_md(s):
    s = s.replace("\\", "\\\\")
    s = re.sub(r"([*_`])", r"\\\1", s)
    return s


def inline(node):
    """text of an inline fragment with footnote markers as <sup>n</sup>"""
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(esc_md(str(c)))
        elif isinstance(c, Tag):
            cls = c.get("class") or []
            if c.name == "span" and "footnote" in cls:
                sup = c.find("sup")
                n = norm(sup.get_text()) if sup else ""
                out.append(f"<sup>{n}</sup>")
                continue
            if c.name == "sup":
                out.append(f"<sup>{norm(c.get_text())}</sup>")
                continue
            if c.name == "sub":
                out.append(f"<sub>{norm(c.get_text())}</sub>")
                continue
            if c.name == "br" or (c.name == "div" and ("clbr" in cls)):
                out.append("\n\n")
                continue
            if c.name == "div" and "na" in cls:
                continue
            if c.name == "table":
                out.append("\n\n" + table(c) + "\n\n")
                continue
            if c.name in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"):
                out.append("\n\n" + inline(c) + "\n\n")
                continue
            if c.name in ("b", "strong"):
                t = inline(c).strip()
                out.append(f"**{t}**" if t else "")
                continue
            if c.name in ("i", "em"):
                t = inline(c).strip()
                out.append(f"*{t}*" if t else "")
                continue
            if c.name in ("script", "style", "img"):
                continue
            out.append(inline(c))
    return "".join(out)


def table(t):
    rows = t.find_all("tr")
    simple = rows and all(not c.get("rowspan") and not c.get("colspan") for r in rows for c in r.find_all(["td", "th"]))
    if simple:
        data = [[norm(inline(c)).replace("|", "\\|") for c in r.find_all(["td", "th"], recursive=False)] for r in rows]
        data = [d for d in data if any(d)]
        if data:
            w = max(len(d) for d in data)
            data = [d + [""] * (w - len(d)) for d in data]
            lines = ["| " + " | ".join(data[0]) + " |", "|" + "---|" * w]
            lines += ["| " + " | ".join(d) + " |" for d in data[1:]]
            return "\n".join(lines)
    # complex: keep cleaned HTML
    for tag in t.find_all(True):
        for a in list(tag.attrs):
            if a not in ("rowspan", "colspan"):
                del tag[a]
    return re.sub(r"\s+", " ", str(t))


def paras(text):
    ps = [norm(p) for p in re.split(r"\n\s*\n", text)]
    out = []
    for p in ps:
        if not p:
            continue
        if p.startswith(("#", ">", "- ", "+ ")) or re.match(r"^\d+\.\s", p) and False:
            p = "\\" + p
        out.append(p)
    return out


def convert(path, rec):
    s = decode(open(path, "rb").read())
    soup = BeautifulSoup(s, "lxml")
    box = soup.find(class_="boxed-layout")
    if box is None:
        return None
    h3 = box.find("h3")
    title_md = norm(inline(h3)) if h3 else rec["title"]
    title_plain = norm(re.sub(r"<sup>.*?</sup>", "", title_md)).replace("\\", "")
    h4 = box.find("h4")
    ident = norm(h4.get_text()).strip("() ") if h4 else ""
    pd = box.find(class_="publish-date")
    date = parse_date(pd.get_text()) if pd else None
    lang = "bn" if re.search(r"[ঀ-৿]", title_plain) else "en"
    out = []
    role = box.find(class_="act-role-style")
    if role and norm(role.get_text()):
        out += [p for p in paras(inline(role))]
    pre = box.find(class_="pad-right")
    if pre:
        out += paras(inline(pre))
    nsec = 0
    for row in box.find_all(class_="lineremoves"):
        for g in row.find_all(class_=["act-part-group", "act-chapter-group"], recursive=True):
            kind = "part" if "act-part-group" in g["class"] else "chapter"
            no = g.find(class_=f"act-{kind}-no")
            nm = g.find(class_=f"act-{kind}-name")
            h = " — ".join(x for x in [norm(inline(no)) if no else "", norm(inline(nm)) if nm else ""] if x)
            if h:
                out.append(("## " if kind == "part" else "### ") + h)
        for sh in row.find_all(class_="act-section-head"):
            t = norm(inline(sh))
            if t:
                out.append(f"**{t}**")
        head = row.find(class_="txt-head")
        det = row.find(class_="txt-details")
        htxt = norm(inline(head)) if head else ""
        body = paras(inline(det)) if det else []
        if not htxt and not body:
            continue
        num = None
        if body:
            m = re.match(r"^(?:<sup>[^<]*</sup>\s*)?\[?\s*([0-9০-৯]+[A-Zক-হ]{0,3})\s*[\.।]", body[0])
            if m:
                num = m.group(1)
        if htxt or num:
            hd = (f"{num}. " if num and lang == "en" else (f"{num}। " if num else "")) + htxt
            out.append("#### " + hd.strip())
            nsec += 1
        out += body
    # footnotes
    fl = box.find(class_="footnoteListAll")
    notes = []
    if fl:
        for li in fl.find_all("li"):
            h6 = li.find("h6")
            n = norm(h6.get_text()) if h6 else ""
            if h6:
                h6.extract()
            notes.append((n, norm(inline(li))))
    md = []
    for blk in out:
        md.append(blk)
    body_md = "\n\n".join(md)
    if notes:
        body_md += "\n\n---\n\n" + ("## Footnotes" if lang == "en" else "## পাদটীকা") + "\n\n"
        body_md += "\n".join(f"- <sup>{n}</sup> {t}" for n, t in notes)
    return {"title": title_plain, "title_md": title_md, "identifier": ident, "date": date, "lang": lang,
            "body": body_md.strip() + "\n", "sections": nsec}


def law_type(ident, title, lang):
    t = (ident + " " + title).lower()
    if "constitution" in t or "সংবিধান" in t:
        return "constitution"
    if "ordinance" in t or "অধ্যাদেশ" in t:
        return "ordinance"
    if "regulation" in t:
        return "regulation"
    if re.search(r"\bp\.\s*o\.|president'?s order|order", t):
        return "order"
    return "act"


def main():
    idx = json.load(open(f"{RAW}/index.json"))
    stats = {"written": 0, "empty": [], "missing": [], "by_lang": {}, "by_type": {}}
    for rec in idx:
        if rec["repealed"]:
            continue
        p = f"{RAW}/act/{rec['id']}.html"
        if not os.path.exists(p):
            stats["missing"].append(rec["id"])
            continue
        d = convert(p, rec)
        if not d or len(d["body"]) < 50:
            stats["empty"].append(rec["id"])
            continue
        typ = law_type(d["identifier"], d["title"], d["lang"])
        year = (rec.get("year") or "").translate(BN_DIGITS)
        year = year if re.fullmatch(r"\d{4}", year) else (d["date"] or "0000")[:4]
        if typ == "constitution":
            rel = f"constitution/constitution-{d['lang']}.md"
        else:
            sl = slug(d["title"]) if d["lang"] == "en" else ""
            rel = f"laws/{year}/act-{rec['id']}{'-' + sl if sl else ''}.md"
        fm = ["---", f"title: {q(d['title'])}"]
        if d["identifier"]:
            fm.append(f"identifier: {q(d['identifier'])}")
        fm.append(f"bdlaws_id: {rec['id']}")
        fm += [f"type: {typ}", "jurisdiction: bd", f"language: {d['lang']}"]
        if d["date"]:
            fm.append(f"date: {d['date']}")
        fm.append("status: in_force")
        fm.append(f"source: {q(f'{BASE}/act-details-{rec[chr(105)+chr(100)]}.html')}")
        fm.append(f"retrieved: {RETRIEVED}")
        fm.append("---")
        md = "\n".join(fm) + "\n\n# " + d["title_md"] + "\n\n"
        if d["identifier"]:
            md += f"({d['identifier']})\n\n"
        md += d["body"]
        path = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        stats["written"] += 1
        stats["by_lang"][d["lang"]] = stats["by_lang"].get(d["lang"], 0) + 1
        stats["by_type"][typ] = stats["by_type"].get(typ, 0) + 1
    json.dump(stats, open(f"{RAW}/convert-stats.json", "w"), indent=1)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in stats.items()}))


if __name__ == "__main__":
    main()

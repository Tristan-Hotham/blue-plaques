"""Step 1. Parse the English Heritage (and predecessor) London blue plaques from the English Wikipedia lists.

Sources (CC BY-SA 4.0, wikitext retrieved 27 October 2026, in /home/claude/hist/_data10/wikipedia_blue_plaques.json.gz):
  List of English Heritage blue plaques in London (all boroughs except the three below, as {{Plaque table row}} templates)
  ... in the London Borough of Camden (a plain wikitable)
  ... in the Royal Borough of Kensington and Chelsea ({{Plaque table row}})
  ... in the City of Westminster ({{Plaque table row}})
Writes work/eh_raw.json: one record per plaque with borough, year, address, inscription, the raw subject
cell, the people linked in it (link target, display text, dates in order) and the Open Plaques plaque id.
Run: python3 01_eh_london.py
"""
import gzip, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = "/home/claude/hist/_data10/wikipedia_blue_plaques.json.gz"
W = json.load(gzip.open(SRC))
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)

LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
YEARS = re.compile(r"(?:c\.\s*|born\s*|b\.\s*)?(\d{3,4})\s*[–—−\-]\s*(?:c\.\s*)?(\d{2,4})|\(\s*(?:born|b\.)\s*(\d{4})\s*\)")


def strip_refs(s):
    s = re.sub(r"<ref[^>]*?/>", "", s, flags=re.S)
    s = re.sub(r"<ref.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    return s


def plain(s):
    s = strip_refs(s)
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = LINK.sub(lambda m: m.group(2) or m.group(1), s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", s).strip()


def split_top(s, sep="|"):
    """Split on sep at depth 0 of [[ ]] and {{ }}."""
    out, cur, i, d1, d2 = [], "", 0, 0, 0
    while i < len(s):
        two = s[i:i + 2]
        if two == "[[": d1 += 1; cur += two; i += 2; continue
        if two == "]]": d1 -= 1; cur += two; i += 2; continue
        if two == "{{": d2 += 1; cur += two; i += 2; continue
        if two == "}}": d2 -= 1; cur += two; i += 2; continue
        if s[i] == sep and d1 == 0 and d2 == 0:
            out.append(cur); cur = ""; i += 1; continue
        cur += s[i]; i += 1
    out.append(cur)
    return out


def templates(text, name="Plaque table row"):
    """Yield (start offset, body) of each {{name ...}} with balanced braces."""
    for m in re.finditer(r"\{\{\s*" + re.escape(name), text):
        i, depth = m.start(), 0
        while i < len(text):
            if text.startswith("{{", i): depth += 1; i += 2; continue
            if text.startswith("}}", i):
                depth -= 1; i += 2
                if depth == 0: break
                continue
            i += 1
        yield m.start(), text[m.end():i - 2]


def params(body):
    P = {}
    for part in split_top(body)[1:]:
        if "=" in part:
            k, v = part.split("=", 1); P[k.strip()] = v.strip()
    return P


def people_in(cell):
    """Linked people in a subject cell, in order, with their display text."""
    cell = strip_refs(cell)
    out = []
    for m in LINK.finditer(cell):
        tgt = m.group(1).strip()
        if tgt.lower().startswith(("file:", "image:", "category:")): continue
        out.append({"link": tgt, "display": plain(m.group(2) or tgt)})
    return out


def dates_in(s):
    s = plain(s)
    out = []
    for m in YEARS.finditer(s):
        if m.group(3):
            out.append((int(m.group(3)), None)); continue
        a, b = m.group(1), m.group(2)
        if len(b) == 2: b = a[:2] + b
        out.append((int(a), int(b)))
    return out


def year_of(s):
    m = re.search(r"\b(18[6-9]\d|19\d\d|20[0-2]\d)\b", plain(s))
    return int(m.group(1)) if m else None


rows = []
# 1. London article, by borough section
t = W["List of English Heritage blue plaques in London"]
secs = [(m.start(), m.group(1).strip()) for m in re.finditer(r"\n===\s*([^=\n]+?)\s*===", t)]


def section_at(pos):
    s = None
    for a, n in secs:
        if a < pos: s = n
    return s


def add_template_rows(text, borough_fn, article):
    for pos, body in templates(text):
        P = params(body)
        subj = P.get("subject", "")
        rows.append(dict(article=article, borough=borough_fn(pos), subject_raw=plain(subj), subject_wikitext=strip_refs(subj),
                         people=people_in(subj), dates=dates_in(P.get("subject_dates", "")) or dates_in(subj),
                         inscription=plain(P.get("inscription", "")), inscription_wikitext=strip_refs(P.get("inscription", "")),
                         address=plain(P.get("street_address", "")), town=plain(P.get("town", "")),
                         year=year_of(P.get("year", "")), year_raw=plain(P.get("year", "")),
                         open_plaques=re.sub(r"\D", "", P.get("open_plaques", "")) or None, notes=plain(P.get("notes", ""))))


add_template_rows(t, section_at, "List of English Heritage blue plaques in London")
add_template_rows(W["List of English Heritage blue plaques in the Royal Borough of Kensington and Chelsea"], lambda p: "Kensington and Chelsea",
                  "List of English Heritage blue plaques in the Royal Borough of Kensington and Chelsea")
add_template_rows(W["List of English Heritage blue plaques in the City of Westminster"], lambda p: "City of Westminster",
                  "List of English Heritage blue plaques in the City of Westminster")

# 2. Plain wikitables: the Camden list and several borough sections of the London list


def add_wikitables(text, borough_fn, article):
    for tm in re.finditer(r"\{\|", text):
        end = text.find("\n|}", tm.start())
        tab = text[tm.start():end]
        parts = tab.split("\n|-")
        head = " ".join(parts[:2]) if "!" in parts[0] or len(parts) < 2 else parts[0]
        hdr = [plain(h.split("|")[-1]).lower() for h in re.findall(r"^!([^\n]*)", tab, flags=re.M)]
        if not any("person" in h for h in hdr): continue
        col = {k: next((i for i, h in enumerate(hdr) if k in h), None) for k in ("person", "inscription", "address", "year", "notes")}
        for chunk in parts[1:]:
            chunk = chunk.strip("\n")
            if not chunk.strip() or chunk.lstrip().startswith("!"): continue
            cells = [x for x in re.split(r"\n\|(?![-}])", "\n" + chunk) if x.strip() != ""]
            flat = []
            for x in cells: flat += split_top(x.replace("||", "\u0001"), "\u0001")
            cells = [x.strip() for x in flat]
            g = lambda k: cells[col[k]] if col[k] is not None and col[k] < len(cells) else ""
            if len(cells) < 4: continue
            person = g("person")
            rows.append(dict(article=article, borough=borough_fn(tm.start()), subject_raw=plain(person), subject_wikitext=strip_refs(person),
                             people=people_in(person), dates=dates_in(person), inscription=plain(g("inscription")),
                             inscription_wikitext=strip_refs(g("inscription")), address=plain(g("address")), town="",
                             year=year_of(g("year")), year_raw=plain(g("year")), open_plaques=None, notes=plain(g("notes"))))


add_wikitables(t, section_at, "List of English Heritage blue plaques in London")
add_wikitables(W["List of English Heritage blue plaques in the London Borough of Camden"], lambda p: "Camden",
               "List of English Heritage blue plaques in the London Borough of Camden")

json.dump(rows, open(os.path.join(ROOT, "work", "eh_raw.json"), "w"), ensure_ascii=False, indent=0)
from collections import Counter
print(len(rows), "plaques"); print(Counter(r["borough"] for r in rows).most_common())
print("no year:", sum(r["year"] is None for r in rows), "no people link:", sum(not r["people"] for r in rows))

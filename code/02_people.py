"""Step 2. People: the Wikidata people with an Open Plaques subject ID, and the people on the English
Heritage London plaques (from step 1), matched to Wikidata where possible.

Inputs: /home/claude/hist/_data10/wd_osm_bundle10.json.gz (Wikidata CC0 via QLever, OSM ODbL), work/eh_raw.json.
Outputs:
  data/openplaques_people.csv  one row per Wikidata human with an Open Plaques subject ID (P1430)
  data/eh_london_plaques.csv   one row per English Heritage London plaque (Wikipedia lists)
  data/eh_london_people.csv    one row per person named on those plaques, with gender and its source
Gender comes from Wikidata (P21) where a person is matched; otherwise from a title in the subject cell
(Sir, Dame, Lord, Lady...); otherwise from the first name, using names that are at least 95% one gender
among at least three Wikidata Open Plaques people. Unresolved people stay unknown.
Occupation group: for plaques, the earliest occupation word in the inscription (what the plaque calls
the person); otherwise the Wikidata occupations, by a fixed priority order (see GROUPS).
Run: python3 02_people.py
"""
import gzip, io, json, os, re, unicodedata
from collections import Counter, defaultdict
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
B = json.load(gzip.open("/home/claude/hist/_data10/wd_osm_bundle10.json.gz"))
tsv = lambda k: pd.read_csv(io.StringIO(B[k]), sep="\t", dtype=str, keep_default_na=False, quoting=3)
qid = lambda s: s.rsplit("/", 1)[-1].rstrip(">") if s else ""
lab = lambda s: re.sub(r'^"(.*)"(@\w+)?$', r"\1", s) if s else ""


def yr(s):
    m = re.match(r'"?(-?\d{1,4})-\d\d-\d\d', s or "")
    return int(m.group(1)) if m else None


# ---------- occupation groups ----------
# order = priority when a Wikidata person has several occupations (broad labels like writer last)
GROUPS = [
    ("Sport", r"footballer|football player|cricketer|athlete|boxer|sportsman|sportsperson|tennis|rugby|jockey|swimmer|golfer|cyclist|rower|mountaineer|racing driver|olympic|sprinter|runner|wrestler|motorcycle racer|chess player"),
    ("Music", r"composer|musician|singer|conductor|pianist|violinist|organist|guitarist|songwriter|cellist|opera|bandleader|music hall|jazz|librettist|hymn writer|musicologist"),
    ("Stage and screen", r"actor|actress|comedian|dancer|ballerina|ballet|film director|film producer|theatre|entertainer|music-hall|clown|magician|puppeteer|broadcaster|television presenter|screenwriter|tragedian|impresario|film"),
    ("Art and design", r"painter|artist|sculptor|illustrator|architect(?! of)|designer|engraver|photographer|cartoonist|potter|printmaker|draftsperson|caricaturist|etcher|lithographer|craftsman|typographer|typefounder|landscape gardener|garden designer|furniture|dressmaker|silversmith|woodcarver|stained glass|art critic|art historian"),
    ("Science and medicine", r"scientist|physicist|chemist|biologist|botanist|naturalist|mathematician|astronomer|geologist|zoologist|physician|surgeon|doctor|nurse|pharmac|physiologist|anatomist|psychologist|psychoanalyst|neurologist|statistician|economist|anthropologist|archaeologist|egyptologist|crystallographer|geographer|ornithologist|entomologist|bacteriologist|pathologist|meteorologist|palaeontologist|paleontologist|aural surgeon|medical|scientific|horticulturist|philosopher|sociologist"),
    ("Engineering and invention", r"engineer|inventor|aviator|aircraft|pioneer of television|aviation|shipbuilder|locomotive|railway|telegraph|industrialist|manufacturer|car designer|aeronautical"),
    ("Military and exploration", r"admiral|general|field marshal|soldier|military|naval|navigator|explorer|commander|army officer|air marshal|resistance fighter|aircraft pilot|privateer|sailor|seafarer|agent"),
    ("Politics, law and public life", r"politician|prime minister|statesman|statesperson|member of parliament|diplomat|lawyer|barrister|judge|jurist|governor|viceroy|monarch|king|queen|emperor|president|civil servant|colonial administrator|ambassador|aristocrat|lord chancellor|foreign secretary|chancellor|solicitor|lord mayor|founder of the|trade unionist|local government"),
    ("Campaigners and reformers", r"reformer|campaigner|suffragist|suffragette|abolitionist|activist|philanthropist|social worker|feminist|pacifist|anti-slavery|revolutionary|nationalist|patriot|socialist|emancipat|educationist|educator"),
    ("Religion", r"priest|bishop|cleric|theologian|cardinal|preacher|minister of religion|missionary|divine|rabbi|evangelist|founder of methodism|nun|hymn"),
    ("Business", r"businessperson|entrepreneur|banker|merchant|publisher|retailer|bookseller|brewer|financier|shopkeeper|businessman|businesswoman|founder of .* stores|tea merchant"),
    ("Writing", r"writer|novelist|poet|author|dramatist|playwright|essayist|journalist|critic|diarist|editor|biographer|historian|man of letters|lexicographer|translator|humorist|satirist|scholar|antiquary|antiquarian|philologist|literary|children's"),
]
GRX = [(g, re.compile(r"\b(?:" + p + r")", re.I)) for g, p in GROUPS]


def group_from_occs(occs):
    for g, rx in GRX:
        if any(rx.search(o) for o in occs): return g
    return "Other" if occs else None


def group_from_text(t):
    best = None
    for g, rx in GRX:
        m = rx.search(t or "")
        if m and (best is None or m.start() < best[1]): best = (g, m.start())
    return best[0] if best else None


# ---------- Wikidata people ----------
p = tsv("wd_openplaques_people")
rec = {}
for r in p.itertuples(index=False):
    q = qid(r[0]); x = rec.setdefault(q, dict(qid=q, label=lab(r[1]), opids=set(), genders=set(), births=set(), deaths=set(), occs=set(), cit=set()))
    x["opids"].add(lab(r[2]))
    if r[4]: x["genders"].add(lab(r[4]))
    if yr(r[5]) is not None: x["births"].add(yr(r[5]))
    if yr(r[6]) is not None: x["deaths"].add(yr(r[6]))
    if r[7]: x["occs"].update(lab(r[7]).split("|"))
    if r[8]: x["cit"].add(qid(r[8]))
UK = {"Q145", "Q174193", "Q161885", "Q179876", "Q230791", "Q15179", "Q22", "Q21", "Q25", "Q26"}
WP = []
for x in rec.values():
    g = x["genders"]
    gender = "female" if g == {"female"} else "male" if g == {"male"} else ("other" if g and not g & {"male organism", "female organism"} else ("" if not g else "not human"))
    human = (gender in ("male", "female", "other")) or (bool(x["births"]) and gender != "not human")
    if not human: continue
    WP.append(dict(qid=x["qid"], label=x["label"], gender=gender or "unknown", birth=min(x["births"]) if x["births"] else None,
                   death=max(x["deaths"]) if x["deaths"] else None, occupations="|".join(sorted(x["occs"])),
                   group=group_from_occs(sorted(x["occs"])) or "Unknown", uk_citizen=bool(x["cit"] & UK),
                   openplaques_subject_ids="|".join(sorted(x["opids"]))))
WP = pd.DataFrame(WP).sort_values("qid")
WP["birth"] = WP["birth"].astype("Int64"); WP["death"] = WP["death"].astype("Int64")
WP.to_csv(os.path.join(ROOT, "data", "openplaques_people.csv"), index=False)
print("Wikidata Open Plaques items", len(rec), "humans", len(WP), WP.gender.value_counts().to_dict())


# ---------- first-name gender table from Wikidata people ----------
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^a-z ]+", " ", s).split()


TITLES_F = {"dame", "lady", "mrs", "miss", "queen", "princess", "baroness", "countess", "duchess", "marchioness", "viscountess", "madame", "mother", "sister"}
TITLES_M = {"sir", "lord", "earl", "duke", "viscount", "baron", "marquess", "marquis", "admiral", "general", "field", "marshal", "cardinal", "bishop",
            "king", "prince", "captain", "mr", "rev", "reverend", "father", "colonel", "major", "brigadier", "count"}
STRIP = TITLES_F | TITLES_M | {"dr", "the", "professor", "prof", "st", "saint", "rt", "hon", "right", "honourable", "first", "1st", "2nd", "3rd", "4th", "5th", "of", "ch", "cbe", "obe", "om", "kg"}
fn = defaultdict(Counter)
for r in WP.itertuples():
    if r.gender in ("male", "female"):
        t = [w for w in norm(r.label) if w not in STRIP]
        if len(t) >= 2: fn[t[0]][r.gender] += 1
FIRST = {n: c.most_common(1)[0][0] for n, c in fn.items() if sum(c.values()) >= 3 and c.most_common(1)[0][1] / sum(c.values()) >= 0.95 and len(n) > 1}
# second fallback: US Social Security baby names 1880 to 2009 (public domain), via github.com/hadley/data-baby-names,
# reduced to names at least 95% one sex (data/first_names_ssa.csv)
SSA = {n.lower(): g for n, g in pd.read_csv(os.path.join(ROOT, "data", "first_names_ssa.csv")).set_index("name")["gender"].items()}
print("first-name table", len(FIRST))

# ---------- index of Wikidata humans by normalised label ----------
IDX = defaultdict(list)
for r in WP.itertuples():
    IDX[" ".join(norm(r.label))].append(r)
WPi = WP.set_index("qid")

# plaque id -> subject QID, from OSM and Wikidata plaque items
op2q = defaultdict(set)
for k, ci, si in (("osm_openplaques_any", 2, 3), ("osm_plaques", 4, 3)):
    for r in tsv(k).itertuples(index=False):
        if r[ci] and r[si]:
            for o in lab(r[ci]).split(";"):
                for s in lab(r[si]).split(";"): op2q[o.strip()].add(s.strip())
for r in tsv("wd_plaques").itertuples(index=False):
    if r[4]: op2q[lab(r[2])].add(qid(r[4]))


def match(link, display, birth):
    keys = [" ".join(norm(link)), " ".join(w for w in norm(display) if w not in STRIP)]
    for k in keys:
        c = IDX.get(k, [])
        if birth is not None:
            c2 = [x for x in c if x.birth is not None and abs(int(x.birth) - birth) <= 1]
            if c2: c = c2
            elif c and all(x.birth is not None for x in c): c = []
        if len(c) == 1: return c[0].qid
    c = IDX.get(keys[0], [])
    if len(c) == 1 and keys[0].count(" ") >= 1: return c[0].qid  # unique full Wikipedia title: accept even if the listed dates disagree
    return None


# Hand-checked residue: people the automatic steps left unknown or got wrong, checked against the linked
# Wikipedia article title (all are well-known figures); and three linked "subjects" that are not people.
MANUAL = {"Camille Silvy": "male", "Laurie Cunningham": "male", "Sri Aurobindo": "male", "Dusé Mohamed Ali": "male", "Edvard Grieg": "male",
          "Aneurin Bevan": "male", "Krystyna Skarbek": "female", "Marion Dorn": "female", "P. L. Travers": "female", "Asquith Xavier": "male",
          "Ottobah Cugoano": "male", "Yehudi Menuhin": "male", "Wolfgang Amadeus Mozart": "male", "Mustafa Reşid Pasha": "male",
          "Lokamanya Tilak": "male", "Archibald Hill": "male", "A. E. Housman": "male", "V. K. Krishna Menon": "male", "Capability Brown": "male",
          "Ardaseer Cursetjee": "male", "Kamal Chunchie": "male", "Abdus Salam": "male", "Frederich Engels": "male", "Ernst Gombrich": "male",
          "László Moholy-Nagy": "male", "Noor Inayat Khan": "female", "Piet Cornelis Mondrian": "male", "Christopher R. W. Nevinson": "male",
          "A. J. P. Taylor": "male", "W. Heath Robinson": "male", "James Samuel Risien Russell": "male"}
# Four typos in the Wikipedia listings' dates, corrected from the people's own Wikipedia articles (checked 27 October 2026)
DATE_FIX = {"Asquith Xavier": (1920, 1980), "Diana Beck": (1900, 1956), "Agnes Garrett": (1845, 1935), "Hans Sloane": (1660, 1753)}
NOT_PEOPLE = {"SS Great Eastern", "Short Brothers", "Huxley family"}
INSTITUTION = re.compile(r"\bSS\b|prison|yard|observation|authority|county hall|embassy|society|club|league|theatre|hall|unit|school|company|works|studio|home|brotherhood|television|bbc|street|square|house|tree|conspiracy|strike|bomb|cross|china|church|chapel|hospital|college|institute|museum|gallery|embassy|foundry|bank|office|press|guild|association|union|committee|party|federation|mission|trust|fund|movement|terrace|adelphi|road|lane|place|garden|cinema|abbey|palace|railway|station", re.I)

raw = json.load(open(os.path.join(ROOT, "work", "eh_raw.json")))
plaques, people = [], []
for i, r in enumerate(raw):
    pid = f"EH{i + 1:04d}"
    ppl = list(r["people"])
    subj = r["subject_raw"]
    if not r["people"]:
        # people linked in the inscription instead (address-titled or unlinked rows)
        ins = r["inscription_wikitext"]
        ppl = [dict(link=m.group(1).strip(), display=re.sub(r"\s+", " ", (m.group(2) or m.group(1))).strip())
               for m in re.finditer(r"\[\[([^\]|#]+)(?:\|([^\]]*))?\]\]", ins)]
    elif re.match(r"^\d", subj):
        ins = r["inscription_wikitext"]
        ppl = [dict(link=m.group(1).strip(), display=(m.group(2) or m.group(1)).strip())
               for m in re.finditer(r"\[\[([^\]|#]+)(?:\|([^\]]*))?\]\]", ins)]
    dates = r["dates"]
    seen = set(); ppl = [x for x in ppl if not (x["link"] in seen or seen.add(x["link"]))]
    found = []
    opq = op2q.get(r["open_plaques"] or "", set())
    for j, x in enumerate(ppl):
        b = dates[j][0] if j < len(dates) else None
        q = match(x["link"], x["display"], b)
        src = "name match"
        if q is None and len(ppl) == 1 and len(opq) == 1 and list(opq)[0] in WPi.index:
            cand = WPi.loc[list(opq)[0]]
            sur = (norm(x["display"]) or [""])[-1]
            if sur and sur in norm(cand.label) and (b is None or pd.isna(cand.birth) or abs(int(cand.birth) - b) <= 1):
                q = list(opq)[0]; src = "Open Plaques plaque id"
        if q is None and (INSTITUTION.search(x["link"]) or x["link"] in NOT_PEOPLE): continue  # an institution, building or event, not a person
        if q is None and not b and not (set(norm(x["display"])) & (TITLES_F | TITLES_M)) and len(ppl) > 1 and not FIRST.get((norm(x["display"]) or [""])[0]):
            continue  # unlinked-looking non-person in a multi-link inscription
        found.append((x, q, b, j, src))
    # unlinked single person with dates
    if not found and dates and subj and not INSTITUTION.search(subj):
        found.append((dict(link="", display=subj), None, dates[0][0], 0, ""))
    kinds = []
    for x, q, b, j, src in found:
        disp = x["display"]
        w = WPi.loc[q] if q else None
        if w is not None and w.gender in ("male", "female"):
            g, gs = w.gender, "Wikidata"
        else:
            t = set(norm(re.split(r"\(", disp)[0])[:3])
            # titles are read from the subject cell text around the link too
            ctx = set(norm(r["subject_raw"])) if len(found) == 1 else t
            if (t | ctx) & TITLES_F and not (t & TITLES_M): g, gs = "female", "title"
            elif (t | ctx) & TITLES_M and not (t & TITLES_F): g, gs = "male", "title"
            else:
                first = [z for z in norm(disp) if z not in STRIP]
                g = FIRST.get(first[0]) if first else None
                gs = "first name (Wikidata)" if g else ""
                if not g and first and SSA.get(first[0]):
                    g, gs = SSA[first[0]], "first name (US baby names)"
                if not g and len(found) == 1 and re.search(r"\b(actress|ballerina|suffragette|vicereine|she|her|first woman|heroine|sculptress|authoress)\b", r["inscription"], re.I):
                    g, gs = "female", "inscription wording"
                g = g or "unknown"
        if x["link"] in MANUAL: g, gs = MANUAL[x["link"]], "hand-checked"
        wb = int(w.birth) if w is not None and pd.notna(w.birth) else None
        wd = int(w.death) if w is not None and pd.notna(w.death) else None
        lb = dates[j][0] if j < len(dates) else None
        ld = dates[j][1] if j < len(dates) else None
        # Wikidata dates where the person is matched (the listing's dates are paired with names by position); listing otherwise
        birth = wb if wb is not None else lb
        death = wd if wd is not None else ld
        if x["link"] in DATE_FIX: birth, death = DATE_FIX[x["link"]]
        grp_w = w.group if w is not None else None
        people.append(dict(plaque_id=pid, person=disp, wikipedia=x["link"], qid=q or "", match=src if q else "", gender=g, gender_source=gs,
                           birth=birth, death=death, year=r["year"], borough=r["borough"],
                           wikidata_group=grp_w if grp_w not in (None, "Unknown") else ""))
        kinds.append(g)
    grp = group_from_text(r["inscription"])
    plaques.append(dict(plaque_id=pid, borough=r["borough"], year=r["year"], subject=subj, inscription=r["inscription"],
                        address=(r["address"] + (", " + r["town"] if r["town"] else "")).strip(", "), open_plaques_id=r["open_plaques"] or "",
                        n_people=len(found), women=kinds.count("female"), men=kinds.count("male"), unknown=kinds.count("unknown"),
                        inscription_group=grp or "", source_article=r["article"]))
P = pd.DataFrame(plaques); Q = pd.DataFrame(people)
# a person's group: plaque inscription if it names one, else Wikidata
P_g = P.set_index("plaque_id")["inscription_group"]
Q["group"] = [P_g[a] or b or "Unknown" for a, b in zip(Q.plaque_id, Q.wikidata_group)]
for c in ("birth", "death", "year"): Q[c] = Q[c].astype("Int64")
P["year"] = P["year"].astype("Int64")
P.to_csv(os.path.join(ROOT, "data", "eh_london_plaques.csv"), index=False)
Q.to_csv(os.path.join(ROOT, "data", "eh_london_people.csv"), index=False)
print(len(P), "plaques;", len(Q), "people;", Q.gender.value_counts().to_dict(), Q.gender_source.value_counts().to_dict())
print("matched to Wikidata", (Q.qid != "").sum(), "plaques with no person", (P.n_people == 0).sum())
print(Q.group.value_counts().to_dict())

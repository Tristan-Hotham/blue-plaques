"""Step 4. Every number used in the page, paper, blog and collage, written to data/results.json,
plus the compact page data (data/page_data.json).
Run: python3 04_analyse.py
"""
import gzip, io, json, os, re
from collections import Counter
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
DD = os.path.join(ROOT, "data")
P = pd.read_csv(os.path.join(DD, "eh_london_plaques.csv"))
Q = pd.read_csv(os.path.join(DD, "eh_london_people.csv"))
WP = pd.read_csv(os.path.join(DD, "openplaques_people.csv"))
O = pd.read_csv(os.path.join(DD, "uk_plaques_osm.csv"), keep_default_na=False)
PL = pd.read_csv(os.path.join(DD, "places_plaques.csv"))
MP = pd.read_csv(os.path.join(DD, "multi_plaque_people.csv"))
R = {}
GROUPS = ["Writing", "Art and design", "Science and medicine", "Politics, law and public life", "Campaigners and reformers", "Stage and screen",
          "Music", "Military and exploration", "Engineering and invention", "Sport", "Business", "Religion"]
R["groups"] = GROUPS
ERAS = [("soa", "Society of Arts", 1866, 1900), ("lcc", "London County Council", 1901, 1964), ("glc", "Greater London Council", 1965, 1985),
        ("eh", "English Heritage", 1986, 2026)]


def share(s, v="female"):
    s = s[s.isin(["male", "female"])]
    return float((s == v).mean()) if len(s) else None


# ---------------- English Heritage London ----------------
Qp = Q[Q.gender.isin(["male", "female"])]
eh = dict(plaques=len(P), plaques_with_year=int(P.year.notna().sum()), plaques_no_person=int((P.n_people == 0).sum()),
          plaques_with_person=int((P.n_people > 0).sum()), people=len(Q), people_gender_known=len(Qp), women=int((Qp.gender == "female").sum()),
          men=int((Qp.gender == "male").sum()), share_women=share(Q.gender), wikidata_matched=int((Q.qid.fillna("") != "").sum()),
          gender_sources={k: int(v) for k, v in Q.gender_source.fillna("unknown").replace("", "unknown").value_counts().items()},
          boroughs=int(P.borough.nunique()), year_min=int(P.year.min()), year_max=int(P.year.max()),
          wikipedia_stated_total=1018)
eh["matched_share"] = eh["wikidata_matched"] / eh["people"]
eh["plaques_with_woman"] = int((P.women > 0).sum()); eh["plaques_with_woman_share"] = eh["plaques_with_woman"] / eh["plaques_with_person"]
big3 = P.borough.isin(["City of Westminster", "Kensington and Chelsea", "Camden"])
eh["big3"] = int(big3.sum()); eh["big3_share"] = float(big3.mean())
eh["by_borough"] = {k: int(v) for k, v in P.borough.value_counts().items()}
for b in ["City of Westminster", "Kensington and Chelsea", "Camden"]:
    eh["n_" + b.split()[-1].lower()] = int((P.borough == b).sum())
# by decade of erection
Qy = Q[Q.year.notna()].copy(); Qy["decade"] = (Qy.year // 10 * 10).astype(int)
dec = []
for d, g in Qy.groupby("decade"):
    gg = g[g.gender.isin(["male", "female"])]
    dec.append(dict(decade=int(d), plaques=int(P[(P.year // 10 * 10) == d].shape[0]), people=len(gg), women=int((gg.gender == "female").sum()),
                    share=float((gg.gender == "female").mean()) if len(gg) else None,
                    groups={k: int(v) for k, v in g.group.value_counts().items()}))
eh["by_decade"] = dec
R_dec = {x["decade"]: x for x in dec}
eh["share_1860s_1890s"] = share(Qy[Qy.decade < 1900].gender)
eh["share_2010s"] = R_dec[2010]["share"]; eh["share_2020s"] = R_dec[2020]["share"]
eh["women_2020s"] = R_dec[2020]["women"]; eh["people_2020s"] = R_dec[2020]["people"]
eh["women_2010s"] = R_dec[2010]["women"]; eh["people_2010s"] = R_dec[2010]["people"]
eh["share_pre2000"] = share(Qy[Qy.year < 2000].gender); eh["share_2000on"] = share(Qy[Qy.year >= 2000].gender)
eh["share_since2016"] = share(Qy[Qy.year >= 2016].gender)
eh["women_since2016"] = int(((Qy.year >= 2016) & (Qy.gender == "female")).sum()); eh["people_since2016"] = int(((Qy.year >= 2016) & Qy.gender.isin(["male", "female"])).sum())
eh["low_decade"] = min((x for x in dec if x["people"] >= 30), key=lambda x: x["share"])
eh["high_decade"] = max((x for x in dec if x["people"] >= 30), key=lambda x: x["share"])
# eras
er = {}
for k, nm, a, b in ERAS:
    g = Qy[(Qy.year >= a) & (Qy.year <= b)]; gp = P[(P.year >= a) & (P.year <= b)]
    gap = (g.year - g.death).dropna()
    gs = g.group.value_counts(normalize=True)
    er[k] = dict(name=nm, start=a, end=b, plaques=len(gp), people=int(g.gender.isin(["male", "female"]).sum()), share_women=share(g.gender),
                 women=int((g.gender == "female").sum()), median_gap=float(gap.median()) if len(gap) else None,
                 groups={x: float(gs.get(x, 0)) for x in GROUPS + ["Other", "Unknown"]})
eh["eras"] = er
# first women
fw = Qy[Qy.gender == "female"].sort_values("year")
eh["first_women"] = [dict(person=r.person, year=int(r.year), borough=r.borough) for r in fw.head(5).itertuples()]
# groups overall and women's share within groups
gg = Q.group.value_counts()
eh["groups_overall"] = {k: int(gg.get(k, 0)) for k in GROUPS + ["Other", "Unknown"]}
eh["group_share_women"] = {k: share(Q[Q.group == k].gender) for k in GROUPS}
eh["writing_share"] = gg.get("Writing", 0) / len(Q); eh["art_share"] = gg.get("Art and design", 0) / len(Q)
eh["sport_n"] = int(gg.get("Sport", 0)); eh["sport_first_year"] = int(Q[Q.group == "Sport"].year.min())
# birth and death
Qb = Q[Q.birth.notna()]
ob = Qb.sort_values("birth").iloc[0]; yb = Qb.sort_values("birth").iloc[-1]
eh["oldest_born"] = dict(person=ob.person, birth=int(ob.birth), year=int(ob.year) if pd.notna(ob.year) else None, borough=ob.borough)
eh["oldest_born_5"] = [dict(person=r.person, birth=int(r.birth)) for r in Qb.sort_values("birth").head(5).itertuples()]
eh["youngest_born"] = dict(person=yb.person, birth=int(yb.birth), year=int(yb.year) if pd.notna(yb.year) else None)
eh["youngest_born_5"] = [dict(person=r.person, birth=int(r.birth), year=int(r.year) if pd.notna(r.year) else None) for r in Qb.sort_values("birth").tail(5).itertuples()]
single = Q[Q.plaque_id.isin(P[P.n_people == 1].plaque_id) & Q.birth.notna()].sort_values("birth")
eh["oldest_born_single"] = [dict(person=r.person, birth=int(r.birth), year=int(r.year) if pd.notna(r.year) else None, borough=r.borough) for r in single.head(5).itertuples()]
ep = P[P.year.notna()].sort_values("year").iloc[0]
eh["earliest_plaque"] = dict(subject=ep.subject, year=int(ep.year), borough=ep.borough)
Qb2 = Qb.copy(); Qb2["cent"] = (Qb2.birth // 100 * 100).astype(int)
eh["by_birth_century"] = [dict(century=int(c), people=int(g.gender.isin(["male", "female"]).sum()), share=share(g.gender)) for c, g in Qb2.groupby("cent") if len(g) >= 5]
gap = (Qy.year - Qy.death).dropna(); gap = gap[gap >= 0]
eh["median_gap_all"] = float(gap.median())
# people on several EH plaques
key = Q.qid.fillna("").where(Q.qid.fillna("") != "", Q.wikipedia.fillna(""))
kc = key[key != ""].value_counts()
eh["people_multi"] = int((kc > 1).sum())
eh["people_multi_list"] = [dict(person=Q[key == k].person.iloc[0], n=int(v)) for k, v in kc[kc > 1].items()][:12]
R["eh"] = eh

# ---------------- Wikidata people with an Open Plaques subject ID ----------------
WPg = WP[WP.gender.isin(["male", "female"])]
op = dict(items=6271, humans=len(WP), gender_known=len(WPg), women=int((WPg.gender == "female").sum()), men=int((WPg.gender == "male").sum()),
          share_women=share(WP.gender), uk_citizens=int(WP.uk_citizen.sum()), share_women_uk=share(WP[WP.uk_citizen].gender),
          with_birth=int(WP.birth.notna().sum()))
Wb = WP[WP.birth.notna()].copy(); Wb["cent"] = (Wb.birth // 100 * 100).astype(int)
op["by_birth_century"] = [dict(century=int(c), people=int(g.gender.isin(["male", "female"]).sum()), women=int((g.gender == "female").sum()), share=share(g.gender),
                               groups={k: float(v) for k, v in g.group.value_counts(normalize=True).items()})
                          for c, g in Wb.groupby("cent") if c >= 1500]
op["born_before_1500"] = int((Wb.birth < 1500).sum())
o5 = Wb.sort_values("birth").head(8)
op["oldest_born"] = [dict(label=r.label, birth=int(r.birth), group=r.group) for r in o5.itertuples()]
y5 = Wb.sort_values("birth").tail(8)
op["youngest_born"] = [dict(label=r.label, birth=int(r.birth), death=int(r.death) if pd.notna(r.death) else None, group=r.group) for r in y5.itertuples()]
op["alive"] = int(WP.death.isna().sum() - 0)
gw = WP.group.value_counts()
op["groups_overall"] = {k: int(gw.get(k, 0)) for k in GROUPS + ["Other", "Unknown"]}
op["group_share_women"] = {k: share(WP[WP.group == k].gender) for k in GROUPS}
c19 = next(x for x in op["by_birth_century"] if x["century"] == 1800); c20 = next(x for x in op["by_birth_century"] if x["century"] == 1900)
op["share_born_1800s"] = c19["share"]; op["share_born_1900s"] = c20["share"]
c17 = next(x for x in op["by_birth_century"] if x["century"] == 1700); op["share_born_1700s"] = c17["share"]
W20 = Wb[Wb.birth >= 1900]
op["share_born_1950on"] = share(Wb[Wb.birth >= 1950].gender); op["n_born_1950on"] = int(Wb[Wb.birth >= 1950].gender.isin(["male", "female"]).sum())
R["openplaques"] = op

# ---------------- OSM: where ----------------
osm = dict(objects=len(O), memorial_plaque=int((O.memorial_plaque == "True").sum() if O.memorial_plaque.dtype == object else O.memorial_plaque.sum()),
           openplaques_linked=int((O.openplaques_linked == "True").sum() if O.openplaques_linked.dtype == object else O.openplaques_linked.sum()),
           subject_linked=int((O.subject_qid != "").sum()), person_linked=int(O.person_gender.isin(["male", "female"]).sum()))
reg = PL[PL.kind == "region"].set_index("place")
osm["regions"] = {k: dict(plaques=int(r.plaques), pop=None if pd.isna(r.population_2021) else int(r.population_2021),
                          per_100k=None if pd.isna(r.per_100k) else float(r.per_100k)) for k, r in reg.iterrows()}
lon = reg.loc["London"]
osm["london"] = int(lon.plaques); osm["london_share"] = lon.plaques / len(O)
ewreg = reg[reg.population_2021.notna()]
rest = ewreg.drop("London")
osm["ew_pop"] = int(ewreg.population_2021.sum()); osm["london_pop_share"] = lon.population_2021 / osm["ew_pop"]
osm["london_per_100k"] = float(lon.per_100k); osm["rest_ew_per_100k"] = float(rest.plaques.sum() / rest.population_2021.sum() * 1e5)
osm["london_ratio"] = osm["london_per_100k"] / osm["rest_ew_per_100k"]
osm["london_share_of_ew"] = lon.plaques / ewreg.plaques.sum()
osm["london_linked_per_100k"] = float(lon.linked_per_100k); osm["rest_linked_per_100k"] = float(rest.openplaques_linked.sum() / rest.population_2021.sum() * 1e5)
osm["scotland"] = int(reg.loc["Scotland"].plaques); osm["ni"] = int(reg.loc["Northern Ireland"].plaques)
bu = PL[(PL.kind == "built-up area") & (PL.place != "Greater London")].sort_values("per_100k", ascending=False)
osm["n_big_bua"] = int(len(bu) + 1)
osm["top_bua"] = [dict(place=re.sub(r" \(.*\)$", "", r.place), plaques=int(r.plaques), pop=int(r.population_2021), per_100k=float(r.per_100k),
                       linked=int(r.openplaques_linked)) for r in bu.head(12).itertuples()]
osm["bottom_bua"] = [dict(place=re.sub(r" \(.*\)$", "", r.place), plaques=int(r.plaques), pop=int(r.population_2021), per_100k=float(r.per_100k))
                     for r in bu[bu.population_2021 >= 250000].tail(6).itertuples()]
osm["london_rank_bua"] = int((bu.per_100k > lon.per_100k).sum() + 1)
for nm in ["Manchester", "Birmingham", "Liverpool", "Leeds", "Bristol", "Sheffield", "Brighton and Hove", "York", "Oxford", "Cheltenham"]:
    r = bu[bu.place == nm]
    if len(r): osm["bua_" + nm.split()[0].lower()] = dict(plaques=int(r.plaques.iloc[0]), pop=int(r.population_2021.iloc[0]), per_100k=float(r.per_100k.iloc[0]),
                                                          linked=int(r.openplaques_linked.iloc[0]))
# people on OSM plaques: women London vs rest
Op = O[O.person_gender.isin(["male", "female"])]
osm["person_women_share"] = share(Op.person_gender)
osm["person_women_london"] = share(Op[Op.region == "London"].person_gender); osm["person_n_london"] = int((Op.region == "London").sum())
osm["person_women_rest"] = share(Op[Op.region != "London"].person_gender); osm["person_n_rest"] = int((Op.region != "London").sum())
lg = Op[Op.region == "London"].person_group.value_counts(normalize=True); rg = Op[Op.region != "London"].person_group.value_counts(normalize=True)
osm["groups_london"] = {k: float(lg.get(k, 0)) for k in GROUPS}; osm["groups_rest"] = {k: float(rg.get(k, 0)) for k in GROUPS}
# colours
Oc = O[O.colour_family != ""]
osm["colour_tagged"] = len(Oc); osm["colour_tagged_share"] = len(Oc) / len(O)
osm["colours"] = {k: int(v) for k, v in Oc.colour_family.value_counts().items()}
osm["blue_share_tagged"] = osm["colours"].get("blue", 0) / len(Oc)
cp = []
for pl, g in Oc.groupby(Oc.bua.where(Oc.bua != "", Oc.region)):
    if len(g) >= 12:
        cp.append(dict(place=re.sub(r" \(.*\)$", "", pl), n=len(g), colours={k: int(v) for k, v in g.colour_family.value_counts().items()}))
osm["colour_places"] = sorted(cp, key=lambda x: -x["n"])
# several plaques
osm["multi_people"] = int((MP.n > 1).sum()); osm["multi_people_3plus"] = int((MP.n >= 3).sum())
osm["multi_top"] = [dict(label=r.label, n=int(r.n), places=r.places if isinstance(r.places, str) else "") for r in MP.head(10).itertuples()]
R["osm"] = osm

# ---------------- extra context ----------------
R["context"] = dict(scheme_start=1866, first_plaque=1867, first_woman_wikipedia="Sarah Siddons", first_woman_year_wikipedia=1876, rule_years_dead=20,
                    retrieved="27 October 2026")


def dash(s):
    """Visible text rule: no en or em dashes or double hyphens; year ranges become 'to'."""
    s = re.sub(r"(\d)\s*[\u2013\u2014]\s*(\d)", r"\1 to \2", s)
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    while "--" in s: s = s.replace("--", "-")
    return s


def clean(o):
    if isinstance(o, str): return dash(o)
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return None if np.isnan(o) else round(float(o), 6)
    if isinstance(o, (np.bool_,)): return bool(o)
    return o


R = clean(R)
json.dump(R, open(os.path.join(DD, "results.json"), "w"), indent=1, ensure_ascii=False)

# ---------------- page data ----------------
gi = {g: i for i, g in enumerate(GROUPS + ["Other", "Unknown"])}
pts = []
for r in O.itertuples():
    nm = r.person_label or r.name or (r.inscription[:60] + ("..." if len(r.inscription) > 60 else ""))
    pts.append([round(r.lat, 4), round(r.lon, 4), nm, {"female": 1, "male": 2}.get(r.person_gender, 0), r.colour_family, 1 if r.openplaques_linked in (True, "True") else 0,
                gi.get(r.person_group, -1)])
ehp = []
Pi = P.set_index("plaque_id")
for pid, g in Q.groupby("plaque_id"):
    p = Pi.loc[pid]
    ehp.append([g.person.iloc[0] if len(g) == 1 else " and ".join(g.person.astype(str))[:90], None if pd.isna(p.year) else int(p.year), p.borough,
                "f" if (g.gender == "female").all() else ("m" if (g.gender == "male").all() else "x"), gi.get(g.group.iloc[0], -1),
                str(p.inscription)[:120], str(p.address)[:80],
                None if pd.isna(g.birth.iloc[0]) else int(g.birth.iloc[0]), None if pd.isna(g.death.iloc[0]) else int(g.death.iloc[0])])
json.dump(clean(dict(pts=pts, eh=ehp)), open(os.path.join(DD, "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(json.dumps({k: R["eh"][k] for k in ["plaques", "people", "women", "share_women", "share_2010s", "share_2020s", "share_pre2000", "share_since2016", "median_gap_all", "big3_share", "people_multi"]}, indent=0))
print([(x["decade"], x["people"], round(x["share"], 3)) for x in R["eh"]["by_decade"]])
print({k: (v["plaques"], v["share_women"], v["median_gap"]) for k, v in R["eh"]["eras"].items()})
print(R["eh"]["first_women"], R["eh"]["oldest_born_5"], R["eh"]["youngest_born_5"])
print({k: R["openplaques"][k] for k in ["humans", "share_women", "share_women_uk", "share_born_1800s", "share_born_1900s", "share_born_1950on"]})
print(R["openplaques"]["oldest_born"], R["openplaques"]["youngest_born"])
print({k: R["osm"][k] for k in ["objects", "london", "london_share", "london_pop_share", "london_per_100k", "rest_ew_per_100k", "london_ratio", "person_women_london", "person_women_rest", "london_rank_bua", "colour_tagged", "blue_share_tagged", "multi_people"]})
print(R["osm"]["colour_places"])

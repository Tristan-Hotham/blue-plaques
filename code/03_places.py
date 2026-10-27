"""Step 3. Where the plaques are: OpenStreetMap plaques in the UK, placed in regions and built-up areas,
with colours and the people they name.

Inputs (read in place):
  /home/claude/hist/_data10/wd_osm_bundle10.json.gz: osm_plaques (memorial=plaque inside the UK), osm_openplaques_any
     (objects tagged openplaques:id inside the UK), wd_plaques (Wikidata items with an Open Plaques plaque ID)
  /home/claude/hist/_data8/ons_geo.json (MSOA 2021 population-weighted centroids, MSOA to BUA 2022 lookup, BUA 2022 GB)
  /home/claude/hist/_data8/lsoa21_bua22_lookup.json and census/census2021-ts001-{lsoa,rgn,ctry}.csv
  data/openplaques_people.csv (step 2)
Outputs: data/uk_plaques_osm.csv, data/places_plaques.csv, data/multi_plaque_people.csv, work/places.json
Run: python3 03_places.py
"""
import gzip, io, json, os, re
from collections import Counter
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
D8 = "/home/claude/hist/_data8"
B = json.load(gzip.open("/home/claude/hist/_data10/wd_osm_bundle10.json.gz"))
tsv = lambda k: pd.read_csv(io.StringIO(B[k]), sep="\t", dtype=str, keep_default_na=False, quoting=3)
lab = lambda s: re.sub(r'^"(.*)"(@\w+)?$', r"\1", s) if s else ""
qid = lambda s: s.rsplit("/", 1)[-1].rstrip(">") if s else ""

# ---- OSM objects: union of memorial=plaque and openplaques:id ----
a = tsv("osm_plaques"); b = tsv("osm_openplaques_any")
rows = {}
for r in a.itertuples(index=False):
    rows[r[0]] = dict(osm=r[0].strip("<>"), name=lab(r[1]), inscription=lab(r[2]).replace("\\n", " "), subject_qid=lab(r[3]), openplaques_id=lab(r[4]),
                      colour=lab(r[5]).lower(), wkt=r[6], memorial_plaque=True)
for r in b.itertuples(index=False):
    x = rows.setdefault(r[0], dict(osm=r[0].strip("<>"), name=lab(r[1]), inscription="", subject_qid="", openplaques_id="", colour="", wkt=r[5], memorial_plaque=False))
    x["openplaques_id"] = x["openplaques_id"] or lab(r[2]); x["subject_qid"] = x["subject_qid"] or lab(r[3]); x["colour"] = x["colour"] or lab(r[4]).lower()
O = pd.DataFrame(rows.values())


def pt(w):
    m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", w)
    if m: return float(m.group(1)), float(m.group(2))
    nums = [float(v) for v in re.findall(r"-?\d+\.\d+", w)]
    if not nums: return np.nan, np.nan
    return float(np.mean(nums[0::2])), float(np.mean(nums[1::2]))


O["lon"], O["lat"] = zip(*O.wkt.map(pt))
O = O.dropna(subset=["lon"]).drop(columns="wkt")


# colour: named colours as tagged; hex codes to the nearest of a few named families
def colour_family(c):
    c = c.split(";")[0].strip()
    if not c: return ""
    if c.startswith("#") and len(c) == 7:
        r, g, bb = (int(c[i:i + 2], 16) for i in (1, 3, 5))
        if bb > r + 40 and bb > g: return "blue"
        if g >= r and g >= bb and max(r, g, bb) - min(r, g, bb) > 25: return "green"
        if max(r, g, bb) > 225 and min(r, g, bb) > 215: return "white"
        if max(r, g, bb) < 70: return "black"
        return "other"
    for k, v in {"lightblue": "blue", "blue": "blue", "seagreen": "green", "darkgreen": "green", "green": "green", "black": "black", "grey": "grey",
                 "gray": "grey", "silver": "grey", "red": "red", "maroon": "red", "brown": "brown", "white": "white", "cream": "white", "gold": "other"}.items():
        if k in c: return v
    return "other"


O["colour_family"] = O.colour.map(colour_family)

# ---- place each object: England and Wales by nearest MSOA population-weighted centroid ----
G = json.load(open(os.path.join(D8, "ons_geo.json")))
ms = pd.DataFrame(G["msoa21_pwc"]); lk = pd.DataFrame(G["msoa21_bua22_lookup"]).set_index("MSOA21CD")
ms = ms.join(lk[["BUA22CD", "BUA22NM", "LAD22NM", "RGN22NM"]], on="MSOA21CD")
K = np.cos(np.radians(54))
tree = cKDTree(np.c_[ms._x * K, ms._y])
dist, idx = tree.query(np.c_[O.lon * K, O.lat])
O["dist_km"] = dist * 111.2
near = ms.iloc[idx].reset_index(drop=True)
bua = pd.DataFrame(G["bua22_gb"])
sc = bua[bua.BUA22CD.str.startswith("S")]
st = cKDTree(np.c_[sc.LONG * K, sc.LAT])
d2, i2 = st.query(np.c_[O.lon * K, O.lat])
ni = ((O.lon < -5.45) & (O.lat < 55.35) & (O.lat > 53.9)).values
# England and Wales: nearest MSOA centroid within 15 km and nearer than any Scottish built-up area
ew = (O.dist_km.values < 15) & (O.dist_km.values <= d2 * 111.2) & ~ni
O["region"] = np.where(ew, near.RGN22NM.fillna("").values, "")
O.loc[ew & near.MSOA21CD.str.startswith("W").values, "region"] = "Wales"
O["bua"] = np.where(ew & (O.dist_km.values < 4), near.BUA22NM.fillna("").values, "")
O["lad"] = np.where(ew, near.LAD22NM.fillna("").values, "")
O.loc[ni, "region"] = "Northern Ireland"
O.loc[~ew & ~ni & (O.lat.values > 54.6), "region"] = "Scotland"
r_sc = np.sqrt(sc.Shape__Area.values / np.pi) / 1000 + 1.5
inb = (d2 * 111.2) < r_sc[i2]
mask = (O.region == "Scotland").values & inb
O.loc[mask, "bua"] = sc.BUA22NM.values[i2][mask]
O["region"] = O.region.replace("", np.nan)
O["region"] = O.region.fillna("Unplaced")
O["bua"] = O.bua.fillna("").replace("nan", "")
O.loc[O.region == "London", "bua"] = "Greater London"

# ---- populations ----
lsoa = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-lsoa.csv")).rename(columns={"geography code": "code", "Residence type: Total; measures: Value": "pop"})
L = pd.DataFrame(json.load(open(os.path.join(D8, "lsoa21_bua22_lookup.json")))).merge(lsoa[["code", "pop"]], left_on="LSOA21CD", right_on="code")
buapop = L.groupby("BUA22NM")["pop"].sum()
rg = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-rgn.csv")).set_index("geography")["Residence type: Total; measures: Value"]
ct = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-ctry.csv")).set_index("geography")["Residence type: Total; measures: Value"]
regpop = {("East of England" if k == "East" else k): v for k, v in dict(rg).items()}; regpop["Wales"] = int(ct["Wales"])
buapop["Greater London"] = regpop["London"]

# ---- who is named: subject QIDs to Wikidata humans ----
WP = pd.read_csv(os.path.join(ROOT, "data", "openplaques_people.csv")).set_index("qid")
O["subject_qid"] = O.subject_qid.str.split(";").str[0].str.strip()
O["person_gender"] = O.subject_qid.map(WP["gender"]).fillna("")
O["person_group"] = O.subject_qid.map(WP["group"]).fillna("")
O["person_label"] = O.subject_qid.map(WP["label"]).fillna("")
O["openplaques_linked"] = O.openplaques_id != ""
O = O.sort_values("osm").reset_index(drop=True)
O.round({"lon": 5, "lat": 5, "dist_km": 2}).to_csv(os.path.join(ROOT, "data", "uk_plaques_osm.csv"), index=False)

# ---- places table ----
rowsP = []
for reg, g in O.groupby("region"):
    pop = regpop.get(reg)
    rowsP.append(dict(kind="region", place=reg, plaques=len(g), openplaques_linked=int(g.openplaques_linked.sum()), population_2021=pop,
                      per_100k=len(g) / pop * 1e5 if pop else None, linked_per_100k=g.openplaques_linked.sum() / pop * 1e5 if pop else None))
for bn, g in O[O.bua != ""].groupby("bua"):
    pop = buapop.get(bn)
    if pop is None or pop < 100000: continue
    rowsP.append(dict(kind="built-up area", place=bn, plaques=len(g), openplaques_linked=int(g.openplaques_linked.sum()), population_2021=int(pop),
                      per_100k=len(g) / pop * 1e5, linked_per_100k=g.openplaques_linked.sum() / pop * 1e5))
PL = pd.DataFrame(rowsP)
PL.round(2).to_csv(os.path.join(ROOT, "data", "places_plaques.csv"), index=False)

# ---- people with several plaques (OSM objects naming the same Wikidata subject) ----
m = O[O.subject_qid != ""].groupby("subject_qid").agg(n=("osm", "size"), name=("name", "first"), places=("bua", lambda s: "; ".join(sorted(set(x for x in s if x)))),
                                                       regions=("region", lambda s: "; ".join(sorted(set(s)))))
m["label"] = pd.Series(m.index.map(WP["label"]), index=m.index).fillna(m["name"])
m["gender"] = pd.Series(m.index.map(WP["gender"]), index=m.index).fillna("")
m = m.sort_values(["n", "label"], ascending=[False, True])
m[["label", "n", "gender", "regions", "places"]].to_csv(os.path.join(ROOT, "data", "multi_plaque_people.csv"))
print(len(O), "OSM objects;", O.region.value_counts().to_dict())
print(PL.sort_values("per_100k", ascending=False).head(25).to_string())
print(m.head(15).to_string())
print("colour tagged", (O.colour_family != "").sum(), O.colour_family.value_counts().to_dict())

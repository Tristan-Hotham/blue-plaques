"""Reddit collage (2400 x 3000 px): who gets a blue plaque?
Every number is read from ../data/results.json and the data CSVs.
Run from this folder: FONT_DIR=/path/to/fonts python3 collage.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F1E8D6"; FG = "#1C2230"; MUT = "#6B6253"; BLUE = "#1F4E8F"; BRICK = "#B5462A"; LAND = "#E2D5BC"; WHITE = "#FFFFFF"; BRICKBAND = "#E7DAC2"
PCOL = {"blue": "#2459A8", "green": "#3B7D4F", "black": "#22252B", "grey": "#8B8B8B", "red": "#B23A2E", "brown": "#7A5230", "white": "#FFFFFF", "other": "#C8A44A"}
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
Q = pd.read_csv(os.path.join(ROOT, "data", "eh_london_people.csv"))
O = pd.read_csv(os.path.join(ROOT, "data", "uk_plaques_osm.csv"), keep_default_na=False)
e, o, op = R["eh"], R["osm"], R["openplaques"]
pc = lambda v: f"{v * 100:.0f}%"

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# faint brick courses across the background
bg = fig.add_axes([0, 0, 1, 1], zorder=-5); bg.axis("off"); bg.set_xlim(0, 1); bg.set_ylim(0, 1)
for i, y in enumerate(np.arange(0, 1, 0.0125)):
    bg.axhline(y, color=BRICKBAND, lw=.7)
    off = 0.025 if i % 2 else 0
    for x in np.arange(off, 1, 0.05): bg.plot([x, x], [y, y + 0.0125], color=BRICKBAND, lw=.7)
bg.add_patch(Rectangle((0.025, 0.015), 0.95, 0.97, fc=BG, ec="none", alpha=.86))

fig.text(0.05, 0.968, "Who gets a blue plaque?", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(0.05, 0.912, f"Every person named on an English Heritage plaque in London, 1867 to 2026, one disc each, stacked by the\n"
         f"decade their plaque went up. {e['people']:,} people on {e['plaques']:,} plaques. Red: women. Blue: men.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.4)

# ---------- hero: a wall of plaques ----------
ax = fig.add_axes([0.05, 0.50, 0.90, 0.365]); ax.axis("off")
Qy = Q[Q.year.notna() & Q.gender.isin(["male", "female"])].copy(); Qy["decade"] = (Qy.year // 10 * 10).astype(int)
decs = list(range(1860, 2030, 10)); per = 4; gap = 1.3
ymax = 0
for j, d in enumerate(decs):
    g = Qy[Qy.decade == d].sort_values("gender")  # female first, at the bottom
    x0 = j * (per + gap)
    for k, gd in enumerate(g.gender):
        cx, cy = x0 + (k % per) + .5, (k // per) + .5
        col = BRICK if gd == "female" else BLUE
        ax.add_patch(Circle((cx, cy), .46, fc=col, ec="none"))
        ax.add_patch(Circle((cx, cy), .33, fc="none", ec=WHITE, lw=.55, alpha=.9))
        ymax = max(ymax, cy)
    n = len(g); w = (g.gender == "female").sum()
    ax.text(x0 + per / 2, -1.3, f"{d}s", ha="center", va="top", family=MONO, fontsize=10.5, color=FG)
    if n >= 10: ax.text(x0 + per / 2, (n - 1) // per + 1.6, pc(w / n), ha="center", va="bottom", family=MONO, fontsize=11, color=BRICK if w / n > .3 else MUT,
                        fontweight="medium" if w / n > .3 else "normal")
W = len(decs) * (per + gap)
ax.set_xlim(-1, W); ax.set_ylim(-4.2, ymax + 4); ax.set_aspect("equal")
ax.text(0, ymax + 2.6, "share of women in each decade", family=MONO, fontsize=11, color=MUT, va="center")
ax.text(4 * (per + gap) + .5, ymax - 4, f"In the 2020s so far, {e['women_2020s']} of the {e['people_2020s']}\npeople honoured are women.\nBefore 2000 it was about one in nine.",
        family=SER, fontsize=14, color=BRICK, va="top", linespacing=1.35)

# ---------- big numbers ----------
nums = [(pc(e["share_women"]), BRICK, f"of the people on London's\nofficial plaques are women.\n{pc(e['share_pre2000'])} before 2000."),
        (pc(e["share_2020s"]), BRICK, f"of those honoured since 2020.\nThe line was flat for a century,\nthen turned."),
        (f"{o['london_ratio']:.1f}×", BLUE, f"mapped plaques per head in\nLondon vs the rest of England\nand Wales ({o['london_per_100k']:.1f} vs {o['rest_ew_per_100k']:.1f} per 100k)."),
        (f"{o['top_bua'][0]['per_100k']:.0f}", BLUE, f"plaques per 100k people in\nCheltenham, the top large town.\nLondon ranks {o['london_rank_bua']}th.")]
for i, (big, c, small) in enumerate(nums):
    x = 0.05 + i * 0.232
    fig.text(x, 0.47, big, fontproperties=DISP, fontsize=44, color=c, va="top")
    fig.text(x, 0.418, small, family=SER, fontsize=12.5, color=FG, va="top", linespacing=1.3)

# ---------- supporting row ----------
COAST = json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")))
K = np.cos(np.radians(54.5))
m = fig.add_axes([0.03, 0.08, 0.30, 0.25]); m.axis("off")
for g in COAST:
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        r = np.array(poly[0]); m.add_patch(Polygon(np.c_[r[:, 0] * K, r[:, 1]], closed=True, fc=LAND, ec="#CDBFA4", lw=.4))
q = O[O.person_gender == ""]; m.scatter(q.lon * K, q.lat, s=1.2, c=BLUE, alpha=.3, lw=0, rasterized=True)
q = O[O.person_gender != ""].sample(frac=1, random_state=2)
m.scatter(q.lon * K, q.lat, s=np.where(q.person_gender == "female", 9, 3.5), c=q.person_gender.map({"female": BRICK, "male": BLUE}).fillna(BLUE), lw=0, rasterized=True)
m.set_xlim(-8.2 * K, 1.9 * K); m.set_ylim(49.9, 58.9); m.set_aspect("equal")
fig.text(0.05, 0.345, f"{o['objects']:,} plaques mapped in\nOpenStreetMap, UK", family=MONO, fontsize=11, color=FG, va="top", linespacing=1.35)

b = fig.add_axes([0.47, 0.09, 0.19, 0.215])
rows = sorted([(x["place"], x["per_100k"], "#7F9CCB") for x in o["top_bua"][:7]] + [("Greater London", o["london_per_100k"], BLUE)], key=lambda r: -r[1])
b.barh(range(len(rows)), [r[1] for r in rows], color=[r[2] for r in rows], height=.72)
for i, r in enumerate(rows): b.text(r[1] + 2, i, f"{r[1]:.0f}", va="center", family=MONO, fontsize=10.5, color=FG)
b.set_yticks(range(len(rows))); b.set_yticklabels([r[0].replace("Brighton and Hove", "Brighton & Hove") for r in rows], family=MONO, fontsize=10.5, color=FG)
b.invert_yaxis(); b.set_xticks([]); b.set_facecolor("none")
for s in b.spines.values(): s.set_visible(False)
b.tick_params(length=0)
fig.text(0.34, 0.345, "Mapped plaques per 100,000\npeople, large towns", family=MONO, fontsize=11, color=FG, va="top", linespacing=1.35)

c = fig.add_axes([0.80, 0.09, 0.16, 0.215])
cp = [x for x in o["colour_places"] if x["place"] in ("Greater London", "Bristol", "Hertford", "Thetford", "Beccles", "Gloucester", "York")]
for i, r in enumerate(cp):
    left = 0
    for col, n in sorted(r["colours"].items(), key=lambda kv: -kv[1]):
        c.barh(i, n / r["n"], left=left, color=PCOL[col], edgecolor=FG, lw=.4, height=.72); left += n / r["n"]
c.set_yticks(range(len(cp))); c.set_yticklabels([x["place"].replace("Greater London", "London") for x in cp], family=MONO, fontsize=10.5, color=FG)
c.invert_yaxis(); c.set_xticks([]); c.set_xlim(0, 1); c.set_facecolor("none")
for s in c.spines.values(): s.set_visible(False)
c.tick_params(length=0)
fig.text(0.70, 0.345, f"Not always blue: plaque colour\nwhere tagged ({o['colour_tagged']} plaques)", family=MONO, fontsize=11, color=FG, va="top", linespacing=1.35)

foot = [f"Gender from Wikidata for {pc(e['matched_share'])} of London plaque people, otherwise from titles and first names. OpenStreetMap counts are",
        "mapped plaques, which depend on volunteers. Data: Wikipedia lists of English Heritage blue plaques in London (CC BY-SA 4.0);",
        "Wikidata people with an Open Plaques ID (CC0); © OpenStreetMap contributors (ODbL); ONS Census 2021 (OGL v3); Natural Earth.",
        "Analysis and chart: Tristan Hotham, with Python and matplotlib.   tristan-hotham.github.io/blue-plaques"]
for i, l in enumerate(foot): fig.text(0.05, 0.062 - i * 0.012, l, family=MONO, fontsize=9.5, color=MUT, va="top")
fig.savefig(os.path.join(HERE, "who_gets_a_blue_plaque.png"), dpi=200, facecolor=BG)
print("collage written")

"""Step 7. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png), from data/.
Run: FONT_DIR=/path/to/fonts python3 07_figures.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    p = os.path.join(FD, f)
    if os.path.exists(p): fm.fontManager.addfont(p)
MONO = "IBM Plex Mono"; SER = "Source Serif 4"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
O = pd.read_csv(os.path.join(ROOT, "data", "uk_plaques_osm.csv"), keep_default_na=False)
BG = "#F2EBDD"; FG = "#1C2230"; MUT = "#685F51"; RULE = "#D6CCB8"; BLUE = "#1F4E8F"; BLUEL = "#7F9CCB"; BRICK = "#B24A2B"; BRICKL = "#E2A58D"; LAND = "#E3D8C2"
GROUPS = R["groups"]
GCOL = ["#1F4E8F", "#B24A2B", "#2E7D6B", "#6B4E9B", "#C8902B", "#C04A7A", "#5A95C8", "#7A7464", "#8C6A3F", "#4C9A3F", "#A39C8C", "#8E6A96"]
PCOL = {"blue": "#2459A8", "green": "#3B7D4F", "black": "#22252B", "grey": "#8B8B8B", "red": "#B23A2E", "brown": "#7A5230", "white": "#FFFFFF", "other": "#C8A44A"}
COAST = json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")))
K = np.cos(np.radians(54.5))
OUTP = os.path.join(ROOT, "release", "paper"); OUTB = os.path.join(ROOT, "release", "blog")
os.makedirs(OUTP, exist_ok=True); os.makedirs(OUTB, exist_ok=True)


def style(blog):
    plt.rcParams.update({"font.family": MONO, "font.size": 13 if blog else 8.5, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                         "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": BG if blog else "white", "axes.facecolor": BG if blog else "white",
                         "savefig.facecolor": BG if blog else "white", "axes.titleweight": "normal"})


def save(fig, name, blog):
    if blog: fig.savefig(os.path.join(OUTB, "b_" + name + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.25)
    else: fig.savefig(os.path.join(OUTP, "f_" + name + ".png"), dpi=250, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def land(ax):
    for g in COAST:
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            r = np.array(poly[0]); ax.add_patch(Polygon(np.c_[r[:, 0] * K, r[:, 1]], closed=True, fc=LAND, ec="#C7BCA6", lw=.5, zorder=0))


def fig_map(blog):
    style(blog)
    fig = plt.figure(figsize=(7.6, 7.6) if blog else (6.4, 6.2))
    ax = fig.add_axes([0, 0, .62, 1]); land(ax)
    q = O[O.person_gender == ""]
    ax.scatter(q.lon * K, q.lat, s=3 if blog else 1.6, c=BLUE, alpha=.25, lw=0, zorder=1, rasterized=True)
    q = O[O.person_gender != ""].sample(frac=1, random_state=2)
    ax.scatter(q.lon * K, q.lat, s=9 if blog else 4.5, c=q.person_gender.map({"female": BRICK, "male": BLUE}).fillna(BLUE), lw=0, zorder=2, rasterized=True)
    ax.set_xlim(-8.3 * K, 1.9 * K); ax.set_ylim(49.8, 59.0); ax.set_aspect("equal"); ax.axis("off")
    x0, x1, y0, y1 = -0.36, 0.16, 51.39, 51.62
    ax.add_patch(Rectangle((x0 * K, y0), (x1 - x0) * K, y1 - y0, fill=False, ec=FG, lw=1, zorder=4))
    b = fig.add_axes([.63, .30, .37, .52]); land(b)
    q = O[O.region == "London"].sample(frac=1, random_state=1)
    q = pd.concat([q[q.person_gender == ""], q[q.person_gender != ""]])
    cols = q.person_gender.map({"female": BRICK, "male": BLUE}).fillna("#9DB0CF")
    b.scatter(q.lon * K, q.lat, s=np.where(q.person_gender == "", 5 if blog else 2.5, 14 if blog else 7), c=cols, lw=0, rasterized=True)
    b.set_xlim(x0 * K, x1 * K); b.set_ylim(y0, y1); b.set_aspect("equal"); b.set_xticks([]); b.set_yticks([])
    for s_ in b.spines.values(): s_.set_visible(True); s_.set_color(FG)
    b.set_facecolor("#ECE4D4" if blog else "#F4F1EA")
    b.text(0, 1.02, "Greater London", transform=b.transAxes, va="bottom", fontsize=13 if blog else 8, color=FG)
    fs = 12 if blog else 7.5
    lg = fig.add_axes([.63, .02, .37, .24]); lg.axis("off"); lg.set_xlim(0, 1); lg.set_ylim(0, 1)
    for i, (c, lab_, s) in enumerate([(BRICK, "names a woman", 60), (BLUE, "names a man", 40), (BLUE, "no person linked", 15)]):
        lg.scatter([.04], [.9 - i * .2], s=s if blog else s / 2, c=c, alpha=.3 if i == 2 else 1)
        lg.text(.1, .9 - i * .2, lab_, va="center", fontsize=fs, color=FG)
    lg.text(0, .05, f"{R['osm']['objects']:,} plaques mapped in\nOpenStreetMap, UK", fontsize=fs, color=MUT, va="bottom")
    save(fig, "map", blog)


def fig_decades(blog):
    style(blog)
    ds = R["eh"]["by_decade"]
    fig, ax = plt.subplots(figsize=(7.6, 4.2) if blog else (6.2, 3.0))
    x = np.arange(len(ds)); v = [d["share"] or 0 for d in ds]
    ax.bar(x, v, color=[BRICKL if d["people"] < 10 else BRICK for d in ds], width=.78)
    for i, d in enumerate(ds): ax.text(i, v[i] + .012, str(d["people"]), ha="center", fontsize=9 if blog else 6, color=MUT)
    ax.set_xticks(x); ax.set_xticklabels([f"{d['decade']}s" if i % 2 == 0 else "" for i, d in enumerate(ds)], fontsize=10 if blog else 6.5)
    ax.set_yticks([0, .1, .2, .3, .4, .5]); ax.set_yticklabels(["0%", "10%", "20%", "30%", "40%", "50%"])
    ax.yaxis.grid(True, color=RULE, lw=.8); ax.set_axisbelow(True)
    ax.set_ylabel("women among people honoured")
    save(fig, "decades", blog)


def fig_births(blog):
    style(blog)
    cs = [1600, 1700, 1800, 1900]
    eh = {d["century"]: d for d in R["eh"]["by_birth_century"]}; op = {d["century"]: d for d in R["openplaques"]["by_birth_century"]}
    fig, ax = plt.subplots(figsize=(7.6, 3.8) if blog else (5.6, 2.7))
    x = np.arange(len(cs)); w = .38
    a = [eh[c]["share"] if c in eh else 0 for c in cs]; b = [op[c]["share"] for c in cs]
    ax.bar(x - w / 2, a, w, color=BRICK, label="English Heritage, London")
    ax.bar(x + w / 2, b, w, color=BRICKL, label="All Open Plaques people (Wikidata)", hatch="//" if not blog else None, edgecolor="white" if not blog else None)
    for i in range(len(cs)):
        ax.text(x[i] - w / 2, a[i] + .006, f"{a[i] * 100:.0f}%", ha="center", fontsize=10 if blog else 7)
        ax.text(x[i] + w / 2, b[i] + .006, f"{b[i] * 100:.0f}%", ha="center", fontsize=10 if blog else 7)
    ax.set_xticks(x); ax.set_xticklabels([f"born {c}s" for c in cs])
    ax.set_yticks([0, .1, .2, .3]); ax.set_yticklabels(["0%", "10%", "20%", "30%"]); ax.yaxis.grid(True, color=RULE, lw=.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=11 if blog else 7)
    save(fig, "births", blog)


def fig_eras(blog):
    style(blog)
    eras = [R["eh"]["eras"][k] for k in ("soa", "lcc", "glc", "eh")]
    fig, ax = plt.subplots(figsize=(7.6, 4.6) if blog else (6.4, 3.3))
    for i, e in enumerate(eras):
        left = 0
        for gi, g in enumerate(GROUPS):
            v = e["groups"].get(g, 0)
            ax.barh(i, v, left=left, color=GCOL[gi], edgecolor=BG if blog else "white", lw=.6, hatch=None if blog else ["", "..", "//", "xx", "\\\\", "", "..", "//", "xx", "", "..", ""][gi])
            if v > .07: ax.text(left + v / 2, i, f"{v * 100:.0f}%", ha="center", va="center", color="white", fontsize=10 if blog else 6.5)
            left += v
        ax.barh(i, 1 - left, left=left, color=RULE)
    ax.set_yticks(range(4)); ax.set_yticklabels([f"{e['name']}\n{e['start']} to {e['end']}" for e in eras], fontsize=11 if blog else 7)
    ax.invert_yaxis(); ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.legend([Rectangle((0, 0), 1, 1, fc=c) for c in GCOL], GROUPS, ncol=3, frameon=False, fontsize=10 if blog else 6.3, loc="upper center", bbox_to_anchor=(.42, -.1))
    save(fig, "eras", blog)


def fig_places(blog):
    style(blog)
    o = R["osm"]
    rows = [(b["place"], b["per_100k"], BLUEL) for b in o["top_bua"]] + [("Greater London", o["london_per_100k"], BLUE)]
    rows = sorted(rows, key=lambda r: -r[1]) + [(b["place"], b["per_100k"], "#A39C8C") for b in o["bottom_bua"]]
    fig, ax = plt.subplots(figsize=(7.6, 7.0) if blog else (5.6, 4.6))
    y = np.arange(len(rows))
    ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows])
    for i, r in enumerate(rows): ax.text(r[1] + 1, i, f"{r[1]:.1f}", va="center", fontsize=10 if blog else 6.5, color=MUT)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis()
    for t in ax.get_yticklabels():
        if t.get_text() == "Greater London": t.set_fontweight("bold"); t.set_color(BLUE)
    ax.set_xlabel("mapped plaques per 100,000 residents (Census 2021)")
    ax.axhline(len(o["top_bua"]) + .5, color=MUT, lw=.6, ls=":")
    save(fig, "places", blog)


def fig_regions(blog):
    style(blog)
    reg = sorted([(k, v) for k, v in R["osm"]["regions"].items() if v["per_100k"] is not None], key=lambda kv: -kv[1]["per_100k"])
    fig, ax = plt.subplots(figsize=(7.6, 4.6) if blog else (5.2, 3.0))
    ax.barh(range(len(reg)), [v["per_100k"] for k, v in reg], color=[BLUE if k == "London" else BLUEL for k, v in reg])
    for i, (k, v) in enumerate(reg): ax.text(v["per_100k"] + .2, i, f"{v['per_100k']:.1f}", va="center", fontsize=10 if blog else 6.5, color=MUT)
    ax.set_yticks(range(len(reg))); ax.set_yticklabels([k for k, v in reg]); ax.invert_yaxis()
    ax.set_xlabel("mapped plaques per 100,000 residents")
    save(fig, "regions", blog)


def fig_colours(blog):
    style(blog)
    cp = R["osm"]["colour_places"]
    fig, ax = plt.subplots(figsize=(7.6, 5.0) if blog else (5.6, 3.4))
    for i, r in enumerate(cp):
        left = 0
        for c, n in sorted(r["colours"].items(), key=lambda kv: -kv[1]):
            ax.barh(i, n / r["n"], left=left, color=PCOL[c], edgecolor=FG, lw=.4); left += n / r["n"]
        ax.text(1.01, i, str(r["n"]), va="center", fontsize=10 if blog else 6.5, color=MUT)
    ax.set_yticks(range(len(cp))); ax.set_yticklabels([r["place"] for r in cp]); ax.invert_yaxis()
    ax.set_xlim(0, 1.08); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0%", "50%", "100%"])
    ax.legend([Rectangle((0, 0), 1, 1, fc=PCOL[c], ec=FG, lw=.4) for c in ["blue", "green", "black", "grey", "brown", "red", "white"]],
              ["blue", "green", "black", "grey", "brown", "red", "white"], ncol=7, frameon=False, fontsize=10 if blog else 6.3, loc="upper center", bbox_to_anchor=(.45, -.08),
              handlelength=1, columnspacing=.9)
    save(fig, "colours", blog)


def fig_gwomen(blog):
    style(blog)
    g = sorted([(k, v) for k, v in R["eh"]["group_share_women"].items() if R["eh"]["groups_overall"][k] >= 10 and v is not None], key=lambda kv: -kv[1])
    fig, ax = plt.subplots(figsize=(7.6, 4.8) if blog else (5.2, 3.0))
    ax.barh(range(len(g)), [v for k, v in g], color=BRICK)
    for i, (k, v) in enumerate(g): ax.text(v + .005, i, f"{v * 100:.0f}% of {R['eh']['groups_overall'][k]}", va="center", fontsize=10 if blog else 6.5, color=MUT)
    ax.set_yticks(range(len(g))); ax.set_yticklabels([k for k, v in g]); ax.invert_yaxis()
    ax.set_xlim(0, .62); ax.set_xticks([0, .2, .4, .6]); ax.set_xticklabels(["0%", "20%", "40%", "60%"]); ax.set_xlabel("share of women in each group")
    save(fig, "gwomen", blog)


for blog in (False, True):
    fig_map(blog); fig_decades(blog); fig_births(blog); fig_eras(blog); fig_places(blog); fig_colours(blog); fig_gwomen(blog)
    if not blog: fig_regions(blog)
print("figures written")

# blog images: exactly 1520 px wide
from PIL import Image
for f in os.listdir(OUTB):
    if f.startswith("b_") and f.endswith(".png"):
        im = Image.open(os.path.join(OUTB, f)).convert("RGB")
        im.resize((1520, round(im.size[1] * 1520 / im.size[0])), Image.LANCZOS).save(os.path.join(OUTB, f), optimize=True)

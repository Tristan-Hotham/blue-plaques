"""Step 8. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Who_Gets_a_Blue_Plaque.tex and compile it with xelatex (figures from 07_figures.py).
Placeholders: {{path|fmt}} as in 05_build_site.py, with % escaped for LaTeX.
Run: python3 08_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Who_Gets_a_Blue_Plaque"
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
rows = ""
for k in ("soa", "lcc", "glc", "eh"):
    e = R["eh"]["eras"][k]
    top = sorted(((g, v) for g, v in e["groups"].items() if g not in ("Other", "Unknown")), key=lambda x: -x[1])[:2]
    rows += (f"{tex(e['name'])} & {e['start']} to {e['end']} & {e['plaques']:,} & {e['people']:,} & {e['women']} & {e['share_women'] * 100:.1f} & "
             f"{e['median_gap']:.0f} & {tex(', '.join(f'{g} {v * 100:.0f}' for g, v in top))}\\\\\n")
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{English Heritage and predecessor plaques in London by the body that put them up (year of erection). "
      "People: named people of known gender. Gap: median years from the person's death to the plaque. Top groups: the two largest occupation groups, \\% of people.}\\label{tab:eras}"
      "{\\footnotesize\\begin{tabular}{llrrrrr>{\\raggedright\\arraybackslash}p{4.3cm}}\\toprule Body & Years & Plaques & People & Women & \\% women & Gap & Top groups (\\%)\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}}\\end{table}")
o = R["osm"]
rows = ""
allp = sorted([(b["place"], b["plaques"], b["linked"], b["pop"], b["per_100k"]) for b in o["top_bua"]] +
              [("Greater London", o["london"], None, o["regions"]["London"]["pop"], o["london_per_100k"])], key=lambda r: -r[4])
for i, (p, n, l, pop, r) in enumerate(allp):
    rows += f"{i + 1} & {tex(p)} & {n:,} & {'' if l is None else f'{l:,}'} & {pop:,} & {r:.1f}\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Built-up areas of 100,000 residents or more with the highest rates of mapped plaques, and Greater London. "
      "Linked: plaques linked to Open Plaques. Population: Census 2021 usual residents.}\\label{tab:places}"
      "\\begin{tabular}{rlrrrr}\\toprule Rank & Place & Plaques & Linked & Population & Per 100,000\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_ERAS}}", TE).replace("{{TABLE_PLACES}}", TP)
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)

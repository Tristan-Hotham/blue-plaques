"""Step 6. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf and
IBMPlexMono-Medium.ttf as FONT_DIR (from github.com/google/fonts); otherwise system serif is used.
Coastline: Natural Earth 1:10m land for the British Isles, as extracted for the lighthouse project.
Run: FONT_DIR=/path/to/fonts python3 06_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -8.4 * K, 2.0 * K, -59.0, -49.8
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in poly[0])) + "Z"
dots = ""
for p in sorted(P["pts"], key=lambda p: (p[3] != 0, p[3] == 1)):
    x, y = pr(p[0], p[1])
    if p[3] == 1: dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#B24A2B"/>'
    elif p[3] == 2: dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#1F4E8F"/>'
    else: dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.5" fill="#1F4E8F" fill-opacity=".28"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
e, o = R["eh"], R["osm"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 80% 50%,#F8F3E9 0%,#F2EBDD 55%,#E6DCC8 100%);color:#1C2230;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:66px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#685F51;display:flex;gap:12px;align-items:center}}
.k b{{background:#1F4E8F;color:#F2EBDD;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:104px;margin:0;font:900 96px/.92 Fraunces,Georgia,serif;letter-spacing:-.02em;color:#1C2230;width:720px}}
h1 em{{font-style:normal;color:#1F4E8F}}
p{{position:absolute;left:70px;top:328px;width:640px;margin:0;font-size:27px;line-height:1.36}}
p b{{color:#B24A2B}}
.f{{position:absolute;left:70px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#685F51}}
svg{{position:absolute;right:30px;top:10px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Plaques × people · 1867 to 2026</span></div>
<h1>Who gets a <em>blue plaque?</em></h1>
<p>Only <b>{e['share_women'] * 100:.0f}%</b> of the people on London's official plaques are women, but <b>{e['share_2020s'] * 100:.0f}%</b> of those honoured since 2020. London has {o['london_ratio']:.1f} times as many mapped plaques per head as the rest of England and Wales.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E3D8C2" stroke="#C7BCA6" stroke-width="1"/>{dots}</svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")

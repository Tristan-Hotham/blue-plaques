"""Step 9. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 09_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "05_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)(.+?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
e, o = R["eh"], R["osm"]
pc = lambda v: f"{v * 100:.0f}%"
meta = dict(
    title="Who gets a blue plaque?",
    slug="blue-plaques",
    excerpt=(f"I read all {e['plaques']:,} English Heritage plaques listed in London and mapped {o['objects']:,} plaques across the UK. "
             f"Only {pc(e['share_women'])} of the people on London's plaques are women, but {pc(e['share_2020s'])} of those honoured since 2020."),
    seo_description=f"Who Britain remembers on its walls: only {pc(e['share_women'])} of London's blue plaque people are women, but {pc(e['share_2020s'])} since 2020. Writers, colours and places.",
    tags=["blue plaques", "English Heritage", "London", "public history", "women's history", "commemoration", "maps", "data"],
    header_alt=(f"Title card reading 'Who gets a blue plaque?' in dark ink and plaque blue on a London stock brick cream background, beside a map of the UK "
                f"dotted with plaques, blue for men and brick red for women. Text: only {pc(e['share_women'])} of the people on London's official plaques are women, "
                f"but {pc(e['share_2020s'])} of those honoured since 2020; London has {o['london_ratio']:.1f} times as many mapped plaques per head as the rest of England and Wales."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Who_Gets_a_Blue_Plaque"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("$<$", "<")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="Who Gets a Blue Plaque? Gender, Occupation and Place in Britain's Commemorative Plaques",
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/blue-plaques/. Data and code: https://github.com/Tristan-Hotham/blue-plaques. Blog post: to follow.</p>",
    keywords=["blue plaques", "commemoration", "public history", "gender", "English Heritage", "London", "Open Plaques", "OpenStreetMap", "Wikidata", "open data"],
    licence="cc-by-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/blue-plaques", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/blue-plaques/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://en.wikipedia.org/wiki/Blue_plaque", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://openplaques.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ons.gov.uk/census", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://github.com/hadley/data-baby-names", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["eh_london_plaques.csv", "eh_london_people.csv", "openplaques_people.csv", "uk_plaques_osm.csv", "places_plaques.csv", "multi_plaque_people.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "blue-plaques_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"blue-plaques/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"blue-plaques/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split()))

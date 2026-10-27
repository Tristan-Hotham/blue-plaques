# Who Gets a Blue Plaque?

Who Britain chooses to remember on its walls, and where: {{eh.plaques|int}} English Heritage (and predecessor) blue plaques in London parsed from Wikipedia's lists, {{openplaques.humans|int}} people in Wikidata with an Open Plaques subject ID, and {{osm.objects|int}} plaques mapped in OpenStreetMap across the UK.

**Interactive version:** https://tristan-hotham.github.io/blue-plaques/

This repository holds the interactive page, derived data and the analysis code for the data study *Who Gets a Blue Plaque? Gender, occupation and place in Britain's commemorative plaques* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23691880

## Headline results

- Of the {{eh.people|int}} people named on {{eh.plaques|int}} English Heritage and predecessor plaques in London, {{eh.women|int}} ({{eh.share_women|pct0}}) are women.
- The share barely moved for a century: {{eh.eras.lcc.share_women|pct0}} of people honoured by the London County Council (1901 to 1964), {{eh.eras.glc.share_women|pct0}} by the Greater London Council (1965 to 1985). Under English Heritage (1986 on) it is {{eh.eras.eh.share_women|pct0}}: {{eh.share_2010s|pct0}} in the 2010s and {{eh.share_2020s|pct0}} since 2020 ({{eh.women_2020s|int}} of {{eh.people_2020s|int}} people).
- Writers are the largest group ({{eh.groups_overall.Writing|int}} people, {{eh.writing_share|pct0}}), then art and design ({{eh.groups_overall.Art and design|int}}), science and medicine ({{eh.groups_overall.Science and medicine|int}}) and politics, law and public life ({{eh.groups_overall.Politics, law and public life|int}}). Writing fell from {{eh.eras.lcc.groups.Writing|pct0}} (LCC) to {{eh.eras.eh.groups.Writing|pct0}} (English Heritage); stage and screen rose from {{eh.eras.lcc.groups.Stage and screen|pct0}} to {{eh.eras.eh.groups.Stage and screen|pct0}}.
- Among all {{openplaques.gender_known|int}} Wikidata people with an Open Plaques subject ID, {{openplaques.share_women|pct0}} are women, from {{openplaques.share_born_1700s|pct0}} of those born in the 1700s to {{openplaques.share_born_1900s|pct0}} of those born in the 1900s.
- London holds {{osm.london_share_of_ew|pct0}} of the plaques mapped in England and Wales but {{osm.london_pop_share|pct0}} of the people: {{osm.london_per_100k|f1}} per 100,000 residents against {{osm.rest_ew_per_100k|f1}} elsewhere ({{osm.london_ratio|f1}} times). But among large built-up areas it ranks {{osm.london_rank_bua|int}}th, behind Cheltenham ({{osm.top_bua.0.per_100k|f1}}), York ({{osm.top_bua.1.per_100k|f1}}), Oxford, Bristol and Brighton and Hove.
- Of the {{osm.colour_tagged|int}} mapped plaques with a colour tag, {{osm.blue_share_tagged|pct0}} are blue; Bristol's are mostly green and York's black.
- The median London plaque goes up {{eh.median_gap_all|int}} years after its subject's death. Charles Dickens has the most mapped plaques linked to him in the UK ({{osm.multi_top.0.n|int}}).

## Files

- `index.html`: the interactive page (Leaflet map, charts, searchable plaque list).
- `header.png`: social card.
- `data/eh_london_plaques.csv`: one row per English Heritage London plaque parsed from Wikipedia: borough, year erected, subject, inscription, address, Open Plaques plaque ID (where given), people named, women and men, occupation group from the inscription, source article.
- `data/eh_london_people.csv`: one row per person named on those plaques: name, Wikipedia title, Wikidata QID and how it was matched, gender and its source (Wikidata, title, first name, hand-checked), birth and death years, year of the plaque, borough, occupation group.
- `data/openplaques_people.csv`: Wikidata humans with an Open Plaques subject ID (P1430): label, gender, birth, death, occupations, occupation group, UK citizenship flag.
- `data/uk_plaques_osm.csv`: OpenStreetMap plaques in the UK (memorial=plaque or openplaques:id): name, inscription, subject QID, Open Plaques ID, colour and colour family, coordinates, region, built-up area, the named person's gender and group where linked. Derived from OpenStreetMap, so under the ODbL.
- `data/places_plaques.csv`: plaques, Open Plaques-linked plaques, Census 2021 population and rates per 100,000 by region and for built-up areas of 100,000 people or more.
- `data/multi_plaque_people.csv`: Wikidata subjects linked to more than one mapped plaque.
- `data/first_names_ssa.csv`: first names that are at least 95% one sex in US Social Security baby-name records 1880 to 2009 (used only as a fallback for gender).
- `data/page_data.json`: compact data for the page. `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_eh_london.py` (parse the Wikipedia lists), `02_people.py` (Wikidata people, matching, gender and occupation), `03_places.py` (OpenStreetMap plaques, places and populations), `04_analyse.py` (all statistics), `05_build_site.py` (page and README), `06_header.py` (social card), `07_figures.py` (paper and blog figures), `08_paper.py` (paper PDF via xelatex), `09_release.py` (blog post and Zenodo files). `reddit/collage.py` makes the collage.

## Method in brief

**London plaques.** Wikitext of Wikipedia's *List of English Heritage blue plaques in London* and its borough lists for Camden, Kensington and Chelsea, and the City of Westminster, retrieved 27 October 2026; both the Plaque table row templates and plain tables are parsed. People are the linked names in the person column, or in the inscription where the person column holds an address. Buildings, institutions and events are left out ({{eh.plaques_no_person|int}} plaques).

**Gender.** Wikidata sex or gender for {{eh.wikidata_matched|int}} of {{eh.people|int}} people matched by Wikipedia title or name and birth year; otherwise a title in the listing (Sir, Dame, Lord, Lady...); otherwise the first name (names at least 95% one gender among at least three Wikidata Open Plaques people, then US baby-name records); the last {{eh.gender_sources.hand-checked|int}} checked by hand. Four date typos in the listings were corrected from the people's Wikipedia articles.

**Occupation.** The first occupation word in the plaque's inscription, else the person's Wikidata occupations by a fixed priority; twelve groups, defined in `02_people.py`.

**Places.** OpenStreetMap objects inside the UK tagged memorial=plaque or openplaques:id, from QLever. Each is placed at the nearest ONS 2021 MSOA population-weighted centroid (England and Wales, within 15 km) for its region, and within 4 km for its 2022 built-up area; Scotland and Northern Ireland are counted but have no population here. Rates use Census 2021 usual residents.

**Caveats.** The Wikipedia lists cover surviving plaques (the main list says {{eh.wikipedia_stated_total|int}}; I parsed {{eh.plaques|int}} rows); lost plaques are excluded, so early decades are small. Open Plaques, Wikidata and OpenStreetMap are volunteer records whose coverage varies from place to place: a low count can mean unmapped plaques. Colour is tagged on only {{osm.colour_tagged_share|pct0}} of mapped plaques. Gender and occupation are inferred and some individual assignments will be wrong.

## How to rerun

Python 3 with pandas, numpy, scipy and matplotlib (and Playwright for the header). From `code/`: `python3 01_eh_london.py && python3 02_people.py && python3 03_places.py && python3 04_analyse.py && python3 05_build_site.py`. Inputs are read one folder up and are not included: `_data10/wikipedia_blue_plaques.json.gz`, `_data10/wd_osm_bundle10.json.gz` and `_data8/` (ONS Census 2021 and geography files).

## Sources and licence

- Plaque lists: Wikipedia contributors, *List of English Heritage blue plaques in London*, *... in the London Borough of Camden*, *... in the Royal Borough of Kensington and Chelsea*, *... in the City of Westminster*, and *Blue plaque* (CC BY-SA 4.0), retrieved 27 October 2026.
- People: Wikidata (CC0), items with an Open Plaques subject ID (P1430) and plaque items with an Open Plaques plaque ID (P1893), via QLever.
- Plaque locations and colours: © OpenStreetMap contributors, Open Database Licence (ODbL), via QLever.
- Census 2021 (TS001) and ONS geography lookups: Office for National Statistics, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- First-name fallback: US Social Security Administration baby names 1880 to 2009 (public domain), via https://github.com/hadley/data-baby-names.
- Base map tiles on the page: Esri. Map library: Leaflet.

The derived data and page text are released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), because they include Wikipedia material; `data/uk_plaques_osm.csv` and the map points are a derived OpenStreetMap database under the ODbL (https://opendatacommons.org/licenses/odbl/). Code is MIT (see `LICENSE`).

Companion studies: [Still Standing: the oldest buildings](https://tristan-hotham.github.io/oldest-buildings/) and [more history data posts](https://blog.tristanhotham.com/).

## Citation

Hotham, T. (2026) *Who Gets a Blue Plaque? Gender, occupation and place in Britain's commemorative plaques*. Zenodo. https://doi.org/10.5281/zenodo.23691880

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

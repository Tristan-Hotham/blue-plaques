## Title

[OC] Who gets a blue plaque? I stacked all 1,081 people named on London's English Heritage plaques by the decade their plaque went up: for a century about 1 in 10 was a woman, but since 2020 it is 39 of 72 (54%)

## Body

I parsed Wikipedia's lists of English Heritage blue plaques in London (1,037 plaques, with the year each went up) and matched the people to Wikidata for gender and occupation.

Overall 16% of the people are women. Under the London County Council (1901 to 1964) it was 8%, and 11% for all plaques before 2000. Then it turns: 20% in the 2010s and 54% since 2020. Across 6,476 plaques mapped in OpenStreetMap, London has 2.3 times as many per head as the rest of England and Wales, but Cheltenham, York, Oxford, Bristol and Brighton beat it.

Caveat: gender is inferred for a minority of people (titles, first names), and OpenStreetMap counts depend on volunteer mapping.

Interactive map and searchable list: https://tristan-hotham.github.io/blue-plaques/

## Source comment

Source: Wikipedia, "List of English Heritage blue plaques in London" and its borough lists for Camden, Kensington and Chelsea, and the City of Westminster, plus "Blue plaque" (CC BY-SA 4.0, wikitext retrieved 27 October 2026); Wikidata people with an Open Plaques subject ID, P1430 (CC0, via QLever); plaque locations and colours © OpenStreetMap contributors (ODbL, via QLever); ONS Census 2021 TS001 and ONS 2022 built-up areas (Open Government Licence v3.0); first-name fallback from US Social Security baby names 1880 to 2009 (public domain, github.com/hadley/data-baby-names); Natural Earth coastline (public domain).

Tools: Python (pandas, numpy, scipy, matplotlib).

Interactive version: https://tristan-hotham.github.io/blue-plaques/
Blog post: https://blog.tristanhotham.com/2026/10/27/blue-plaques/
Paper and data: https://doi.org/10.5281/zenodo.23691880

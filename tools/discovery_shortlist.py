"""Shortlist of new Earth analog candidates (terrain match + Moon/Mars-like surface conditions).

Reads the ML result documents (``python -m pipeline.ml infer --geo ... --env ...``)
and keeps an AOI for an objective only if all of these hold:

1. terrain: objective F >= 0.5 and robustly in the top 10 % (rank P95 over 200
   perturbation draws <= 10 % of eligible AOIs);
2. conditions: exposed surface (ESA WorldCover bare_frac >= 0.7) and arid
   (GPM IMERG precip_mm <= 250 mm/yr), because terrain-only objectives otherwise
   rank e.g. flat rainforest as a Mars landing analog;
3. data: coverage L4_validated (all stages ran and passed QA);
4. new: farther than 150 km from every documented analog site in the reference
   set and every pilot window. "New" means "not in our list", not "never used".

Region names come from OpenStreetMap Nominatim reverse geocoding (coordinates only)
and are stored in the output so the run is reproducible offline.

Written with AI assistance (Claude Code); human review pending.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.ml.evaluate import haversine_km  # noqa: E402

RULES = {"F_min": 0.5, "rank_p95_share_max": 0.10, "bare_frac_min": 0.7, "precip_mm_max": 250.0,
         "coverage_level": "L4_validated", "min_km_from_known": 150.0}

REGIONS = {  # Nominatim reverse geocoding, zoom 6, accessed 2026-11-15
    "SM_E064.275_N33.323": "Ghor Province, Afghanistan",
    "SM_E088.272_N42.406": "Turpan, Xinjiang, China",
    "SM_E012.445_N16.628": "Diffa Region, Niger",
    "SM_E022.552_N29.356": "Al Wahat, Libya",
    "SM_E026.496_N26.620": "New Valley, Egypt",
    "SM_E036.670_N20.393": "Red Sea State, Sudan",
    "SM_E056.315_N32.716": "Tabas County, South Khorasan, Iran",
    "SM_E057.245_N34.350": "Boshruyeh County, South Khorasan, Iran",
    "SM_E060.488_N29.596": "Zahedan County, Sistan and Baluchestan, Iran",
    "SM_E104.764_N38.565": "Alxa League, Inner Mongolia, China",
    "SM_W002.775_N23.704": "Bordj Badji Mokhtar, Algeria",
    "SM_W009.541_N28.648": "Assa-Zag Province, Guelmim-Oued Noun, Morocco",
    "SM_W074.290_S15.440": "Ayacucho, Peru",
}

# Quick literature check, 15 November 2026 (English web search, one or two queries per site; not exhaustive).
# status: region_known = the wider region is a published Mars/Moon analog; mentioned = only passing or distant
# mentions; none_found = no analog study found for the region.
LITERATURE = {
    "SM_E026.496_N26.620": ("region_known", "Western Desert of Egypt: aeolian landforms studied as Mars analogs "
                            "(El-Baz et al. 1979, JGR; NASA reports on the Kharga depression, ~400 km east)",
                            "https://pubs.usgs.gov/publication/70012315"),
    "SM_W002.775_N23.704": ("region_known", "Tanezrouft Basin: salt-flat deposits proposed as a Mars Sample Return "
                            "analog (AZALEA project, EPSC-DPS 2025)",
                            "https://meetingorganizer.copernicus.org/EPSC-DPS2025/EPSC-DPS2025-1671.html"),
    "SM_W009.541_N28.648": ("region_known", "Southern Morocco: Tindouf Basin soils as a Noachian Mars analog "
                            "(Oberlin et al. 2018); other Moroccan sites near Erfoud (MARS2013, ESA rover tests)",
                            "https://research-portal.st-andrews.ac.uk/en/publications/evaluation-of-the-tindouf-basin-region-in-southern-morocco-as-an-/"),
    "SM_E056.315_N32.716": ("region_known", "Lut Desert (northern Lut begins near Tabas): megaripples and yardangs "
                            "as Mars analogs (Foroutan & Zimbelman 2016, Icarus)", "https://profiles.si.edu/display/sro_139430"),
    "SM_E060.488_N29.596": ("region_known", "East of the Lut Desert analog region (Foroutan & Zimbelman 2016); "
                            "nothing found for Zahedan itself", "https://profiles.si.edu/display/sro_139430"),
    "SM_E088.272_N42.406": ("mentioned", "Turpan depression appears only as a site caption on a popular Mars-analog "
                            "page; Chinese Mars-analog work concentrates on the Qaidam Basin", "https://planete-mars.com/?p=1094"),
    "SM_E022.552_N29.356": ("mentioned", "Sahara-wide analog proposals; the nearest specific Libyan analog is "
                            "Wau-an-Namus volcano (~600 km away)", "https://programme.exordo.com/ims2016/delegates/presentation/444"),
    "SM_E012.445_N16.628": ("mentioned", "Ténéré linear dunes compared with Mars and Titan dunes (far north of Diffa)",
                            "https://www.futura-sciences.com/sciences/actualites/cea-dunes-mars-titan-mieux-comprises-grace-desert-tenere-60334/"),
    "SM_E064.275_N33.323": ("none_found", "No planetary-analog study of Ghor Province found", None),
    "SM_E036.670_N20.393": ("none_found", "Red Sea Hills of Sudan described by NASA Earth Observatory, not as an analog",
                            "https://eol.jsc.nasa.gov/Collections/EarthObservatory/articles/TheRedSeaHillsofSudan.htm"),
    "SM_E057.245_N34.350": ("none_found", "No analog study found for Boshruyeh (north of the Lut analog region)", None),
    "SM_E104.764_N38.565": ("none_found", "Alxa deserts: only a tourist 'Mars Base 1'; no scientific analog study found", None),
    "SM_W074.290_S15.440": ("none_found", "Nearest Peruvian Mars analog is Pampas de La Joya (~260 km SE); nothing found "
                            "for this area", None),
}


def build(results_dir: Path, geo_dir: Path, env_dir: Path, sites_csv: Path) -> dict:
    catalog = {a["aoi_id"]: a for a in json.loads((geo_dir / "aoi_catalog.json").read_text(encoding="utf-8"))["aois"]}
    env = {r["aoi_id"]: r for r in json.loads((env_dir / "environment.json").read_text(encoding="utf-8"))["records"]}
    known = [(float(r["lon"]), float(r["lat"]), r["site_id"]) for r in csv.DictReader(sites_csv.open(encoding="utf-8"))
             if r["lat"]]
    known += [(a["centroid"]["lon"], a["centroid"]["lat"], a["aoi_id"]) for a in catalog.values() if a["pool"] == "pilot"]
    sites: dict[str, dict] = {}
    for path in sorted(glob.glob(str(results_dir / "*__*.json"))):
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        profile = doc["mission_profile"]
        eligible = [c for c in doc["candidates"] if c["rank"] is not None]
        n = len(eligible)
        for c in eligible:
            a = catalog[c["aoi_id"]]
            stab = c["components"]["ranking_stability"]["value"] or {}
            F = c["components"]["deterministic_fidelity"]["value"]
            bare = a["summary"].get("bare_frac")
            precip = env.get(c["aoi_id"], {}).get("precip_mm")
            dist, nearest = min((haversine_km(c["lon"], c["lat"], lo, la), sid) for lo, la, sid in known)
            if not (F >= RULES["F_min"] and stab.get("rank_p95", 1e9) <= RULES["rank_p95_share_max"] * n
                    and a["coverage_level"] == RULES["coverage_level"] and bare is not None
                    and bare >= RULES["bare_frac_min"] and precip is not None and precip <= RULES["precip_mm_max"]
                    and dist > RULES["min_km_from_known"]):
                continue
            site = sites.setdefault(c["aoi_id"], {
                "aoi_id": c["aoi_id"], "region": REGIONS.get(c["aoi_id"]), "lon": c["lon"], "lat": c["lat"],
                "nearest_known": {"site": nearest, "km": round(dist)},
                "literature": dict(zip(("status", "note", "url"), LITERATURE.get(c["aoi_id"], ("unchecked", "", None)))),
                "conditions": {"bare_frac": bare, "precip_mm": round(precip, 1),
                               "t_min_c": env[c["aoi_id"]]["t_min_c"], "t_max_c": env[c["aoi_id"]]["t_max_c"],
                               "relief_m": a["summary"].get("relief_m"), "elev_p50_m": a["summary"].get("elev_p50_m"),
                               "geo_lith_label": a["summary"].get("geo_lith_label")},
                "matches": []})
            site["matches"].append({
                "target": doc["target"]["id"], "objective": profile["objective_id"], "objective_name": profile["name"],
                "F": round(F, 3), "rank": c["rank"], "eligible": n, "rank_p95": stab.get("rank_p95"),
                "matching": c["explanation"]["matching"], "mismatches": c["explanation"]["mismatches"],
                "attributes": [{k: x[k] for k in ("attr", "earth_value", "target_value", "fidelity")}
                               for x in c["explanation"]["attributes"]]})
    ordered = sorted(sites.values(), key=lambda s: (-len(s["matches"]), -max(m["F"] for m in s["matches"])))
    return {"schema": "egiz.discovery_shortlist", "schema_version": "0.1.0", "rules": RULES,
            "inputs": {"results": str(results_dir), "geo": str(geo_dir), "env": str(env_dir), "known": str(sites_csv)},
            "caveats": [
                "Similarity of measured conditions for a task, not suitability: access, safety, permits not assessed.",
                "'New' = farther than 150 km from our reference list and pilots; a quick literature check is in 'literature'.",
                "Geology label is a map-unit proxy at the AOI centre, not mineralogy.",
                "Earth cannot reproduce vacuum, gravity, radiation or full thermal conditions of the Moon or Mars.",
                "Cold/dry objectives O5 and M4 are not included: target surface temperatures are not curated yet.",
            ],
            "sites": ordered}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="artifacts/ml/discovery-env")
    parser.add_argument("--geo", default="data/geo/geo-0.1.0")
    parser.add_argument("--env", default="data/env/env-0.1.0")
    parser.add_argument("--sites", default="data/ml/reference/reference_sites-0.1.0.csv")
    parser.add_argument("--out", default="data/ml/discovery/shortlist-0.1.0.json")
    args = parser.parse_args(argv)
    doc = build(Path(args.results), Path(args.geo), Path(args.env), Path(args.sites))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    for s in doc["sites"]:
        print(s["aoi_id"], s["region"], [(m["objective"], m["rank"], m["F"]) for m in s["matches"]])
    print(f"wrote {out}: {len(doc['sites'])} sites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

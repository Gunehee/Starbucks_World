"""
update_data.py
--------------
Fetches every Starbucks location worldwide from OpenStreetMap (via the Overpass
API) and rebuilds assets/starbucks_world.geojson.

Why OpenStreetMap instead of a static CSV:
  The project previously pulled from chrismeller/StarbucksLocations, a CSV
  snapshot that stopped being updated in 2017. OSM is community-maintained,
  covers every country, and can be re-queried at any time, so it is the
  closest thing to a "live" worldwide source that doesn't require scraping
  Starbucks' private app API (which would need reverse engineering and would
  violate their Terms of Service).

Coverage caveat:
  OSM coverage depends on community mapping activity. It is very complete in
  the US, Canada, Korea, Japan and Western Europe, and sparser in some other
  regions. Menu/price data is NOT sourced here — see assets/menu.json for the
  manually curated, per-country reference menu (Starbucks has no public
  per-store pricing API).

Runs automatically via GitHub Actions (.github/workflows/update-data.yml).
"""

import json
import os
import sys
import time

import requests

GEOJSON_PATH = "assets/starbucks_world.geojson"

# If the freshly fetched dataset has fewer than this fraction of the previous
# run's stores, assume a widespread Overpass outage (not real store closures)
# and keep the old file rather than overwrite good data with a partial scan.
MIN_RETAIN_RATIO = 0.7

# Overpass mirrors, tried in order with backoff on failure/timeout/rate-limit.
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

HEADERS = {"User-Agent": "Starbucks-World-Map/1.0 (github.com update script)"}

# Starbucks' Wikidata QID — the one tag that reliably identifies a Starbucks
# location regardless of the local-language name (스타벅스, スターバックス, 星巴克, ...).
BRAND_WIKIDATA_ID = "Q37158"

# ISO 3166-1 alpha-2 country codes to query, one Overpass call each so that a
# slow/failed country never blocks the rest and each request stays fast
# enough for the public API. This list covers every country with a
# significant Starbucks presence; a handful of very small markets may be
# missing, which is a known limitation of this best-effort worldwide scan.
COUNTRIES = [
    "US", "CA", "MX", "GT", "CR", "PA", "CO", "PE", "CL", "AR", "BR", "UY",
    "GB", "IE", "FR", "DE", "NL", "BE", "LU", "CH", "AT", "ES", "PT", "IT",
    "GR", "PL", "CZ", "SK", "HU", "RO", "BG", "SE", "NO", "DK", "FI", "IS",
    "CY", "MT", "MC", "AD",
    "TR", "RU", "GE", "AZ", "KZ",
    "AE", "SA", "KW", "QA", "BH", "OM", "JO", "LB", "IL", "EG", "MA",
    "ZA", "NG",
    "IN", "PK", "LK", "BD",
    "CN", "HK", "MO", "TW", "JP", "KR", "MN",
    "TH", "VN", "PH", "MY", "SG", "ID", "KH", "LA", "MM", "BN",
    "AU", "NZ",
]

DRIVE_THRU_KEYS = ("drive_through", "drive_thru")


def overpass_query(query: str, tries_per_endpoint: int = 2) -> dict:
    """POST a query to Overpass, retrying across mirrors with backoff."""
    last_err = None
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(tries_per_endpoint):
            try:
                resp = requests.post(
                    endpoint, data={"data": query}, headers=HEADERS, timeout=290
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:  # noqa: BLE001 - want to retry on anything
                last_err = e
                print(f"    ! {endpoint} attempt {attempt+1} failed: {e}")
                time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")


def fetch_country(code: str) -> list:
    query = f"""
    [out:json][timeout:270];
    area["ISO3166-1"="{code}"][admin_level=2]->.a;
    node["brand:wikidata"="{BRAND_WIKIDATA_ID}"](area.a);
    out body;
    """
    result = overpass_query(query)
    elements = result.get("elements", [])
    for el in elements:
        el["_country"] = code
    return elements


def to_feature(node: dict) -> dict:
    tags = node.get("tags", {})
    addr_parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:street", ""),
    ]
    street = " ".join(p for p in addr_parts if p).strip()
    city = tags.get("addr:city", "")
    state = tags.get("addr:state", "")
    postcode = tags.get("addr:postcode", "")
    name = tags.get("name") or tags.get("name:en") or "Starbucks"
    branch = tags.get("branch", "")
    display_name = f"{name} ({branch})" if branch else name

    drive_thru = any(tags.get(k) == "yes" for k in DRIVE_THRU_KEYS)

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [node["lon"], node["lat"]]},
        "properties": {
            "id": node["id"],
            "name": display_name,
            "country": node["_country"],
            "street": street,
            "city": city,
            "state": state,
            "postcode": postcode,
            "phone": tags.get("phone") or tags.get("contact:phone", ""),
            "opening_hours": tags.get("opening_hours", ""),
            "website": tags.get("website") or tags.get("contact:website", ""),
            "driveThru": drive_thru,
        },
    }


def main():
    all_features = []
    seen_ids = set()
    failed_countries = []

    for i, code in enumerate(COUNTRIES, 1):
        print(f"[{i}/{len(COUNTRIES)}] Fetching {code}...")
        try:
            elements = fetch_country(code)
        except Exception as e:  # noqa: BLE001
            print(f"    x giving up on {code}: {e}")
            failed_countries.append(code)
            continue

        new_count = 0
        for el in elements:
            if el["id"] in seen_ids:
                continue
            seen_ids.add(el["id"])
            all_features.append(to_feature(el))
            new_count += 1
        print(f"    -> {new_count} stores")

        time.sleep(3)  # be polite to the shared public Overpass instances

    print(f"\nTotal stores collected: {len(all_features)}")
    if failed_countries:
        print(f"Countries that failed and were skipped: {failed_countries}")

    if len(all_features) == 0:
        print("No stores fetched at all -- aborting without touching the existing file.")
        sys.exit(1)

    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            previous = json.load(f)
        prev_count = len(previous.get("features", []))
        if prev_count > 0 and len(all_features) < prev_count * MIN_RETAIN_RATIO:
            print(
                f"New count ({len(all_features)}) is far below previous "
                f"({prev_count}) -- likely a partial Overpass outage. "
                "Keeping the existing file untouched."
            )
            sys.exit(1)

    geojson = {
        "type": "FeatureCollection",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "OpenStreetMap via Overpass API (ODbL) -- https://www.openstreetmap.org/copyright",
        "failed_countries": failed_countries,
        "features": all_features,
    }

    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Saved -> {GEOJSON_PATH}")


if __name__ == "__main__":
    main()

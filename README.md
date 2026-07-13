<div align="center">

# ☕ Starbucks Worldwide

### Interactive Location Finder

**A geospatial web application mapping every Starbucks location tracked in OpenStreetMap, worldwide.**
Search by name, filter by country, view a per-country menu reference, and get directions — refreshed automatically every day.

<br>

<a href="https://gunehee.github.io/Starbucks_World/">
  <img src="https://img.shields.io/badge/📄%20View%20Project%20Page-1A6335?style=for-the-badge&logoColor=white" alt="Project Page" height="44">
</a>

<br><br>

</div>

---

## Overview

This project started as a class assignment mapping the ~100 Starbucks locations in Seattle, WA. It has since been rebuilt to cover every country with a mapped Starbucks presence — searchable, filterable by country, and kept current by a daily automated data refresh.

> **[→ Open the interactive map](https://gunehee.github.io/Starbucks_World/map.html)** to explore stores worldwide.

---

## Features

| Feature | Description |
|---|---|
| **Worldwide Coverage** | Every Starbucks location tagged in OpenStreetMap, across ~80 countries |
| **Marker Clustering** | Tens of thousands of markers stay smooth and readable at any zoom level |
| **Country Filter** | Narrow the map and list down to a single country |
| **Real-Time Search** | Filter by store name, city, or address as you type |
| **Store Detail Panel** | Address, phone, hours, and store webpage link, where available |
| **Per-Country Menu Reference** | A representative menu + price list for major markets in each store's local currency |
| **Google Maps Integration** | One-click "Get Directions" button in every store detail view |
| **Automatic Daily Refresh** | A GitHub Actions workflow re-queries OpenStreetMap every day and commits the update |

---

## Dataset

**Source:** [OpenStreetMap](https://www.openstreetmap.org/copyright), queried live through the [Overpass API](https://overpass-api.de/).

The project originally used a static 2021 Kaggle CSV (*Starbucks Locations Worldwide*) filtered to Seattle only. That snapshot has been retired — OSM is community-maintained, covers every country, and can be re-queried at any time, which is what makes daily automatic refresh possible without scraping Starbucks' private, ToS-protected app API.

**Pipeline** (`scripts/update_data.py`):
1. **Query** — For each of ~80 countries, ask Overpass for every node tagged `brand:wikidata=Q37158` (Starbucks' Wikidata ID — catches localized names like 스타벅스 / スターバックス / 星巴克 too) inside that country's administrative boundary
2. **Dedupe & Normalize** — Merge by OSM node ID; extract name, address, phone, hours, and website from OSM tags
3. **Safety Check** — If a run returns far fewer stores than last time (a likely partial Overpass outage rather than real store closures), keep the previous good file instead of overwriting it
4. **Publish** — Write one worldwide `assets/starbucks_world.geojson`, fetched by the map at runtime

| File | Description |
|---|---|
| `assets/starbucks_world.geojson` | All worldwide store locations — regenerated daily |
| `assets/menu.json` | Manually curated reference menu + representative pricing per country |

### Known limitations

- **Coverage depends on OSM mapping activity.** It's very complete in the US, Canada, Korea, Japan, and Western Europe, and sparser in some other regions. A store not mapped in OSM won't appear here.
- **Menu prices are reference-only, not live.** Starbucks does not publish a public per-store pricing API. Scraping the official app's private API would require reverse engineering it and would violate Starbucks' Terms of Service, so `assets/menu.json` instead holds a small, manually compiled, representative menu and price list per country. Always confirm exact current pricing in the official Starbucks app.
- **Service type (drive-thru vs. in-store) isn't reliably taggable worldwide**, so — unlike the original Seattle-only version — this map doesn't filter by service type globally.
- The country-boundary query list covers ~80 countries with a known Starbucks presence; a handful of very small markets may be missing.

---

## Tech Stack

| Technology | Role |
|---|---|
| [Leaflet.js v1.9.4](https://leafletjs.com/) | Interactive map rendering |
| [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) | Clusters tens of thousands of markers for performance |
| [OpenStreetMap](https://www.openstreetmap.org/) | Base map tile layer + store location data (no API key) |
| GeoJSON | Store location data, fetched by the map at runtime |
| Vanilla JavaScript (ES6+) | Filtering, search, and all interactivity |
| CSS3 | Layout, animations, and Starbucks-themed design |
| Python + `requests` | Overpass API data collection script |
| GitHub Actions | Scheduled daily data refresh |
| [Google Maps URLs](https://developers.google.com/maps/documentation/urls/get-started) | Directions deep link (no key required) |

All dependencies load via CDN. No build tools, no framework, no API key required.

---

## Repository Structure

```
Starbucks_World/
├── index.html                        # Portfolio landing page
├── map.html                          # Interactive map application  ← main demo
├── README.md
├── scripts/
│   └── update_data.py                # Overpass fetch + GeoJSON rebuild
├── .github/workflows/
│   └── update-data.yml               # Daily scheduled data refresh
└── assets/
    ├── starbucks_world.geojson       # All worldwide store locations
    └── menu.json                     # Per-country reference menu + pricing
```

`map.html` fetches `assets/starbucks_world.geojson` and `assets/menu.json` at runtime — unlike the original Seattle-only version, this one is **not** a fully offline single file, since embedding tens of thousands of stores inline isn't practical. It works great on GitHub Pages; running it locally needs a static server (see below).

---

## Running Locally

```bash
git clone https://github.com/Gunehee/Starbucks_World.git
cd Starbucks_World
python3 -m http.server 8000
# then open http://localhost:8000/map.html
```

A local server is required because `map.html` loads the store data via `fetch()`, which most browsers block on `file://` URLs.

To refresh the data yourself:

```bash
pip install requests
python3 scripts/update_data.py
```

This takes roughly 20–40 minutes since it queries ~80 countries sequentially against the public Overpass API.

---

## Team

Originally developed as a group assignment for **GEOG 495: Digital Geographies** at the **University of Washington**, then extended to worldwide coverage with automatic refresh and menu pricing.

| Contributor | Responsibilities |
|---|---|
| **Gunhee** | Geocoder, sidebar panel, project rebuild and deployment; worldwide data pipeline and map rebuild |
| **Haochen** | Layer toggle logic, GeoJSON data loading |
| **Sophia L.** | Map frame, interactive feature implementation |
| **Sophia S.** | Data collection, cleaning, and GeoJSON export |

---

## References

**Data**
- OpenStreetMap contributors. (n.d.). *Starbucks locations*, queried via the Overpass API. https://www.openstreetmap.org/copyright (ODbL)
- Menu and pricing reference manually compiled per country — Starbucks has no public per-store pricing API.
- Kukuroo3. (2021). *Starbucks Locations Worldwide 2021 Version*. Kaggle. https://www.kaggle.com/datasets/kukuroo3/starbucks-locations-worldwide-2021-version — original data source for the Seattle-only version of this project.

**Libraries**
- Agafonkin, V. (2010). *Leaflet.js* (v1.9.4). https://leafletjs.com/
- Danzel. (2012). *Leaflet.markercluster*. https://github.com/Leaflet/Leaflet.markercluster
- OpenStreetMap contributors. (n.d.). *OpenStreetMap*. https://www.openstreetmap.org/copyright

**Context & Background**
- Starbucks. (n.d.). *Our Heritage*. https://www.starbucks.com/about-us/our-heritage/
- Seattle Metropolitan. (2015, August). *Every Single Starbucks in Seattle, Ranked*. https://www.seattlemet.com/eat-and-drink/2015/08/every-single-starbucks-in-seattle-ranked
- The Commons Cafe. (n.d.). *Starbucks Dominates the Coffee Market in Seattle*. https://www.thecommonscafe.com/starbucks-dominates-the-coffee-market-in-seattle/
- Starbucks Melody. (2018, November). *Your Seattle Starbucks Checklist*. http://www.starbucksmelody.com/2018/11/24/starbucks-checklist/
- Choose Washington State. (n.d.). *Starbucks: A Legendary Washington State Business Since 1971*. http://choosewashingtonstate.com/success-stories/starbucks/
- Condé Nast Traveler. (n.d.). *Starbucks Reserve Roastery, Seattle*. https://www.cntraveler.com/bars/seattle/starbucks-reserve-roastery

---

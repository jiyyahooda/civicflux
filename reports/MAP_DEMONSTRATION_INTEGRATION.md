# Geographic demonstration maps and live AQI

Implemented locally on 28 October 2026. No retraining or original dataset replacement. No GitHub commit/push for this map pass.

## What is available

- City map > Air quality: current WAQI station values, coloured markers, station detail cards, source links, IST observation times, six US EPA AQI categories and optional illustrative interpolation. The supplied token was verified against the provider; 24 Delhi-area reporting stations were returned at the check. Numbers can change. The API's AQI and pollutant subindices are not interpreted as raw concentrations or Indian NAQI.
- City map > Water supply: defaults to the clearly marked simulated network view. Available observations still shows real report/source locations separately. Demonstration views include roads, pumps, water points, drainage, facilities and labelled blockages.
- City map > Traffic > Simulated scenario: adjustable vehicle volume/capacity with a visible ratio, category and threshold explanation. The existing separate Google TrafficLayer implementation is retained; live Google access still requires its own restricted browser key, API activation and billing.
- City map > Rainfall: original observations remain. Optional OpenWeather precipitation tiles are wired through a server-side key route. No OpenWeather key was supplied, so live imagery is unverified/unavailable; the scenario view offers an explicitly illustrative rainfall layer.
- Planning > What-if assessment: a geographic map sits alongside the existing schematic graph, cascade results and allocation tools. It uses the saved scenario's declared outages, rainfall/blockage forcing, actual review flags and selected proposed inspections. Green inspection rings do not imply a completed repair or risk reduction.
- Predictions > Traffic volume: the real saved artifact runs as before, followed by an optional interpretation using an editable assumed capacity. The benchmark junction remains anonymous; this does not turn it into a forecast for a named Delhi road.

## Real geography versus generated conditions

Eight OSM road/waterway references were retrieved through rate-limited Nominatim queries after Overpass endpoints were unavailable: Mathura Road, Mahatma Gandhi Marg, Vikas Marg, Lodhi Road, Mehrauli Badarpur Road, Najafgarh Nallah, Sardar Patel Marg and Shanti Path. Source way IDs, URLs and licence attribution are retained in `data/geography/delhi_osm_sources.json`.

Only the retrieved OSM segments are included; these are not complete municipal corridor or drain inventories. Display geometry is clipped to a declared demo extent (77.05–77.35 longitude, 28.48–28.78 latitude), which is not an administrative boundary. The waterway display anchor is selected from its sourced geometry. Other demo assets use deterministic illustrative offsets around these references. No municipal pipe topology or surveyed pump site is claimed.

`data/geography/delhi_demo.json` contains 40 explicitly synthetic display assets and the existing model graph's edges/IDs/fingerprint. Geographic names are demonstration associations only. No asset was inserted into the citizen-report database or authorized inventory. Chennai/Chandigarh do not inherit Delhi geography.

Reproduce offline with:

```sh
python scripts/build_demo_geography.py
```

The source snapshot is bundled, so regeneration does not query a provider. The script writes the GeoJSON, demonstration JSON and frontend label lookup. Model IDs and artifacts are preserved.

The scenario export endpoint returns a JSON attachment with validated rain, blockage, volume/capacity and selected outage inputs. It always remains synthetic with real_incidents=false. The running HTTP export was verified. The in-app browser's download-event capture timed out for the original Blob approach; the implementation now uses a normal HTTP attachment. A native browser save dialog was not separately verified.

## Interpretation and explainability

The traffic display uses volume / assumed capacity. Demonstration thresholds are low <0.50, moderate <0.80, high <=1.00 and over capacity >1.00. For example, 900/1200=0.75 means moderate assumed pressure. These are declared illustration rules, not a learned congestion model or a validated road-engineering standard. Volume alone cannot establish queues, speed or travel time. No invented feature contributions or SHAP values are presented. Existing actual priority-factor explanations remain available for allocation.

Display names such as road_1 are not the target labels used to train the models. Replacing their text cannot improve accuracy. A future synthetic training study would need its own documented generator, held-out mechanisms and separate evaluation; it would still not establish real-world validity. This pass changes presentation and demonstration geography only.

## Keys, providers and data handling

The WAQI token exists only in the ignored private `.env`, with file mode 0600. It is absent from source, built assets and the geographical export. WAQI calls are server-side, responses use Cache-Control: no-store, and no provider responses are written to the existing persistent provider cache or archived as a training dataset. The original CAMS adapter remains intact in its own module; WAQI uses `backend/integrations/waqi.py`.

Configuration names:

- `WAQI_API_TOKEN`: server-only, configured locally.
- `VITE_GOOGLE_MAPS_API_KEY`: existing Google browser key; intentionally visible to browsers, requires approved-origin/API restrictions. No configured key was supplied for verification.
- `OPENWEATHERMAP_API_KEY`: server-only optional precipitation access. No key supplied.

Sources and usage:

- [WAQI official API](https://aqicn.org/api/) and [Delhi map](https://aqicn.org/map/delhi/): attribution to WAQI and the originating agency is shown. The API terms restrict commercial use and cached/archived redistribution, and specify notification/agreement requirements for public applications. Check those terms before public hosting. No organization was contacted or agreement accepted by this implementation.
- [OpenStreetMap licence](https://www.openstreetmap.org/copyright): geographical reference/derived data carry ODbL attribution and licence links. No third-party screenshot was copied into the map. The uploaded colour-map example describes groundwater depth; it was used only as visual inspiration, not AQI or flood evidence.
- [Google TrafficLayer](https://developers.google.com/maps/documentation/javascript/trafficlayer): live map needs the official configured provider access; Google tiles are not copied into Leaflet.
- [OpenWeather map documentation](https://openweathermap.org/api/weathermaps): optional precipitation imagery needs a separate provider key and applicable access.

## Verification

- Full backend suite: **112 passed, one existing warning**, 8.47 seconds.
- After parser hardening: all seven map integration tests passed again.
- Production TypeScript/Vite build passed, 2.15 seconds; existing nonblocking 3D chunk-size warning remains.
- Browser: 24 live WAQI markers, shading canvas, station details and local timestamps; water/drainage/road layer changes; low/moderate/over-capacity interpretation; named scenario markers and labelled blockages; real saved traffic forecast (75.597 vehicles/hour) followed by its 0.06 assumed-capacity ratio; geographic what-if map coexisting with original graph/optimizer.
- API: source/simulation separation, no key leakage, no WAQI archive, malformed station rows, missing access, capacity validation, optional tile bounds/access and scenario attachment inputs are covered by tests.
- SHA-256: **273 original artifact/notebook files unchanged**.
- New map behavior was checked on macOS. No native Windows browser run was performed for this pass. Live Google traffic and OpenWeather imagery remain unverified until their separate keys are configured.

Implementation: `backend/api/maps.py`, `backend/integrations/waqi.py`, map components in `frontend/src/components`, existing CityMap/Planning/Predictions integration, city-aware label formatting, `data/geography/`, `scripts/build_demo_geography.py`, and `tests/test_geographic_maps.py`.

# Live sources and dashboard verification

Verified 27 October 2026, Asia/Kolkata. Project root:
`C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux`.

## Working sources

| Source | Result | Meaning |
| --- | --- | --- |
| IMD public SYNOP map layer | HTTP 200; verified station readings in all three cities | Station weather observations, with original UTC observation times |
| CAMS global via Open-Meteo | HTTP 200 in all three cities | Gridded atmospheric model estimates; US EPA AQI, never CPCB/Indian AQI |
| CPCB via data.gov.in | Connector implemented; unavailable without the user's API key | Official pollutant reports cannot yet be verified end to end |

IMD's authenticated current-weather endpoint returned 401 without credentials; the legacy endpoint required whitelisting. The [official public IMD map](https://mausam.imd.gov.in/index_en.php?lang=en) instead references a public WFS layer at `https://reactjs.imd.gov.in/geoserver/imd/ows`, using `service=WFS`, `version=1.0.0`, `request=GetFeature`, `typeName=imd:synop_data_layer`, `outputFormat=application/json`. This layer returned 466 station features during verification. Public feed availability is not a guaranteed service contract.

City configuration now records actual provider identifiers and coordinates, validated against city identity and a documented city reference:

| City | Preferred IMD station | Other mapped stations |
| --- | --- | --- |
| Delhi | 42182, New Delhi-Safdarjung | 42181 Palam; 42184 Ridge; 42180 Ayanagar |
| Chandigarh | 42105, Chandigarh-City | None |
| Chennai | 43278, Chennai-Nungambakkam | 43279 Meenambakkam |

The city reference coordinates use GeoNames results through Open-Meteo geocoding, with provenance in each YAML. They locate the map; they do not establish an infrastructure asset mapping. `verified_asset_mapping` remains false.

Example source responses at verification: Delhi Safdarjung 18.8 °C, 87% humidity, 0 mm rainfall over the preceding 24 hours; Chandigarh 18.4 °C; Chennai Nungambakkam 26.5 °C. These are recorded source values at specific observation times, not evergreen current conditions. Two Delhi station reports were older than the six-hour freshness threshold and correctly appeared stale. Rainfall is never converted into an unsupported hourly rate.

[CAMS/Open-Meteo documentation](https://open-meteo.com/en/docs/air-quality-api) describes the global model's approximate 45 km grid. The separate connector supplies PM2.5, PM10, US AQI and hourly model values. Its valid time is preserved; model issuance time is not available in this response. Future hourly conditions use a dashed chart line. The values are not monitoring-station observations or CivicFlux research-model forecasts.

## Enabling official CPCB access

1. Obtain your own API key through [data.gov.in](https://www.data.gov.in/). No account was created and no personal key was available during this work.
2. Copy `.env.example` to `.env` only if `.env` does not already exist. Set `DATA_GOV_IN_API_KEY=your_key` locally, preserving other settings.
3. Restart `START-CIVICFLUX.cmd`. Expand **Connect official CPCB access** in the dashboard for the same instructions.

The connector targets the [CPCB real-time resource](https://www.data.gov.in/resource/real-time-air-quality-index-various-locations), resource ID `3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69`. It checks city, state, country, station coordinates and source timestamps. Its no-key state is explicit. A public resource download attempt also failed from this host; successful authenticated connectivity remains unverified.

Raw `pollutant_avg` values have no unit verified by this connector. They therefore remain publisher reports with an explicit unverified-unit label. The code does not invent concentration units, derive an overall Indian AQI, or merge them with CAMS. A complete official feed still requires successful authenticated access and verification of publisher unit semantics. Source timestamps lacking a timezone are explicitly interpreted as Asia/Kolkata. Pagination completeness is reported.

Keys remain server-side, are excluded from cache key material and are not returned to the frontend. No API key is embedded in source files or Vite variables.

## Failure and freshness behavior

Providers are fetched independently so one outage does not remove other results. Source data is validated for identity, coordinates, finite values, units and future timestamps. Freshness uses source observation/valid time, not download time. IMD freshness is capped at six hours; CPCB and CAMS at three hours.

SQLite caches successful provider JSON for five minutes (IMD) or fifteen minutes (air feeds). A request failure may expose a previous response up to 24 hours old with a warning and stale status; its original timestamps remain intact. No cached response means unavailable. `CIVICFLUX_PUBLIC_FEEDS=0` disables provider requests. Optional existing canonical gateway overrides remain supported.

These environmental feeds are not automatically accepted as ML model inputs. Historical and synthetic model contracts and abstention rules remain in force.

## Attached image references and UI

Both supplied dashboard images informed the revised map-first overview: real station markers, independently toggled layers, compact environment cards, a resource ring, explainable plan choices and an event timeline. The interface retains the requested white/orange and black/green themes, glass controls and motion. The scroll-splitting city intro remains accessible through **Experience intro** rather than blocking access to the dashboard.

The default interactive map uses Leaflet and OpenStreetMap tiles with attribution. Google remains an optional reference view. Actual station and model-grid coordinates are distinct. Synthetic infrastructure remains in the separately labeled dependency graph, with 40 assets and 96 dependencies. The reference images' sample incidents, percentages, heatmaps and infrastructure coordinates were not treated as real project data. There is no verified city sustainability score, so the ring displays actual research readiness or hypothetical resource headroom.

All seven pages remain available: Overview, Predictions, Infrastructure, Cascade analysis, Planning, Operations and Model validation. This change connects `/api/observations?city_id=delhi` (also `chandigarh` and `chennai`) to the new sources and retains `/api/cities`, model inventory/predictions, scenario/graph, feedback and complaint workflows. `/openapi.json`, `/api/health`, `/api/models`, `/api/cities`, observation responses for all three cities and the built frontend were checked over actual HTTP.

## Validation

- 30 backend tests passed, zero failures/errors, including eight observation-source tests, API access restrictions, scenario integration, feedback persistence and portable model recovery. Evidence: `windows/live-source-tests.xml`. One existing Starlette/httpx deprecation warning remains.
- TypeScript and Vite production build passed. Output includes separate map and chart bundles.
- Real provider responses: `windows/live-source-verification.json`; actual server responses: `windows/live-source-http.json`.
- Browser verified Delhi, Chandigarh and Chennai updates; source marker popups; fresh/stale distinctions; layer toggles; source setup instructions; dependency graph; light/dark layouts and mobile width 390 px (no horizontal overflow).
- In isolated `var/live-source-preview.sqlite3`, admin ran a trained-surrogate heavy-rainfall scenario. CP-SAT returned OPTIMAL, 10 selected actions, hypothetical budget ₹48,677 / ₹50,000, 2 / 4 pumps, and crew hours within constraints. Review status stayed pending. Preview records were not inserted into the normal application database.
- Original research preservation recheck: all 290 protected datasets/notebooks/artifacts unchanged; 75 / 75 negative abstention checks passed. No retraining or notebook execution.

Screenshots: `windows/civicflux-live-control-room-dark.png`, `windows/civicflux-live-control-room-light.png`, `windows/civicflux-live-control-room-mobile.png`. They include an explicitly hypothetical research plan generated in the isolated preview. Approval remains prohibited by the existing research workflow; nothing is dispatched.

Restart the normal local application using `START-CIVICFLUX.cmd` to load the new adapters and final frontend build. The verification server on port 8001 is temporary and is stopped after testing. Official CPCB access, verified pollutant units and operational asset mappings remain the outstanding data dependencies.

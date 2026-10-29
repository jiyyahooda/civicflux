# Chennai and Chandigarh open-data integration — 30 October 2026

The user approved using the current application as the baseline because the referenced
main specification was not supplied. Delhi is excluded: no Delhi coordinates, data,
model files, source feeds, cards or normal portal navigation were changed. All original
103 PINs are retained. Eight directory-sourced Chennai PINs were added (111 total);
existing IDs and activation states are preserved. The 19 target non-Delhi PINs have
source-derived coordinates matching the supplied reference within 0.002 degrees.

This is a data integration, not model retraining. Authentication, jurisdiction checks,
budget calculations, saved scenario/model contracts and top-level tab order are retained.

## Commands and operation

Run from the CivicFlux project root after the usual native platform setup:

```sh
corepack pnpm run data:fetch
corepack pnpm run data:build
corepack pnpm run data:verify
corepack pnpm run data:status
corepack pnpm run preflight -- --warm
corepack pnpm run verify
```

`data:verify` checks snapshot integrity; `data:verify -- --strict` additionally fails
when mandatory sources are unavailable. `verify` includes strict data verification,
the Python regression suite and the frontend production build. Currently strict source
completeness exits 1: the 2015 zone resource returns HTTP 404 and both Overpass requests
return HTTP 406 in this environment. These layers are not fabricated or shown as empty
successful datasets. The app remains usable without them. Rerun fetch/build on a network
that permits the fixed Overpass endpoint. A removed OpenCity resource needs a verified
replacement ID and an explicit catalogue update, not an invented URL.

The Node wrapper selects `.venv/bin/python` on macOS and `.venv-windows/Scripts/python.exe`
on Windows (or native `.venv/Scripts/python.exe`). Normal launch: `bash scripts/start_mac.sh`
on macOS or `START-CIVICFLUX.cmd` on Windows; open http://127.0.0.1:8001/.
Development uses the existing backend on 8001 and Vite on 5173.

Raw downloads and CKAN metadata are ignored under `data/raw/open_city/`. Processed files,
`seed/pincodes.json` and `data/manifest.json` are intended for Git and require no deployment
network access. Fetching allows only fixed HTTPS hosts and revalidates redirects. Downloads
use 60-second request timeouts and up to two retries. Live calls run independently under a
three-second total deadline per kind, with a persisted 30-minute cache and stale fallback.
No browser call goes directly to these data APIs. Existing map tiles/integrations are unchanged.

## Verified changes to supplied fixtures

The user explicitly approved using the verified downloaded structures:

- PIN directory SHA256 matches exactly; 157126 rows, 19300 PINs. Missing latitude is
  represented by `NA` in 8838 rows, rather than an empty CSV string.
- Hazard CATEGORY has five explicit values: Very Low, Low, Moderate, High, Very High.
  All five are retained with a labelled sequential blue legend; no merging or invented classes.
- Reservoir files use a Year column plus Jan–Dec columns, rather than date/storage rows.
  Their actual last observations are December 2021, despite 2025 catalogue dates.
  Null month padding is retained; first_month denotes the first non-null measurement.
  Puzhal units are confirmed by the recorded CKAN description, which explicitly says mcft.
- Provided capacity constants sum to 13222 mcft. Their official CMWSSB verification is
  still pending; the site withholds percent-full calculations and labels this limitation.
- No open facility snapshot was downloaded here. No operational complaint data or simulated
  reports were inserted. Optional D8/D9 extras were skipped because mandatory source completeness
  is not green.

## Source status and provenance

Exact URLs, resource IDs/commits, retrieval times, attribution, raw byte counts and checksums,
input/output counts, geometry processing and served sizes are in the manifest. This table
reports actual results, including unavailable sources.

| Source ID | Status | Input → output records | Served gzip bytes | Licence | Raw SHA256 | Used by |
|---|---|---|---|---|---|---|
| chd_boundary | OK | 1 → 1 | 3820 | CC BY-SA 2.5 India | 47b39133b1f349b7afe74f6be6dc56dfe2cafa901939365e518e81e60e03e679 | Map scenario boundaries and coordinate validation |
| chd_sectors | OK | 63 → 63 | 5368 | CC BY-SA 2.5 India | 06c17c07e07c2999d684feac37e360d103d2f2d5e478563dff4418dc2718e995 | Map scenario boundaries and coordinate validation |
| che_cma | OK | 1 → 1 | 6403 | CC BY-SA 2.5 India | 89e81f8309a40ea9f24cf5e35c832b75ed937b65b111389d8ed8df4931804ad7 | Map scenario boundaries and coordinate validation |
| che_flood_hazard | OK | 7453 → 7189 | 1301046 | Public Domain | edfc46d45b49e5850d4e37d785d9560c0df81e40e280730cb7df7de7ce527a59 | Historical flood exposure, never an operational warning |
| che_flood_points_2015 | OK | 753 → 753 | 27472 | Public Domain | 5b7d79bc3ba0b59ef5b14b79d8eba65caa905eaf0f5f468b33a6177ffb16704e | Historical flood exposure, never an operational warning |
| che_flood_zone_2015 | NOT FETCHED | None → None | — | Public Domain | NOT FETCHED | Historical flood exposure, never an operational warning |
| che_inundation_points | OK | 192 → 192 | 4325 | Public Domain | b4bbbdaeb62c78151cee81d33d993dac51f2af9595bbcd275d75440ea1e6215b | Historical flood exposure, never an operational warning |
| che_wards | OK | 201 → 200 | 58258 | CC BY-SA 2.5 India | 2dff80b6f514e644b9a428696909216e9d22aedd07c8ebab33192ec9e3cb1ab2 | Map scenario boundaries and coordinate validation |
| facilities_chandigarh | NOT FETCHED | None → None | — | ODbL | NOT FETCHED | Nearby facility reference points; availability is unknown |
| facilities_chennai | NOT FETCHED | None → None | — | ODbL | NOT FETCHED | Nearby facility reference points; availability is unknown |
| lake_chembarambakkam | OK | 228 → 228 | 5735 | Public Domain | 6437baa8db19d5f2ae4f23799a883b4326d398c4c3b739d1ee80d99ca7c41ce9 | Historical monthly reservoir storage |
| lake_cholavaram | OK | 228 → 228 | 5735 | Public Domain | 725e4d77f41fb185eb06f267e5ccd270083d244a32bf880dada1fd2f3581cf6b | Historical monthly reservoir storage |
| lake_kannankottai | OK | 24 → 24 | 5735 | Public Domain | cdc29fd8cb5ae7bf5494d1ef1f40882c37fde5032939ecf534dd519f6b7f175f | Historical monthly reservoir storage |
| lake_poondi | OK | 228 → 228 | 5735 | Public Domain | 292ea15b679827e8e047dceb789d4c941d90944c626324cae4eb80703bdcc7e8 | Historical monthly reservoir storage |
| lake_puzhal | OK | 228 → 228 | 5735 | Public Domain | ed62df0a3a0b702c3509e9e5aa6013b68de0305dbf30bcbb1966d30d2f19a9f2 | Historical monthly reservoir storage |
| lake_veeranam | OK | 228 → 228 | 5735 | Public Domain | b1babdeacf8bcab065bd074bc0c653586d89f4567c4b576ec8ef213fc6b8204c | Historical monthly reservoir storage |
| pin_directory | OK | 157126 → 19 | 950 | GODL-India | 84af12fa29adddedfa9addcf46546000d89d2e2899b2993dc88050fafc8861e2 | Postal reference points; Delhi is excluded from all updates. |

## Geometry and exposure evidence

The hazard source contains 7453 placemarks. Topology repair was required 38 times; 264 features collapse under the required 0.00001-degree grid. All remaining 7189 output geometries are valid. Original object IDs are preserved. The simplification tolerance is 2e-05 degrees. Class-wise combined repair/rounding/simplification geodesic area drift: {"High": 0.00023299747486234162, "Low": 0.0002205335766952398, "Moderate": 0.00024341007530393106, "Very High": 0.0002651576539146891, "Very Low": 0.00015698651197249035}. The maximum is below 0.027%, well within the 2% gate. The hazard gzip is 1300428 bytes; each served layer is below 1.5 MB gzip and all processed files total under 7 MB.

Exposure uses 2 km great-circle distance from the postal point, not the full PIN area. Missing layers produce null metrics, never zero or “safe”. Chandigarh has no flood fields in its UI. Facility deduplication, typed symbols and exposure computation are implemented and fixture-tested, but real facility counts are unavailable until a successful Overpass fetch.

## UI and endpoints

Chennai/Chandigarh Overview adds Conditions below the weather/forecast content. Chennai also shows six historical reservoir series and accessible 24-month values. Decisions → What-if assessment → Map scenario uses the existing Leaflet instance with lazy boundary/flood toggles, visible linked attribution, a postal point and text containment alternative, plus Exposure and services. Delhi receives none of these new cards/layers. Data and sources is reachable through non-Delhi footer links and an admin header action, without inserting a top-level tab. The catalogue can also be opened at `/data-sources`.

Public endpoints: `/api/data/layers?pin=`, `/api/data/layer/{fixed_id}`, `/api/data/manifest`, `/api/data/exposure?pin=`, `/api/data/reservoirs?pin=`, `/api/live/conditions?pin=`. Admin layer/conditions endpoints derive PIN from the session and ignore a client `pin` parameter; public requests in an admin session cannot cross its PIN/city. Static layers use ETag, negotiated gzip and one-hour public cache headers. Raw downloads are never served.

## Verification evidence

- 174 tests pass, including 26 additional parameterized/open-data tests; all prior regressions pass with expected Chennai seed coverage updated from 2 to 10.
- Production TypeScript/Vite build passes. Existing large Three.js chunk warning remains.
- All nine saved model components load; supported prediction/abstention smoke checks pass; pip check reports no conflicts.
- All 313 original data/config/model/notebook file hashes match the pre-change baseline.
- Two real-source builds produced byte-identical processed files. A separate tiny offline-fixture build is also tested twice.
- Snapshot integrity passes. Strict source completeness is INCOMPLETE (three sources), not claimed as PASS.
- Live preview preflight: air returned for all 19 target PINs; river returned for all 9 Chandigarh PINs and 4 of 10 Chennai PINs. Other river results remain unavailable, with no coordinate nudging or false local-river identity. Availability is provider-dependent.
- Browser preview checked Chennai ward 176 / ADYAR, flood toggle and five-class legend, exposure values, six historical reservoir cards, source catalogue, Chandigarh sector 17 with no Chennai flood toggle, and Delhi with no new cards/layers. No console errors observed in these checks; no horizontal overflow at the tested desktop viewport. This is not a claim of exhaustive device or native Windows testing.
- Test databases and preview are isolated from operational records; private backups are outside Git.

## Attribution and evaluated sources

- Chandigarh boundary: Chandigarh Municipal Spatial Data via DataMeet India community (CC BY-SA 2.5 India); CC BY-SA 2.5 India. [Source](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chandigarh/Chandigarh_Boundary.geojson).
- Chandigarh sectors: Chandigarh Municipal Spatial Data via DataMeet India community (CC BY-SA 2.5 India); CC BY-SA 2.5 India. [Source](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chandigarh/Chandigarh_Sectors.geojson).
- Chennai metropolitan outline: Chennai Municipal Data, received from the Transparent Chennai team, via DataMeet India community (CC BY-SA 2.5 India); CC BY-SA 2.5 India. [Source](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chennai/CMA.geojson).
- Flood hazard zones: Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=e61afe07-0f52-4be9-bdf3-5eb0f62b2ed6).
- Flooding points in 2015: Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=80ed2fa7-1150-4f55-8125-682ab55282ac).
- 2015 inundation zone: chennaifloodsdss.in via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=7cb3cecf-a95a-4786-8032-9c7417655d24).
- Inundation depth points: Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=ceddf53f-03c0-4866-8ba8-5e84c8007a85).
- Chennai wards: Chennai Municipal Data, received from the Transparent Chennai team, via DataMeet India community (CC BY-SA 2.5 India); CC BY-SA 2.5 India. [Source](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chennai/Wards.geojson).
- Chandigarh facilities: ©️ OpenStreetMap contributors (ODbL); ODbL. [Source](https://overpass-api.de/api/interpreter).
- Chennai facilities: ©️ OpenStreetMap contributors (ODbL); ODbL. [Source](https://overpass-api.de/api/interpreter).
- Chembarambakkam historical storage: Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=db41b1a4-5746-46d0-a006-e8fe2b1545a9).
- Cholavaram historical storage: Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=20dc9876-ef1d-4cf1-9c42-f9d6c1f137db).
- Kannankottai-Thervoy Kandigai historical storage: Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=e0355257-d2d9-48be-a31e-6596a5fcdc07).
- Poondi historical storage: Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=8b0c0edc-4204-4f0f-8dc7-2db4817af04f).
- Puzhal (Red Hills) historical storage: Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=febf2951-71eb-4807-9a06-246dadc1ef04).
- Veeranam historical storage: Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain); Public Domain. [Source](https://data.opencity.in/api/3/action/resource_show?id=a2f9aaad-7ac2-4a01-90d6-801eeef7d4b6).
- All India Pincode Directory: Department of Posts, Government of India, All India Pincode Directory (data.gov.in), Government Open Data License - India, via community mirror; GODL-India. [Source](https://raw.githubusercontent.com/dropdevrahul/pincodes-india/d817d3e652e8167a70507350d9a8e4acda9113ef/pincode.csv).

Live: Air quality: CAMS ENSEMBLE data provider (Copernicus Atmosphere Monitoring Service) via Open-Meteo.com; River discharge: GloFAS via Open-Meteo.com. Weather: Weather data by Open-Meteo.com (CC BY 4.0). Free public Open-Meteo endpoints are non-commercial. Derived DataMeet layers remain CC BY-SA 2.5 India; their licence notice is shipped alongside them.

- **Chandigarh wards**: Duplicate ward 5, reserve polygon, missing and duplicated population values; sectors used instead.
- **Chennai Wards-2008**: Pre-2011 boundaries; excluded.
- **Princeton / Stanford Chandigarh shapefiles**: Access restricted.
- **Census 2011 ward data**: Identifiers do not match shipped layers; no formula requires it.
- **GCC Budget 2026-27**: PDF; link only: https://data.opencity.in/dataset/gcc-budget-2026-27
- **GCC Relief Centres**: October 2024 PDF; link only: https://data.opencity.in/dataset/gcc-relief-centres
- **GCC stormwater base maps**: PDF; link only, not parsed.
- **Return-period flood KMLs**: Out of scope.
- **GCC GIS REST server**: Availability and licence unconfirmed.
- **Smart Cities portal**: No Chandigarh catalogue enumerated.
- **Complaint datasets**: No verified open complaint data supplied; existing records retained, no synthetic operational reports added.
- **AQICN**: Requires token and separate terms; existing Delhi integration unchanged.
- **GCC fire stations**: Optional; no licence stated, not redistributed.
- **GCC health centres**: Optional, not integrated; coordinate columns not verified.
- **GCC flood hotspots 2020**: Optional; not integrated.
- **CPCB data.gov.in**: Optional; no verified API resource/key configured for this integration.

## Activation and launcher

The tested backend was activated on 8001 while Vite remained on 5173. A fresh private SQLite backup was taken immediately before activation. All 77 original Delhi administrator rows and 55 pre-existing operational records matched that backup; the original 313 data/config/model/notebook file hashes also matched. The real launcher HTTP check passed. The POSIX launcher probe now uses the same SO_REUSEADDR behaviour as uvicorn so a normal restart does not mistake TIME_WAIT sockets for an active server; Windows exclusivity is unchanged. Live verification on 5173 confirmed the Chennai hazard layer, ward containment and exposure panel with no console errors or horizontal overflow at the current mobile viewport.

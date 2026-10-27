# CivicFlux platform enhancement — 27 October 2026

The existing application was enhanced locally. GitHub work is paused at the user's request; no push or merge was performed for these changes.

## Delivered application behavior

One header navigation contains six public pages: Overview, City map, Infrastructure, Predictions, Report a problem, and Open reports. Review reports and Planning appear only after sign-in, with authorization enforced by the backend. Opening animation, theme, fonts, existing stylesheet files, icons, forecast plots, model contracts, notebooks, saved models, review restrictions and SQLite records are preserved.

Overview now centers on available city observations, Open-Meteo current weather, seven-day forecasts, hourly rainfall/temperature, air-quality trends, the real geographic map, official-source links, active imported notices and public reports. The monsoon scenario and resource proposals are confined to administrator Planning. Source health remains available to administrators. Model validation and the original technical request editor remain inside administrator-only details on Predictions.

City changes filter every public context/report/weather consumer by city identity, including the transition while requests are loading. Previous-city observations, budgets, notices and incidents cannot be carried into another city's UI. The original city configuration supplies the map centers and IMD station identity mappings.

## Nine components, eleven notebooks

Notebook 10 compares and validates models. Notebook 11 validates integration. They are supporting studies, not two additional predictors. All eleven notebook headings and all exported feature schemas were inspected without executing notebook cells.

| Component | Existing implementation | Verified result | Applicability and uncertainty |
|---|---|---|---|
| Rainfall | Saved Random Forest bundle | Loads and predicts | Delhi historical state aggregate; saved 90% residual interval |
| PM2.5 | Saved Ridge bundle | Loads and predicts | Delhi historical aggregate; lineage/unit caveats retained; saved interval |
| Traffic | Original XGBoost/preprocessing with existing verified portable export | Loads and predicts | Anonymous benchmark junctions; no named-road mapping; saved interval |
| Flood/catchment | Saved XGBoost plus existing separate water-balance tool in Planning | Loads and predicts | Hypothetical catchment; calibrated scenario score is not an actual city flood probability or depth |
| Infrastructure anomaly | Existing saved detector collection | Loads and predicts | Registered benchmark sensors; score/threshold is not equipment-failure probability |
| Water network | Existing L-TOWN bundle | Loads and predicts | Simulated benchmark network; weak onset evidence, operational abstention retained |
| Cascade | Existing graph and fitted cascade component | Loads and predicts | Explicitly declared outages on the compatible hypothetical network |
| Resource optimization | Existing OR-Tools CP-SAT code and comparison algorithms | Executes feasibly | Declared candidate costs, pumps, crew-hours and budget; no live municipal inventory implied |
| Intervention outcomes | Existing saved duration component | Loads and predicts | Benchmark duration only; success probability and causal benefit remain unavailable |

`backend/api/assessments.py` adapts the actual serving outputs into readable summaries, numerical measures, intervals and charts. It does not create replacement predictions. Public inputs follow the saved schemas and supported numeric/category ranges. Optional CSV history uses the original time/entity/value columns. Unsupported live-city requests return an unavailable result. The serving functions, model metadata, uncertainty calculations and trained files are unchanged.

## Public reports and officer review

New public multipart submission requires title, category, address/locality, description, listed city PIN, valid email and 1–3 actual JPEG/PNG files. Each image is capped at 5 MB and 20 million pixels, validated by decoding, oriented, resized and re-encoded without EXIF, and stored using a generated filename beside the SQLite database. Filenames supplied by users are not used as storage paths. Private email/internal notes are excluded through a public response allowlist. Uploaded photos and descriptions are explicitly public.

Reports receive persistent IDs and survive reload. Open reports offers city, issue-type and status filtering, photos, timestamps, verification status and public officer replies. A report pin appears on the public map only after an officer verifies its coordinates and marks the report valid. No benchmark assets are placed at invented city coordinates.

Officers can correct the category/address, record validity, urgency, department, private notes, public reply, completion evidence and resource proposals. Completion requires an evidence reference. Resource proposals require a current authorized roster and cannot individually exceed it. These proposals do not reserve inventory or dispatch workers. An audit entry records changes. Separate scenario review and independent outcome verification remain available.

The legacy JSON complaint-creation API is retained for authorized administrative imports. The public form uses the stricter new multipart API. Two existing tests were migrated to the intentionally changed authentication/upload contract; their status-transition and routing checks remain. New tests also ensure there is no anonymous legacy bypass.

## Planning and infrastructure

Planning has Current situation and What-if assessment modes. Current situation shows confirmed records, current available observations and a separately recorded operational roster. With no confirmed issues it displays the requested sentence: “No confirmed active issues in the available records.” Missing information remains distinguishable from an empty confirmed queue.

What-if mode preserves flood controls, declared outages, service pressure, the interactive graph, all resource constraints, prior saved plans, policy-weight controls, review and independent verification. Plans use the requested readable labels: Recommended plan, Benefit-first alternative, and Urgent-issues-first alternative. The UI reports selected/unaddressed candidates, proposed costs, pump use, crew-hours and remaining assumed budget. Algorithm labels and objectives are inside technical details.

Before/after comparison covers defensible capacity and budget arithmetic. It does not invent prevented failures, population affected, water saved, carbon savings, travel-time benefits or success probabilities. Headcounts cannot be derived from crew-hours; vehicles are not a supported constraint in the supplied optimizer. The outcome duration reference remains independent rather than being falsely fused into a city intervention-effect estimate.

Infrastructure exposes water/drainage, roads/traffic, air-quality issues, verified publications, operational resources, active incidents and notices. Authorized import forms support source-linked historical budget/staffing figures and current dated resource rosters. There are no confirmed publication figures or operational rosters in the live workspace, so those panels explicitly show unavailable information.

## Sources, maps and remaining external limits

- Weather: [Open-Meteo Weather documentation](https://open-meteo.com/en/docs). Current units, city/grid identity, timestamps and daily dates are validated. The current source offers a city grid, not fine-resolution rainfall coverage.
- Air: [Open-Meteo Air Quality / CAMS](https://open-meteo.com/en/docs/air-quality-api). PM2.5/PM10 units and provider US AQI are retained; regional source resolution is disclosed. The marker colors follow the [AirNow US AQI categories](https://www.airnow.gov/aqi/aqi-basics/), not Indian AQI.
- The supplied application actually uses Leaflet/OpenStreetMap. Its map remains working; no MapLibre installation existed in this repository. Map modes change source markers and accompanying cards. No unsupported pollution gradient or arbitrary neighborhood rainfall layer is generated from a single grid sample.
- Google traffic is implemented using the official [Maps JavaScript API TrafficLayer](https://developers.google.com/maps/documentation/javascript/trafficlayer), on a separate Google Map. Live traffic is unverified because no restricted browser key was supplied. Activation, billing, HTTP-referrer/API restrictions and coverage must be verified in the user's Google project. The original Google geographic-reference embed remains available separately. Google tiles are not copied onto the Leaflet map.
- Traffic sources: [Delhi Traffic Police](https://traffic.delhipolice.gov.in/en/news-alertadvisory/advisory), [Greater Chennai Traffic Police](https://gctp.in/), and [Chandigarh Police](https://portal.chandigarhpolice.gov.in/). No invented real-time official API or ongoing prohibited scraping is used. A reviewed Delhi notice snapshot is included with explicit start/end dates and a source link; its active display expires automatically. Chennai and Chandigarh currently have source links but no active imported official notice records.
- Postal records come from [Delhi government](https://dmnewdelhi.delhi.gov.in/std-pin-codes/), [Chennai district](https://chennai.nic.in/public-utility-category/postal/), and [Chandigarh district](https://chandigarhdistrict.nic.in/about-district/std-pin-codes/). Exact listed records are used, never a PIN prefix rule. Coverage is partial: 410 Delhi locality records, 50 Chandigarh records, and two Chennai postal areas. Unlisted PINs need an authoritative reference update. There are no verified city-boundary polygons included; location verification remains an officer responsibility beyond the broad vicinity sanity check.
- No city budget, workforce or available crew figure was invented. Source-linked publication and roster import tools are functional; sourcing a complete municipal inventory is still required. Chennai's official finance publications are available at [GCC Finance](https://chennaicorporation.gov.in/gcc/department/finance/); annual figures must not be treated as current dispatch funds.
- CPCB remains optional and unavailable without its key. No active OpenWeatherMap adapter existed in this source; the UI says it is not configured.

## Verification

- Existing environment: **94 tests passed**, one Starlette/httpx compatibility deprecation warning.
- Clean minimal environment: **94 tests passed**, same warning. New Pillow, multipart and email-validation dependencies installed successfully; `pip check` passed.
- Original model/API smoke script passed saved-artifact loading, bounded predictions, abstention, SQLite, authentication, flood/cascade and resource planning.
- TypeScript compilation and Vite production build passed. The pre-existing large WebGL chunk warning remains nonblocking.
- Real HTTP provider checks returned seven daily forecast rows and 48 hourly weather points for each city. IMD and CAMS were fresh in Delhi, Chennai and Chandigarh; CPCB was unavailable without a key. Full recorded results are in `civic-enhancement/live-check.json`. Provider status can change later.
- Browser checks covered all six public tabs, city switching to Chennai, mode-dependent air-map content, the real saved rainfall result and its interval, required reporting fields, admin login/logout, both Planning modes, existing graph/plans, and the Review reports tools. Clean-reload admin Planning produced no new browser errors. A temporary HMR error occurred while component props were edited; final props and a clean page load were rechecked successfully.
- Report uploads, private-note exclusion, persistence, public replies, expired notices, protected endpoints and roster limits were exercised with temporary test databases. No fake citizen reports or operational rosters were inserted into the live workspace for screenshots.
- **273 original artifact/notebook files were rehashed and remain byte-identical**, including all eleven notebooks and trained artifacts. No training or notebook execution occurred.
- Native Windows execution has not been performed in this Mac session. The existing cross-platform dependency/startup work remains, but Windows browser/runtime QA is not claimed.

Local application: http://127.0.0.1:5173. API documentation: http://127.0.0.1:8001/docs.

## Files changed

- `.env.example`
- `README.md`
- `backend/api/assessments.py`
- `backend/api/civic.py`
- `backend/api/feedback.py`
- `backend/api/scenarios.py`
- `backend/db/repository.py`
- `backend/integrations/weather.py`
- `backend/main.py`
- `backend/services/civic_service.py`
- `config/official_notices.json`
- `config/postal_reference.json`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/components/CascadeGraph.tsx`
- `frontend/src/components/CivicPanels.tsx`
- `frontend/src/components/DeveloperTools.tsx`
- `frontend/src/components/GoogleTraffic.tsx`
- `frontend/src/components/RainfallChart.tsx`
- `frontend/src/components/ResourceAllocation.tsx`
- `frontend/src/components/ReviewPanel.tsx`
- `frontend/src/components/SourceStatus.tsx`
- `frontend/src/components/StationMap.tsx`
- `frontend/src/enhancements.css`
- `frontend/src/main.tsx`
- `frontend/src/pages/Cascade.tsx`
- `frontend/src/pages/CityMap.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Infrastructure.tsx`
- `frontend/src/pages/OpenReports.tsx`
- `frontend/src/pages/Planning.tsx`
- `frontend/src/pages/Predictions.tsx`
- `frontend/src/pages/ReportProblem.tsx`
- `frontend/src/pages/ReviewReports.tsx`
- `frontend/src/pages/ScenarioPlanning.tsx`
- `frontend/src/types/civic.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/vite.config.ts`
- `reports/civic-enhancement/build.txt`
- `reports/civic-enhancement/clean-tests.txt`
- `reports/civic-enhancement/live-check.json`
- `reports/civic-enhancement/model-smoke.txt`
- `reports/civic-enhancement/overview.png`
- `reports/civic-enhancement/planning.png`
- `reports/civic-enhancement/prediction-result.png`
- `reports/civic-enhancement/tests-final.txt`
- `requirements-backend.txt`
- `tests/test_api_feedback.py`
- `tests/test_civic_workflows.py`
- `tests/test_current_outlook_and_routing.py`

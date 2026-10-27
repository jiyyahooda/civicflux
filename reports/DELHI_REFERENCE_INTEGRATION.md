# Delhi reference, resource review and model integration

Verified locally on macOS, 27 October 2026. GitHub publication is paused; no commit or push was performed.

## Result and scope

The existing application at `http://127.0.0.1:5173/` now displays the supplied Delhi briefing in Infrastructure and compact reference panels in Overview, City map and Planning. All nine saved model/algorithm assessment adapters remain connected to the original `src/civicflux/serving.py`. No retraining, artifact migration or replacement serving framework occurred. Eleven notebooks remain eleven research studies, not eleven predictive models. No reference screenshots were supplied with this request, so the new panels follow the existing interface rather than claiming a pixel match.

The actual repository contains a Three.js orbital/globe welcome scene and Leaflet maps, rather than the building and MapLibre mentioned in the request. Those existing implementations were preserved. A small floating movement respects reduced motion; initialization progress reflects actual ready component counts. Native Windows/mobile rendering was not tested.

## Project structure and changed areas

```text
backend/
  api/assessments.py       registry-backed assessment forms and adapters
  api/references.py        city-specific reference JSON and source PDF
  api/resources.py         authorized pools, atomic reservations, decision history
  api/civic.py             existing report review and roster constraint checks
  db/repository.py        additive table initialization
  services/civic_service.py  reference/current-pool context
  main.py                 additional routers
frontend/src/
  components/DelhiReference.tsx
  components/OperationalResources.tsx
  components/ImpactComparison.tsx
  components/ResourceAllocation.tsx
  components/StationMap.tsx
  components/CascadeGraph.tsx
  components/CityHero.tsx, FluxScene.tsx, ReviewPanel.tsx
  pages/Infrastructure.tsx, Dashboard.tsx, CityMap.tsx
  pages/Planning.tsx, ScenarioPlanning.tsx, Predictions.tsx
  types/reference.ts, operational.ts, civic.ts
  enhancements.css
 data/reference/
  delhi_reference.json
  delhi_mcd_budget_2025_26.csv
  delhi_drainage_basins.csv
  delhi_official_road_corridors.csv
  delhi_transport_2025_26.json
  delhi_infrastructure_reference.pdf
 tests/test_reference_and_resources.py
 tests/test_api_feedback.py
 README.md
 reports/delhi-integration/   logs, discovery inventory, preservation proof, screenshots
```

This is additive to the existing report/photo/authentication/notice/forecast implementation and previous uncommitted enhancements. No database was replaced. The full working-tree list is in `delhi-integration/working-tree.txt`.

## Discovered artifacts and selected components

Eleven `.joblib` files were found. `delhi-integration/model-inventory.json` contains exact paths, byte sizes, registry metadata and schema references. Its discovery-time readiness fields predate inference; the subsequent execution evidence below is authoritative for tested callability. Older versions remain intact.

| Component / Predictions location | Selected artifact/version | Human input and supported result |
| --- | --- | --- |
| Rainfall / Weather and air | rainfall/pipeline.joblib, legacy unversioned | Original Delhi state-aggregate daily history (`date,state_name,actual`), mm/day, assessment clock; next-day research forecast |
| PM2.5 / Weather and air | aqi/pipeline.joblib, legacy unversioned | Original Delhi aggregate hourly history (`timestamp,location_name,pm25`), declared source units, clock; next-hour research forecast, lineage limitations retained |
| Traffic / Roads and water | traffic/pipeline.joblib, legacy unversioned | Anonymous registered junction and historical counts (`DateTime,Junction,Vehicles`); next-hour count, no real-road assignment |
| Waterlogging / Roads and water | flood/pipeline.joblib, legacy unversioned | Existing catchment/precipitation/condition assumptions and validated units; hypothetical flood assessment score, not depth |
| Unusual readings / Infrastructure | infrastructure_anomaly/v1.0.0/detectors.joblib | Supported registered sensor selection plus timestamped value history (`time,value`); actual saved detector score and alert threshold |
| Water network / Roads and water | water_network/v1.1.0/pipeline.joblib | L-TOWN reference or all three CSV families: Pressures, Flows, Levels, original Timestamp/sensor columns/order, at least 24 hours at 5-minute intervals; weak benchmark onset assessment |
| Knock-on disruptions / Infrastructure | cascade_risk/v1.1.0/pipeline.joblib | Declared initial outages and scenario assumptions on existing synthetic service graph; propagation assessment and connected graph |
| Resource recommendation / Planning and outcomes | registry version 1.1.0, existing OR-Tools algorithm, no joblib | Original scenario candidates, priority weights, budget, pumps, crew-hours; CP-SAT allocation and two baseline comparisons under identical limits |
| Duration reference / Planning and outcomes | intervention_outcomes/v1.1.0/pipeline.joblib | Existing declared intervention/case assumptions; completed synthetic intervention duration research, no real-world success promise |

Additional files discovered: water_network/v1.0.0, cascade_risk/v1.0.0 and intervention_outcomes/v1.0.0 pipelines. Registry selection remains at v1.1.0. No additional trained models were manufactured from notebooks 10/11. Model/schema/metadata internals remain in authorized technical details.

CSV inputs require unit confirmation; malformed or incompatible histories abstain or return validation errors. Freshness is relative to the declared benchmark clock, not the current city clock. No component is certified for live local prediction. Five actually trained anomaly sensor suites are selectable; a specification without a trained detector is not presented as callable. Compatible histories can be supplied when an original raw benchmark dataset is absent.

## Delhi data provenance and corrections

The supplied six-page briefing is preserved byte-for-byte and linked in the UI. Normalized records retain fiscal/measurement date, original source attribution, briefing page, primary page where known, scope and verification status.

- Budget: 16 department/year rows, eight groups in each of FY 2024-25 revised estimate and FY 2025-26 budget estimate. Reported totals are 15,767.78 and 17,011.92 crore INR. Group sums are 15,534.60 and 16,131.02 crore. Unresolved differences of 233.18 and 880.90 crore are prominently flagged; no missing head or available cash is inferred. The original MCD budget PDF was not supplied, so its page references remain attributed to the briefing and primary verification is pending.
- Drainage: Najafgarh 123, Barapullah 44, Trans-Yamuna 34, total 201 natural drains. These are the 1976 inventory reproduced in a 2018 plan, not all current street drains. [Attributed DDA drainage plan](https://dda.gov.in/sites/default/files/qac/Main_report%20DMP_Version506092018.pdf) was unavailable during the primary fetch. No verified named-drain/GIS list was provided.
- Roads: 29 Category-A entries, including 9A, transcribed with approximate lengths and briefing pages. [Attributed Delhi Traffic Police inventory](https://traffic.delhipolice.gov.in/major-corridors) did not respond during verification. No geometries were invented and these rows do not become traffic incidents.
- Transport: checked against [Delhi Economic Survey 2025-26](https://delhiplanning.delhi.gov.in/sites/default/files/2026-03/economic_survey_english_0.pdf): 8,761,919 registered motor vehicles at 19 March 2026 (PDF p261); 6,100 public buses (p256); 4,338 electric buses and 2,983 bus marshals/Home Guards (p259); approximate 352 km metro network and separate GNCTD transport allocation/utilization references (p268). Workforce figures describe transport deployment, not deployable municipal staff. An inconsistent vehicle-share percentage was deliberately omitted.

Historical annual allocations, registered fleets and staffing references never populate operational inventory. Chennai/Chandigarh return unavailable reference states instead of inheriting Delhi figures. No OpenCity dataset was supplied or imported.

## Resource allocation, review and impact

Admin Planning has four capacity cards. Missing authorized pools display **Not recorded**. No demonstration roster was inserted into the live database. The create/edit form requires city, department, service area, specialization, workers on shift/available, crews, pumps, vehicles, discretionary budget, skill-specific crew-hours, equipment notes, dates and authorization reference. Responsible admin and update time are persisted.

Pools expose assigned and unreserved amounts. Only current pools count as available. Overlapping duplicate rosters with the same city/department/area/specialization are rejected. Pools must represent disjoint inventory; the system does not independently identify individual equipment IDs or prove ownership.

A supervisor selects the actual saved plan, enters crew/worker/vehicle packages for its selected actions and adds a note. The backend derives cost/pumps/crew-hours from the saved optimizer result rather than trusting submitted totals. City, validity and all capacities are checked inside the same SQLite `BEGIN IMMEDIATE` transaction as reservation and review writes. Competing requests cannot consume the same remaining capacity. Reapproval excludes its own old hold, supersedes it and preserves history. Deferral, rejection, change request or release frees its hold. Inventory edits cannot reduce below held capacity. Expired pools are excluded from current availability; holds are conservative capacity accounting, not a scheduling/completion system.

Internal approval does not approve research models for deployment. Existing scientific review still rejects approval, and every new decision explicitly records external_dispatch=false. No staff, agency or outside service was contacted.

The actual CP-SAT plan and existing utility/severity baselines populate action tables, costs, time, pump requirements, unresolved candidates and capacity meters. Priority explanations show actual signed weighted scenario contributions with readable labels. Headcounts/vehicles require officer assignment. Scenario asset names are explicitly hypothetical; source/uncertainty and missing exposure data remain visible.

Impact cards compare assessed problems with proposed spending/resources and unresolved issues. Before/proposed graph views highlight selected inspection assets against unchanged assessed risks. The models do not establish causal reductions in flooding, emissions, exposed residents or failure rates, so these remain unavailable. Highlighting an inspection never implies a repair was performed.

## Maps, auth and preservation

Leaflet continues to request visible OpenStreetMap raster tiles with attribution. Dark mode styles the existing tiles. OSM community tile hosting is subject to its [usage policy](https://operations.osmfoundation.org/policies/tiles/); free software does not confer unlimited hosted tile capacity. No bulk downloads, new provider or fictional geographic lines were introduced. The separate optional Google Traffic integration still requires a configured restricted key; no live Google verification was possible.

Verified report pins have category glyphs and urgent coloring, readable detail cards, mode filtering and aggregation below zoom 13. Existing weather and CAMS source markers remain distinct. No current verified incident records exist in the live local database, so cluster interaction with multiple reports was not browser-tested. Basin/corridor shading is unavailable without verified boundaries/geometry. Resource counts without verified positions remain in panels.

Public report/image/PIN/email validation, public privacy allowlists, admin sessions, report review, notices, completion evidence and audit trails remain covered by the passing suite. New pool and decision endpoints require admin authorization. Public pool summaries exclude authorization references and responsible-admin identity. Existing palette, theme toggle, public/admin navigation and graph interactions are retained.

SHA-256 comparison against the original baseline: **273 artifact/notebook files checked, zero changed**. See `delhi-integration/preservation.json`.

## Verification evidence

- Project Python environment: **100 passed, 1 warning**, 7.17s (`tests.txt`).
- Clean pinned-dependency environment: **100 passed, 1 warning**, 7.09s (`clean-tests.txt`).
- `python -m pip check`: no broken requirements.
- `npm run build`: TypeScript and Vite production build passed, 2.04s; nonblocking existing Three.js chunk-size warning.
- All nine adapters executed the actual saved serving/algorithm system and returned supported benchmark/simulation metrics in `test_all_nine_assessment_adapters_call_saved_systems_and_abstain`; incompatible city requests were unavailable. Custom anomaly and three-family water histories also executed with unit validation.
- New tests cover reference/PDF identity, reconciliation, geometry absence, city isolation, admin auth, create/edit/overlap/expiry checks, reapproval/release/audit, and simultaneous reservation conflict (one success, one 409).
- Final test run used a disposable configured password. Two existing tests were corrected to use the configured password and assert login success rather than relying on a historical default; no credentials were changed.
- Browser: observed Infrastructure data and source/reconciliation text, Planning missing-inventory cards and authorized input form, all nine Predictions options, map filter changes and CAMS marker detail. Executed the actual water-network assessment, which returned a saved benchmark score and a clear nonoperational limitation. Captured browser error log was empty at this check. Screenshots accompany this report.
- Native Windows execution, mobile browser performance, real field dispatch, external inventory authority, live Google traffic and real city causal impact remain unverified. Windows setup scripts and CI configuration are retained, but no remote CI run was triggered while GitHub work is paused.

## Use locally

Open Infrastructure for the full Delhi reference. Open admin Planning to enter authorized current capacity, use unreserved constraints in a what-if assessment, compare plans and review an internal reservation. Open Predictions for the nine historical/what-if tools and compatible history inputs. See README for Mac/Windows setup, cloning, local changes, dependencies and collaboration guidance.

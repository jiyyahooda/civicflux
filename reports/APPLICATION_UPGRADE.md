# CivicFlux application upgrade

Superseded source/UI details: the 27 October [live-source and dashboard report](LIVE_SOURCES_AND_DASHBOARD.md)
documents connected IMD observations, separate CAMS estimates, CPCB setup and the
revised map-first interface. Earlier unavailable-source descriptions below are historical.

Completed and verified on 26 October 2026 (Asia/Kolkata).

Project: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux`.

The existing React/TypeScript/Vite/Tailwind application and FastAPI services were extended in place. No parallel frontend, duplicate model registry, or alternative inference pipeline was created. All original research artifacts, datasets, metadata and notebooks remain preserved. This is a local Windows application; no hosted deployment was performed.

## Design and motion

- Exact light-theme orange `#FF6B00`, white surfaces and dark text; exact dark background `#0D0D0D`, neon green `#00E676` and white text. The toggle persists across reloads.
- Syne display typography paired with Inter, with system fallbacks if Google Fonts cannot load.
- Frosted glass buttons, inset highlights, blurred translucent navigation and login overlay, hover lift, animated graph edges and viewport-based card reveals.
- A code-rendered CSS 3D city responds to pointer movement. On scroll, its two halves move apart while the dashboard enters below. The floating navbar contracts as the page scrolls.
- Reduced-motion preferences disable decorative animations and the extended sticky-scroll sequence.
- Responsive navigation, keyboard focus styles, accessible graph controls, modal focus trapping and Escape dismissal.

The [Rimor reference](https://www.rimor.tech) was inspected visually for its floating navigation, bold typography, restrained accent lighting and spacious motion-led opening. CivicFlux uses its own city graphic and dashboard composition. The supplied images and six-page project PDF informed the system graph, scenario, resource comparison and governance workflow; their illustrated numbers were not copied into the application as data.

## Completed pages and connected endpoints

| Page | Working functionality | Existing endpoints used |
| --- | --- | --- |
| Overview | Split-city opening; city selector; measured model readiness; actual complaint/scenario counts; infrastructure graph; resource-plan summary; forecast switches; source freshness | `/api/models`, `/api/cities`, `/api/observations`, `/api/scenarios`, `/api/scenarios/graph`, `/api/complaints`, `/api/predictions/{component}/series` |
| Predictions | Nine model examples; scope, units, horizon, historical clock and input age; supported numeric outputs; uncertainty intervals; warnings; admin research request editor | `/api/predictions/{component}/example`, `/fixture`, `/series`, POST `/api/predictions/{component}` |
| Infrastructure | 40 saved synthetic assets and 96 dependencies; asset search; type filtering; keyboard selection; connected-edge highlighting; zoom/reset; optional Google reference map | `/api/scenarios/graph`, `/api/scenarios`, `/api/cities` |
| Cascade analysis | Saved scenario selection; declared outages; node risk bars; 60-minute synthetic scores and review flags | `/api/scenarios`, `/api/scenarios/graph` |
| Planning | Six editable supported templates; one flood-engine selector; model/simulator selection; eight flood inputs; outage assumptions; policy weights; budget, pumps and crews; saved results; solver comparisons | `/api/scenarios/defaults`, `/api/scenarios/graph`, GET/POST `/api/scenarios` |
| Operations | Civilian complaint submission; tracking receipt; status/text filters; admin response history; human review; separate simulation outcome evidence; audit trail | `/api/complaints`, POST `/api/complaints/{id}`, `/api/feedback`, POST `/api/feedback/{id}/review`, POST `/api/feedback/{id}/verification`, `/api/audit` |
| Model validation | Searchable model inventory, research readiness, provenance, validation limitations, artifact/schema paths, saved metrics | `/api/models` |

Authentication reuses `/api/auth/login`, `/api/auth/me` and `/api/auth/logout`. Requested local credentials remain **ADMIN001 / 001**, configurable through the existing environment settings. Credentials are sent to FastAPI; there is no frontend-only authentication shortcut.

## Scenarios and explainable allocation

Six templates were checked against the actual trained-surrogate and graph contracts: **Light stress**, **Heavy rainfall**, **Water disruption**, **Road disruption**, **Pump outage**, and **Compound stress**. These are explicit hypothetical inputs. Every template declares at least one asset outage; the light-stress case is not a claim that a real city is operating normally.

Both existing flood engines remain available. The default mass-balance simulator reports depth in metres. The recovered XGBoost surrogate reports a calibrated synthetic research score. Neither is presented as a validated municipal flood forecast. Chosen outages are independent operator assumptions; no unsupported rainfall-to-asset mapping is inferred.

Resource comparisons reuse the existing CP-SAT, utility-greedy and severity-greedy implementations under the same constraints. Bar charts compare policy utility; the donut shows selected interventions by crew family; meters show budget, pumps and crew-hour usage. Expandable candidates show their actual weighted urgency, cascade, service, equity-proxy, environmental and carbon-penalty contributions. Policy utility is not labeled as causal benefit, lives saved, carbon avoided or monetary savings.

Browser verification ran **UI verification · monsoon** in the isolated preview database: 100 mm rainfall forcing, load 1.3, declared `drainage_0` outage, trained flood engine, INR 50,000, four pumps and 24 hours per crew family. CP-SAT returned **OPTIMAL**, selected **10** candidates, used **INR 48,677** and **two pumps**, and reported utility **4.875**. This is a synthetic test record, not city evidence.

## Human control and persistence

Two defects were fixed:

1. The Planning page contained three identical flood-engine controls. It now has one selector.
2. A saved review did not update the scenario's visible review status. Review persistence now atomically stores the review, updates the scenario to pending/deferred/rejected, and writes the audit event in SQLite. The current selected scenario resolves to refreshed server data.

Existing approval restrictions remain intact: attempting approval returns 409, and all scenarios retain `dispatch_allowed=false`. The admin can adjust research inputs, review or reject proposals, and progress complaint statuses. The UI does not grant permission to dispatch a real intervention or edit trained model parameters.

Outcome evidence remains separate from reviewer opinion. Existing validation requires a completed-time record, valid chronology, an evidence reference and a named verifier distinct from the reviewer/recorder. It is recorded as simulation evidence; the system does not authenticate real field evidence or promote a synthetic result to a verified municipal outcome.

Public users can inspect research, source status, saved scenarios and community progress and can submit a complaint. Admin response controls, scenario mutation, review controls and the audit portal require an authenticated session. The server continues enforcing authentication and cross-origin checks.

## Validation evidence

- Production TypeScript compilation and Vite build pass. Chart code is split into a separate chunk; the final build has no large-chunk warning.
- **22 integration/regression tests pass**, including all six templates, restored flood inference, shared graph identities, resource limits, independent evidence checks, approval rejection, unauthorized mutation, complaint transitions and review-status persistence.
- **22 actual HTTP responses** were verified against the running FastAPI app, including all nine model examples, three saved forecast series, graph/defaults, observations, cities and model inventory.
- Browser checks covered light/dark themes, persistence across reload, admin login/logout, trained-model scenario execution, complaint submission with a tracking ID, admin complaint response, persisted deferral and audit history, graph selection/zoom, and Google Maps rendering.
- Mobile checks at **390 × 844** confirmed the responsive hero, scenario controls and navigation. Document scroll width remained within the viewport. The temporary viewport override was reset afterward.
- Browser console checks found no unexpected JavaScript errors. One existing Starlette/httpx deprecation warning remains in the Python test environment.
- The final archive audit reconfirmed that all **290 original research artifact, dataset and notebook files** match the supplied ZIP byte for byte. All nine model components retain their passing research verification.

Evidence files: `windows/application-upgrade-tests.xml`, `windows/http-upgrade.json`, `windows/openapi-upgrade.json`, `windows/migration_reverification.json`, and `windows/inference/*.json`. Screenshots are saved beside these reports.

Browser write checks used the separate `var/ui-preview.sqlite3` database. They did not add QA complaints or scenarios to the user's normal `var/civicflux.sqlite3` database. TestClient tests used separate temporary databases.

## Remaining external inputs and limits

- Live IMD/CPCB observations require verified gateway URLs, source contracts and city/station IDs. Current configurations lack those mappings, so readings are explicitly unavailable. No live observations were fabricated.
- Delhi has aggregate rainfall/PM2.5 research support. Chandigarh and Chennai do not acquire trained forecasts merely by selecting them. Anonymous traffic junctions and the simulated L-TOWN water network remain in their original scopes.
- The optional Google map provides geographic context using a city-name query. Actual municipal asset coordinates are absent; synthetic nodes are never plotted as real assets. The map depends on Google/network availability and is only loaded on request. Its dark treatment is a visual CSS treatment of the embed, not a separately verified municipal basemap.
- Coupled pollution/solid-waste simulations, calibrated real flood hydraulics, a real resource inventory, authenticated field verification and operational model approval are not supported by the supplied research. They are not represented as completed capabilities.
- External Google Fonts and the optional Google Maps embed require internet access. System fonts and the saved schematic remain usable without them.
- Existing previously generated complete ZIP archives predate these changes; the current project folder and rebuilt frontend distribution are authoritative.

## Run the application

From the project root, run `START-CIVICFLUX.cmd`, then open **http://127.0.0.1:8000**. It uses the normal database and rebuilt `frontend/dist` output.

For development, the existing Vite configuration proxies `/api` to FastAPI on port 8000. Keep API and frontend origins consistent with the existing admin-origin checks. No deployment or approval rule was relaxed for previewing.

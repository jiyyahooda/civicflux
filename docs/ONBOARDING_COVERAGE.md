# Interactive onboarding — inspection and feature checklist

Inspection completed before implementation, 30 October 2026. Source: this local app's
App.tsx routes, rendered pages, their child components and API contracts. No repository
was downloaded, and no interface was recreated. This checklist is the implementation plan.

| Path / topic | Features to cover on the real interface | Conditions / safety |
|---|---|---|
| Public welcome and navigation | Landing Explore action, public tabs, city menu/search/selection, theme, refresh, admin sign-in | Tour never signs in or signs out automatically |
| Public overview | PIN-local notice/dismiss/locality; city map preview; condition/temperature/PM2.5/report counts; weather; air chart; forecast periods | Local notice only when supplied; provider failure is explained |
| Non-Delhi overview | Postal data-card selector; modelled AQI/river data, timestamps/staleness; six Chennai reservoir series and values | Chennai / Chandigarh only; reservoirs need snapshot |
| Notifications | Bell, unread/read states, sources/times, individual/all read, refresh, polling limitations | Anonymous local storage; no push permission |
| City map (both roles) | All six modes; map pan/zoom/recenter, markers/details, grouped reports, legends/credits; rain chart/optional imagery; air stations/list/shading/credits; Google traffic + geographic embed | Distinguish provider grids, verified reports and missing network survey; Google/WAQI availability conditional |
| Admin scenario map | Observation/scenario choice; all/road/water/drainage layers; vehicle volume/capacity; rain/blockage; assets/details; provenance; geographic overlays and 2 km exposure | Hypothetical nodes; Chennai/Chandigarh snapshots only if present |
| Public report | City, title/category/address/PIN/email, impact estimates, description, photo validation/preview, optional map pin, postal coverage, submit/receipt/email status | Never auto-submit, populate private details or upload files; deliberate save confirmation |
| Tracking / community reports | Report ID lookup, status, verification/photos/public response; community search/status/category filters | Lookup requires a real ID; community page exists in App but has no ordinary nav entry; tour may navigate to it |
| Predictions (both) | Provider forecast; available component tiles; benchmark inputs; CSV upload/paste, clock/units; run/result/uncertainty/scope; saved explanation; traffic capacity interpretation | Public rainfall/PM2.5/traffic; admin also flood/cascade/water/optimization/outcomes. Catalog and data availability govern access; no synthetic result |
| Admin diagnostics | Validation readiness/search/scope/artifacts, original request loader/editor/inference | Authenticated only; anomaly excluded by existing UI |
| Admin overview | Report-stage counts/queue shortcuts, local map, environment signals, roster shortcut, latest reports, weather/air/forecast | PIN/session scope preserved |
| Review reports | Queue, images; review/category/location/verification/status/urgency/department; severity/population evidence/cost/crew package; coordinate verification; public/private response; completion evidence/resource proposal; save | Existing report required; never save automatically |
| Admin assignments/notices | Area/account status/deactivation; locality notice form/validity/publish | Deactivation closes session. Never auto-deactivate or publish |
| Supervisor records/audit | Notice/import/roster/publication form modes; source/validity; audit table | Only system_supervisor as already implemented; don't manufacture a supervisor |
| Planning | Current inventory, unreserved quantities, edit/new roster/validity; use in what-if; locality priorities/population caveats; authorized budget/weights/funding/duration/proposal; plans/status/alternatives/actions/unfunded/notes; approve/change/defer/reject/release; assignments/blockers/history | Existing pools/funding/plans conditional; every save/reservation needs deliberate confirmation |
| Decisions | Current situation/confirmed incidents/resources/next steps; saved what-if assessments; explanation; map; six stress presets; outage/rain/load/engine/budget/pumps/crew assumptions; advanced flood/policy weights; run/save | Running a scenario persists it; never auto-run |
| Scenario outputs | Allocation alternatives/meters/priority explanations/constraints/selected-only; before/proposal resource comparison/overlay; network graph asset/search/type filters/zoom/reset/pan/inspector; knock-on scores | Existing saved scenario required; never claim physical risk reduction |
| City infra | City-wide scope; Delhi finance fiscal year/reconciliation/drainage/road search/transport/workforce/PDF; other cities' source coverage/reservoir summaries/official links/retry | Admin only; same content within city across PINs |
| Data and sources | Source status/use/licence/dates/counts/checksums; live feeds/deviations/evaluated-not-used | Shown for Chennai/Chandigarh navigation; source links open externally only by user |
| Tour itself | First-use offer/defer, role paths, feature topic picker, full/short tours, Back/Next/skip/exit/progress/restart; persisted completion | Keyboard/focus, reduced motion, narrow screens, missing targets, manual navigation, role changes |

## Explicit exclusions discovered in inspection

- Legacy Operations.tsx, standalone Model validation route, PredictionCard, InfrastructureMap,
  SevenDays, NoticePanel, Suggestions, ReviewPanel and old forecast-chart variants are not
  reachable from normal current navigation/child composition. Do not create new product
  features to demonstrate unused code. Validation embedded inside admin Predictions is covered.
- No automated real complaint, upload, budget, inventory, plan, review, notice, account
  deactivation, reservation or external account is created by onboarding. There is no isolated
  practice mode in the running app; write controls are explained and guarded during the tour.
- No live feed, surveyed network, municipal dispatch, scientific approval, inbox delivery or
  model applicability is invented. Conditional steps explain missing prerequisites and offer
  retry/skip. Tour does not change permissions or authenticate on behalf of the user.

Implementation and validation evidence will be appended after checking the finished tour.

## Implemented coverage

**99 uniquely identified steps across 25 topics.** Paths are filtered by the real role and city. Conditional records/feeds are resolved on the actual page; missing prerequisites offer retry/skip and are never labelled successful. The full path updates its available city-specific steps when the city changes.

| City | Public steps | Area admin steps | System supervisor steps |
|---|---:|---:|---:|
| delhi | 45 | 70 | 72 |
| chennai | 49 | 74 | 76 |
| chandigarh | 48 | 73 | 75 |

The public path begins with Explore; the admin path begins with its assigned area.
The previous text-only CivicHelp component is no longer mounted. No GitHub source, new
tour service, frontend dependency or authentication bypass was introduced.

### Complete step index

Every row is implemented in frontend/src/tour/catalog.ts and has a stable target or an
explicit conditional-unavailable explanation. This index describes coverage, not a claim
that every external feed and every optional record was available during testing.

| Step ID | Topic | Real page | Additional condition | Interaction |
|---|---|---|---|---|
| landing | Getting started | Overview | public | User action required |
| public-nav | Getting started | Overview | public | Inspect real control / output |
| city-trigger | City and display | City map | public | User action required |
| city-menu | City and display | City map | public | User action required |
| theme | City and display | City map | Both roles | User action required |
| refresh | City and display | City map | public | Inspect real control / output |
| dashboard | Overview and local conditions | Overview | public | Inspect real control / output |
| local-notice | Overview and local conditions | Overview | public | Inspect real control / output |
| weather | Overview and local conditions | Overview | Both roles | Inspect real control / output |
| air-chart | Overview and local conditions | Overview | Both roles | Inspect real control / output |
| forecast | Overview and local conditions | Overview | Both roles | User action required |
| postal-data | Postal data cards | Overview | nonDelhi | Inspect real control / output |
| conditions | Postal data cards | Overview | nonDelhi | Inspect real control / output |
| reservoirs | Postal data cards | Overview | chennai | Inspect real control / output |
| notification-trigger | Notifications | City map | public | User action required |
| notification-panel | Notifications | City map | public | Inspect real control / output |
| map-modes | Map observations | City map | Both roles | User action required |
| station-map | Map observations | City map | Both roles | Inspect real control / output |
| station-inspector | Map observations | City map | Both roles | Inspect real control / output |
| rain-chart | Rain and air maps | City map | Both roles | Inspect real control / output |
| air-map | Rain and air maps | City map | Both roles | Inspect real control / output |
| air-stations | Rain and air maps | City map | public | Inspect real control / output |
| traffic-map | Traffic and network maps | City map | Both roles | Inspect real control / output |
| water-note | Traffic and network maps | City map | Both roles | Inspect real control / output |
| infrastructure-map-note | Traffic and network maps | City map | Both roles | Inspect real control / output |
| map-source | Scenario map and layers | City map | admin | Inspect real control / output |
| scenario-map | Scenario map and layers | City map | admin | Inspect real control / output |
| scenario-road | Scenario map and layers | City map | admin | Inspect real control / output |
| scenario-rain | Scenario map and layers | City map | admin | Inspect real control / output |
| open-layers | Scenario map and layers | City map | nonDelhi | Inspect real control / output |
| report-form | Create a report | Report a problem | public | Inspect real control / output |
| report-impact | Create a report | Report a problem | public | Inspect real control / output |
| report-photos | Create a report | Report a problem | public | Inspect real control / output |
| report-map | Create a report | Report a problem | public | Inspect real control / output |
| report-postal | Create a report | Report a problem | public | Inspect real control / output |
| report-submit | Create a report | Report a problem | public | Inspect real control / output |
| report-receipt | Create a report | Report a problem | public | Inspect real control / output |
| report-tracking | Track and browse reports | Report a problem | public | Inspect real control / output |
| community-filters | Track and browse reports | Open reports | public | User action required |
| report-card | Track and browse reports | Open reports | public | Inspect real control / output |
| forecast-runner | Forecasts and predictions | Predictions | Both roles | User action required |
| forecast-response | Forecasts and predictions | Predictions | Both roles | Inspect real control / output |
| assessment-tools | Forecasts and predictions | Predictions | Both roles | User action required |
| assessment-inputs | Forecasts and predictions | Predictions | Both roles | Inspect real control / output |
| history-inputs | Forecasts and predictions | Predictions | Both roles | Inspect real control / output |
| measurement-inputs | Forecasts and predictions | Predictions | admin | Inspect real control / output |
| model-rainfall | Individual assessments | Predictions | Both roles | Inspect real control / output |
| model-aqi | Individual assessments | Predictions | Both roles | Inspect real control / output |
| model-traffic | Individual assessments | Predictions | Both roles | Inspect real control / output |
| model-flood | Individual assessments | Predictions | admin | Inspect real control / output |
| model-water_network | Individual assessments | Predictions | admin | Inspect real control / output |
| model-cascade_risk | Individual assessments | Predictions | admin | Inspect real control / output |
| model-resource_optimization | Individual assessments | Predictions | admin | Inspect real control / output |
| model-intervention_outcomes | Individual assessments | Predictions | admin | Inspect real control / output |
| assessment-run | Forecasts and predictions | Predictions | Both roles | User action required |
| assessment-output | Forecasts and predictions | Predictions | Both roles | Inspect real control / output |
| assessment-explanation | Forecasts and predictions | Predictions | Both roles | Inspect real control / output |
| traffic-interpretation | Forecasts and predictions | Predictions | Both roles | Inspect real control / output |
| admin-login | Admin access | City map | public | Inspect real control / output |
| admin-area | Municipal overview | Overview | admin | Inspect real control / output |
| admin-summary | Municipal overview | Overview | admin | Inspect real control / output |
| admin-operations | Municipal overview | Overview | admin | Inspect real control / output |
| review-queue | Review and respond | Review reports | admin | Inspect real control / output |
| officer-review | Review and respond | Review reports | admin | Inspect real control / output |
| severity-package | Review and respond | Review reports | admin | Inspect real control / output |
| review-response | Review and respond | Review reports | admin | Inspect real control / output |
| review-save | Review and respond | Review reports | admin | Inspect real control / output |
| admin-assignments | Notices and assignments | Review reports | admin | Inspect real control / output |
| notice-composer | Notices and assignments | Review reports | admin | Inspect real control / output |
| supervisor-records | Supervisor administration | Review reports | supervisor | Inspect real control / output |
| audit | Supervisor administration | Review reports | supervisor | Inspect real control / output |
| inventory-form | Inventory and funding | Planning | admin | Inspect real control / output |
| inventory-current | Inventory and funding | Planning | admin | Inspect real control / output |
| locality-priorities | Inventory and funding | Planning | admin | Inspect real control / output |
| budget-form | Inventory and funding | Planning | admin | Inspect real control / output |
| proposal | Inventory and funding | Planning | admin | Inspect real control / output |
| plans | Plans and reservations | Planning | admin | Inspect real control / output |
| plan-details | Plans and reservations | Planning | admin | Inspect real control / output |
| reservation-review | Plans and reservations | Planning | admin | Inspect real control / output |
| decision-mode | Decisions and stress tests | Decisions | admin | User action required |
| current-situation | Decisions and stress tests | Decisions | admin | Inspect real control / output |
| saved-assessments | Decisions and stress tests | Decisions | admin | Inspect real control / output |
| scenario-lab | Decisions and stress tests | Decisions | admin | User action required |
| scenario-inputs | Decisions and stress tests | Decisions | admin | Inspect real control / output |
| scenario-advanced | Decisions and stress tests | Decisions | admin | Inspect real control / output |
| scenario-run | Decisions and stress tests | Decisions | admin | Inspect real control / output |
| current-assessment | Assessment outputs and graph | Decisions | admin | Inspect real control / output |
| allocation | Assessment outputs and graph | Decisions | admin | Inspect real control / output |
| allocation-actions | Assessment outputs and graph | Decisions | admin | Inspect real control / output |
| impact | Assessment outputs and graph | Decisions | admin | Inspect real control / output |
| graph | Assessment outputs and graph | Decisions | admin | Inspect real control / output |
| cascade | Assessment outputs and graph | Decisions | admin | Inspect real control / output |
| city-infra | City infrastructure references | City infra | admin | Inspect real control / output |
| delhi-reference | City infrastructure references | City infra | delhi | Inspect real control / output |
| corridor-search | City infrastructure references | City infra | delhi | Inspect real control / output |
| other-infra-reference | City infrastructure references | City infra | nonDelhi | Inspect real control / output |
| model-validation | Model diagnostics | Predictions | admin | Inspect real control / output |
| developer-tools | Model diagnostics | Predictions | admin | Inspect real control / output |
| data-sources | Data provenance | Data and sources | nonDelhi | Inspect real control / output |

## Validation performed

- **8 Node tour tests passed**: unique steps; role restrictions; officer/supervisor
  capabilities; city-specific content; malformed-storage handling; all declared target
  identifiers; no write control in automatic preparations; no hidden anomaly/legacy routes.
- **191 existing Python tests passed**, with the existing Starlette/httpx warning.
- **TypeScript + Vite build passed**. The existing Three.js large-chunk warning remains.
- The real local launcher smoke passed with a disposable database, built HTML/JS/CSS,
  authenticated admin, 40 original graph assets and nine model components.
- All **307 original artifact/data/config snapshot hashes** remain unchanged.

Browser checks used the actual app and controls, at 1440×900 desktop and 375×812
mobile (also inspected the existing narrow 319 px app viewport):

| Check | Actual result |
|---|---|
| First-use offer / Maybe later / permanent Help | Observed public and separate area-admin offers; deferral survives reload |
| Full and feature paths / direct step jump | Public full start and municipal full start; feature paths and direct City infra step navigated to real pages |
| Real action gating | Next locked before Explore, city-menu, notification, prediction selection and stress preset actions; unlocked after observed control events |
| Read-only outcomes | Provider forecast returned real cards; traffic assessment returned 75.597 vehicles/hour and its saved 90% interval, with scope/uncertainty. Result and explanation panels highlighted |
| Public report form | Impact, map-pin and postal disclosures opened; photo/submit controls highlighted; receipt correctly unavailable without submission |
| No automatic writes | Report, inventory and scenario Run controls opened the explicit real-change confirmation. Cancelled each; no report, inventory or scenario was created by these checks |
| Missing records | Missing inventory and missing report receipt explained; retry/skip available; no synthetic data or success state |
| Navigation | Next, Back, Skip, Finish, Exit, full restart, topic picker and single-step jump checked |
| Keyboard | Enter activates real controls; Tab reaches highlighted-feature focus control; Escape exits; Alt+Left/Right moves Back/Next; focus heading and return-to-help observed |
| Persistence | Completed/skipped counts survived reload; public and separate admin identities received separate paths |
| Cities / roles | Public Delhi and Chennai; Chandigarh and Chennai area-admin sessions; Chennai-only topics and 24 scenario water markers, 8 road markers, rain/blockage inputs and real ward/hazard overlays checked |
| Async page refresh | Real Retry map data refreshed parent app data while touring; spotlight reconnected and remained usable after controls were replaced |
| Manual navigation | Opened Predictions during a map step; tour paused with Return to City map, then restored the actual layer controls |
| Mobile / theme | No horizontal overflow at 375 px; light and dark panels checked; mobile Explore button remained outside the explanation panel and usable |
| Motion | Tour scrolling is instant; reduced-motion CSS disables tour transitions/animation. No OS-level motion setting was changed during testing |

Not every one of the 99 steps was manually clicked end-to-end, and not every optional
external feed was available. The complete target/role/city catalog was checked by tests;
representative real interactions and the sensitive-save boundaries were exercised above.
Supervisor-only record/audit topics were checked by catalog role tests and the existing
backend suite, not by fabricating a supervisor login. Actual save acceptance, production
email delivery, external dispatch and native Windows execution were not performed.
There is no onboarding practice database exposed to users; the testing preview used an
isolated local database with SMTP explicitly disabled. Ordinary application permissions
and source availability still apply.

## How to review / maintain

1. Start CivicFlux using the existing Mac or Windows launcher. The dev site is
   http://127.0.0.1:5173/ and the built backend-served app is http://127.0.0.1:8001/.
2. Refresh an already-open tab. Use **Show me around** on first use or **Help / Take a tour**
   at bottom right. Choose a full walkthrough, topic, or expand its **Feature checklist**
   to jump to one step. Use **Focus highlighted feature** for keyboard interaction.
3. Sign in normally for the municipal path. The guide never signs in, signs out,
   deactivates an account or grants access automatically.
4. Use **Skip step** for unavailable records, **Exit** or Escape to stop, and
   **Restart from beginning** to reset this identity's tour progress. Other browser
   data and all application records remain intact. Moving to another app page can
   reset unsaved form drafts, just as normal page navigation does; finish or copy
   important draft text before starting a different tour topic.
5. Tour progress is local to this origin/browser, using `civicflux-tour:v1:<identity>`
   keys. Anonymous progress is browser-local; municipal progress uses the existing
   profile ID. No server account or personal details are stored for onboarding.
6. Test with `corepack pnpm --dir frontend test:tour`, then
   `corepack pnpm --dir frontend build`. The existing `.venv` Python suite remains
   `python -m pytest -q` from the configured environment. No new dependencies or services.
7. To extend: add a stable `data-tour` target and catalog entry. Keep automatic
   preparations limited to navigation/display controls. Mark every new real-save
   form or button with an accurate `data-tour-save` description so the tour's
   capture guard requires a deliberate confirmation, including keyboard submits.

Implemented and validated locally first. At the user’s subsequent request, these changes are being published to jiyyahooda/civicflux main on 30 October 2026. No manual deployment is part of this publishing step.

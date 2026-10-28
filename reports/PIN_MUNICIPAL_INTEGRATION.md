# PIN-based municipal administration and interface refinement

Implemented in the existing Desktop/CivicFlux folder. No models were retrained,
no original notebook/artifact files were changed, and no new ZIP was created.
These changes are local; this feature pass has not been pushed to GitHub.

## Data preservation and migration

Backups are private under `var/backups/before-pin-administration.sqlite3` and
`before-pin-live-switch.sqlite3`. The live switch preserved all 48 preexisting
JSON records byte-for-byte, including their IDs and history; resource tables were
also unchanged. All 273 original artifact/notebook hashes matched the baseline.
All nine model components still report ready for supported research inference.

Migration 1 is additive and idempotent. It creates normalized cities, pincodes,
admin_users, admin_city_assignments, admin_pincode_assignments,
complaint_jurisdictions, locality_budgets, auth_attempts, report_deduplication and
schema_migrations. Compatibility views expose complaint/notice fields from the
existing records store. Foreign keys and triggers reject mismatched city/PIN
relations. Districts, PIN coordinates and ward boundaries are not invented.

## Actual postal coverage

The government snapshots already supplied with this project yield:

| City | Unique imported PINs | Postal reference |
|---|---:|---|
| Delhi | 77 | https://dmnewdelhi.delhi.gov.in/std-pin-codes/ |
| Chandigarh | 24 | https://chandigarhdistrict.nic.in/about-district/std-pin-codes/ |
| Chennai | 2 | https://chennai.nic.in/public-utility-category/postal/ |

These are 103 listed PINs, not complete city coverage. Chennai coverage is
particularly limited. All source locality names are retained when several areas
share a PIN. The source timestamp describes the bundled reference snapshot;
it is not a claim that a postal boundary was surveyed then. PIN membership does
not establish municipal/ward jurisdiction.

## Authentication and jurisdiction

- Existing configured local administrator access is migrated to a scrypt password
  hash (N=16384, r=8, p=1, random 16-byte salt). Existing local credentials remain.
- New installations generate a private initial supervisor password. Setup no
  longer resets accounts to a public fixed password. Provider values in the
  local .env are preserved; example configuration has no credentials.
- Trusted local provisioning and the system-supervisor account manager can create
  PIN officers and city supervisors. New passwords need eight characters and may
  not be a public PIN. Role/assignment changes revoke existing sessions.
- Private queries and mutations enforce city/PIN authorization server-side:
  report review/routing, inventories, funding, scenarios, plan decisions, feedback
  and audit access. Unassigned legacy reports remain supervisor-only until routed.
- Session cookies are HttpOnly/SameSite Strict and Secure under HTTPS. Login
  verifies same-origin requests and throttles repeated failed attempts.
- Platform accounts cannot claim government-official identity. Official advisory
  imports require the city authority's HTTPS source host and retain import labels.

## Public reporting, location and notices

Images still undergo decoding, EXIF removal and bounded JPEG sanitization.
Submission, duplicate claiming and PIN routing are transactional. Identical
submissions within ten minutes return the saved report; extra duplicate files
are cleaned up. Citizen impact claims remain separate from officer assessments,
population evidence and completion/outcome verification. Review assessments have
an appended history; older clients do not erase new package fields by omission.

Use my location is optional. Coordinates travel in a POST body to the configured
HTTPS Nominatim provider, rounded for cached lookup and throttled in the local
single-process service. The suggested PIN must be listed and manually confirmed;
manual selection remains available if denied, unavailable or ambiguous. No
precise location was requested during browser verification. Provider success and
fallback were tested with controlled responses. Policy:
https://operations.osmfoundation.org/policies/nominatim/

Local notices show only active citywide/selected-PIN notices and reviewed local
incidents. Unattributed legacy platform notices remain stored but require authenticated review before appearing as verified local alerts. Expired notices have an archive; future notices are not treated as
expired. Unreviewed complaints do not become official alerts.

## Navigation, Decisions and Planning

Admin tabs: Overview, Planning, Decisions, City map, Infrastructure, Predictions,
Review reports. Report a problem remains available to citizens, not administrators.
The workspace header identifies the city and selected/assigned PIN.

Decisions reuses current observations, reviewed incidents, the scenario form,
NetworkX/cascade view, saved model inference, allocation alternatives and impact
comparison. Current scenario → Current assessment → Map scenario → What-if
controls → Allocations → Impact/cascade views. Map scenario directly follows
Current assessment. Cascades are only rendered in Decisions. Using a recorded
pool in a what-if passes its available capacities into this page.

Planning retains authorized inventory and the existing scenario supervisor
controls. Added locality funding declarations, per-PIN severity/population/funding
summaries, response proposals, status filtering and persistent approved-plan details.

The existing OR-Tools backend is extended with declared locality funds, assessed
severity/population, minimum costs, crews, workers, vehicles, pumps and specialized
crew-hours. Initial weights are 60/40, normalized before combining. Unknown
population stays unknown; available severity weight is renormalized. Sums of
population estimates may overlap and are not unique exposed residents. Crew-hours
include crew count × action duration; interventions must fit the work window.

Approval rechecks scope, active inventory, locality funding, current assessed
packages, required staffing, conflicting incidents and existing reservations under
BEGIN IMMEDIATE. Repeated identical approvals reuse a single reservation. Changes,
rejection, deferral and release preserve decision history and free reservations.
Approval does not dispatch crews or certify scientific model deployment.

## Interface cleanup and weather

Dark accent: #F97316 / #FF6B00. Light accent: #800020 / #991B1B. Tokens are
centralized; the animated globe reads the same accent token. Warning/success and
AQI category colours keep their meanings.

Removed the requested hero captions/progress strip, footer slogan, CAMS badge,
old forecast heading, shade checkbox, repeated empty map/infrastructure cards,
scenario download action, and prominent PDF action. Map explanations, provenance,
provider credits and source links are compact accessible details rather than
repeated ordinary-page paragraphs. A visible Simulated conditions badge remains.

Temperature charts were removed from the weather views. Tomorrow / 7 days /
10 days use the actual Open-Meteo daily forecast. Feels-like and humidity are
means of available hourly provider values, labelled as such. Missing optional
values display unavailable. Live verification returned 14 available days with
provider weather code, rain probability, feels-like and humidity fields.
Provider forecasts remain separate from saved rainfall ML predictions.

CivicFlux Help is a role-aware, searchable deterministic guide and walkthrough.
It opens real pages, keeps public/admin actions separate, and cannot approve or
modify records. No paid AI dependency or transmission of complaint data is added.

Explain this assessment also exposes unchanged saved permutation-importance
exports for rainfall, PM2.5, traffic, flood, water-network and cascade models.
The original notebook scoring methods are identified. These are global evaluation
factors, not local SHAP values, confidence percentages or causal explanations.
Success-classifier importance is not misrepresented as duration-model evidence.

## Verification and practical limits

- Full backend suite: **137 passed**, one existing Starlette/httpx deprecation warning.
- Frontend TypeScript/Vite production build: passed. Existing large Three.js chunk
  warning remains; no build failure.
- Controlled tests cover migration, hashed login, account revocation, city/PIN
  validation and attacks, duplicate reports, local/expired notices, geocoder
  suggestion/fallback, funding, stale/conflicting approvals, package validation,
  persistence across a fresh application process, population handling and crew-hours.
- Browser checks use the existing supervisor identity: navigation order, removed
  labels, both theme tokens, real forecast card counts, current/what-if controls,
  map ordering, help and public reporting controls. No consent to precise location
  was granted or claimed. Actual browser permission-denial behaviour was not invoked.
- Automatic approval review blocked seeding an additional QA officer identity and
  sample operational records in the browser-test database. Restricted identities
  and approval transitions were verified in disposable automated test fixtures;
  a newly created officer was not exercised manually in the browser.
- Existing municipal inventories were empty. Real approval needs a current,
  authorized roster, explicit locality funds and validated/costed reports. No
  workforce, current faults, geographic dependency links, causal improvements or
  success probabilities were fabricated.
- Official budget/workforce/jurisdiction evidence for complete Chennai/Chandigarh
  operations is still absent. Existing Delhi historical references remain dated
  reference material, not available operating funds.
- Windows-compatible paths and separate native dependency setup remain. This
  feature pass was tested on the Mac; native Windows CI for this new pass has not
  been run because this local feature pass has not been published.

## Files created or modified

- `.env.example`
- `APPLICATION.md`
- `OPEN_ON_WINDOWS.txt`
- `README.md`
- `backend/api/assessments.py`
- `backend/api/civic.py`
- `backend/api/feedback.py`
- `backend/api/locality_planning.py`
- `backend/api/municipal.py`
- `backend/api/resources.py`
- `backend/api/scenarios.py`
- `backend/auth.py`
- `backend/db/municipal.py`
- `backend/db/repository.py`
- `backend/main.py`
- `backend/optimizer.py`
- `backend/services/administration.py`
- `backend/services/civic_service.py`
- `backend/services/municipal.py`
- `backend/services/outlook_service.py`
- `backend/services/scenario_service.py`
- `frontend/src/App.tsx`
- `frontend/src/components/AdminAccounts.tsx`
- `frontend/src/components/AirQualityMap.tsx`
- `frontend/src/components/AssessmentExplanation.tsx`
- `frontend/src/components/CityHero.tsx`
- `frontend/src/components/CivicHelp.tsx`
- `frontend/src/components/DelhiReference.tsx`
- `frontend/src/components/EnvironmentalChart.tsx`
- `frontend/src/components/FluxScene.tsx`
- `frontend/src/components/ForecastTabs.tsx`
- `frontend/src/components/LocalContext.tsx`
- `frontend/src/components/NoticeComposer.tsx`
- `frontend/src/components/OperationalResources.tsx`
- `frontend/src/components/RainfallChart.tsx`
- `frontend/src/components/ScenarioMap.tsx`
- `frontend/src/main.tsx`
- `frontend/src/municipal.css`
- `frontend/src/pages/CityMap.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Decisions.tsx`
- `frontend/src/pages/Infrastructure.tsx`
- `frontend/src/pages/Planning.tsx`
- `frontend/src/pages/Predictions.tsx`
- `frontend/src/pages/ReportProblem.tsx`
- `frontend/src/pages/ReviewReports.tsx`
- `frontend/src/types/api.ts`
- `frontend/src/types/civic.ts`
- `frontend/src/types/municipal.ts`
- `frontend/src/types/operational.ts`
- `reports/PIN_MUNICIPAL_INTEGRATION.md`
- `reports/municipal-administration/build.txt`
- `reports/municipal-administration/decisions.png`
- `reports/municipal-administration/overview.png`
- `reports/municipal-administration/tests.txt`
- `reports/municipal-administration/verification.json`
- `scripts/launch_app.py`
- `scripts/local_config.py`
- `scripts/provision_admin.py`
- `tests/conftest.py`
- `tests/test_municipal_administration.py`

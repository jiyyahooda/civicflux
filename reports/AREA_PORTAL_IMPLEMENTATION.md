# CivicFlux UI and postal-area portal — 29 October 2026

Implemented locally in the existing project. The Render deployment and GitHub have
not been updated by this pass. The local app serves the new build at
http://127.0.0.1:8001/. A backup of the original SQLite database is at
`var/backups/before-area-portal.sqlite3`. No ZIP was created, model retrained,
research file changed, or private credential committed.

## Changes by requested item

| Item | Implementation and principal files |
|---|---|
| A1 notification | `LocalContext.tsx`, `Dashboard.tsx`, `App.tsx`: one latest active notice below the globe, area/PIN chip, timestamp, dismiss, selector inside the card; no card with no active notice; no archive/location-information UI and no notice on other tabs. Citywide notices remain identified by area instead of an invented PIN. |
| A2 navigation/brand | `App.tsx`, `portal.css`: fixed/inert civilian bar initially translated out of view, 80px scroll threshold, 0.5s transform-only transition, reduced-motion handling, geometric system-font wordmark and separate always-available Admin link. |
| A3 globe | `FluxScene.tsx`, `portal.css`: burgundy/red/gold dark material, lights, particles, rings and glow. Light rendering retains its previous palette. |
| A4–A7 removals | `CityHero.tsx`, `CivicPanels.tsx`, `EnvironmentalChart.tsx`, `ForecastTabs.tsx`: removed Meet the models and requested expandable copy; data and required provider attribution remain. |
| A8 simulations | `CityMap.tsx`, `maps.py`, `jurisdiction.py`: public City Map has observations only. All simulation geometry/download and hypothetical assessment actions require a valid admin session. Area simulation positions are explicitly hypothetical around its sourced postal reference. |
| A9 forecast | `WeatherForecastRunner.tsx`, `Predictions.tsx`: direct existing provider-outlook action, disabled/loading state, result cards, friendly error/retry. The prior saved-model action required raw historical inputs that are deliberately absent from GitHub. Provider forecasts are clearly separate from those unchanged saved ML models. Browser-verified both public and PIN-scoped requests. |
| A10 email | `complaint_email.py`, `civic.py`, `ReportProblem.tsx`: validated email already required; server-only Gmail SSL/STARTTLS multipart receipt after durable registration; tracking ID, details, time/status instructions; escaped HTML; once per ID, 10/IP/hour and 3/recipient/hour; failure retains tracking ID and shows a notice. No generic send-mail endpoint. |
| B typography | `portal.css` and existing CSS files: shared fluid rem scale, 18px mobile/20px desktop body, small text floor, proportional old component styles, larger map markers/touch controls, wrapped forms/nav, scrollable tables. |
| C1 identity | `areas.py`, `auth.py`, `AdminAccounts.tsx`, seed/provision scripts: 103 unique area rows with fixed username admin; only active six-digit PIN login; server-side random session token, Strict HttpOnly cookie (Secure on HTTPS), 30-minute API-idle timeout, eight-hour maximum; five failed attempts/IP trigger 15-minute lockout, sanitized login audit. Old username/password accounts retained as history, cannot sign in. |
| C2 scope/migration | `scope.py`, `jurisdiction.py`, `repository.py`, area/civic/resource/map/city services: session determines PIN, SQL record filter/index, direct foreign record/photo access denied, body/query/city tampering rejected. Exact locality matches and parent-scenario scope can be migrated; unmatched records stay unassigned. Complaint area relation references the new single source of truth. |
| C3 portal | `AdminShell.tsx`, `AdminOverview.tsx`, `portal.css`: distinct navy command centre/sidebar/header with area and scope badge, animated KPI counters, area map/layers/admin-only simulation, queue, provider weather/air/forecasts, existing Review/Planning/Decisions workflows. |

## Configuration and scripts

- Add private `SMTP_USER=civicflux1001@gmail.com`, `SMTP_PASS` (Gmail App Password),
  and optional `SMTP_PORT=465` (SSL) or `587` (STARTTLS). Restart the backend.
  `.env.example` contains placeholders only and `.env` is ignored.
- `python scripts/seed_area_admins.py` prints/reconciles every sourced area. It is
  idempotent and does not reactivate deactivated areas.
- `python scripts/provision_admin.py --pin 110001 --deactivate` deactivates it;
  omit `--deactivate` to restore it from the trusted server console.
- Windows uses `.venv-windows/Scripts/python.exe`; macOS uses `.venv/bin/python`.
- No random login PIN/password is created. Prior `CIVICFLUX_ADMIN_ID` and
  `CIVICFLUX_ADMIN_PASSWORD` settings no longer control login. Default `001` is retired.

## Verified

- **148 tests passed**, including independent PIN X/Y reads/mutations/images,
  unauthenticated simulation/review rejection, wrong username/unknown/short PIN,
  rate lockout, session expiry, revocation, forecast coordinates, transactional
  allocation, complaint deduplication, email transport/failure/escaping/rate limits.
- Production TypeScript/Vite build passed; no lint script is defined by this repo.
  `pip check` passed. Existing large Three.js chunk and Starlette deprecation
  warnings remain.
- All nine saved model components loaded; supported inference/abstention smoke
  checks passed; actual launcher HTTP checks passed with admin/PIN login and map.
- 273 research/artifact/notebook SHA256 values equal their saved baseline.
- Browser checked civilian and admin Overview layouts at 320, 375, 768, 1024 and
  1440px, both theme preferences: no horizontal document overflow and no sampled
  body/label/button text below 14px. Mobile body18px; desktop20px.
- Browser checked all seven admin navigation tabs with no console errors at the
  available desktop viewport; provider Run forecast returned result cards in both
  public and scoped contexts. Admin sign-in persisted across backend restart.
- Full manual visual/keyboard coverage of every control at every width, external
  provider availability over time, and new native Windows execution were not
  exhaustively verified. No claim of a formal WCAG audit is made.

## Assumptions and limits

1. Cross-area account activation is a trusted console operation: a PIN admin can
   inspect/deactivate only its own area through Administrator assignments. This
   preserves the explicit requirement that X cannot read or modify Y. Adding a
   new area requires a sourced postal registry entry followed by seeding.
2. GeoNames postal coordinates are estimates, not surveyed boundaries or official
   centroids. 101 listed PINs matched; 160021 and 160035 did not and show unavailable.
   Attribution/licence/source rows and download hash are in `config/postal_centroids.json`.
   No guess from proximity is used to assign a complaint's PIN.
3. Public WAQI stations remain public. An area workspace uses CAMS/provider grids
   at its postal coordinate and does not claim unverified WAQI station membership.
   Saved city/anonymous-junction benchmark models are not asserted to be validated
   for postal-area inference. Missing inputs/coverage stay explicitly unavailable.
4. Postal PINs are public identifiers; this requested login is an area selector
   with rate-limited access, not proof of a person's government identity.
5. Gmail App Password is **not configured** here. Successful delivery to a real
   mailbox was not verified. All SMTP tests used mocks; no real complaint email
   was sent during verification. Registration with missing SMTP is supported.
6. Existing local records are retained. **47 unassigned records** (46 scenarios,
   one civic notice) cannot be reliably mapped and are invisible to area accounts.
   Their IDs/types are listed below and in `area-portal/unassigned-records.json`.

## Unassigned record inventory

The local private inventory is in `reports/area-portal/unassigned-records.json`.
It is excluded from Git along with the private database and uploads. Counts and
record types above provide the public migration summary without publishing IDs.

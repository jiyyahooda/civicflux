# CivicFlux

CivicFlux is a civic resilience research application: a FastAPI/SQLite backend,
React + TypeScript dashboard, and eleven completed ML notebooks. It connects
saved research predictions, city observations, synthetic flood/cascade scenarios,
OR-Tools resource plans, citizen incidents, and human review. It does not dispatch
resources automatically or claim operational public-safety validity.

## Open a new clone or downloaded ZIP

The repository includes source, models and map references. Python environments
and the compiled website are **created by setup on each device**; they are not
missing deliverables. Install Python 3.13, Node 24 and Corepack first (and Homebrew
on macOS). Extract a ZIP fully before starting; do not run files inside the ZIP.

- **Windows:** double-click `START-CIVICFLUX.cmd`. It runs setup when the native
  `.venv` or frontend build is missing, then starts the built website.
- **macOS:** open Terminal in this folder and run `bash scripts/start_mac.sh`.
- Open **http://127.0.0.1:8001/** and sign in with username admin and the six-digit postal PIN for your area.
- Keep the server terminal open. The initial setup requires internet access.

For editing with automatic frontend updates, use the separate development servers
and port 5173 described below. After `git pull`, rerun your platform setup script
to update dependencies and rebuild the website before the single-server launch.

## Architecture and files

The browser sends same-origin `/api` requests through Vite on port 5173 to
FastAPI on port 8001. FastAPI uses the shared serving modules and unchanged
saved artifacts; SQLite stores local incidents, sessions, scenarios, and reviews.

```text
backend/                 FastAPI routes, integrations, services, SQLite repository
frontend/src/            React dashboard, navigation, map, predictions, reports
frontend/pnpm-lock.yaml  Locked frontend and package-manager dependencies
src/civicflux/           Serving, portable loading, graph, optimization, validation
civicflux_core.py        Classes and feature logic required by saved bundles
project_paths.py         Central project-relative paths
artifacts/               Original bundles, portable UBJSON, metadata and schemas
notebooks/               Eleven completed notebooks (01 through 11)
config/                  Cities, graph and research configuration
data/                    Dataset source metadata; local raw data under data/raw
reports/                 Research results and verification evidence
scripts/                 Cross-platform setup, launch and inference checks
tests/                   Existing Python/API/model tests
var/                     Private local runtime data; ignored by Git
```

The notebook sequence covers rainfall, air quality, traffic, flood, infrastructure
anomalies, water networks, cascade risk, resource optimization, intervention
outcomes, model validation, and backend integration. Setup never executes or
regenerates notebooks, retrains models, or changes datasets.

## Prerequisites

Use native 64-bit Python **3.13** (tested on macOS arm64 with 3.13.5), Node.js
**24** (tested with 24.22.1), Git, and Corepack. The frontend pins pnpm **12.15.0**;
run it with `corepack pnpm`. If Corepack is absent, install it with
`npm install -g corepack` using a user-owned Node installation.

macOS requires Homebrew and `libomp`. Windows requires native 64-bit Python with
the `py` launcher; install Microsoft's Visual C++ 2015–2022 Redistributable x64
if XGBoost reports missing native runtime DLLs. Native Windows and macOS CI smoke checks passed for the prior integration.
The workflow also checks every update to `main`; see GitHub Actions for the
current commit result. This covers model/API/build checks, not full browser QA.

**Each machine must create its own `.venv` and `node_modules`.** Never transfer or
commit these directories. Rename an old Windows `.venv` before setting up on Mac,
and vice versa; scripts reject an environment without the native interpreter.

## Get the source

Clone the main branch into a folder you own:

```sh
git clone --branch main https://github.com/jiyyahooda/civicflux.git
cd civicflux
```

Cloning saves the project source on your own computer. You can open that folder
in VS Code or another editor. The `main` branch contains the current shared application.

## macOS installation and run

Install Homebrew following https://brew.sh and native Python 3.13 and Node 24.
From the project directory:

```sh
bash scripts/setup_mac.sh
```

This installs `libomp` if missing, creates a local environment if absent, installs
backend/test requirements, checks dependencies and ML imports, creates `.env`
only when absent, installs the frozen frontend lockfile, and builds the frontend.
Setup creates local configuration once. Existing administrator settings, API keys
and database paths are preserved. New administrator passwords are hashed in SQLite.

Run in two terminals:

```sh
bash scripts/run_mac.sh backend
```

```sh
bash scripts/run_mac.sh frontend
```

Equivalent manual commands, from the root:

```sh
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
# Separate terminal:
cd frontend
corepack pnpm dev
```

## Windows installation and run

Open PowerShell in the project directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_windows.ps1
```

The process-scoped execution policy does not change the machine's policy. Normal
project setup does not need administrator privileges. If execution is centrally
restricted, follow your organization's policy rather than changing it globally.

Run in two PowerShell terminals:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_windows.ps1 backend
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_windows.ps1 frontend
```

Equivalent backend command:

```powershell
.\.venv-windows\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

For the frontend, `cd frontend` then `corepack pnpm dev`.
The root Windows `.cmd` launcher now uses the native `.venv-windows` and backend
port 8001 as the platform scripts.

## Local URLs and configuration

- Application: http://127.0.0.1:5173
- API health: http://127.0.0.1:8001/api/health
- Swagger docs: http://127.0.0.1:8001/docs
- OpenAPI: http://127.0.0.1:8001/openapi.json

Use `127.0.0.1` consistently for cookie-based administration. Vite uses a strict
5173 port and proxies `/api` to 8001. A production build is also served by the
backend at `/` when `frontend/dist` exists. Both scripts bind only to loopback. Startup scripts set `PYTHONUTF8=1` so
Unicode research metadata behaves consistently on Windows.
Stop each server with Ctrl+C.

| Variable | Purpose |
|---|---|
| `CIVICFLUX_DB` | SQLite path; default `var/civicflux.sqlite3`, relative to root |
| `CIVICFLUX_PUBLIC_FEEDS` | `1` enables public observations; `0` disables network feeds |
| `CIVICFLUX_IMD_URL`, `CIVICFLUX_CPCB_URL` | Optional verified JSON feeds |
| `DATA_GOV_IN_API_KEY` | Optional server-side official CPCB source key |
| `CIVICFLUX_ROOT` | Optional absolute project root override, set in the shell before launch |

Copy `.env.example` to `.env` for provider configuration. Area login uses username
`admin` and the area’s listed six-digit postal PIN. The previous `001` login is retired.
Keep server credentials out of `VITE_*` variables. The optional restricted
Google Maps browser key uses `VITE_GOOGLE_MAPS_API_KEY` and is public in the browser
by design; WAQI and OpenWeather keys must remain server-only. Missing feeds produce unavailable/abstained
states, not fabricated observations. Public feeds and map tiles require network
access and can fail independently of the application.

## Models and original datasets

All original `.joblib` artifacts, metadata, feature schemas, model registry, and
`portable-windows/booster.ubj` exports are preserved. The portable directory name
is historical; `src/civicflux/portable.py` verifies hashes and loads the same
exports on either OS. Keep `civicflux_core.py` and `src/civicflux` beside the
artifacts. Load only trusted joblib files. No replacement predictions are used.

The eleven joblib files range from roughly 5.5 KiB to 5.9 MiB, so they do not
require Git LFS. The repository does not grant a new license to third-party data
or trained derivatives. See [DATASET_GUIDE.md](DATASET_GUIDE.md): rainfall has
noncommercial/share-alike terms, traffic has educational-use restrictions, AQI
provenance is unverified, and water-network simulation has attribution terms.
Confirm redistribution rights before public publication or commercial reuse.

Raw data and archives are intentionally not committed; existing local files are
preserved. Saved forecast examples and several tests need the original CSVs.
Acquire the documented source versions with:

```sh
# Use .venv-windows/Scripts/python.exe instead on Windows.
.venv/bin/python download_data.py
.venv/bin/python download_battledim.py
```

These download data, not models or training outputs. Alternatively copy the
original licensed `data/raw` folder locally. Verify hashes against model metadata
and `reports/data_inventory.json`; upstream datasets can change. Required paths
include `rainfall/daily-rainfall-at-state-level.csv`,
`aqi/processed_aqi_data.csv`, `traffic/traffic.csv`, and `battledim/*_SCADA_*.csv`
under `data/raw`. Missing historical inputs return HTTP 503 with setup guidance.
Keep the delivered `data/flood_scenarios.csv`; do not regenerate it for setup.

## Dependencies and verification

`requirements-backend.txt` pins runtime/model dependencies without FastAPI
standard/cloud extras. OR-Tools **9.14.6206** is paired with protobuf **6.31.1**.
FastAPI **0.162.0** and Uvicorn **0.54.0** are retained. `requirements-serving.txt`
includes the minimal runtime; `requirements-test.txt` adds pytest.
`requirements.txt` remains the research/notebook environment; installing it is
optional for serving. Do not blindly upgrade serialized-model dependencies.

```sh
.venv/bin/python -m pip check
.venv/bin/python scripts/verify_runtime.py
.venv/bin/python -m pytest -q
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm build
```

Windows equivalents:

```powershell
.\.venv-windows\Scripts\python.exe -m pip check
.\.venv-windows\Scripts\python.exe scripts/verify_runtime.py
$env:PYTHONUTF8='1'
.\.venv-windows\Scripts\python.exe -m pytest -q
Set-Location frontend
corepack pnpm install --frozen-lockfile
corepack pnpm build
```

Verification checks all nine serving components in fresh processes, positive
research/simulation requests, negative abstention, and artifact hashes. It writes
`reports/integration` and refreshes legacy `reports/windows/inference` only if that
directory already exists. Reports identify the actual platform. No training occurs.
There is no frontend unit-test script in the supplied package; `build` runs
TypeScript compilation and Vite production bundling. Browser navigation and API
smoke checks complement the Python tests.

## Troubleshooting

- **`Library not loaded: @rpath/libomp.dylib`:** run `brew install libomp`, then
  `.venv/bin/python -c 'import xgboost; print(xgboost.__version__)'`. Keep Python,
  Homebrew, and wheels on the same architecture. Do not copy DLLs/dylibs or alter
  models. No `DYLD_LIBRARY_PATH` workaround is needed for this verified setup.
- **protobuf conflict:** install `requirements-backend.txt` in a fresh local venv.
  Avoid `fastapi[standard]` and its optional protobuf-dependent exporters.
- **TestClient rejects `httpx.URL`:** the supplied tests use httpx 0.28.1. An
  optional `httpx2` left by FastAPI extras takes precedence in Starlette. In this
  project's venv, remove that unused extra with `python -m pip uninstall httpx2`
  and rerun `pip check`; a fresh minimal install does not install it.
- **Stale model readiness:** run `scripts/verify_runtime.py` with original datasets
  present. A hash mismatch must be investigated, never bypassed.
- **pnpm frozen-lock failure:** use Corepack and the pinned pnpm version. The lock
  includes pnpm 12 package-manager metadata; do not regenerate dependency versions.
- **Port in use:** stop the existing process you own; do not kill unrelated apps.
  Keep the backend and Vite proxy ports consistent if deliberately changing them.
- **Missing DLL on Windows:** check 64-bit Python and the Microsoft VC++ runtime.
- **No live data:** verify provider configuration, key, network, and timestamps.
  Historical benchmarks and simulations are labeled separately from observations.
- **Missing dataset or model:** restore the original source files and artifacts.
  Do not train replacements or insert dummy outputs to silence the error.

## Save the project locally and start contributing

1. Install the prerequisites above on your own Mac or Windows computer.
2. Run the clone command above in Terminal (Mac) or PowerShell (Windows). Do not
   copy someone else's virtual environment or node_modules.
3. Run your platform's setup script. Obtain the original datasets using the
   documented download instructions if you need historical examples or full tests.
4. Open the cloned folder in your editor. Frontend changes belong in
   `frontend/src`; API changes in `backend`; shared inference changes in
   `src/civicflux`. Leave trained artifacts and completed notebooks unchanged
   unless your task explicitly requires research changes.
5. Create your own feature branch using the commands below. Save edited files
   normally in your editor. Saving changes files only on your computer; a Git
   commit records them locally, and a Git push shares your branch on GitHub.
6. Run the tests/build, review the diff, commit only intended files, push your
   branch, and open a pull request targeting `main`.
7. After review and merge, switch back to the main branch and run
   `git pull --ff-only`. Rerun setup when dependency files change.

The `.github/workflows/cross-platform.yml` workflow checks Windows and macOS
on every main/feature-branch push and pull request. It installs the minimal backend,
loads all saved model components, exercises API/SQLite/flood/cascade/planning,
checks supported simulation predictions and abstention, then builds the frontend.
It does not download restricted raw datasets or retrain anything. The full
112-test suite and historical-data checks must also be run locally with the
original datasets. A green workflow proves these smoke checks on its runner;
it is not full Windows browser QA. Check the Actions tab for the actual result.

## Collaboration workflow

Never push to a teammate's branch or force-push shared history. Before changing
work, commit or stash local changes and update your development branch:

```sh
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/my-change
# Edit, run Python verification and frontend build, then inspect the diff.
git diff
git add <specific-files>
git diff --cached
git commit -m "Describe the change"
git push -u origin codex/my-change
```

Open a pull request on GitHub targeting `main`. Review before merging. Each
teammate should use a separate feature branch and recreate dependencies locally. If `pull --ff-only` fails,
inspect divergence and reconcile explicitly; never overwrite remote work.

## Research limitations

Models support bounded historical research or declared simulation only. Traffic
junction geography is unknown; counts are not travel time. Flood/cascade and
resource plans use synthetic infrastructure assumptions. Water fault onset is
weak and not operationally validated. Outcomes do not establish causal effects.
Human review remains separate from approval and field verification. API responses
carry scope, provenance, limitations, and abstention reasons. For measured results
and known failures see `reports/CROSS_PLATFORM_VERIFICATION.md` and the original
research reports. Older reports describe earlier environments and are not proof
of current Windows execution.

## Citizen information and officer workflows

The application keeps one header navigation with six public pages: Overview,
City map, Infrastructure, Predictions, Report a problem, and Open reports.
Review reports and Planning appear after administrator sign-in. Their APIs,
saved scenarios, feedback and audit history require backend session authorization.
The original opening animation, theme, plots, dependency graph, model validation,
scenario algorithms and notebooks remain available.

Overview uses Open-Meteo current weather and seven-day forecasts, existing IMD
station observations, CAMS air estimates, source-linked notices and city reports.
The City map has conditions/rainfall/air/traffic/water/infrastructure modes.
The actual supplied map implementation is Leaflet with OpenStreetMap tiles;
there was no MapLibre implementation in this project to migrate. No benchmark
network asset is assigned a fictional city coordinate. Only officer-verified
report pins appear on the city map.

Predictions offers nine actual saved-model/algorithm assessments grouped by
weather and air, roads and water, infrastructure, and planning/outcomes. Notebook
10 compares models and Notebook 11 validates integration; they are not extra
predictors. Benchmark clocks and geography are shown explicitly. The original
serving implementation validates inputs and abstains; the UI formats supported
results and genuine saved intervals without inventing confidence. Compatible
CSV history is optional for rainfall, PM2.5 and anonymous junction traffic.

Public report submission requires a title, category, description, address/locality,
a listed city PIN, a syntactically valid email and one to three actual JPEG/PNG
uploads. Each image is limited to 5 MB and 20 million pixels, decoded, oriented,
resized and re-encoded without EXIF metadata under a generated filename in
`var/uploads` (or alongside a custom SQLite DB). Photos and descriptions are
public; email and internal notes are excluded from public response allowlists.
Do not upload personal information or identifiable people. File storage and the
SQLite database must both be backed up to retain reports/photos.

Postal membership uses exact records from government references in
`config/postal_reference.json`, never PIN prefixes. Coverage is incomplete:
Delhi has 410 listed locality records, Chandigarh 50, and Chennai two postal
areas. An unlisted PIN must be added from an authoritative source before it can
be accepted. A PIN is not a ward, boundary or exact location. Optional user map
pins require separate officer verification. No verified city-boundary polygons
are included; the form only performs a broad city-vicinity sanity check.

Officers can review issue validity, status, urgency, department, public reply,
private notes, location evidence and completion evidence. Closing a report
requires an evidence reference. A current, dated authorized roster is required
for resource proposals, and individual proposals cannot exceed its capacities.
Proposals do not reserve resources or dispatch crews. Review reports also exposes
forms for city-specific platform notices, source-linked police-notice imports,
operational rosters, and published financial/staffing references. Audit history
is retained. Annual published budgets are kept separate from operational funds.
No invented budget, workforce or live crew figures are prefilled.

Planning separates current confirmed issues/rosters from what-if inputs. The
existing flood tools, graph, cascade model and OR-Tools planner remain the core
implementation. The duration model is available as an explicitly independent
benchmark; the supplied evidence does not support success probability or a
causal prediction of intervention benefit. Resource plans show feasible proposed
spending, equipment, crew-hours and remaining capacity. Worker headcounts and
vehicle constraints cannot be inferred from this optimizer.

### External data and traffic configuration

- Google traffic uses the official Google Maps JavaScript API `TrafficLayer` on
  a separate Google Map. Set `VITE_GOOGLE_MAPS_API_KEY` in the root private `.env`
  and restart Vite. Browser keys are visible by design: restrict HTTP referrers
  to your approved origins and restrict the key to Maps JavaScript API. Activation,
  billing and local traffic coverage must be checked in the Google project.
  No key was supplied during this work, so live Google traffic is unverified.
- Police sources are city-specific: Delhi Traffic Police, Greater Chennai
  Traffic Police, and Chandigarh Police. `config/official_notices.json` holds a
  reviewed Delhi source snapshot with an explicit validity end. Expired notices
  disappear from active panels. Other notices require approved imports; there is
  no claimed real-time police API or prohibited scraping loop.
- Chennai/Chandigarh currently have no imported active official notices. Their
  official source links remain available. Missing publications/rosters are shown
  as unavailable rather than populated with another city's values.
- Open-Meteo free access is subject to its current terms, quotas and attribution.
  CAMS is displayed at its actual regional resolution and US AQI is labeled as
  US AQI. Indian AQI is not calculated from incompatible instantaneous values.
  Optional CPCB is preserved; no OpenWeatherMap adapter was present to enable.

New routes live under `/api/civic` and `/api/assessments`. The legacy JSON
`POST /api/complaints` is now an admin-only record-import interface. New public
submissions must use multipart `POST /api/civic/reports`. Two existing tests
were migrated to this intentional authentication/upload contract; their routing
and status-transition assertions remain. The full suite now contains 100 tests.

See `reports/CIVIC_PLATFORM_ENHANCEMENT.md` for the component inventory, test
results, sources and remaining limitations. Earlier GitHub publication was paused; the current integration is published on
`codex/civicflux-ui-model-integration`.


## Delhi references and internal resource reservations

Infrastructure displays the supplied Delhi briefing as dated reference information;
compact summaries also appear in Overview, City map and Planning. Normalized
files live under `data/reference/`: budget rows for both fiscal years, three
historical drainage basins, 29 corridor entries, transport/workforce references,
and the unchanged supplied PDF. Each record carries its source, page, scope and
verification status. `GET /api/reference/delhi` serves the reference; the `/source`
route serves its PDF. Other cities do not inherit Delhi figures.

The eight reported expenditure groups do not reconcile with the reported overall
totals: FY 2024–25 differs by ₹233.18 crore and FY 2025–26 by ₹880.90 crore.
The site flags both differences. The original MCD budget document was not supplied;
primary verification remains pending. Transport figures were checked against the
Delhi Economic Survey 2025–26. No verified drain/corridor GIS geometry was provided.
No fictional map coordinates, current municipal workforce, or spendable balance
are inferred from this document.

In admin Planning, expand **Record an authorized operational inventory**. Record
city, department, service area, specialization, available workers and crews,
equipment, authorized funds, crew-hours and the roster's timezone-aware validity
window. Supply its authorization reference. Enter disjoint pools; do not copy the
same equipment into multiple departments. The API prevents overlapping duplicate
rosters with the same city/department/area/specialization, but does not maintain
physical asset IDs or independently verify inventory ownership.

Use a pool's unreserved constraints in a what-if assessment. Compare the three
existing planning algorithms, assign real crew/worker/vehicle packages to the
selected scenario actions, enter a note, then approve the internal plan. Resource
checks and reservation writes share a SQLite `BEGIN IMMEDIATE` transaction.
Reapproval replaces that plan's prior reservation; request changes, rejection,
deferral or release frees it and preserves review/audit history. Capacity edits
cannot shrink below reservations. Expired rosters are excluded from availability;
reservations are conservative capacity holds, not shift scheduling or evidence
that work finished. There is no external dispatch integration. Internal approval
does not grant scientific/operational approval to benchmark models.

The impact panel compares recorded scenario risks with proposed resource usage;
inspection overlays do not change model risk values or imply completion. Resident
exposure, causal risk reduction and environmental savings remain unavailable where
unsupported. Priority explanations show the optimizer's actual weighted scenario
contributions. Headcounts and vehicles require explicit officer assignments.

Predictions additionally accepts timestamped anomaly history and three compatible
L-TOWN CSV measurement families (pressures, flows, levels) with explicit units and
clocks. Follow the field-level column guidance. These remain benchmark inputs;
Delhi provider measurements are never substituted for incompatible network data.

Verification and remaining limitations are recorded in
`reports/DELHI_REFERENCE_INTEGRATION.md`. Native Windows execution still needs a
Windows run; the existing Windows instructions and CI configuration are preserved.
The integrated project is published on `codex/civicflux-ui-model-integration`;
private `.env`, runtime databases and uploaded reports stay local.


## Targeted interface cleanup and report tracking

Navigation now has text-only tabs and no Open reports entry. Public users can
submit mandatory JPEG/PNG issue photos with previews, then keep the confirmed
report ID and use **Track your report** on Report a problem. Review reports remains
admin-only and shows saved images, status, review decisions and public replies.
The complete current suite has 103 passing tests. Internal approval now explains
missing inventory, staff packages, notes and capacity; identical approval retries
reuse one reservation. See `reports/TARGETED_UI_CLEANUP.md` for the exact changes,
root-cause findings and isolated browser verification. The current integration branch is `codex/civicflux-ui-model-integration`.


### Planning control placement

Current situation and What-if assessment appear below the operational inventory
and supervisor-review panels, immediately above the selected planning content.
This restores their earlier position after the targeted cleanup.


## Named geographic demonstrations and WAQI

City map now separates available observations from a simulated Delhi scenario.
Water supply opens an illustrative network; use its Road network and Drainage and
rain controls to explore named geographic anchors, assumed volume/capacity and
labelled simulated blockages. Planning > What-if assessment includes the same
geographic display with saved model review flags and proposed inspection rings.
Predictions > Traffic volume adds a transparent capacity interpretation after the
actual saved forecast. These display associations do not validate real asset maps.

Air quality uses live WAQI station data and optional, clearly labelled illustrative
colour interpolation. Configure server-only `WAQI_API_TOKEN` in private `.env`;
restart the backend after changing keys. Configure provider keys in your private `.env`. WAQI is used by the backend;
only the restricted Google Maps browser key is embedded in the frontend build.
`OPENWEATHERMAP_API_KEY` enables optional rain imagery; the existing restricted
`VITE_GOOGLE_MAPS_API_KEY` enables Google TrafficLayer and requires a Vite restart.
Static scenario layers work without either of those two optional keys.

Regenerate the geographical demonstration offline with
`python scripts/build_demo_geography.py`. Data/source IDs and ODbL attribution are
under `data/geography/`. See `reports/MAP_DEMONSTRATION_INTEGRATION.md` for tested
behavior, provider terms and remaining limits. The current map integration and interface cleanup are included in `main`.


## What a fresh clone includes

The current interface, all nine saved model components, eleven notebooks, Delhi
reference documents, and static scenario geography are versioned. A fresh clone
starts with an empty local database: your local reports, uploads and sessions are deliberately excluded. Provider credentials remain local environment settings. Setup creates a private
`.env` for a new installation and preserves existing local account settings.

For the same optional provider layers, edit your private `.env` after setup:

- `VITE_GOOGLE_MAPS_API_KEY`: your restricted Google Maps browser key. Enable
  Maps JavaScript API with billing and allow your localhost/deployed referrers.
- `WAQI_API_TOKEN`: your WAQI token for station AQI.
- `OPENWEATHERMAP_API_KEY`: optional precipitation imagery.

Restart both servers after configuring provider keys; rebuild the frontend if
using the single-server production launcher. Provider quotas and restrictions apply.
The app can run without these keys; affected live layers explain missing setup.
Public weather feeds still require internet access and their availability can vary.
To reproduce historical rainfall, AQI, traffic and water examples, also acquire
the original datasets as explained above and in DATASET_GUIDE.md. A missing
restricted dataset is reported explicitly; the application does not invent data.

Open http://127.0.0.1:5173 after running both servers. GitHub displays source code;
it does not run this Python backend just by opening an HTML file. Use the setup
and run commands above on Windows or macOS. No paid hosting is needed locally.


### If the browser shows `{"detail":"Not Found"}`

Do not keep using an older server terminal after updating the files. Stop it with
Ctrl+C, pull the latest main (or fully extract the new ZIP), and run the root
launcher again. Open the exact website address printed by the new launcher,
normally http://127.0.0.1:8001/. Paths under `/api` are API endpoints, not pages.
The launcher now rebuilds the frontend on every start and checks for a conflicting
server before printing its URL. It does not kill unrelated processes. If the
frontend is absent on a directly started backend, `/` displays setup instructions.


## PIN-based administration and municipal decisions

The postal registry contains 77 Delhi, 24 Chandigarh and 2 Chennai PINs (partial coverage).
One `admins` row is seeded for every listed PIN. All usernames are `admin`; the
six-digit public postal PIN identifies the account and is its requested password.
There are no random PINs or additional login secrets. Postal PINs are public, so
this login identifies an area, not an independently verified municipal officer.

Use `/admin/login`, for example `admin` / `110001`. An active area session is
server-derived, HttpOnly, SameSite=Strict, Secure on HTTPS, with a 30-minute idle
limit and eight-hour maximum lifetime. Five failures per IP lock login for 15
minutes. Login audit stores time, IP, PIN (never arbitrary password text) and result.
Old supervisor/password identities remain historical records but cannot log in.

```sh
.venv/bin/python scripts/seed_area_admins.py
.venv/bin/python scripts/provision_admin.py --pin 110001 --deactivate
.venv/bin/python scripts/provision_admin.py --pin 110001
```

Windows uses `.\.venv-windows\Scripts\python.exe` for these scripts. Seeding is
idempotent and preserves deactivated areas. To add an entirely new area, first add
its sourced postal reference to `config/postal_reference.json`, then run the seed
script. Review reports > Administrator assignments shows only the signed-in area
and can deactivate it. Cross-area activation/deactivation is a trusted server
console operation, so an area admin cannot modify another area's access.

Area queries filter records in SQLite; missing or unmatched PINs stay unassigned
and are visible to no area account. Exact unambiguous locality matches are
backfilled. Coordinates alone are not assigned without a postal-boundary source.
Citywide source data is not relabelled as postal data. Provider weather/CAMS uses
GeoNames' approximate postal coordinates (CC BY 4.0), independently of complaint
scope. No coordinate exists in the supplied reference for 160021 and 160035; those
areas report unavailable instead of using a city-centre fallback. Station AQI is
hidden in an area session unless postal membership can be verified. The public
site retains citywide station maps. See `config/postal_centroids.json` for provenance.

The civilian Overview alone displays the latest active notice below the globe.
The fixed navbar is inert/hidden at the top and reveals after 80px of scrolling.
The admin portal has its own permanent navigation and area command-centre palette.
Simulation maps and actions require a valid area session.

Use Review reports to validate evidence and record assessed severity, population
(unknown/estimated/verified), and an intervention package. A verified population
claim needs an evidence reference; citizen estimates stay separate. Record a
current, authorized PIN inventory in Planning. Declare only locality funds
actually available for the exercise, then create a response proposal. Published
municipal budgets never become operational capacity automatically.

OR-Tools uses proposed 60% severity / 40% population weights, normalized inputs,
minimum intervention costs, staff, vehicles, pumps and specialized crew-hours.
Unknown population remains unknown; available severity weight is renormalized
when appropriate. Population sums can overlap and are not unique exposed people.
Approval rechecks current inventory, stale assessments, jurisdiction, locality
funding, duplicate incidents and reservations inside one SQLite write transaction.
Approved/deferred/rejected/released decisions and active reservations persist.
There is no external crew dispatch or unsupported causal risk-reduction estimate.

Decisions reuses the saved research models, graph and optimizer. Current
assessment is followed immediately by Map scenario, then the what-if controls,
allocations, impact comparison and cascade view. Real locality packages and the
hypothetical research graph remain explicitly distinct.

Weather offers Tomorrow, 1 week and 10 days from Open-Meteo. Missing optional
fields display unavailable. Feels-like and humidity are daily means from hourly
provider forecasts. These forecasts do not replace saved ML rainfall inference.

CivicFlux Help is a searchable, role-aware deterministic walkthrough. It does
not send complaint contents to an AI service or change administrative records.
See `reports/PIN_MUNICIPAL_INTEGRATION.md` for the implementation, tests and limits.

## Online deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the Render setup, environment variables,
persistence requirements and included Linux container checks.

## Complaint confirmation email

Set `SMTP_USER=civicflux1001@gmail.com`, `SMTP_PASS` to that Gmail account's App
Password, and `SMTP_PORT=465` (SSL) or `587` (STARTTLS) in your private `.env` or
host environment. Restart the backend after changes. Never commit the password.
Receipts are sent only for successfully registered complaints, once per tracking
ID, with per-IP (10/hour) and per-recipient (3/hour) limits. Email failures do not
remove the complaint or its tracking ID. SMTP is mocked in automated tests.

## Chennai and Chandigarh open data

Delhi remains unchanged. The application retains its 103 original PINs and adds eight verified Chennai entries. New map snapshots, historical reservoir storage and independently cached modelled conditions are documented in [the integration report](docs/OPEN_DATA_INTEGRATION.md). Three remote sources are currently unavailable (OpenCity 2015 zone: HTTP 404; Overpass facilities: HTTP 406). They are omitted from maps and listed explicitly in Data and sources.

```sh
corepack pnpm run data:fetch
corepack pnpm run data:build
corepack pnpm run data:verify
corepack pnpm run data:status
corepack pnpm run preflight -- --warm
corepack pnpm run verify
```

The final command includes strict source completeness and therefore reports failure until all mandatory sources are fetched. The existing site remains usable. No models are retrained. Reservoir readings end in December 2021 and are historical; percentages are withheld pending official capacity verification. See the report for the exact fixture differences approved by the user, full source checksums, licence obligations and verification limits.

### Snapshot and live sources

- [Chandigarh boundary](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chandigarh/Chandigarh_Boundary.geojson) — chandigarh; OK; CC BY-SA 2.5 India; Chandigarh Municipal Spatial Data via DataMeet India community (CC BY-SA 2.5 India). Used for Map scenario boundaries and coordinate validation.
- [Chandigarh sectors](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chandigarh/Chandigarh_Sectors.geojson) — chandigarh; OK; CC BY-SA 2.5 India; Chandigarh Municipal Spatial Data via DataMeet India community (CC BY-SA 2.5 India). Used for Map scenario boundaries and coordinate validation.
- [Chennai metropolitan outline](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chennai/CMA.geojson) — chennai; OK; CC BY-SA 2.5 India; Chennai Municipal Data, received from the Transparent Chennai team, via DataMeet India community (CC BY-SA 2.5 India). Used for Map scenario boundaries and coordinate validation.
- [Flood hazard zones](https://data.opencity.in/api/3/action/resource_show?id=e61afe07-0f52-4be9-bdf3-5eb0f62b2ed6) — chennai; OK; Public Domain; Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain). Used for Historical flood exposure, never an operational warning.
- [Flooding points in 2015](https://data.opencity.in/api/3/action/resource_show?id=80ed2fa7-1150-4f55-8125-682ab55282ac) — chennai; OK; Public Domain; Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain). Used for Historical flood exposure, never an operational warning.
- [2015 inundation zone](https://data.opencity.in/api/3/action/resource_show?id=7cb3cecf-a95a-4786-8032-9c7417655d24) — chennai; NOT FETCHED; Public Domain; chennaifloodsdss.in via OpenCity.in (Public Domain). Used for Historical flood exposure, never an operational warning.
- [Inundation depth points](https://data.opencity.in/api/3/action/resource_show?id=ceddf53f-03c0-4866-8ba8-5e84c8007a85) — chennai; OK; Public Domain; Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain). Used for Historical flood exposure, never an operational warning.
- [Chennai wards](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/Chennai/Wards.geojson) — chennai; OK; CC BY-SA 2.5 India; Chennai Municipal Data, received from the Transparent Chennai team, via DataMeet India community (CC BY-SA 2.5 India). Used for Map scenario boundaries and coordinate validation.
- [Chandigarh facilities](https://overpass-api.de/api/interpreter) — chandigarh; NOT FETCHED; ODbL; ©️ OpenStreetMap contributors (ODbL). Used for Nearby facility reference points; availability is unknown.
- [Chennai facilities](https://overpass-api.de/api/interpreter) — chennai; NOT FETCHED; ODbL; ©️ OpenStreetMap contributors (ODbL). Used for Nearby facility reference points; availability is unknown.
- [Chembarambakkam historical storage](https://data.opencity.in/api/3/action/resource_show?id=db41b1a4-5746-46d0-a006-e8fe2b1545a9) — chennai; OK; Public Domain; Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain). Used for Historical monthly reservoir storage.
- [Cholavaram historical storage](https://data.opencity.in/api/3/action/resource_show?id=20dc9876-ef1d-4cf1-9c42-f9d6c1f137db) — chennai; OK; Public Domain; Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain). Used for Historical monthly reservoir storage.
- [Kannankottai-Thervoy Kandigai historical storage](https://data.opencity.in/api/3/action/resource_show?id=e0355257-d2d9-48be-a31e-6596a5fcdc07) — chennai; OK; Public Domain; Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain). Used for Historical monthly reservoir storage.
- [Poondi historical storage](https://data.opencity.in/api/3/action/resource_show?id=8b0c0edc-4204-4f0f-8dc7-2db4817af04f) — chennai; OK; Public Domain; Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain). Used for Historical monthly reservoir storage.
- [Puzhal (Red Hills) historical storage](https://data.opencity.in/api/3/action/resource_show?id=febf2951-71eb-4807-9a06-246dadc1ef04) — chennai; OK; Public Domain; Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain). Used for Historical monthly reservoir storage.
- [Veeranam historical storage](https://data.opencity.in/api/3/action/resource_show?id=a2f9aaad-7ac2-4a01-90d6-801eeef7d4b6) — chennai; OK; Public Domain; Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain). Used for Historical monthly reservoir storage.
- [All India Pincode Directory](https://raw.githubusercontent.com/dropdevrahul/pincodes-india/d817d3e652e8167a70507350d9a8e4acda9113ef/pincode.csv) — chennai,chandigarh; OK; GODL-India; Department of Posts, Government of India, All India Pincode Directory (data.gov.in), Government Open Data License - India, via community mirror. Used for Postal reference points; Delhi is excluded from all updates..

Live: Air quality: CAMS ENSEMBLE data provider (Copernicus Atmosphere Monitoring Service) via Open-Meteo.com; River discharge: GloFAS via Open-Meteo.com (CC BY 4.0, free non-commercial service).

### Evaluated, not used

- Chandigarh wards: Duplicate ward 5, reserve polygon, missing and duplicated population values; sectors used instead.
- Chennai Wards-2008: Pre-2011 boundaries; excluded.
- Princeton / Stanford Chandigarh shapefiles: Access restricted.
- Census 2011 ward data: Identifiers do not match shipped layers; no formula requires it.
- GCC Budget 2026-27: PDF; link only: https://data.opencity.in/dataset/gcc-budget-2026-27
- GCC Relief Centres: October 2024 PDF; link only: https://data.opencity.in/dataset/gcc-relief-centres
- GCC stormwater base maps: PDF; link only, not parsed.
- Return-period flood KMLs: Out of scope.
- GCC GIS REST server: Availability and licence unconfirmed.
- Smart Cities portal: No Chandigarh catalogue enumerated.
- Complaint datasets: No verified open complaint data supplied; existing records retained, no synthetic operational reports added.
- AQICN: Requires token and separate terms; existing Delhi integration unchanged.
- GCC fire stations: Optional; no licence stated, not redistributed.
- GCC health centres: Optional, not integrated; coordinate columns not verified.
- GCC flood hotspots 2020: Optional; not integrated.
- CPCB data.gov.in: Optional; no verified API resource/key configured for this integration.

### Source publication and record counts

| Source | Published | Retrieved (UTC) | Input → output |
|---|---|---|---|
| chd_boundary | 2023-11-16 | 2026-10-29T20:21:33.669536+00:00 | 1 → 1 |
| chd_sectors | 2023-11-16 | 2026-10-29T20:21:33.711828+00:00 | 63 → 63 |
| che_cma | 2023-11-16 | 2026-10-29T20:21:33.702206+00:00 | 1 → 1 |
| che_flood_hazard | 2025-11-25 | 2026-10-29T20:21:39.141827+00:00 | 7453 → 7189 |
| che_flood_points_2015 | 2025-11-25 | 2026-10-29T20:21:34.979541+00:00 | 753 → 753 |
| che_flood_zone_2015 | 2024-01-10 | None | None → None |
| che_inundation_points | 2025-11-25 | 2026-10-29T20:21:35.011077+00:00 | 192 → 192 |
| che_wards | 2023-11-16 | 2026-10-29T20:21:33.936996+00:00 | 201 → 200 |
| facilities_chandigarh | Not supplied | None | None → None |
| facilities_chennai | Not supplied | None | None → None |
| lake_chembarambakkam | 2025-11-27 | 2026-10-29T20:21:37.289021+00:00 | 228 → 228 |
| lake_cholavaram | 2025-11-27 | 2026-10-29T20:21:36.556854+00:00 | 228 → 228 |
| lake_kannankottai | 2025-11-27 | 2026-10-29T20:21:37.234220+00:00 | 24 → 24 |
| lake_poondi | 2025-11-27 | 2026-10-29T20:21:36.584546+00:00 | 228 → 228 |
| lake_puzhal | 2025-11-27 | 2026-10-29T20:21:38.052749+00:00 | 228 → 228 |
| lake_veeranam | 2025-11-27 | 2026-10-29T20:21:37.266674+00:00 | 228 → 228 |
| pin_directory | Not supplied | 2026-10-29T20:21:37.618563+00:00 | 157126 → 19 |

## City infra, notifications and email review

Infrastructure now lives in the authenticated **City infra** tab. Its static reference
is shared across PINs within a city; operational permissions remain PIN-scoped. Public
interior pages keep their navigation visible. See [the portal review and sender setup](docs/PORTAL_FIXES_REVIEW.md)
for the complete checklist, local review steps, Windows instructions, unavailable feeds,
notification polling limits and the verified free Gmail SMTP option. No mailbox is
created by setup and no email delivery is claimed without provider acceptance.

## Interactive onboarding (local)

Use **Show me around** on first use, or **Help / Take a tour** at the bottom right.
Choose the full public/municipal path or a feature topic. Sign in normally to access
admin topics; the guide does not grant permissions. During a tour, saving a report,
scenario, notice, inventory, budget or decision requires a separate real-change confirmation.
Completion is stored locally per account/anonymous browser. **Restart from beginning**
resets this tour progress, not application records.

See [the complete feature audit and review checklist](docs/ONBOARDING_COVERAGE.md).
Run tour regressions with `corepack pnpm --dir frontend test:tour`.

## Postal-area transparency update

Monetary history shows recorded allocation and paid expenditure for a selected PIN and fiscal year. Missing records stay unrecorded; plan reservations are separate. Phone navigation now uses a hamburger. Water/infrastructure maps include an explicitly illustrative, read-only network. Public notifications require an area selection, suggested through browser location permission or selected manually. See [the update and verification notes](docs/AREA_TRANSPARENCY.md). Gmail credential setup is deferred; keep credentials in private environment variables.

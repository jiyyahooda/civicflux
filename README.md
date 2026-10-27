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
- Open **http://127.0.0.1:8001/** and sign in with **admin / 001**.
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
Setup applies the shared administrator login **admin / 001**, including on
existing clones. API keys, database paths and other `.env` settings are preserved.

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
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

For the frontend, `cd frontend` then `corepack pnpm dev`.
The root Windows `.cmd` launcher now uses the same native `.venv` and backend
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
| `CIVICFLUX_ADMIN_ID` | Local administrator username |
| `CIVICFLUX_ADMIN_PASSWORD` | Shared local password: `001` |
| `CIVICFLUX_PUBLIC_FEEDS` | `1` enables public observations; `0` disables network feeds |
| `CIVICFLUX_IMD_URL`, `CIVICFLUX_CPCB_URL` | Optional verified JSON feeds |
| `DATA_GOV_IN_API_KEY` | Optional server-side official CPCB source key |
| `CIVICFLUX_ROOT` | Optional absolute project root override, set in the shell before launch |

Copy `.env.example` to `.env` when configuring manually. The shared login is
**Admin ID: `admin` · Password: `001`**.
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
# Use .venv/Scripts/python.exe instead on Windows.
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
# Existing legacy tests use a fixed synthetic login, only for this test process:
CIVICFLUX_ADMIN_PASSWORD=001 .venv/bin/python -m pytest -q
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm build
```

Windows equivalents:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/verify_runtime.py
$env:PYTHONUTF8='1'
$env:CIVICFLUX_ADMIN_PASSWORD='001' # Shared local development login
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:CIVICFLUX_ADMIN_PASSWORD
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
restart the backend after changing keys. The owner has explicitly shared the Google Maps and WAQI keys in `.env.example`.
Setup copies these into a new local `.env`; the WAQI token is used by the backend,
not embedded in frontend code.
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
starts with an empty local database: your local reports, uploads and sessions are deliberately excluded. Google Maps and WAQI provider
keys are intentionally included in `.env.example` with the owner’s permission. Setup creates a local `.env` and applies the shared login **admin / 001**.

For the same optional provider layers, edit your private `.env` after setup:

- `VITE_GOOGLE_MAPS_API_KEY`: your restricted Google Maps browser key. Enable
  Maps JavaScript API with billing and allow your localhost/deployed referrers.
- `WAQI_API_TOKEN`: your WAQI token for station AQI.
- `OPENWEATHERMAP_API_KEY`: optional precipitation imagery.

Restart both servers after configuring keys. The shared Google Maps and WAQI
keys can be copied and used by anyone with repository access; their quotas and
provider restrictions still apply.
The app can run without these keys; affected live layers explain missing setup.
Public weather feeds still require internet access and their availability can vary.
To reproduce historical rainfall, AQI, traffic and water examples, also acquire
the original datasets as explained above and in DATASET_GUIDE.md. A missing
restricted dataset is reported explicitly; the application does not invent data.

Open http://127.0.0.1:5173 after running both servers. GitHub displays source code;
it does not run this Python backend just by opening an HTML file. Use the setup
and run commands above on Windows or macOS. No paid hosting is needed locally.


### Shared map keys: existing clones

New installations receive the owner-provided Google Maps and WAQI keys from
`.env.example` when setup creates `.env`. Existing `.env` files are preserved.
After `git pull origin main`, copy just `VITE_GOOGLE_MAPS_API_KEY` and
`WAQI_API_TOKEN` from the updated `.env.example` into your local `.env`. Run `scripts/local_config.py` with your virtual-environment Python to apply
the shared **admin / 001** login. Restart both development servers. If
serving a production build, run `corepack pnpm build` inside `frontend` again
before restarting the backend, because the Google browser key is set at build time.

The OpenStreetMap base maps and static networks do not require either key. If
all maps are blank, first check that the backend is running on port 8001, the
frontend is opened at http://127.0.0.1:5173, and the network permits map tiles.


### Same administrator login on every contributor's machine

For the current local project setup, everyone uses **Admin ID `admin`** and
**Password `001`**. Both platform setup scripts apply this shared login while
preserving provider configuration and the local database.

Existing clones: pull `main`, then run one command from the repository root:

```sh
# macOS
.venv/bin/python scripts/local_config.py
```

```powershell
# Windows
.\.venv\Scripts\python.exe scripts/local_config.py
```

Restart the backend and sign in. This is an intentionally shared, weak local
development login; use individual strong credentials before public hosting.
Each machine still has its own reports and database; a shared login does not
synchronize those records. Historical prediction examples still require the
documented original datasets.


### If the browser shows `{"detail":"Not Found"}`

Do not keep using an older server terminal after updating the files. Stop it with
Ctrl+C, pull the latest main (or fully extract the new ZIP), and run the root
launcher again. Open the exact website address printed by the new launcher,
normally http://127.0.0.1:8001/. Paths under `/api` are API endpoints, not pages.
The launcher now rebuilds the frontend on every start and checks for a conflicting
server before printing its URL. It does not kill unrelated processes. If the
frontend is absent on a directly started backend, `/` displays setup instructions.

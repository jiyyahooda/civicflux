# Latest application update

The latest interface uses a cursor-responsive 3D network globe and scroll chapters,
sticky top navigation, and a compact searchable city picker. See
[interface verification](reports/ORBITAL_INTERFACE_20261027.md) and the complete
[CPCB account/API setup guide](CPCB_SETUP.md).

IMD weather now uses verified public station reports for Delhi, Chandigarh and Chennai.
The map-first overview separately displays CAMS air-quality estimates and source
freshness. Official CPCB access requires your own `DATA_GOV_IN_API_KEY` in `.env`;
setup instructions are available inside the dashboard. Restart the launcher after
updating. See [live-source verification](reports/LIVE_SOURCES_AND_DASHBOARD.md).

The interface now includes glass controls, orange/white and neon-green/black themes,
a scroll-splitting CSS city, six scenario templates, connected research charts,
searchable dependency graphs, a Google reference map and tracked civic complaints.
Review decisions now atomically update scenario status while preserving all approval
restrictions. See `reports/APPLICATION_UPGRADE.md` for current pages and validation.

# CivicFlux local application

A GitHub clone or ZIP contains source and saved models, not a preinstalled Python
environment or compiled UI. These are created on each device by setup. Do not copy
a virtual environment from a different OS. See [README](README.md) for prerequisites.

- Windows: install Python 3.13 (with `py` launcher), Node 24 and Corepack, then
  double-click `START-CIVICFLUX.cmd`. First run performs setup and builds the UI.
- macOS: install Homebrew, Python 3.13, Node 24 and Corepack, then run
  `bash scripts/start_mac.sh` from Terminal in the project folder.
- Open **http://127.0.0.1:8001** for this single-server launch. Keep its terminal open.
- Admin ID: **admin**. Password: **001**. Initial dependency downloads require internet.

## Development

For separate frontend/backend processes, use `scripts/run_windows.ps1 backend`
and `scripts/run_windows.ps1 frontend`, or their `scripts/run_mac.sh` equivalents.
Then open **http://127.0.0.1:5173**. Vite proxies `/api` to port **8001**.
After frontend edits, rebuild before using the single-server launcher:
`cd frontend` then `corepack pnpm build`.

Both Windows setup entry points use native Python 3.13 in `.venv-windows`.
macOS uses `.venv`. A copied Python 3.12 Windows environment is preserved as a
timestamped backup and replaced; old instructions using port 8000 are obsolete.

## Pages and access

Overview, Predictions, Infrastructure, Cascade analysis, Planning, Operations,
and Model validation use the FastAPI API. Civilians can view saved analyses and submit
complaints. Admin sessions enable research requests, scenario inputs, resource and
policy-weight changes, complaint status updates, defer/reject reviews, and separate
simulation evidence records. Credentials and authorization are checked server-side.
Reviews, outcomes, complaints, sessions and append-only application audit events persist
in `var/civicflux.sqlite3`. Tests use isolated databases.

The original research review function forbids approval. Approve requests return 409,
and no code dispatches interventions. The civilian portal cannot call admin mutations.
Review notes never become independently verified outcome labels. External verifier names
are attestations; their identities are not authenticated by this prototype.

## Research and scenario boundaries

Models are selected from `artifacts/model_validation/v1.0.0/model_registry.json`.
No duplicate inference pipeline or model registry was introduced. The API imports
`src.civicflux.serving.serve`. Windows checks are separate in `reports/windows/inference`;
the old macOS reports remain intact and cannot certify a changed interface.

The application scenario is declared in `config/scenarios/research.yaml`. It uses saved
synthetic graph 100 with its exact fingerprint. The old graph-42 planning manifest does
not match the graph regenerated on this Windows environment, so its risk evidence is
not fused. The new application scenario explicitly assigns the existing fictional cost
and policy template to matching graph-100 asset IDs, discards old cascade scores, and
recomputes scores using the saved cascade model on graph 100. Known outage seeds are
declared failed assumptions, not predicted probabilities. OR-Tools and two greedy
baselines use identical budgets, pumps and crew-hour limits. Factor breakdowns are shown.

The default flood engine is the existing `civicflux_core.simulate_depth` mass-balance
simulator. It is explicitly distinct from the trained flood surrogate. Selecting the
trained surrogate uses the recovered native model export, preserving calibration. Flood
and cascade run as parallel scenario evidence: no unvalidated flood-to-asset dependency
is invented. Uncertainty is unavailable for mass-balance simulation and is shown as such.

Traffic and flood now load through verified native UBJSON exports while retaining the
original joblib preprocessing, calibration and thresholds. All nine serving components
pass fresh-process inference and abstention checks. See `reports/WINDOWS_MODEL_RECOVERY.md`.
Historical saved charts
remain labeled as evaluation results; they are never presented as live predictions.

Delhi has only aggregate rainfall and PM2.5 research support. AQI research forecasts
PM2.5, not an official AQI index. Chandigarh and Chennai have no supplied model or
station mapping. Anonymous traffic and L-TOWN water research are not relocated to cities.

IMD/CPCB adapters accept only explicitly configured JSON gateways and verified station
mappings; no endpoints, readings or coordinates are guessed. All cities currently show
unavailable observations. Gateway payload contract: `source`, `city_id`, `station_id`,
timezone-aware `observed_at`, and `readings` mapping metric names to `{value, unit}`.
Supported units are declared in `backend/services/data_service.py`. Source configuration
must be independently verified before adding mappings. No supported live traffic source
is configured.

## Verification

```powershell
.\.venv-windows\Scripts\python.exe scripts\verify_windows.py
.\.venv-windows\Scripts\python.exe -m pytest tests -q
cd frontend
pnpm build
```

The model verification script deliberately exits nonzero while any saved model fails.
See `reports/WINDOWS_MIGRATION.md` and `reports/APPLICATION_VERIFICATION.md` for the
measured results and remaining limitations. No notebooks or trained artifacts were
regenerated or retrained. Model training remains a future, separately authorized step.


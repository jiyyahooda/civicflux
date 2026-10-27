# Windows migration verification

> Historical baseline before the authorized recovery. Traffic and flood have since been recovered; see [WINDOWS_MODEL_RECOVERY.md](WINDOWS_MODEL_RECOVERY.md) for current results. The JSON inference reports now contain the post-recovery checks.

Verified: 2026-10-26T22:29:12.644872+05:30.

## Scope and existing files

This run stops at migration and research inference verification. Backend and frontend files were already present when this request began; they were preserved and were not implemented, extended, or certified by this run. Earlier application reports describe earlier workspace state and are not evidence of work performed in this run.

Canonical project root: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux`.

Source ZIP: `C:\Users\kusha\OneDrive\Desktop\civicflux_ml.zip`. Read and compared all 414 substantive files, excluding transferred virtual environments, caches, and Apple resource files. All required research files were already extracted, so no overwrite or redundant extraction was necessary. Missing originals: 0.

Protected research files: 290. Artifacts, datasets, and notebooks match the ZIP: **True**. No training, notebook execution, artifact conversion, or metadata regeneration was performed.

Existing differences from the ZIP: `.gitignore`, `tests/test_review_and_serving.py`, `src/civicflux/serving.py`. These differences predated this run; this run did not alter those files. Original serving code remains accessible in the source ZIP. No automatic copy merge or deletion was performed.

Other complete copies checked: `C:\Users\kusha\OneDrive\Desktop\civicflux_ml\civicflux_ml`. Per-file comparisons are in `windows/migration_reverification.json`. Matching research content cannot be ranked by transfer timestamps. The workspace copy is canonical for this task. The workspace also contains `CivicFlux-Complete.zip`, a previously generated application bundle, which was not extracted or treated as the research source.

## Windows environment

Python 3.12.14; executable: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\.venv-windows\Scripts\python.exe`. Reused the existing Windows environment at `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\.venv-windows` after rerunning imports, dependency checks, and fresh-process inference. It was not recreated unnecessarily. The transferred macOS `.venv` was not used. Its recorded Python version is 3.13.5; cross-version artifact compatibility is established only for components that actually pass here.

All existing requirements satisfied: **True**. `pip check`: exit 0, No broken requirements found.. Complete measured versions: `windows/requirements-windows.lock.txt`. Required imports including scikit-learn, XGBoost, NetworkX, OR-Tools, and all twelve requested source files pass. Detailed module hashes and requirement comparisons are in the JSON evidence.

The system `python` and `py` commands resolve to inaccessible WindowsApps aliases in this session. Use the explicit environment executable above. No machine-wide PATH or security settings were changed.

## Model verification

Selection follows the existing `artifacts/model_validation/v1.0.0/model_registry.json`, not directory sorting. All selected artifacts, metadata/model cards, and feature schemas exist. All available version directories remain intact and are listed in the evidence JSON. Selected artifact paths below are relative to the canonical root; absolute paths, units, scope, provenance, horizon, and selected metadata/schema paths are in `windows/migration_inventory.json`.

| Component | Registry version | Artifact or implementation | Fresh-process verification |
| --- | --- | --- | --- |
| rainfall | legacy-unversioned | `artifacts\rainfall\pipeline.joblib` | PASS: supported_research |
| aqi | legacy-unversioned | `artifacts\aqi\pipeline.joblib` | PASS: supported_research |
| traffic | legacy-unversioned | `artifacts\traffic\pipeline.joblib` | FAIL: abstained |
| flood | legacy-unversioned | `artifacts\flood\pipeline.joblib` | FAIL: abstained |
| infrastructure_anomaly | 1.0.0 | `artifacts\infrastructure_anomaly\v1.0.0\detectors.joblib` | PASS: supported_research |
| water_network | 1.1.0 | `artifacts\water_network\v1.1.0\pipeline.joblib` | PASS: supported_simulation |
| cascade_risk | 1.1.0 | `artifacts\cascade_risk\v1.1.0\pipeline.joblib` | PASS: supported_simulation |
| resource_optimization | 1.1.0 | `src/civicflux/optimization.py (CP-SAT; no trained model)` | PASS: supported_simulation |
| intervention_outcomes | 1.1.0 | `artifacts\intervention_outcomes\v1.1.0\pipeline.joblib` | PASS: supported_simulation |

Fresh-process checks used the existing `scripts/check_research_inference.py` through `scripts/verify_windows.py`. **7/9 components pass** supported historical/synthetic inference and their negative checks. The anomaly check covers each of the five registered sensors. **75/75 negative requests returned abstention**. For traffic and flood, a model-load failure can mask later payload validation; their complete input-validation behavior is therefore not certified.

Traffic and flood positive cases abstain with `input stream corrupted` while loading joblib-embedded XGBoost state. Their saved files match the ZIP and XGBoost imports successfully; the exact serialization incompatibility is unresolved. Neither component was substituted, retrained, rewritten, or declared ready. Their old macOS success reports do not establish Windows compatibility.

Research contracts remain enforced: explicit scope, units, horizons, historical/simulation clocks, freshness, provenance, and operational abstention. Rainfall is Delhi aggregate mm/day for the next day. The AQI component predicts next-hour PM2.5 under incomplete unit/station lineage, not an official AQI index. Traffic has anonymous benchmark junctions. Water uses the simulated L-TOWN network and does not certify actual faults. Flood, cascade, optimization, and outcomes retain synthetic research limitations. Supported responses retain `research_only=true`, `operational_supported=false`, and `dispatch_allowed=false`. Forecast intervals remain research residual intervals with no guaranteed conditional coverage. No live readings or real municipal coordinates were fabricated.

## Central paths and future import

Existing central configuration: `project_paths.py`; optional `CIVICFLUX_ROOT` environment override. Runtime locators use pathlib. The historical macOS paths inside original artifact metadata are provenance and were preserved. `runtime.research_environment()` applies its macOS library handling only on Darwin.

- Project root: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux`
- ML modules: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\src\civicflux`
- Artifacts: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\artifacts`
- Registry: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\artifacts\model_validation\v1.0.0\model_registry.json`
- Datasets: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\data`
- Configuration: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\config`
- Future integration target (already present): `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\backend`

Use the project root as the working directory or add it to PYTHONPATH:

```python
from project_paths import PROJECT_ROOT
from src.civicflux.serving import serve
response = serve(component, request, PROJECT_ROOT)
```

Exact source module: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux\src\civicflux\serving.py`. Reuse this serving function and the existing registry; do not duplicate the inference pipeline.

## Remaining blockers

- Resolve the two saved XGBoost model-loading failures before claiming all nine components ready. This run does not authorize retraining or artifact conversion.
- Verify city/station mappings, source credentials, operational provenance, and municipal asset/resource inventories before operational integration. Current research-only status is not operational approval.
- Inspect and reconcile the already-present application with the requested future workflow in a separately authorized implementation phase. Its pages, API routes, login, and approval persistence were not retested in this migration-only run.

No new Windows compatibility source fix was necessary. Only verification reports and an additive audit script were written during this run. Migration verification is complete with two explicitly unresolved component failures.

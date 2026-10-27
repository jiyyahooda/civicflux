# CivicFlux Windows model recovery

Verified on 26 October 2026 (Asia/Kolkata). **Traffic and flood are recovered. All nine components now pass the existing fresh-process research serving checks. No model was retrained.** This report supersedes the two unresolved model failures in the earlier migration reports.

Project root: `C:\Users\kusha\OneDrive\Documents\ChatGPT\zinnovatio4.0\CivicFlux`.

## Failure and recovery

Both original joblib bundles fail in Windows XGBoost's `XGBoosterUnserializeFromBuffer` with `input stream corrupted`. Their embedded snapshots contain separate `Config` and `Model` objects. The exact native `Model` bytes load successfully through XGBoost's supported `load_model` interface. Native `save_model` UBJSON exports are **byte-identical** to those extracted model sections. No tree, weight, split, feature ordering, calibration value, threshold, or fitted preprocessing value was edited.

The failure is isolated to the full snapshot-loading path on this environment. The precise native deserializer defect has not been established. An [upstream report](https://github.com/dmlc/xgboost/issues/12459) describes similar cross-platform behavior; it does not establish that the same defect caused this case. XGBoost recommends native model exports for durable storage in its [model I/O documentation](https://xgboost.readthedocs.io/en/release_3.2.0/tutorials/saving_model.html).

The original macOS process was unavailable. Recovery was completed locally on Windows and verified against every saved test prediction. Python remains 3.12.14 and XGBoost remains 3.4.1; no package replacement or downgrade was needed.

## Portable files and serving

| Component | Original bundle, preserved | Additive exports |
| --- | --- | --- |
| Traffic | `artifacts/traffic/pipeline.joblib` | `artifacts/traffic/portable-windows/booster.ubj`, `booster.json`, `manifest.json` |
| Flood | `artifacts/flood/pipeline.joblib` | `artifacts/flood/portable-windows/booster.ubj`, `booster.json`, `manifest.json` |

All paths above are relative to the project root. The manifests contain original artifact hashes, snapshot hashes, native-export hashes, environment versions, timestamps, parity checks, and limitations. They are recovery records, not replacement model registries. The existing `artifacts/model_validation/v1.0.0/model_registry.json` still selects the original model versions.

`src/civicflux/portable.py` uses a scoped joblib unpickler to attach the verified native booster to the **original** bundle. Preprocessing, feature recipes, interval radius, flood isotonic calibration, threshold 0.03, metadata, and bundle classes remain sourced from the original joblib. No global XGBoost monkeypatch is installed. A hash mismatch, unverified manifest, or unexpected snapshot layout stops inference. Runtime does not perform automatic recovery or fallback to another model.

The existing `serve()` function now uses that loader for these exports. Other components keep their existing loading path. The original joblib files are intentionally unchanged: calling `joblib.load()` directly on them still encounters the native snapshot problem on this environment. Use the existing serving interface:

```python
from project_paths import PROJECT_ROOT
from src.civicflux.serving import serve
response = serve(component, request, PROJECT_ROOT)
```

Fresh-process reports and readiness checks now bind evidence to the original bundle, portable UBJSON, recovery manifest, and serving source fingerprint. A changed export invalidates previous readiness evidence. The original Mac reports and registry were preserved.

## Measured validation

| Check | Result |
| --- | --- |
| Traffic saved test predictions | All 11,540 rows match; maximum absolute difference 0.00000381 vehicles/hour |
| Traffic 90% interval bounds | All 11,540 lower/upper bounds match within recorded CSV tolerance |
| Flood calibrated probabilities | All 4,420 scenarios match; maximum absolute difference 0.0000000344 |
| Flood alert decisions | All 4,420 identical |
| Native UBJSON round-trip | Exact model-section bytes preserved for both boosters |
| JSON versus UBJSON exports | Same public bundle outputs for supported fixtures |
| Existing fresh-process inference | 9/9 components pass; anomaly checks cover all five sensors |
| Existing negative requests | 75/75 abstain, including traffic/flood payload checks after successful loading |
| Recovery and relevant serving/API regression tests | 33 passed, 0 failures, 0 errors |
| Concurrent loads | Eight concurrent flood loads/predictions agree; global XGBoost method unchanged |
| Altered portable export | Rejected before inference |
| Stale export validation evidence | Cannot certify readiness |

Traffic parity includes all four junctions in the archived evaluation. The serving contract's existing allowlist remains junctions 1–3; recovery did not broaden supported inputs. Floating-point differences above are within the explicit tolerances recorded in the manifests and consistent with saved CSV rounding. No claim of comparison against a currently running Mac process is made.

The API tests cover historical prediction access, synthetic scenario execution using the trained flood surrogate, resource constraints, authentication, and the existing review/audit workflow. They use temporary databases. No new backend route or frontend feature was implemented.

The first test attempt could not create pytest's sandbox temporary directory. Using a workspace temporary path allowed the model checks to run, but FastAPI TestClient then stalled under the sandbox. The final regression run completed outside the sandbox with isolated workspace test data: 33 passed in 6.44 seconds. One existing Starlette/httpx deprecation warning remains; it does not affect these results.

## Preservation and remaining limits

The final archive comparison checked all 414 original substantive files. All **290 original artifact, dataset, and notebook files** remain byte-identical to the source ZIP. Original model versions, notebooks 01–11, datasets, metadata, and registry were not overwritten. The native exports are additive. Source changes in this recovery are the portable loader, its serving connection, validation hash binding, and verification scripts/tests.

Operational predictions and dispatch remain disabled. Traffic remains an anonymous benchmark; flood remains an uncalibrated synthetic research surrogate. Model recovery does not establish municipal geographic mappings, live observation sources, real-world confidence, or operational approval. Existing complete ZIP bundles predate this recovery; use the current workspace files for the repaired system.

## Evidence and reproduction

- `reports/windows/recovery/recovery_results.json`: measured saved-output parity and export hashes.
- `reports/windows/recovery/tests.xml`: final 33-test regression result.
- `reports/windows/migration_inventory.json`: current nine-component loading/inference results and selected versions.
- `reports/windows/inference/*.json`: current supported predictions and negative-input cases.
- `reports/windows/migration_reverification.json`: current original-file integrity comparison.
- `scripts/recover_portable_models.py`: additive recovery/export command; refuses to overwrite an existing export directory.
- `scripts/verify_windows.py`: reruns the existing fresh-process research checks.

From the project root, rerun research verification with:

```powershell
& '.\.venv-windows\Scripts\python.exe' scripts/verify_windows.py
```

Keep each original joblib and its `portable-windows` companion directory together when moving the project. Keep `src/civicflux/portable.py` with the serving source.

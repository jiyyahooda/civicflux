# Cross-platform verification — 2026-10-27

## Measured results

- Host: macOS Apple Silicon; Python 3.13.5, Node 24.22.1, pnpm 12.15.0.
- Homebrew installed libomp 23.1.4. XGBoost 3.4.1 now imports without DYLD workarounds.
- Existing venv: `pip check` passed. Minimal requirements also installed into a
  completely fresh temporary venv; its `pip check` passed.
- Existing environment: **87 Python tests passed**, one deprecation warning.
- Fresh minimal environment: **87 Python tests passed**, one deprecation warning.
- No tests were edited. The warning is Starlette's deprecated httpx compatibility
  path. The current suite uses httpx objects, so the unused optional httpx2 extra
  from the previous FastAPI-standard installation was removed.
- Initial test run had two failures: HTTP client mismatch and stale Windows
  inference evidence. Removing the unused extra and regenerating actual inference
  evidence resolved them; no assertions or model outcomes were bypassed.
- All nine components passed fresh-process saved-model inference plus 75 negative
  request abstention cases in total. Sensor-specific anomaly checks also passed.
- Positive statuses: rainfall, AQI, traffic, infrastructure anomaly =
  supported_research; flood, water network, cascade risk, resource optimization,
  intervention outcomes = supported_simulation.
- Existing tests cover flood/cascade graph consistency, CP-SAT resource feasibility,
  review/approval separation, independent outcome verification, complaints,
  authority routing, SQLite persistence, and invalid input rejection.
- FastAPI startup, `/docs`, `/openapi.json`, health, inventory, cities, observations,
  scenarios, defaults, graph, complaints, feedback and authority APIs passed real
  HTTP checks. All nine prediction POST routes and operational abstention passed.
- Local login/logout, session access via the development origin, and rejection of
  an unrelated origin passed. Only temporary login session rows were used by the
  HTTP smoke check; no citizen reports or scenarios were added to the local DB.
- Frontend root and proxied `/api/health` and `/api/models` returned HTTP 200.
- Frozen pnpm install, TypeScript compilation and production build passed.
  pnpm's package-manager metadata was added to the lock; the application dependency
  document is semantically unchanged. Vite emits a nonblocking >500 kB chunk warning.
- Browser verified Overview, Predictions, Infrastructure/map, Cascade analysis,
  Planning/action plans, Operations/community reports and human review, and Model
  validation. Actual server logs confirmed browser API requests. No browser console
  errors were recorded in the final check. Screenshot: cross-platform/civicflux-map.png.
- IMD measurements and separately labeled CAMS estimates were available during the
  check. Official CPCB was explicitly unavailable without an API key. External
  availability is not guaranteed.

## Preservation and repository safety

All **273 original notebook/artifact files** were SHA-256 checked and unchanged,
including all eleven completed notebooks and eleven joblib files. No training,
notebook execution, model reconstruction or dataset regeneration occurred.
The existing portable model exports were consumed unchanged.

The new branch is `feature/mac-cross-platform-setup`. GitHub returned no refs and
repository size zero; the local Desktop project was initialized on that branch.
No unrelated local repository was used. Authenticated GitHub API checks confirmed
write permission to `kushagrachess21-prog/Zinnovatio-4.0`. Repository-local Git author
email uses the authenticated account's GitHub noreply address.

No push is authorized yet: the user explicitly requested approval before the final
push. No remote history, branches, or default branch have been changed. Recheck
remote refs immediately before publication because another teammate may push first.

The source/artifact publication candidate scan found no email addresses, private
keys, or common credential-token patterns in candidate text files. `.env`, runtime
SQLite databases, citizen uploads, caches, old venvs, node_modules, build output,
raw data archives, machine package inventories and private reference inputs are
ignored. The staged-file audit confirmed these exclusions across 526 files before commit.
All original notebook/artifact blobs matched (excluding ignored .DS_Store metadata).
Pattern scanning is not a guarantee about arbitrary binary contents; joblib files
are preserved research artifacts, not treated as executable validation inputs from
untrusted parties.

Largest model is approximately 5.9 MiB, below GitHub's normal file limit; Git LFS
was not added. Essential trained artifacts and metadata are included. Raw data
remains local and must be acquired using DATASET_GUIDE.md for a fresh clone.
Published dataset metadata records noncommercial/share-alike rainfall terms and
educational-use traffic restrictions. No broad redistribution license for all
trained derivatives was found; rights confirmation remains a publication concern.

## Changed files

- README.md: actual architecture, Mac/Windows setup, local URLs, configuration,
  model/data requirements, tests, troubleshooting and safe branch/PR workflow.
- requirements-backend.txt / requirements-test.txt: minimal pinned runtime/tests.
- requirements-serving.txt: uses minimal backend requirements rather than notebooks.
- requirements.txt: retains ML pins and adds the matching protobuf constraint.
- scripts/setup_mac.sh, setup_windows.ps1, run_mac.sh, run_windows.ps1: native local
  environments, validated prerequisites, fixed ports and UTF-8 mode.
- scripts/local_config.py / check_runtime.py: shared configuration and runtime checks.
- scripts/verify_runtime.py: current platform-labeled fresh-process evidence.
- frontend/package.json / pnpm-lock.yaml: pin pnpm with its metadata.
- frontend/vite.config.ts / src/api/client.ts: correct backend proxy and portable help.
- backend/config.py / auth.py: private configured password; empty config cannot log in.
- backend/api/predictions.py: HTTP 503 with guidance for missing historical datasets.
- backend/services/prediction_service.py: use platform-neutral integration reports.
- scripts/package_complete.py / package_delivery.py: optional references use local
  reference_inputs, not developer-specific Windows paths.
- .gitignore / .gitattributes: private/runtime exclusions and cross-platform line endings.
- reports/integration: refreshed measured evidence. Legacy Windows inference reports
  are refreshed locally for existing test compatibility and remain ignored by Git.
- reports/cross-platform: HTTP results, test summaries, preservation hashes and image.

## Limits and next steps

Native Windows execution is **not verified** in this macOS session. Windows scripts
have been reviewed for PowerShell path/argument handling; tzdata and UTF-8 mode are
included. Run setup, verification and tests on Windows before claiming Windows QA.
There is no frontend unit-test runner in the supplied package; build and browser
checks were used. Current model limitations and API approval restrictions remain
unchanged. Missing providers or historical datasets are not replaced by fake data.

The development servers were started at http://127.0.0.1:5173 and
http://127.0.0.1:8001 (API docs at /docs). Restart using the documented scripts if
the terminal sessions end. The local SQLite workspace stays private and is not
part of the new Git commit.

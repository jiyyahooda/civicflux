# Targeted CivicFlux cleanup and workflow verification

Completed locally on macOS, 27 October 2026. GitHub work remains paused. No commit or push, model changes, retraining, map-provider changes or live demonstration inventory were made.

## Requested changes

- Main navigation now uses text labels only, including the admin tabs. Open reports is absent from navigation. Existing report APIs, records, image URLs and the reusable report card are retained. Public users can track a full report ID from Report a problem; private contact and internal notes remain excluded.
- The whole top-left logo scales to 1.045 on hover/focus. Civic becomes orange (#e8772e), Flux green (#24945f). Icon and text move together. The transition respects reduced motion; other palette/font/scene styling is preserved.
- Decorative page subtitles, the navigation product slogan and decorative footer wording were removed. The existing welcome scene and animation are unchanged.
- Overview places its existing map immediately after the Overview content header. Recommendations remain without Why this appears. Published references are removed here. Travel notices remain without the Sources and freshness dropdown. Weather/air sections remain, and the 14-day outlook is the last Overview panel.
- City map retains modes, pins, controls and side panels, with its duplicate reference section removed.
- Infrastructure retains the source PDF, budget reconciliation, roads, basins, transport/workforce tables and operational data. Only the specifically requested extra geometry/workforce/planning explanations and recommendation dropdowns were removed. Underlying reference metadata and integrity checks remain unchanged.
- Predictions starts with its nine assessment tools. The introductory Understand the conditions box and duplicate 14-day outlook are removed. There was no Suggestions component on this page to remove. Inference inputs, saved outputs, intervals, original adapters and authorized technical details remain.
- Planning mode controls are first. Duplicate reference/weather/travel panels and the first four-card resource summary are removed. Current inventory selection, edit/use-capacity controls, optimizer inputs/results/tables/meters, impact comparison and cascade functionality remain. Missing inventory never receives invented numbers.
- Generic scenario assets use natural labels such as Drainage area 2, Road connection 3, Pumping point 4 and Water supply point 5 in planning/results/graph display. The supplied references do not verify mappings to the synthetic graph. No hypothetical ID was renamed to a real road. Internal graph IDs, select values, optimization and reservation keys remain unchanged.
- The redundant Reason column was removed from the action table; actual weighted factor explanations remain.

## Upload investigation and fixes

A normal real PNG upload succeeded against the pre-existing multipart/storage interface in backend tests; the original reported failure could not be reproduced for that supported case. It would be inaccurate to claim a proven single production cause without the failing file or request.

Confirmed problems were: no pre-submit preview; no client file validation; a silently disabled submit button for missing/count-invalid images; strict MIME-header rejection even when a browser supplied a valid JPEG/PNG without a specific MIME; and unhandled storage permission/write errors. The transport already used FormData correctly without manually setting Content-Type, so its multipart boundary logic was preserved.

The form now previews selected images, rejects unsupported/empty/oversized files clearly, requires actual images, prevents simultaneous submissions using both a synchronous lock and disabled busy state, and clears success before a new attempt. It displays the exact success sentence only after the backend confirms the ID, status and saved photo references. Confirmation includes the initial status and full ID; ID tracking retrieves only the existing public allowlist.

The backend still decodes and verifies JPEG/PNG bytes, enforces 5 MB/20-million-pixel limits, removes metadata and uses generated filenames under the configured database's uploads folder. A missing/generic MIME is allowed only with a JPEG/PNG extension and successful actual image decoding. Disguised files still fail. Interrupted writes are removed, no complaint is created, and a useful 503 storage message replaces an opaque failure. Paths use pathlib and are portable; native Windows execution was not performed.

## Review workflow

Cards now show full ID and category in addition to location, image, dates, status, verification decision and public response. Existing officer assignments, independent completion evidence, private notes and audit forms remain. Background queue refresh retains prior data so an unchanged open editor is not needlessly removed while loading; a saved-review confirmation is retained by the parent queue.

Browser test on an isolated database: selected a real PNG -> saw preview -> submitted -> saw the exact success sentence, UUID and submitted status -> retrieved the public tracking card -> found the same report in admin Review reports -> updated verification, status and public reply -> reopened the queue and observed under_review and the persisted response. The stored image loaded with naturalWidth=160. No test report was inserted into the user's live database.

## Approval root cause and fixes

The previous frontend disabled approval until a current authorized pool, valid assignments for every selected action, selected actions and a 3-character note all existed. Missing live inventory and blank assignment/note fields therefore made the button unavailable, with no explanation beside it. This was not an authorization or solver failure and must not be solved by inventing inventory.

The UI now lists each missing prerequisite and each insufficient capacity, validates whole crew/worker/vehicle counts, and gives actionable feedback when approval is attempted. The button is usable when eligible; it is disabled only while loading/saving or when the exact plan/package is already approved. Rechecking a plan correctly credits its own reservation rather than treating its hold as another plan's usage. Success explicitly confirms internal approval and reservation, without dispatch.

The existing atomic SQLite transaction still validates authoritative saved-plan requirements, current/city inventory and unreserved funds/equipment/staff/crew-hours before writing decision, actor, time, status, hold and audit. Identical repeat approvals now return the existing reservation and decision with already_approved=true, without another decision/audit or resource hold. Revised packages retain capacity checking and replacement semantics. Release/change/defer/reject keep their existing history behavior. Scientific approval and real dispatch remain separate.

An isolated browser test generated a genuine CP-SAT plan and an exact-capacity disposable pool, filled all ten selected action packages and a note, then clicked approval. The UI showed success, zero remaining unreserved capacity and Internal plan already approved. Tests verify one identical retry retains the same reservation and history, release restores capacity, and simultaneous competing plans yield one success and one 409.

## Verification

- Complete backend suite: **103 passed, 1 warning, 7.16s**. Includes every saved assessment adapter, auth/privacy, mandatory/invalid image handling, actual image retrieval, persisted public status/response, storage rollback, capacity checks, idempotence and concurrency.
- Final TypeScript/Vite build: passed, **2.05s**, with the existing nonblocking large Three.js chunk warning.
- Browser DOM checks: zero main-navigation SVG icons; no Open reports tab; hovered logo matrix scale 1.045 and exact requested orange/green computed colours; map is the first element after Overview header; 14-day outlook is last; no duplicated Overview reference/Why/source dropdown; Predictions retains nine tool choices without intro/outlook.
- Original artifact/notebook SHA-256 verification: **273 checked, zero changed**.
- Evidence lives in `reports/targeted-cleanup/`. `upload-preview.png`, `review.png` and `approval.png` show clearly disposable test records from the isolated local copy. `navigation.png` and `overview-map.png` show the real local application.

## Remaining limits

No implementation blocker remains for supported JPEG/PNG uploads and eligible internal reservations under the tests above. Live approval still requires a real administrator-authorized current roster and sufficient capacity; none was fabricated. HEIC must be converted to JPEG/PNG. The original failing file/request remains unknown. Browser verification was macOS only; native Windows and external municipal dispatch were not tested. Models, reference data, existing animation and map implementation remain intact.

## Exact source/test files modified in this cleanup

- `frontend/src/App.tsx`
- `frontend/src/enhancements.css`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/CityMap.tsx`
- `frontend/src/pages/Predictions.tsx`
- `frontend/src/pages/Planning.tsx`
- `frontend/src/pages/ReportProblem.tsx`
- `frontend/src/pages/ReviewReports.tsx`
- `frontend/src/pages/OpenReports.tsx`
- `frontend/src/pages/ScenarioPlanning.tsx`
- `frontend/src/pages/Cascade.tsx`
- `frontend/src/components/CivicPanels.tsx`
- `frontend/src/components/DelhiReference.tsx`
- `frontend/src/components/OperationalResources.tsx`
- `frontend/src/components/ResourceAllocation.tsx`
- `frontend/src/components/CascadeGraph.tsx`
- `frontend/src/utils/assetLabel.ts`
- `backend/api/civic.py`
- `backend/api/resources.py`
- `tests/test_reference_and_resources.py`
- `tests/test_targeted_cleanup.py`
- `README.md`

Documentation/evidence added: `reports/TARGETED_UI_CLEANUP.md` and files under `reports/targeted-cleanup/`. Earlier uncommitted enhancements remain in the working tree.


## Follow-up: restored Planning control position

At the user's subsequent request, Current situation and What-if assessment were
returned below the inventory and supervisor review, above the selected mode content.
The top-position description above records the earlier cleanup, now superseded.
GitHub publication was subsequently authorized on the new branch
`codex/civicflux-ui-model-integration`.

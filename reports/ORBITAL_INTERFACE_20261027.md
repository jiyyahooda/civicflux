# CivicFlux orbital interface and CPCB setup

Completed 27 October 2026, Asia/Kolkata.

The previous splitting-buildings intro has been replaced by a real Three.js/WebGL scene: a reflective network sphere, orbital rings, curved connections, traveling points and a particle field. The visual is a decorative civic-network study, not a geographic map or an incident dataset. No fabricated station data are used in the artwork.

Cursor movement controls camera/scene parallax and lighting. Scroll progress changes the camera, ring positions, scale and three narrative chapters: Sense, Understand and Act. A direct entry button scrolls into the existing live dashboard. The scene loads on demand, caps pixel density, pauses expensive drawing when not visible, cleans up GPU resources and supports reduced motion. A CSS visual is available if WebGL cannot initialize.

The sidebar is removed. All seven page links now live in a sticky top navigation. On smaller screens they form a horizontal scrolling row; city selection, theme and account controls stay on the upper row. The revised city selector has a compact trigger, search, current-selection state, keyboard navigation, outside-click/Escape dismissal and a more-cities notice. It preserves the three verified city configurations.

Existing features from the previous work remain: current 14-day weather graph with a 2-day view, original model contracts, live IMD observations, separate CAMS estimates, locality complaint queues, admin login `admin / 001`, scenario controls, review restrictions and audit persistence. Original datasets, notebooks and model artifacts were not changed.

## CPCB setup

The complete beginner-to-integration instructions are in [CPCB_SETUP.md](../CPCB_SETUP.md). They cover registration, personal API-key generation, the existing OGD resource endpoint, expected fields, local `.env` configuration, safe command-line verification, backend restart, checking the local API, station mapping, source freshness, pollutant-unit verification, troubleshooting and future hosting.

`scripts/check_cpcb.py --city delhi` reads configuration server-side and reports validated station results without printing a key or key-bearing URL. Its missing-key branch was executed successfully and made no provider request. No personal key is available, so authenticated CPCB access remains unverified. Once validated responses exist, the source card now displays their reported pollutant values and publisher-unit labels.

## Validation

- TypeScript check and Vite production build pass.
- 15 targeted API tests passed: current outlook, observation source validation/CPCB missing-key handling, locality routing, feedback persistence and admin restrictions. Evidence: `windows/orbital-checks.xml`. The earlier full 34-test suite remains recorded in `windows/refinements-tests.xml`.
- Browser verified a real WebGL canvas with no fallback, cursor-driven CSS motion values, all three scroll chapters, city-search keyboard selection, top-navigation switching and the current forecast API for Chandigarh.
- At a 390 px viewport, the document fits without horizontal overflow. Navigation scrolls within its own row. Both theme styles remain supported.
- The 3D module is lazy loaded. Vite reports one size warning for that 542 KB minified module (about 137 KB gzip); the main dashboard does not statically import the Three.js scene.
- The normal application was started on `http://127.0.0.1:8000` and its health endpoint returned success. The isolated QA server uses port 8001 and a separate database, and is stopped after verification.
- `RESTART-CIVICFLUX.cmd` was tested successfully against the app instance started during this work. It verifies this workspace's Python executable and CivicFlux command before stopping/restarting that server. The normal application remains running on port 8000 for the user.
- Admin login `admin / 001` and logout were also verified on the restarted normal application, without creating complaints or scenarios in its database.

Screenshots are saved under `reports/windows/` with the `orbital-` prefix. The normal app can also be started with `START-CIVICFLUX.cmd` after a future reboot. Authentication and review permissions are unchanged by the visual redesign.

# CivicFlux UI refinement — 31 October 2026

Implemented in the existing local Desktop/CivicFlux frontend. No new framework, backend change, API/schema modification, data replacement, payment, SMS send, or deployment was part of this task.

## Architecture inspected
- App.tsx: page state navigation, public header, admin/civilian session state, login dialogs, role branching and responsive menu.
- AdminShell/AdminWelcome: existing admin navigation, assigned jurisdiction, entry animation and workspace heading.
- CivilianSession, CivilianProfile, GuestProfile: separate civilian cookies, SMS flow, profile tabs, browser-local guest state.
- ProductTour/catalog/tour.css: real targets, prerequisite navigation, offer/progress persistence, safe-save confirmation, spotlight, keyboard/focus handling, source/city conditions.
- Existing page panels: overview, reports/tracking, report review, city maps/layers, planning, decisions, predictions, infrastructure, budgets and data sources.
- Shared styling: main.tsx stylesheet order, portal.css tokens, public/admin themes, mobile breakpoints and reduced motion.

## Result
Profile is absent from the main navigation; all other tabs keep their existing order. The circular avatar is separate from navigation and aligned at the right of the header action group.

Guest menu: Civilian Login, Admin Login, Guest profile. Guest profile access is retained because this prototype already supports it. Civilian menu: name, Civilian account, Profile, Admin Login, Sign out. Administrator menu: Administrator, the actual first assigned locality and postal PIN where present, Sign out. A missing jurisdiction uses a neutral fallback. All actions call the previous session/login/logout flows; no frontend role grants were introduced.

AccountMenu uses a labelled menu trigger, aria-expanded/controls, focus on opening, Up/Down/Home/End navigation, Escape focus return, focus-leave/click-outside dismissal, and reduced-motion-aware animation.

OperationalPanel groups a workflow heading/description and its content. Report creation and tracking are separate panels; the admin review queue has its heading and existing record actions together. Existing operational panels across maps, planning, decisions, predictions, infrastructure, finances and civilian profile share 14px corners, a 1px border, surface background and responsive padding. No small-element card explosion was introduced.

Typography uses the existing Inter/system sans stack with shared page/section/panel/body/secondary tokens (26–32px page headings, 20–24px sections, 18px subsections, 15px body, 13–14px secondary/labels). Intro typography and signature graphics remain separate. Duplicate admin page headings were removed while keeping the shell heading.

The existing tour engine now receives five steps per role; it keeps Next, Back, Skip, Exit, Finish, topic jump, restart, saved progress, missing-target handling and safe-save guarding. Mobile navigation is opened only as a display prerequisite. The historical full feature inventory remains in ONBOARDING_COVERAGE.md. Existing offer tracking is retained to avoid replaying on every visit.

## Profile preservation
CivilianProfile.tsx, GuestProfile.tsx and their data/storage/API functions were not changed. Details, My complaints, Places & routes, Travel planner, contact fields, report IDs/statuses, map selection, saved routes and account controls remain intact. Guest access and complaint authentication behavior remain as they were when this refactor began.

## Files changed for this task
- frontend/src/App.tsx
- frontend/src/components/AccountMenu.tsx (new)
- frontend/src/components/AdminShell.tsx
- frontend/src/components/OperationalPanel.tsx (new)
- frontend/src/main.tsx
- frontend/src/product-refinements.css (new)
- frontend/src/pages/ReportProblem.tsx
- frontend/src/pages/ReviewReports.tsx
- frontend/src/tour/ProductTour.tsx
- frontend/src/tour/catalog.ts
- frontend/src/tour/catalog.test.mjs
- docs/ONBOARDING_COVERAGE.md
- docs/UI_REFINEMENT.md (this file)

Other pre-existing uncommitted files were not part of this UI task.

## Validation
- Frontend production build/TypeScript check passed. Vite retains its existing large FluxScene chunk advisory.
- All six concise-tour catalogue tests passed: role paths in all supported cities, restricted-page separation, report/decision coverage, IDs/progress parsing, declared targets, no automatic write prerequisites.
- All 22 existing civilian authentication and civic workflow regression tests passed with isolated test data and mocked delivery.
- No lint script or lint configuration exists in this frontend. git diff --check passed for the frontend.
- Chrome: verified signed-in civilian Profile access and all four profile tabs; arrow-key menu navigation; Escape returns focus; no Profile in main nav; dark report form and distinct tracking workflow.
- Chrome: completed public five-step path with Back, Skip, Finish and saved completed/skipped states; completed admin five-step path through real Review reports/Decisions pages without saving records.
- Chrome: actual admin login/assigned Connaught Place PIN 110001, role/location account display, admin logout. Registered civilian session remained independent.
- At 390×844: guest and admin account menus remained inside the viewport; document width matched viewport, mobile report panels fit, page heading measured 26px, hamburger showed existing navigation. Guest login options appeared in the avatar menu. Mobile tour opened the actual navigation, fit its popover inside the viewport, and exited with Escape. Temporary viewport override was reset.
- No reports were created, no photos captured, no budgets/resources saved, and no SMS requested during UI verification. Provider-dependent traffic/routing, camera delivery and real report writes were not retested end-to-end as part of this visual refactor.

Open http://127.0.0.1:5173/ for the local version. Avatar → Profile opens the existing civilian profile. Help / Take a tour → Full walkthrough or Restart from beginning starts the concise guide. Render has not been changed by this UI task.


## Follow-up: Admin Login placement
Admin Login has moved out of both guest and civilian header account menus into the public Overview footer only. It opens the same existing /admin/login flow. The concise tour text now describes this placement.

# City infra, maps, notifications and report receipts — 30 October 2026

Developed and validated locally on `codex/city-infra-navigation-alerts`, then prepared
for publication to `jiyyahooda/civicflux` main at the user’s subsequent request on
30 October 2026. No external mailbox creation or real confirmation email was performed.
Trained artifacts, notebooks, datasets, coordinate snapshots and budget formulas
are unchanged. A private SQLite backup was taken immediately before activation.

## Requirement checklist

| Requirement | Implementation and verified behaviour |
|---|---|
| Public Infrastructure → admin City infra | Removed from civilian navigation and guarded on all known infrastructure URL aliases. `/api/admin/city-infra`, the old reference JSON route and PDF require authentication. Public context no longer embeds the reference. City-wide reference is identical for all PINs within that city; reports, photos, planning budgets and equipment stay PIN-scoped. Delhi's original budget/drain/road tables are preserved. Chennai and Chandigarh show their own verified source coverage, not renamed Delhi data. |
| Chandigarh tabs disappear | The civilian header is now visible on every interior page; its old scroll-only visibility applied even to short pages, making navigation unreachable. Overview keeps the original scroll-in behaviour. Admin navigation stays visible and wraps all seven tabs on narrow screens. A page error boundary preserves admin navigation if a content component fails. |
| Water / infrastructure maps | Provider references are available while readings load; water and infrastructure modes explicitly explain missing surveyed topology and verified-report filtering. Municipal scenario mode shows hypothetical assets and network links, with functioning layer/asset controls, legends, details and retries. Base-tile failures have an explicit retry. Retry refreshes provider data as well as remounting the map. |
| Chennai / Chandigarh | Correct city IDs and source references are retained; non-Delhi scenario exports now carry the correct city ID and filename and remove Delhi geographic source claims. Report forms now include all registered directory-sourced Chennai PINs. Weather accepts India's equivalent Asia/Calcutta and Asia/Kolkata timezone names without accepting a different location. City changes reset incompatible selections/results. |
| Contrast | Solid burgundy/accent buttons, selected controls, badges, map symbols and cards use the correct contrasting text token; burgundy is white-text in light mode and yellow surfaces retain dark text in dark mode. Focus, hover and disabled primary states remain readable. Native option styling remains OS-dependent. |
| Predictions | Infrastructure anomaly is removed from tool tiles and the Predictions model-detail inventory. Saved artifacts, the backend anomaly implementation and unrelated models remain intact. Historical Delhi models are still labelled as benchmarks; they are not claimed to predict Chennai/Chandigarh. |
| Notifications | Civilian bell with unread indicator, source/city/time, individual read, mark-all-read, refresh, empty/loading/error states. Read status is stored per city in anonymous local storage. Source event IDs use observation/publication/status timestamps, not polling time. Report IDs are remembered only after submission or explicit tracking. Threshold inputs and official notices use supported real sources. No browser notification permission or background delivery is claimed. |
| Report confirmation email | Required validated reporter email retained. Persistent queued/sending/sent/failed/rate-limited attempt states, attempt counts and provider-acceptance/failure fields added. A refusal or invalid sender header cannot turn an already-saved report into a failed submission. Duplicate submissions do not send a second receipt. Receipt includes ID, time, location/category and tracking guidance, explicitly stating that no government complaint has been filed. |

## What passed

- Full Python suite: **191 tests passed**. Tests cover role denial, city-wide equality
  across PINs (including a Chandigarh PIN without coordinates), all-three-city report
  registration, source-timestamp notification identity, no cross-city alerts, report
  tracking privacy, SMTP refusal, message-construction failure and acceptance tracking.
- TypeScript/Vite production build passed. Existing Three.js large-chunk warning remains.
- 307 artifact/data/config snapshot hashes match the pre-change baseline.
- Browser: public navigation has no Infrastructure; Chandigarh/Chennai water and
  infrastructure modes keep city-correct maps and usable tabs; anomaly is absent from
  Predictions. An actual imported Delhi notice generated one unread notification;
  individual read persisted after reload and polling refresh did not duplicate it.
- Browser: a clearly labelled LOCAL QA report with a generated QA photo was submitted
  only into a disposable preview database with SMTP credentials explicitly disabled.
  Its receipt showed saved status plus email failure, tracking retrieved the saved
  photo/report, and one report notification appeared. Mark-all-read cleared its unread state.
- Browser: all seven Chandigarh admin tabs fit at 375 px, light and dark themes; its
  illustrative water layer rendered 24 water/pump/facility markers. Native Windows
  execution was not available on this Mac; Windows entry points are preserved.

## Live data limitations

No surveyed water-pipe or pumping topology has been registered for these cities.
Illustrative networks are explicitly hypothetical and do not locate anonymous saved
benchmark networks in a real city. Unknown PIN coordinates remain unavailable rather
than falling back to a city centre. Provider outages, missing CPCB credentials and
Google key restrictions are reported separately. The earlier Overpass HTTP 406 and
OpenCity 2015 inundation-zone HTTP 404 remain unavailable; no dataset was replaced.

## Review the app

1. Open http://127.0.0.1:5173/ (development) or http://127.0.0.1:8001/ (built app).
   Refresh an already-open tab after the update.
2. As a civilian, open City map, switch between Chennai and Chandigarh, and use
   Water supply / Infrastructure alerts. Navigation must remain visible.
3. Open the bell. Existing imported notices or configured threshold events appear
   only when the underlying source supplies them. Use read actions and reload.
4. Sign in with username `admin` and an existing six-digit PIN, e.g. `110001`,
   `160017` or `600020`. Open **City infra**, then switch to another tab.
   The reference is city-wide, while operational queues remain PIN-specific.
5. Predictions must not contain “Unusual sensor readings” / infrastructure anomaly.
6. A real report needs an actual issue photo. Keep the tracking ID even if email
   is unavailable. Do not send fabricated QA incidents into your operational database.

## Dedicated sender setup — user action required

No sender mailbox or SMTP credential is configured here. Choose a dedicated mailbox
you actually own, or create one yourself through its provider; no address has been
invented or claimed to exist. A free personal Gmail account can be used for low-volume
SMTP receipts if that account permits App Passwords. Google requires 2-Step Verification
for App Passwords; managed accounts, security-key-only verification or Advanced Protection
may make that option unavailable. Google documents a personal Gmail limit above 500 emails
per day; anti-abuse limits can apply sooner. This is not a delivery guarantee.

Official requirements checked on 30 October 2026:
- https://support.google.com/accounts/answer/185833
- https://support.google.com/mail/answer/22839

After you create/verify the owned mailbox and enable its permitted authentication,
place these settings only in your private `.env`, then restart the backend:

```dotenv
SMTP_USER=<YOUR_OWNED_GMAIL_MAILBOX>
SMTP_PASS=<YOUR_16_CHARACTER_APP_PASSWORD_WITHOUT_SPACES>
SMTP_PORT=465
CIVICFLUX_ALERT_RAIN_MM=10
CIVICFLUX_ALERT_TEMP_C=40
CIVICFLUX_ALERT_US_AQI=151
```

Port 465 uses authenticated SSL; 587 uses STARTTLS with certificate validation.
Do not use your normal account password. Credentials never belong in VITE variables,
Git, browser forms or frontend bundles. Existing per-IP/per-recipient receipt limits
(10/IP/hour and 3/recipient/hour) remain in place.

`queued` is persisted before the immediate delivery attempt; `sending` means it is
in progress. `sent` means the SMTP provider accepted the message, not confirmed inbox
receipt. `failed` and `rate_limited` preserve the saved report. There is no invented
background queue worker or automatic retry that might duplicate a previously accepted
message. Inbox receipt requires a separate real-mailbox verification after configuration.

## Windows startup

Install native 64-bit Python 3.13, Node 24 and Corepack as described in README.
Extract the project fully, open its folder and double-click `START-CIVICFLUX.cmd`.
The launcher creates the Windows environment and builds the frontend. Open the address
it prints (normally http://127.0.0.1:8001/) and keep the server terminal open.
Do not copy the Mac `.venv` to Windows. `.env.example` contains placeholders only.

For development use two PowerShell terminals in the project folder:

```powershell
.\.venv-windows\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
cd frontend
corepack pnpm dev
```

The `cd frontend` / `corepack pnpm dev` commands run in the second terminal.

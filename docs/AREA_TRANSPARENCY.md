# Postal-area transparency and navigation update

Applied to the final CivicFlux source only. The separate CivicFlux-Round1 folder and
Render deployment were not changed or republished by this update.

- **Monetary history** is available in public and admin navigation. Select a PIN and
  fiscal year. Allocation comes from recorded locality funding; expenditure comes
  from a separate authenticated payment ledger. Reservations are shown separately.
  Neither city-wide historical budgets nor scenario spending become actual expenses.
  Missing allocation/spending is “Not recorded”; the app cannot independently prove
  the completeness of municipal accounts or prevent corruption.
- An area admin can attest a payment using its allocation, amount, date and invoice/
  payment reference. Entries are audited, reject overspending and foreign-area writes,
  and identical retries do not book the same entry twice. No example expenses were
  inserted into the real database. Payment evidence is kept private; public totals
  and counts are scoped to the selected PIN and fiscal year.
- Both public and admin navigation collapse to hamburger menus at 760 px and below.
  Desktop navigation stays horizontal. Menus close on navigation and Escape.
- The introductory desktop page has a top-edge Menu/hover target that reveals the
  header; it also supports keyboard focus. Phone headers remain visible immediately.
- Light-theme burgundy hover surfaces use white text, including nested icons/labels.
- Public Water supply / Infrastructure alerts now open a **read-only illustrative
  network** with 24 / 40 nodes respectively. The observations mode remains available.
  Asset selection is available through markers or an accessible select control;
  selection zooms the map and opens actual details. Scoped admin geography remains
  protected. Public graphs do not expose inventories, funding, surveyed pipes or real
  faults; they show an explicitly hypothetical research topology. Source datasets and
  trained artifacts were not modified.
- Public visitors are asked for location via the browser Geolocation API on opening.
  Browser permission settings determine whether a prompt appears. The app sends the
  requested coordinates to its own backend only, without storing them or forwarding
  them to a reverse-geocoding vendor. It suggests the nearest registered postal
  reference only within 5 km and only with accuracy within 1.5 km; this is labelled
  approximate, not a verified boundary. Outside coverage or denied permission requires
  manual city/PIN selection. Notifications stay off until a PIN is selected, then use
  only that PIN's notices/tracked reports and weather/air grids at its reference point.
  Regional grid estimates still do not establish neighbourhood measurements. Read
  status is stored separately for each city/PIN; old citywide alerts are not reused.
- The complaint receipt now includes title, city, status, ID, category, postal location,
  full description and submission time. **Gmail setup is deferred at the user's request.**
  No supplied account password was saved, no mailbox security settings were changed,
  and no real email was sent. Configure the owned sender and a Google App Password in
  private environment variables when ready; keep credentials out of Git and Vite.

## Verification

- Frontend production build, all 8 tour catalog tests and all 199 backend tests passed.
- Backend tests cover area aggregates, missing vs zero, anonymous/foreign-area denial,
  overspending, duplicate-payment retry, approximate-location bounds, PIN-only alerts,
  real receipt content and all three cities' public network isolation.
- Browser: public water layer rendered 24 nodes; infrastructure rendered 40. Selecting
  an asset displayed its actual details. Phone public/admin menus were hidden until
  opened, closed after selecting a tab, and had no horizontal overflow at 375×812.
  At 1440×900, admin navigation remained horizontal with its hamburger hidden.
- Location permission was not granted in browser testing; manual PIN fallback was
  exercised. No test spending, complaint or scenario was saved to the real database.
- Original local database backup: `/tmp/civicflux-before-area-updates.sqlite3`.

Open http://127.0.0.1:5173/ and refresh. Choose your area, then Monetary history or
City map → Water supply / Infrastructure alerts. On a phone, open the hamburger first.
